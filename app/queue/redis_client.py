from __future__ import annotations

import os

from pydantic import BaseModel, Field
from redis.asyncio import Redis


class RedisConfig(BaseModel):
    """Configuration for Redis connection pooling."""

    url: str = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="Redis URL, including db index",
    )
    decode_responses: bool = Field(default=True, description="Decode responses as str")
    max_connections: int = Field(default=100, ge=1, description="Pool max connections")
    socket_timeout: float = Field(default=5.0, ge=0.1, description="Socket timeout (s)")
    socket_connect_timeout: float = Field(
        default=2.0, ge=0.1, description="Socket connect timeout (s)"
    )


_client: Redis | None = None
_config: RedisConfig | None = None


def get_config() -> RedisConfig:
    global _config
    if _config is None:
        _config = RedisConfig()
    return _config


async def get_client() -> Redis:
    """Get a singleton pooled async Redis client."""
    global _client
    if _client is None:
        cfg = get_config()
        _client = Redis.from_url(
            cfg.url,
            decode_responses=cfg.decode_responses,
            max_connections=cfg.max_connections,
            socket_timeout=cfg.socket_timeout,
            socket_connect_timeout=cfg.socket_connect_timeout,
        )
    return _client


async def ping() -> bool:
    """Ping Redis, returning True if reachable."""
    client = await get_client()
    try:
        res = await client.ping()
        return bool(res)
    except Exception:
        return False


async def close() -> None:
    """Close the global client (used by tests)."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
