import pytest

from app.queue import redis_client


class FakeAsyncRedis:
    async def ping(self):
        return True

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_ping_with_fake_redis(monkeypatch):
    # Ensure clean state
    await redis_client.close()

    # Inject fake client
    monkeypatch.setattr(redis_client, "_client", FakeAsyncRedis())

    assert await redis_client.ping() is True

    # Close should reset client to None
    await redis_client.close()
    assert redis_client._client is None
