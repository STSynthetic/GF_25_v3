from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import AgentRequest
from app.agents.orchestrator import EnhancedQAOrchestrator, OrchestratorResult
from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisType
from app.pipeline_integration import PreparedRun, prepare_run
from app.qa.litellm_client import DEFAULT_ANALYSIS_PARAMS, completion_async


class AnalysisJob(BaseModel):
    analysis_type: AnalysisType = Field(description="One of 21 analysis types")
    base64_image: str = Field(min_length=1, description="Base64-encoded image content")
    extra_placeholders: dict[str, str] | None = Field(
        default=None, description="Optional additional prompt placeholders"
    )


class AnalysisResult(BaseModel):
    analysis_type: AnalysisType = Field(description="Analysis type processed")
    success: bool = Field(description="Whether the model call succeeded")
    content: str | None = Field(default=None, description="Model text output")
    confidence: float | None = Field(default=None, description="Heuristic confidence")
    duration_ms: int = Field(ge=0, description="End-to-end duration in milliseconds")
    error: str | None = Field(default=None, description="Error message if failed")
    raw: dict[str, Any] | None = Field(default=None, description="Raw provider response")
    gpu_id: int | None = Field(default=None, description="Assigned (virtual) GPU id for scheduling")
    qa: dict[str, Any] | None = Field(default=None, description="QA aggregation result if run")


@dataclass
class _Scheduled:
    job: AnalysisJob
    gpu_id: int


class AnalysisWorkflowEngine:
    def __init__(
        self,
        registry: ConfigRegistry,
        *,
        max_concurrency: int = 8,
        timeout_seconds: int = 60,
        gpu_cores: int = 16,
        qa_orchestrator: EnhancedQAOrchestrator | None = None,
    ) -> None:
        self.registry = registry
        self._sem = asyncio.Semaphore(max_concurrency)
        self.timeout_seconds = timeout_seconds
        self.gpu_cores = max(1, gpu_cores)
        self.qa_orchestrator = qa_orchestrator
        self._rr = 0  # round-robin index for GPU assignment

    def _assign_gpu(self) -> int:
        gpu = self._rr % self.gpu_cores
        self._rr += 1
        return gpu

    def _adjust_params(self, prepared: PreparedRun) -> dict[str, Any]:
        # Start with defaults then overlay model params from config and light heuristics
        params: dict[str, Any] = {**DEFAULT_ANALYSIS_PARAMS, **prepared.model_params}
        # Simple dynamic tuning: slightly higher temperature for descriptive types
        descriptive = {AnalysisType.CAPTIONS, AnalysisType.SCENE_DESCRIPTION, AnalysisType.THEMES}
        if prepared.analysis_type in descriptive:
            params["temperature"] = max(0.1, min(0.3, float(params.get("temperature", 0.1)) + 0.1))
        return params

    async def _run_one(self, scheduled: _Scheduled) -> AnalysisResult:
        start = time.perf_counter()
        job = scheduled.job
        gpu_id = scheduled.gpu_id

        async with self._sem:
            try:
                prepared = prepare_run(
                    self.registry,
                    job.analysis_type,
                    base64_image=job.base64_image,
                    extra_placeholders=job.extra_placeholders,
                )

                params = self._adjust_params(prepared)
                # Build chat-like messages input for litellm
                call_args = {
                    **params,
                    "messages": [
                        {"role": "system", "content": prepared.system_prompt},
                        {"role": "user", "content": prepared.user_prompt},
                    ],
                }

                async def _call() -> Any:
                    return await completion_async(call_args)

                resp: Any = await asyncio.wait_for(_call(), timeout=self.timeout_seconds)
                # Extract text content in OpenAI-like schema
                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                # Heuristic confidence (can be replaced by model-provided logprobs)
                confidence = 0.5 if content else 0.0
                duration_ms = int((time.perf_counter() - start) * 1000)

                qa_payload: dict[str, Any] | None = None
                if self.qa_orchestrator is not None:
                    # Feed analysis output into QA orchestrator sequentially
                    qa_req = AgentRequest(
                        analysis_type=job.analysis_type,
                        qa_stage=None,
                        prompt=content,
                        context={"config_version": prepared.config_version},
                    )
                    qa_res: OrchestratorResult = await self.qa_orchestrator.run_sequential(qa_req)
                    qa_payload = {
                        "aggregate_confidence": qa_res.aggregate_confidence,
                        "stages": [
                            {"stage": str(r.stage), "confidence": r.response.confidence}
                            for r in qa_res.results
                        ],
                    }

                return AnalysisResult(
                    analysis_type=job.analysis_type,
                    success=True,
                    content=content,
                    confidence=confidence,
                    duration_ms=duration_ms,
                    error=None,
                    raw=resp,
                    gpu_id=gpu_id,
                    qa=qa_payload,
                )
            except TimeoutError:
                duration_ms = int((time.perf_counter() - start) * 1000)
                return AnalysisResult(
                    analysis_type=job.analysis_type,
                    success=False,
                    content=None,
                    confidence=None,
                    duration_ms=duration_ms,
                    error=f"timeout after {self.timeout_seconds}s",
                    raw=None,
                    gpu_id=gpu_id,
                    qa=None,
                )
            except Exception as ex:  # pragma: no cover - exercised via error test
                duration_ms = int((time.perf_counter() - start) * 1000)
                return AnalysisResult(
                    analysis_type=job.analysis_type,
                    success=False,
                    content=None,
                    confidence=None,
                    duration_ms=duration_ms,
                    error=str(ex),
                    raw=None,
                    gpu_id=gpu_id,
                    qa=None,
                )

    async def run_batch(self, jobs: Iterable[AnalysisJob]) -> list[AnalysisResult]:
        # Assign GPUs in round-robin and schedule tasks
        scheduled = [_Scheduled(job=j, gpu_id=self._assign_gpu()) for j in jobs]
        tasks = [asyncio.create_task(self._run_one(s)) for s in scheduled]
        results = await asyncio.gather(*tasks)
        return results
