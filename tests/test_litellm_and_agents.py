import types
from typing import Any

import pytest

from app.agents.base import AgentRequest
from app.agents.qa_structural import StructuralQAAgent
from app.config_schema import AnalysisType, QAStage
from app.llm.litellm_config import (
    LiteLLMSettings,
    apply_ollama_optimizations,
    get_default_models,
)


def test_ollama_optimizations_env(monkeypatch):
    # Clear env keys and apply
    for k in [
        "OLLAMA_NUM_PARALLEL",
        "OLLAMA_FLASH_ATTENTION",
        "OLLAMA_KV_CACHE_TYPE",
        "OLLAMA_MAX_VRAM",
        "OLLAMA_SCHED_SPREAD",
    ]:
        monkeypatch.delenv(k, raising=False)
    apply_ollama_optimizations()
    # Verify a couple of keys exist
    assert "OLLAMA_NUM_PARALLEL" in __import__("os").environ
    assert __import__("os").environ["OLLAMA_NUM_PARALLEL"] == "8"


def test_default_models_config():
    cfg = get_default_models()
    assert cfg["analysis"]["model"].endswith("qwen2.5vl:32b")
    assert cfg["qa"]["temperature"] == 0.05


@pytest.mark.asyncio
async def test_structural_agent_invokes_litellm(monkeypatch):
    # Mock litellm.completion called inside wrapper
    calls: list[dict[str, Any]] = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        # Return minimal OpenAI-compatible response
        return {
            "choices": [
                {"message": {"content": "ok"}},
            ]
        }

    # Patch litellm.completion symbol imported in wrapper function
    fake_litellm = types.SimpleNamespace(completion=fake_completion)
    monkeypatch.setitem(__import__("sys").modules, "litellm", fake_litellm)

    # Build request
    req = AgentRequest(
        analysis_type=(
            AnalysisType.THEMES if hasattr(AnalysisType, "THEMES") else AnalysisType("themes")
        ),
        qa_stage=(QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural")),
        prompt="hello",
        context=None,
    )

    agent = StructuralQAAgent()
    out = await agent.run(req)

    assert out.content == "ok"
    assert 0.0 <= out.confidence <= 1.0
    assert calls, "litellm.completion should be invoked"

    # Validate base_url and model are passed
    args = calls[0]
    assert "api_base" in args
    assert "model" in args


def test_settings_defaults():
    s = LiteLLMSettings()
    assert s.base_url.startswith("http://")
    assert s.request_timeout_s > 0
