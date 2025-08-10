import types
from typing import Any

import pytest

from app.api.goflow_client import GoFlowClient, GoFlowConfig


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict[str, Any]) -> None:
        self.status_code = status_code
        self._json = json_data
        self.request = types.SimpleNamespace()

    def json(self) -> dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:  # pragma: no cover - exercised by status_code
        if self.status_code >= 400:
            raise AssertionError("HTTP error raised in test")


class FakeAsyncClient:
    def __init__(self, base_url: str, timeout: float, headers: dict[str, str]) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def aclose(self) -> None:  # pragma: no cover
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        # Return a trivial OK
        return FakeResponse(200, {"ok": True, "path": url, "method": method})


@pytest.mark.asyncio
async def test_goflow_client_context_and_get(monkeypatch):
    # Disable tenacity path to simplify
    import app.api.goflow_client as gf

    monkeypatch.setattr(gf, "AsyncRetrying", None)

    # Patch httpx.AsyncClient to our fake
    monkeypatch.setattr(gf.httpx, "AsyncClient", FakeAsyncClient)

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k")
    async with GoFlowClient(cfg) as client:
        # Ensure headers set
        assert client.client.headers["Authorization"].startswith("Bearer ")
        data = await client.get("/ping", params={"a": 1})
        assert data["ok"] is True
        assert data["path"] == "/ping"


@pytest.mark.asyncio
async def test_goflow_client_post(monkeypatch):
    import app.api.goflow_client as gf

    monkeypatch.setattr(gf, "AsyncRetrying", None)
    monkeypatch.setattr(gf.httpx, "AsyncClient", FakeAsyncClient)

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k", timeout_seconds=10.0)
    async with GoFlowClient(cfg) as client:
        data = await client.post("/jobs", json={"x": 1})
        assert data["ok"] is True
        assert data["path"] == "/jobs"
        assert data["method"] == "POST"
