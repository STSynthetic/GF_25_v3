import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.images.downloader import DownloadConfig, DownloadRequest, ImageDownloader


class FakeStreamResponse:
    def __init__(self, status_code: int, chunks: list[bytes]) -> None:
        self.status_code = status_code
        self._chunks = chunks

    async def __aenter__(self):  # pragma: no cover
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        return False

    async def aiter_bytes(self, chunk_size: int) -> AsyncIterator[bytes]:
        for c in self._chunks:
            await asyncio.sleep(0)
            yield c


class FakeAsyncClient:
    def __init__(self, timeout: float, headers: dict[str, str]) -> None:
        self.timeout = timeout
        self.headers = headers
        self.calls: list[tuple[str, str]] = []
        # control behavior
        self.map: dict[str, tuple[int, list[bytes]]] = {}

    async def aclose(self) -> None:  # pragma: no cover
        return None

    def stream(self, method: str, url: str, **kwargs: Any) -> FakeStreamResponse:
        self.calls.append((method, url))
        status, chunks = self.map.get(url, (404, []))
        return FakeStreamResponse(status, chunks)


@pytest.mark.asyncio
async def test_primary_success(monkeypatch, tmp_path):
    import app.images.downloader as dl

    monkeypatch.setattr(dl, "AsyncRetrying", None)

    client = FakeAsyncClient(timeout=1.0, headers={})
    client.map["https://primary/img.jpg"] = (200, [b"abc", b"defgh"])  # total 8 bytes

    def factory(timeout: float, headers: dict[str, str]):
        return client

    monkeypatch.setattr(dl.httpx, "AsyncClient", factory)

    cfg = DownloadConfig(timeout_seconds=5.0, max_retries=1)
    d = ImageDownloader(cfg)

    dest = tmp_path / "out.jpg"
    req = DownloadRequest(primary_url="https://primary/img.jpg")
    res = await d.download_to_path(req, str(dest))

    assert res.bytes_written == 8
    assert res.from_fallback is False
    assert dest.read_bytes() == b"abcdefgh"


@pytest.mark.asyncio
async def test_fallback_on_primary_failure(monkeypatch, tmp_path):
    import app.images.downloader as dl

    monkeypatch.setattr(dl, "AsyncRetrying", None)

    client = FakeAsyncClient(timeout=1.0, headers={})
    client.map["https://primary/broken.jpg"] = (500, [])
    client.map["https://fallback/img.jpg"] = (200, [b"xy", b"z"])  # total 3 bytes

    def factory(timeout: float, headers: dict[str, str]):
        return client

    monkeypatch.setattr(dl.httpx, "AsyncClient", factory)

    cfg = DownloadConfig(timeout_seconds=5.0, max_retries=1)
    d = ImageDownloader(cfg)

    dest = tmp_path / "out2.jpg"
    req = DownloadRequest(primary_url="https://primary/broken.jpg", fallback_url="https://fallback/img.jpg")
    res = await d.download_to_path(req, str(dest))

    assert res.bytes_written == 3
    assert res.from_fallback is True
    assert dest.read_bytes() == b"xyz"


@pytest.mark.asyncio
async def test_both_fail_raises(monkeypatch, tmp_path):
    import app.images.downloader as dl

    monkeypatch.setattr(dl, "AsyncRetrying", None)

    client = FakeAsyncClient(timeout=1.0, headers={})
    client.map["https://primary/nope.jpg"] = (500, [])
    client.map["https://fallback/nope.jpg"] = (404, [])

    def factory(timeout: float, headers: dict[str, str]):
        return client

    monkeypatch.setattr(dl.httpx, "AsyncClient", factory)

    cfg = DownloadConfig(timeout_seconds=5.0, max_retries=1)
    d = ImageDownloader(cfg)

    dest = tmp_path / "out3.jpg"
    req = DownloadRequest(primary_url="https://primary/nope.jpg", fallback_url="https://fallback/nope.jpg")

    with pytest.raises(RuntimeError):
        await d.download_to_path(req, str(dest))
