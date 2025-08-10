import json
import os
import time
from pathlib import Path

import pytest

from app.images.cache import CacheConfig, ImageCache


@pytest.mark.asyncio
async def test_enforce_quota_purges_oldest(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(
        cache_dir=str(cache_dir),
        ttl_seconds=3600,
        compression=False,
        max_cache_bytes=150,
    )
    cache = ImageCache(cfg)

    # create three small files of 100 bytes each
    urls = [f"https://ex.com/{i}.jpg" for i in range(3)]
    srcs = []
    for i in range(3):
        p = tmp_path / f"src{i}.jpg"
        p.write_bytes(os.urandom(100))
        srcs.append(p)

    await cache.put(urls[0], str(srcs[0]))
    time.sleep(0.01)
    await cache.put(urls[1], str(srcs[1]))
    time.sleep(0.01)
    await cache.put(urls[2], str(srcs[2]))

    removed = await cache.enforce_quota()
    # total 300 > 150 => need to purge at least two oldest
    assert removed >= 2

    # newest should remain
    got3 = await cache.get(urls[2])
    assert got3 is not None


@pytest.mark.asyncio
async def test_cleanup_orphans(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(cache_dir=str(cache_dir), ttl_seconds=3600, compression=False)
    cache = ImageCache(cfg)

    # create orphan data
    data = Path(cache_dir) / "orphan.jpg"
    meta = Path(cache_dir) / "orphan.json"
    tmpf = Path(cache_dir) / "x.tmp"
    cache_dir.mkdir(parents=True, exist_ok=True)
    data.write_bytes(os.urandom(10))
    meta.write_text("{ invalid json")
    tmpf.write_text("tmp")

    removed = await cache.cleanup_orphans()
    assert removed >= 2  # data + tmp + invalid meta likely


@pytest.mark.asyncio
async def test_optimize_runs_all(tmp_path):
    cache_dir = tmp_path / "cache"
    cfg = CacheConfig(cache_dir=str(cache_dir), ttl_seconds=1, compression=False, max_cache_bytes=1)
    cache = ImageCache(cfg)

    # create one entry then force expire by touching meta
    src = tmp_path / "src.jpg"
    src.write_bytes(os.urandom(10))
    url = "https://ex.com/z.jpg"
    entry = await cache.put(url, str(src))
    meta_path = Path(entry.data_path).with_suffix(".json")
    meta_data = json.loads(meta_path.read_text())
    meta_data["created_at"] = time.time() - 99999
    meta_path.write_text(json.dumps(meta_data))

    stats = await cache.optimize()
    assert {"expired", "orphans", "purged"}.issubset(stats.keys())
