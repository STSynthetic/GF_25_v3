import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_live_endpoint_ok():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_endpoint_true(monkeypatch):
    # Monkeypatch readiness checker to return True
    from app import models as models_mod

    async def _ready_true(*_args, **_kwargs):
        return True

    monkeypatch.setattr(models_mod, "check_ollama_ready", _ready_true)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/ready")
        assert resp.status_code == 200
        assert resp.json() == {"ready": "true"}


@pytest.mark.asyncio
async def test_ready_endpoint_false(monkeypatch):
    # Monkeypatch readiness checker to return False
    from app import models as models_mod

    async def _ready_false(*_args, **_kwargs):
        return False

    monkeypatch.setattr(models_mod, "check_ollama_ready", _ready_false)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/ready")
        assert resp.status_code == 200
        assert resp.json() == {"ready": "false"}
