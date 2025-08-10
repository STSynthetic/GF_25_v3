import pytest
from sqlalchemy import text

from app.db import schema
from app.db.connection import dispose_engine, get_engine, get_sessionmaker


@pytest.mark.asyncio
async def test_engine_creation_sqlite_aiosqlite(monkeypatch):
    # Ensure sqlite+aiosqlite is used for a self-contained test
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    engine = await get_engine()
    assert engine is not None

    # Create tables using async engine
    async with engine.begin() as conn:
        await conn.run_sync(schema.metadata.create_all)

    # Verify basic statement works
    async with engine.connect() as conn:
        result = await conn.execute(text("select 1"))
        assert result.scalar_one() == 1

    # Sessionmaker should be initialized
    Session = get_sessionmaker()
    async with Session() as session:
        result = await session.execute(text("select 2"))
        assert result.scalar_one() == 2

    await dispose_engine()
