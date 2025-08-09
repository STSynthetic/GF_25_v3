import httpx
import pytest

from app.models import preload_qwen_models


@pytest.mark.asyncio
async def test_preload_qwen_models_triggers_pull_when_missing():
    called: list[tuple[str, str]] = []  # (method, path)

    def handler(request: httpx.Request) -> httpx.Response:
        called.append((request.method, request.url.path))
        if request.method == "GET" and request.url.path.endswith("/api/tags"):
            # Simulate no models are present yet
            return httpx.Response(200, json={"models": []})
        if request.method == "POST" and request.url.path.endswith("/api/pull"):
            return httpx.Response(200, json={"status": "success"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    await preload_qwen_models(
        base_url="http://ollama.local:11434",
        transport=transport,
        concurrency=8,
    )

    # Ensure both models were attempted to be pulled
    pulled = [path for (method, path) in called if method == "POST" and path.endswith("/api/pull")]
    assert len(pulled) == 2

    # Confirm the expected GET tags queries happened
    tag_checks = [
        path for (method, path) in called if method == "GET" and path.endswith("/api/tags")
    ]
    assert len(tag_checks) == 2
