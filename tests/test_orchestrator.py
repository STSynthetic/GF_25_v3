import pytest

from app.agents.base import Agent, AgentRequest, AgentResponse
from app.agents.orchestrator import EnhancedQAOrchestrator
from app.config_schema import AnalysisType, QAStage


class FakeAgent(Agent):
    def __init__(self, confidence: float) -> None:
        super().__init__()
        self._conf = confidence

    async def run(self, request: AgentRequest) -> AgentResponse:  # pragma: no cover
        return AgentResponse(content="ok", confidence=self._conf, raw={})


@pytest.mark.asyncio
async def test_orchestrator_runs_agents_and_aggregates():
    orch = EnhancedQAOrchestrator(max_concurrency=2)

    orch.register(
        QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural"),
        FakeAgent(0.6),
    )
    orch.register(
        QAStage.CONTENT_QUALITY
        if hasattr(QAStage, "CONTENT_QUALITY")
        else QAStage("content_quality"),
        FakeAgent(0.4),
    )

    req = AgentRequest(
        analysis_type=(
            AnalysisType.THEMES if hasattr(AnalysisType, "THEMES") else AnalysisType("themes")
        ),
        qa_stage=None,
        prompt="p",
        context=None,
    )

    result = await orch.run_all(req)

    assert len(result.results) == 2
    # Mean of 0.6 and 0.4
    assert abs(result.aggregate_confidence - 0.5) < 1e-6
    # Registered stages list returned
    listed = orch.list_registered()
    assert listed
