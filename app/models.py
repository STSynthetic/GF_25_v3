import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from app.model_config import ANALYSIS_MODEL, QA_MODEL


@retry(wait=wait_exponential_jitter(initial=0.2, max=2.0), stop=stop_after_attempt(5))
async def _get_tags(client: httpx.AsyncClient, base_url: str) -> set[str]:
    resp = await client.get(f"{base_url}/api/tags")
    resp.raise_for_status()
    data = resp.json()
    names = {m.get("name", "") for m in data.get("models", [])}
    return {n for n in names if n}


@retry(wait=wait_exponential_jitter(initial=0.5, max=2.0), stop=stop_after_attempt(5))
async def _pull_model(client: httpx.AsyncClient, base_url: str, model: str) -> None:
    # Ollama pull may stream; we accept a simple 200 OK for test environment
    resp = await client.post(f"{base_url}/api/pull", json={"name": model})
    resp.raise_for_status()


async def _ensure_model(client: httpx.AsyncClient, base_url: str, model: str) -> None:
    tags = await _get_tags(client, base_url)
    if model not in tags:
        await _pull_model(client, base_url, model)


async def preload_qwen_models(
    base_url: str = "http://localhost:11434",
    concurrency: int = 8,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    """Preload Qwen2.5VL models on a local Ollama server.

    Uses up to `concurrency` tasks concurrently (default 8 per [CORE-STD]).
    """
    targets: list[str] = [ANALYSIS_MODEL.model, QA_MODEL.model]

    semaphore = asyncio.Semaphore(concurrency)

    async def worker(model: str) -> None:
        async with semaphore:
            async with httpx.AsyncClient(timeout=60.0, transport=transport) as client:
                await _ensure_model(client, base_url, model)

    await asyncio.gather(*(worker(m) for m in targets))


async def check_ollama_ready(
    base_url: str = "http://localhost:11434",
    transport: httpx.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
) -> bool:
    """Return True if Ollama responds to /api/tags within timeout.

    Any non-2xx or exception is considered not ready.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
            resp = await client.get(f"{base_url}/api/tags")
            return 200 <= resp.status_code < 300
    except Exception:
        return False
