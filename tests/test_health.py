import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_root():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("message") == "GF-25 v3 is running"


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "gf-25-v3"
        assert data["version"] == app.version
