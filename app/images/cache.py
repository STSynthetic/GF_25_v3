from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    cache_dir: str = Field(description="Directory for cached images")
    ttl_seconds: int = Field(default=24 * 3600, ge=1, description="Time-to-live for cache entries")
    compression: bool = Field(default=False, description="Whether to gzip compress cached images")


class CacheEntry(BaseModel):
    key: str = Field(description="Cache key derived from URL")
    data_path: str = Field(description="Path to the cached file (may be .gz if compressed)")
    created_at: float = Field(ge=0, description="Unix timestamp when cached")
    ttl_seconds: int = Field(ge=1, description="TTL used when cached")
    compressed: bool = Field(description="True if data_path is gzip compressed")
    size_bytes: int = Field(ge=0, description="Size of the cached payload on disk")


@dataclass
class _Paths:
    data: Path
    meta: Path


class ImageCache:
    def __init__(self, cfg: CacheConfig) -> None:
        self.cfg = cfg
        Path(self.cfg.cache_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:40]

    def _paths_for(self, key: str, compressed: bool) -> _Paths:
        base = Path(self.cfg.cache_dir) / key
        data = base.with_suffix(".jpg.gz" if compressed else ".jpg")
        meta = base.with_suffix(".json")
        return _Paths(data=data, meta=meta)

    async def get(self, url: str) -> CacheEntry | None:
        key = self._key(url)
        # try compressed then uncompressed
        for compressed in (self.cfg.compression, not self.cfg.compression):
            paths = self._paths_for(key, compressed)
            if not paths.data.exists() or not paths.meta.exists():
                continue
            entry = await self._read_meta(paths)
            if entry is None:
                continue
            if self._is_expired(entry):
                # Do not remove here; allow cleanup_expired() to handle deletion
                continue
            return entry
        return None

    async def put(self, url: str, src_path: str) -> CacheEntry:
        key = self._key(url)
        compressed = self.cfg.compression
        paths = self._paths_for(key, compressed)

        # ensure directory
        Path(self.cfg.cache_dir).mkdir(parents=True, exist_ok=True)

        # write data
        if compressed:
            await self._gzip_copy(src_path, str(paths.data))
        else:
            await self._atomic_copy(src_path, str(paths.data))

        size = paths.data.stat().st_size if paths.data.exists() else 0
        entry = CacheEntry(
            key=key,
            data_path=str(paths.data),
            created_at=time.time(),
            ttl_seconds=self.cfg.ttl_seconds,
            compressed=compressed,
            size_bytes=size,
        )
        await self._write_meta(paths, entry)
        return entry

    async def cleanup_expired(self) -> int:
        removed = 0
        base = Path(self.cfg.cache_dir)
        for meta_path in base.glob("*.json"):
            try:
                entry = await self._read_meta(_Paths(data=Path(""), meta=meta_path))
            except Exception:
                continue
            if entry is None:
                continue
            paths = self._paths_for(entry.key, entry.compressed)
            if self._is_expired(entry):
                await self._remove(paths)
                removed += 1
        return removed

    def _is_expired(self, entry: CacheEntry) -> bool:
        return (entry.created_at + entry.ttl_seconds) < time.time()

    async def _atomic_copy(self, src: str, dst: str) -> None:
        loop = asyncio.get_running_loop()
        tmp = f"{dst}.tmp"

        def _copy():
            Path(tmp).unlink(missing_ok=True)
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)

        await loop.run_in_executor(None, _copy)

    async def _gzip_copy(self, src: str, dst: str) -> None:
        loop = asyncio.get_running_loop()
        tmp = f"{dst}.tmp"

        def _copy_gz():
            Path(tmp).unlink(missing_ok=True)
            with open(src, "rb") as f_in, gzip.open(tmp, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.replace(tmp, dst)

        await loop.run_in_executor(None, _copy_gz)

    async def _write_meta(self, paths: _Paths, entry: CacheEntry) -> None:
        loop = asyncio.get_running_loop()
        tmp = f"{paths.meta}.tmp"
        payload = entry.model_dump()

        def _write():
            Path(tmp).unlink(missing_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp, paths.meta)

        await loop.run_in_executor(None, _write)

    async def _read_meta(self, paths: _Paths) -> CacheEntry | None:
        loop = asyncio.get_running_loop()

        def _read() -> CacheEntry | None:
            if not paths.meta.exists():
                return None
            with open(paths.meta, encoding="utf-8") as f:
                data = json.load(f)
                return CacheEntry(**data)

        return await loop.run_in_executor(None, _read)

    async def _remove(self, paths: _Paths) -> None:
        loop = asyncio.get_running_loop()

        def _rm():
            Path(paths.data).unlink(missing_ok=True)
            Path(paths.meta).unlink(missing_ok=True)

        await loop.run_in_executor(None, _rm)
