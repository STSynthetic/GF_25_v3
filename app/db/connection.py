from __future__ import annotations

import os

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DbSettings(BaseModel):
    url: str = Field(description="SQLAlchemy async database URL (e.g., postgresql+asyncpg://...)")
    pool_size: int = Field(default=10, ge=1, description="Base pool size for DB connections")
    max_overflow: int = Field(
        default=20,
        ge=0,
        description="Max overflow connections beyond pool_size",
    )
    echo: bool = Field(default=False, description="Enable SQL echo for debugging")


_engine: AsyncEngine | None = None
_Session: async_sessionmaker[AsyncSession] | None = None


def load_settings() -> DbSettings:
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    echo = os.getenv("DB_ECHO", "false").lower() == "true"
    return DbSettings(url=url, pool_size=pool_size, max_overflow=max_overflow, echo=echo)


async def get_engine() -> AsyncEngine:
    global _engine, _Session
    if _engine is None:
        cfg = load_settings()
        if cfg.url.startswith("sqlite+aiosqlite"):
            # SQLite aiosqlite does not use pool params; pass minimal options
            _engine = create_async_engine(
                cfg.url,
                echo=cfg.echo,
            )
        else:
            _engine = create_async_engine(
                cfg.url,
                echo=cfg.echo,
                pool_size=cfg.pool_size,
                max_overflow=cfg.max_overflow,
                pool_pre_ping=True,
            )
        _Session = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _Session is None:
        raise RuntimeError("Engine not initialized. Call get_engine() first.")
    return _Session


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
