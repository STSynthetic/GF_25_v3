import types
from typing import Any

import pytest

from app.api.goflow_client import GoFlowClient, GoFlowConfig
from app.api.goflow_models import JobStatusUpdate


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict[str, Any]) -> None:
        self.status_code = status_code
        self._json = json_data
        self.request = types.SimpleNamespace()

    def json(self) -> dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:  # pragma: no cover
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
        if method == "GET" and url == "/api/v1/agent/next-job":
            return FakeResponse(
                200,
                {
                    "job_id": "j1",
                    "project_id": "p1",
                    "media_id": "m1",
                    "analysis_id": "a1",
                    "payload": {"k": "v"},
                },
            )
        if method == "POST" and url.startswith("/api/v1/agent/projects/"):
            return FakeResponse(200, {"ok": True})
        return FakeResponse(404, {"error": "not found"})


@pytest.mark.asyncio
async def test_get_next_job_and_update_status(monkeypatch):
    import app.api.goflow_client as gf

    # Disable retries for simpler path
    monkeypatch.setattr(gf, "AsyncRetrying", None)
    monkeypatch.setattr(gf.httpx, "AsyncClient", FakeAsyncClient)

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k")
    async with GoFlowClient(cfg) as client:
        job = await client.get_next_job()
        assert job.job_id == "j1"
        assert job.project_id == "p1"

        out = await client.update_project_status(
            "p1", JobStatusUpdate(status="in_progress", progress=0.25)
        )
        assert out["ok"] is True
