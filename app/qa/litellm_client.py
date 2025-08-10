from __future__ import annotations

import os
from typing import Any

import litellm

# [LITELLM-INTEGRATION] Configure LiteLLM for Ollama
# Use local Ollama at default port; can be overridden via env
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Default model presets per [MODEL-CONFIG]
ANALYSIS_MODEL = "ollama/qwen2.5vl:32b"
QA_MODEL = "ollama/qwen2.5vl:latest"

DEFAULT_ANALYSIS_PARAMS: dict[str, Any] = {
    "model": ANALYSIS_MODEL,
    "temperature": 0.1,
    "num_ctx": 32768,
}

DEFAULT_QA_PARAMS: dict[str, Any] = {
    "model": QA_MODEL,
    "temperature": 0.05,
    "num_ctx": 32768,
}


def configure_litellm() -> None:
    """Apply LiteLLM global configuration for Ollama.

    Sets base_url to point at local Ollama. No API keys are required for local.
    """
    # LiteLLM reads environment variables; set base URL for ollama
    os.environ.setdefault("LITELLM_BASE_URL", OLLAMA_BASE_URL)

    # [OLLAMA-OPT] Apply pre-job optimization env vars
    ollama_optimization_vars = {
        "OLLAMA_NUM_PARALLEL": "8",
        "OLLAMA_FLASH_ATTENTION": "1",
        "OLLAMA_KV_CACHE_TYPE": "q8_0",
        "OLLAMA_MAX_VRAM": "22000000000",
        "OLLAMA_SCHED_SPREAD": "true",
    }
    os.environ.update(ollama_optimization_vars)


def completion_sync(params: dict[str, Any]) -> Any:
    """Synchronous completion shim (rarely used; prefer async).

    Provided for simple smoke checks. Prefer async via litellm.acompletion.
    """
    configure_litellm()
    return litellm.completion(**params)


async def completion_async(params: dict[str, Any]) -> Any:
    """Async completion via LiteLLM.

    Caller should pass validated params including model and temperature.
    """
    configure_litellm()
    return await litellm.acompletion(**params)
