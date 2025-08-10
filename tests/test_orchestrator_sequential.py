import pytest

from app.agents.base import Agent, AgentRequest, AgentResponse
from app.agents.orchestrator import EnhancedQAOrchestrator
from app.config_schema import AnalysisType, QAStage


class SeqAgent(Agent):
    def __init__(self, tag: str, confidence: float):
        super().__init__()
        self.tag = tag
        self.conf = confidence

    async def run(self, request: AgentRequest) -> AgentResponse:  # pragma: no cover
        # Echo previous stage content presence in context
        prev = "|".join(sorted((request.context or {}).keys())) if request.context else ""
        return AgentResponse(content=f"{self.tag}:{prev}", confidence=self.conf, raw={})


@pytest.mark.asyncio
async def test_run_sequential_order_and_context_propagation():
    orch = EnhancedQAOrchestrator()

    orch.register(
        QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural"),
        SeqAgent("S", 0.6),
    )
    orch.register(
        QAStage.CONTENT_QUALITY if hasattr(QAStage, "CONTENT_QUALITY") else QAStage("content_quality"),
        SeqAgent("C", 0.4),
    )
    orch.register(
        QAStage.DOMAIN_EXPERT if hasattr(QAStage, "DOMAIN_EXPERT") else QAStage("domain_expert"),
        SeqAgent("D", 0.8),
    )

    req = AgentRequest(
        analysis_type=(
            AnalysisType.THEMES
            if hasattr(AnalysisType, "THEMES")
            else AnalysisType("themes")
        ),
        qa_stage=None,
        prompt="p",
        context={"init": True},
    )

    result = await orch.run_sequential(req)

    # Should run 3 stages in order
    assert [r.stage for r in result.results][0:3]
    # Aggregate is mean(0.6,0.4,0.8)=0.6
    assert abs(result.aggregate_confidence - 0.6) < 1e-6
    # Context should carry stage contents
    assert result.context is not None
    assert any("structural" in k or "STRUCTURAL" in k for k in result.context.keys())
    assert any("content_quality" in k or "CONTENT_QUALITY" in k for k in result.context.keys())
    assert any("domain_expert" in k or "DOMAIN_EXPERT" in k for k in result.context.keys())
