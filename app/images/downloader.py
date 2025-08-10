from __future__ import annotations

import asyncio
import logging

import httpx
from pydantic import BaseModel, Field, HttpUrl

try:  # optional retries
    from tenacity import (  # type: ignore
        AsyncRetrying,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential_jitter,
    )
except Exception:  # pragma: no cover
    AsyncRetrying = None  # type: ignore
    retry_if_exception_type = None  # type: ignore
    stop_after_attempt = None  # type: ignore
    wait_exponential_jitter = None  # type: ignore


class DownloadConfig(BaseModel):
    timeout_seconds: float = Field(default=60.0, description="HTTP timeout")
    max_retries: int = Field(default=3, ge=0, description="Max retries per URL")
    chunk_size: int = Field(default=1024 * 128, ge=1024, description="Stream chunk size")
    user_agent: str | None = Field(default=None, description="Optional custom UA header")


class DownloadRequest(BaseModel):
    primary_url: HttpUrl = Field(description="Primary image URL")
    fallback_url: HttpUrl | None = Field(default=None, description="Optional fallback image URL")


class DownloadResult(BaseModel):
    path: str = Field(description="Destination file path")
    bytes_written: int = Field(ge=0, description="Total bytes written")
    from_fallback: bool = Field(description="Whether fallback URL was used")


class ImageDownloader:
    def __init__(self, cfg: DownloadConfig, *, logger: logging.Logger | None = None) -> None:
        self.cfg = cfg
        self.log = logger or logging.getLogger(__name__)

    async def download_to_path(self, req: DownloadRequest, dest_path: str) -> DownloadResult:
        headers = {"Accept": "image/*"}
        if self.cfg.user_agent:
            headers["User-Agent"] = self.cfg.user_agent

        async with httpx.AsyncClient(timeout=self.cfg.timeout_seconds, headers=headers) as client:
            # try primary first with retries
            ok, written = await self._try_url(client, str(req.primary_url), dest_path)
            if ok:
                return DownloadResult(path=dest_path, bytes_written=written, from_fallback=False)
            # fallback if provided
            if req.fallback_url is not None:
                ok_fb, written_fb = await self._try_url(client, str(req.fallback_url), dest_path)
                if ok_fb:
                    return DownloadResult(path=dest_path, bytes_written=written_fb, from_fallback=True)

            raise RuntimeError("image download failed for both primary and fallback")

    async def _try_url(self, client: httpx.AsyncClient, url: str, dest_path: str) -> tuple[bool, int]:
        # Tenacity path
        if AsyncRetrying is not None and self.cfg.max_retries > 0:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(self.cfg.max_retries),
                wait=wait_exponential_jitter(initial=0.2, max=2.0),
                retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
            ):
                with attempt:
                    ok, written = await self._download_once(client, url, dest_path)
                    if ok:
                        return True, written
            return False, 0

        # Fallback retry
        attempts = max(1, self.cfg.max_retries or 1)
        for i in range(attempts):
            try:
                ok, written = await self._download_once(client, url, dest_path)
                if ok:
                    return True, written
            except (httpx.ConnectError, httpx.ReadTimeout) as ex:  # pragma: no cover
                self.log.warning("network error on %s attempt %d/%d: %s", url, i + 1, attempts, ex)
            await asyncio.sleep(min(2 ** i * 0.2, 2.0))
        return False, 0

    async def _download_once(self, client: httpx.AsyncClient, url: str, dest_path: str) -> tuple[bool, int]:
        self.log.info("downloading %s -> %s", url, dest_path)
        bytes_written = 0
        # Stream and write using thread to avoid sync I/O in event loop
        async with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                self.log.warning("non-200 status %s for %s", resp.status_code, url)
                return False, 0

            # Open file synchronously in a thread
            loop = asyncio.get_running_loop()

            def _write_chunk(chunk: bytes) -> None:
                with open(dest_path, "ab") as f:
                    f.write(chunk)

            # ensure file is empty before writing
            await loop.run_in_executor(None, self._truncate_file, dest_path)

            async for chunk in resp.aiter_bytes(self.cfg.chunk_size):
                if not chunk:
                    continue
                await loop.run_in_executor(None, _write_chunk, chunk)
                bytes_written += len(chunk)

        return True, bytes_written

    @staticmethod
    def _truncate_file(path: str) -> None:
        with open(path, "wb") as f:
            f.truncate(0)
