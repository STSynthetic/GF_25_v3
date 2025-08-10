from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import Agent, AgentRequest, AgentResponse
from app.config_schema import QAStage


class AgentRunResult(BaseModel):
    stage: QAStage = Field(description="QA stage executed")
    response: AgentResponse = Field(description="Agent response for the stage")


class OrchestratorResult(BaseModel):
    results: list[AgentRunResult] = Field(description="Per-stage results")
    aggregate_confidence: float = Field(
        ge=0.0, le=1.0, description="Aggregate confidence across stages"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Orchestrator-shared context for downstream steps"
    )


class EnhancedQAOrchestrator:
    """Coordinates multiple QA agents with concurrency control.

    6.3 scope: build coordination system and aggregation.
    6.4 will add strict sequential workflow + result aggregation rules.
    """

    def __init__(self, max_concurrency: int = 8) -> None:
        self._registry: dict[QAStage, Agent] = {}
        self._sem = asyncio.Semaphore(max_concurrency)

    def register(self, stage: QAStage, agent: Agent) -> None:
        self._registry[stage] = agent

    def unregister(self, stage: QAStage) -> None:
        self._registry.pop(stage, None)

    def list_registered(self) -> list[QAStage]:
        return list(self._registry.keys())

    async def _run_agent(self, stage: QAStage, request: AgentRequest) -> AgentRunResult:
        async with self._sem:
            agent = self._registry[stage]
            resp: AgentResponse = await agent.run(request)
            return AgentRunResult(stage=stage, response=resp)

    async def run_all(
        self, request: AgentRequest, stages: list[QAStage] | None = None
    ) -> OrchestratorResult:
        """Execute all registered agents (optionally filtered) concurrently.

        6.4 will build sequential orchestration; here we focus on coordination.
        """
        selected = stages or list(self._registry.keys())
        tasks: list[asyncio.Task[AgentRunResult]] = []
        for stage in selected:
            if stage in self._registry:
                tasks.append(asyncio.create_task(self._run_agent(stage, request)))
        results: list[AgentRunResult] = []
        if tasks:
            results = await asyncio.gather(*tasks)

        # Simple aggregate: mean of confidences
        if results:
            agg = sum(r.response.confidence for r in results) / len(results)
        else:
            agg = 0.0

        # Placeholder for shared context propagation to 6.4
        shared_context: dict[str, Any] | None = None

        return OrchestratorResult(results=results, aggregate_confidence=agg, context=shared_context)

    async def run_sequential(
        self,
        request: AgentRequest,
        stages: list[QAStage] | None = None,
    ) -> OrchestratorResult:
        """Execute agents in a strict sequence, propagating context.

        Default order: structural -> content_quality -> domain_expert (if registered).
        Aggregation: mean confidence across executed stages.
        """
        default_order = [
            QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural"),
            QAStage.CONTENT_QUALITY
            if hasattr(QAStage, "CONTENT_QUALITY")
            else QAStage("content_quality"),
            QAStage.DOMAIN_EXPERT
            if hasattr(QAStage, "DOMAIN_EXPERT")
            else QAStage("domain_expert"),
        ]
        ordered = stages or default_order

        results: list[AgentRunResult] = []
        shared_context: dict[str, Any] = {}

        for stage in ordered:
            if stage not in self._registry:
                continue
            # Build per-stage request with propagated context
            stage_req = AgentRequest(
                analysis_type=request.analysis_type,
                qa_stage=stage,
                prompt=request.prompt,
                context={**(request.context or {}), **shared_context}
                if shared_context
                else request.context,
            )
            res = await self._run_agent(stage, stage_req)
            results.append(res)

            # Simple propagation: attach each stage's content into context for next stage
            shared_context[f"{str(stage)}_content"] = res.response.content

        agg = sum(r.response.confidence for r in results) / len(results) if results else 0.0
        return OrchestratorResult(
            results=results, aggregate_confidence=agg, context=shared_context or None
        )
