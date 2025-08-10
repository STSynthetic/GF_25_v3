import types
from typing import Any

import pytest

from app.api.goflow_client import GoFlowClient, GoFlowConfig
from app.api.goflow_models import ReportRequest, ResultPayload


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
        if method == "POST" and "/analysis/" in url:
            # Simulate result submission OK
            return FakeResponse(200, {"ok": True, "path": url})
        if method == "POST" and url.endswith("/reports"):
            return FakeResponse(200, {"project_id": "p1", "report_id": "r1", "status": "queued"})
        return FakeResponse(404, {"error": "not found"})


@pytest.mark.asyncio
async def test_submit_result_and_generate_report(monkeypatch):
    import app.api.goflow_client as gf

    # Disable retries for simpler path
    monkeypatch.setattr(gf, "AsyncRetrying", None)
    monkeypatch.setattr(gf.httpx, "AsyncClient", FakeAsyncClient)

    cfg = GoFlowConfig(base_url="https://api.example.com", api_key="k")
    async with GoFlowClient(cfg) as client:
        payload = ResultPayload(
            project_id="p1",
            media_id="m1",
            analysis_id="a1",
            result={"score": 0.9},
            meta={"notes": "ok"},
        )
        res = await client.submit_analysis_result(payload)
        assert res["ok"] is True

        rep = await client.generate_project_report(ReportRequest(project_id="p1"))
        assert rep.project_id == "p1"
        assert rep.report_id == "r1"
        assert rep.status == "queued"
