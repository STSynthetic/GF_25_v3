from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class LiteLLMSettings(BaseModel):
    base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    request_timeout_s: float = Field(default=60.0, description="Default request timeout in seconds")


# [OLLAMA-OPT] environment variables
ollama_optimization_vars: dict[str, str] = {
    "OLLAMA_NUM_PARALLEL": "8",
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KV_CACHE_TYPE": "q8_0",
    "OLLAMA_MAX_VRAM": "22000000000",
    "OLLAMA_SCHED_SPREAD": "true",
}


def apply_ollama_optimizations() -> None:
    os.environ.update(ollama_optimization_vars)


def get_default_models() -> dict[str, Any]:
    return {
        "analysis": {
            "model": "ollama/qwen2.5vl:32b",
            "temperature": 0.1,
            "num_ctx": 32768,
        },
        "qa": {
            "model": "ollama/qwen2.5vl:latest",
            "temperature": 0.05,
            "num_ctx": 32768,
        },
    }


def completion(
    prompt: str,
    *,
    role: str = "user",
    model_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Thin wrapper for litellm.completion. Tests should mock this.

    Ensures base_url to local Ollama and merges provided model_cfg with defaults.
    """
    from litellm import completion as llm_completion  # imported here for easier mocking

    settings = LiteLLMSettings()
    cfg = get_default_models()["analysis"].copy()
    if model_cfg:
        cfg.update(model_cfg)

    return llm_completion(
        model=cfg["model"],
        messages=[{"role": role, "content": prompt}],
        temperature=cfg.get("temperature", 0.1),
        num_ctx=cfg.get("num_ctx", 32768),
        api_base=settings.base_url,
        timeout=settings.request_timeout_s,
    )
