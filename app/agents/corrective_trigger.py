from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.agents.orchestrator import OrchestratorResult

try:
    from redis.asyncio import Redis  # type: ignore
except Exception:  # pragma: no cover - tests may monkeypatch
    Redis = None  # type: ignore


class CorrectiveTriggerConfig(BaseModel):
    aggregate_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Min acceptable aggregate confidence before triggering corrective",
    )
    queue_name: str = Field(
        default="qa:corrective", description="Redis list/stream name for corrective jobs"
    )
    redis_url_env: str = Field(
        default="REDIS_URL", description="Env var name for Redis connection URL"
    )


class CorrectiveTriggerResult(BaseModel):
    triggered: bool = Field(description="Whether a corrective job was enqueued")
    reason: Optional[str] = Field(default=None, description="Reason for trigger decision")
    payload: Optional[Dict[str, Any]] = Field(
        default=None, description="Payload enqueued to corrective queue"
    )


async def _enqueue(redis: Any, queue: str, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload)
    # Use RPUSH to append to a list queue; switch to XADD if streams are preferred
    await redis.rpush(queue, data)


async def trigger_corrective_if_needed(
    *,
    task_id: str,
    orchestrator_result: OrchestratorResult,
    config: CorrectiveTriggerConfig | None = None,
) -> CorrectiveTriggerResult:
    """Decide and enqueue corrective processing based on QA results.

    - Triggers when aggregate_confidence < aggregate_threshold
    - Enqueues payload to Redis queue specified in config
    """
    cfg = config or CorrectiveTriggerConfig()

    agg = orchestrator_result.aggregate_confidence
    if agg >= cfg.aggregate_threshold:
        return CorrectiveTriggerResult(triggered=False, reason="threshold_met")

    redis_url = os.getenv(cfg.redis_url_env, "redis://localhost:6379/0")
    if Redis is None:  # pragma: no cover - test will monkeypatch
        raise RuntimeError("redis.asyncio module unavailable")

    redis = Redis.from_url(redis_url, decode_responses=True)
    try:
        payload = {
            "task_id": task_id,
            "aggregate_confidence": agg,
            "context": orchestrator_result.context or {},
            "results": [
                {
                    "stage": str(r.stage),
                    "content": r.response.content,
                    "confidence": r.response.confidence,
                }
                for r in orchestrator_result.results
            ],
        }
        await _enqueue(redis, cfg.queue_name, payload)
        return CorrectiveTriggerResult(
            triggered=True, reason="threshold_not_met", payload=payload
        )
    finally:
        try:
            await redis.aclose()
        except Exception:
            pass
