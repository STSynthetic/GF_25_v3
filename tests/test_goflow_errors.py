import types
from typing import Any

import pytest

from app.api.goflow_client import GoFlowClient, GoFlowConfig
from app.api.goflow_errors import (
    GoFlowAuthError,
    GoFlowClientError,
    GoFlowNotFound,
    GoFlowServerError,
)


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or {"ok": True}
        self.request = types.SimpleNamespace()

    def json(self) -> dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:  # pragma: no cover
        # We rely on client's mapping instead of raising here
        return None


class FlakyAsyncClient:
    """First returns 500, then 200 to exercise retry path."""

    def __init__(self, base_url: str, timeout: float, headers: dict[str, str]) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers
        self.calls = 0

    async def aclose(self) -> None:  # pragma: no cover
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return FakeResponse(500, {"error": "server"})
        return FakeResponse(200, {"ok": True})


class ErroringAsyncClient:
    """Always return a specific status for mapping tests."""

    def __init__(self, base_url: str, timeout: float, headers: dict[str, str]) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers
        self.status_to_return = 401

    async def aclose(self) -> None:  # pragma: no cover
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        return FakeResponse(self.status_to_return, {"error": "x"})


@pytest.mark.asyncio
async def test_retry_on_5xx_then_success(monkeypatch):
    import app.api.goflow_client as gf

    # Use fallback retry path
    monkeypatch.setattr(gf, "AsyncRetrying", None)
    monkeypatch.setattr(gf.httpx, "AsyncClient", FlakyAsyncClient)

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k", max_retries=2)
    async with GoFlowClient(cfg) as client:
        data = await client.get("/ping")
        assert data["ok"] is True


@pytest.mark.asyncio
async def test_error_mapping(monkeypatch):
    import app.api.goflow_client as gf

    monkeypatch.setattr(gf, "AsyncRetrying", None)
    ec = ErroringAsyncClient("https://api.example.com", 30.0, {"a": "b"})

    class Factory:
        def __call__(self, base_url: str, timeout: float, headers: dict[str, str]):
            return ec

    monkeypatch.setattr(gf.httpx, "AsyncClient", Factory())

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k", max_retries=1)
    async with GoFlowClient(cfg) as client:
        # 401 -> GoFlowAuthError
        ec.status_to_return = 401
        with pytest.raises(GoFlowAuthError):
            await client.get("/ping")
        # 404 -> GoFlowNotFound
        ec.status_to_return = 404
        with pytest.raises(GoFlowNotFound):
            await client.get("/ping")
        # 400 -> GoFlowClientError
        ec.status_to_return = 400
        with pytest.raises(GoFlowClientError):
            await client.get("/ping")
        # 503 -> GoFlowServerError (retryable)
        ec.status_to_return = 503
        with pytest.raises(GoFlowServerError):
            await client.get("/ping")
