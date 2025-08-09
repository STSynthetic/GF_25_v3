import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_text():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text
        assert "http_requests_total" in text
        assert "http_request_duration_seconds" in text
        assert "http_requests_in_progress" in text
