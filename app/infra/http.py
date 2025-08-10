from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(30.0)


@contextlib.asynccontextmanager
async def get_async_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        yield client
