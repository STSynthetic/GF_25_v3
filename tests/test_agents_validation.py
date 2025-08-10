import types
from typing import Any

import pytest

from app.agents.base import AgentRequest
from app.agents.qa_content_quality import ContentQualityQAAgent
from app.agents.qa_domain_expert import DomainExpertQAAgent
from app.agents.qa_structural import StructuralQAAgent
from app.config_schema import AnalysisType, QAStage


@pytest.mark.asyncio
async def test_all_three_agents_call_litellm(monkeypatch):
    calls: list[dict[str, Any]] = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": "ok"}}]}

    fake_litellm = types.SimpleNamespace(completion=fake_completion)
    monkeypatch.setitem(__import__("sys").modules, "litellm", fake_litellm)

    req = AgentRequest(
        analysis_type=(
            AnalysisType.THEMES if hasattr(AnalysisType, "THEMES") else AnalysisType("themes")
        ),
        qa_stage=(QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural")),
        prompt="validate",
        context=None,
    )

    agents = [
        StructuralQAAgent(),
        ContentQualityQAAgent(),
        DomainExpertQAAgent(),
    ]

    results = []
    for agent in agents:
        out = await agent.run(req)
        results.append(out)

    assert len(calls) == 3
    for out in results:
        assert out.content == "ok"
        assert 0.0 <= out.confidence <= 1.0
        # Validate that api_base/model present in calls
    for call in calls:
        assert "api_base" in call
        assert "model" in call
