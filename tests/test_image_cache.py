import json
import os
import time
from pathlib import Path

import pytest

from app.images.cache import CacheConfig, ImageCache


@pytest.mark.asyncio
async def test_cache_put_get_uncompressed(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(cache_dir=str(cache_dir), ttl_seconds=60, compression=False)
    cache = ImageCache(cfg)

    # create a source file
    src = tmp_path / "img.jpg"
    src.write_bytes(b"hello-world")

    url = "https://example.com/image.jpg"
    entry = await cache.put(url, str(src))
    assert Path(entry.data_path).exists()
    assert entry.compressed is False

    got = await cache.get(url)
    assert got is not None
    assert got.key == entry.key
    assert got.data_path == entry.data_path


@pytest.mark.asyncio
async def test_cache_put_get_compressed(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(cache_dir=str(cache_dir), ttl_seconds=60, compression=True)
    cache = ImageCache(cfg)

    src = tmp_path / "img2.jpg"
    src.write_bytes(b"abc" * 100)

    url = "https://example.com/image2.jpg"
    entry = await cache.put(url, str(src))
    assert Path(entry.data_path).suffix.endswith("gz")
    assert entry.compressed is True

    got = await cache.get(url)
    assert got is not None
    assert got.key == entry.key


@pytest.mark.asyncio
async def test_cache_ttl_expiration_and_cleanup(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(cache_dir=str(cache_dir), ttl_seconds=60, compression=False)
    cache = ImageCache(cfg)

    src = tmp_path / "img3.jpg"
    src.write_bytes(os.urandom(32))

    url = "https://example.com/image3.jpg"
    entry = await cache.put(url, str(src))

    # mutate meta to force expiration
    meta_path = Path(entry.data_path).with_suffix(".json")
    data = json.loads(Path(meta_path).read_text())
    data["created_at"] = time.time() - 999999
    Path(meta_path).write_text(json.dumps(data))

    # get should miss and cleanup_expired should remove files
    got = await cache.get(url)
    assert got is None

    removed = await cache.cleanup_expired()
    assert removed >= 1

    assert not Path(entry.data_path).exists()
    assert not meta_path.exists()
