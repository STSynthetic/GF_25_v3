from typing import Any

import pytest

from app.agents.base import AgentResponse
from app.agents.corrective_trigger import (
    CorrectiveTriggerConfig,
    CorrectiveTriggerResult,
    trigger_corrective_if_needed,
)
from app.agents.orchestrator import AgentRunResult, OrchestratorResult
from app.config_schema import QAStage


class FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    @classmethod
    def from_url(cls, *args: Any, **kwargs: Any) -> "FakeRedis":  # type: ignore
        return cls()

    async def rpush(self, queue: str, data: str) -> None:
        self.calls.append((queue, data))

    async def aclose(self) -> None:  # pragma: no cover
        return None


@pytest.mark.asyncio
async def test_trigger_not_needed_when_threshold_met(monkeypatch):
    # Monkeypatch Redis in module
    import app.agents.corrective_trigger as ct

    monkeypatch.setattr(ct, "Redis", FakeRedis)

    # Build orchestrator result above threshold
    res = OrchestratorResult(results=[], aggregate_confidence=0.9, context=None)

    out: CorrectiveTriggerResult = await trigger_corrective_if_needed(
        task_id="t1",
        orchestrator_result=res,
        config=CorrectiveTriggerConfig(aggregate_threshold=0.75),
    )

    assert out.triggered is False
    assert out.reason == "threshold_met"


@pytest.mark.asyncio
async def test_trigger_enqueues_when_below_threshold(monkeypatch):
    # Monkeypatch Redis in module
    import app.agents.corrective_trigger as ct

    fake = FakeRedis()

    # Replace Redis class with a shim that returns our instance
    class RedisShim:
        @staticmethod
        def from_url(*args: Any, **kwargs: Any) -> FakeRedis:  # type: ignore
            return fake

    monkeypatch.setattr(ct, "Redis", RedisShim)

    # Build orchestrator result below threshold
    r1 = AgentRunResult(
        stage=QAStage.STRUCTURAL if hasattr(QAStage, "STRUCTURAL") else QAStage("structural"),
        response=AgentResponse(content="c1", confidence=0.4, raw={}),
    )
    res = OrchestratorResult(results=[r1], aggregate_confidence=0.4, context={"k": "v"})

    out: CorrectiveTriggerResult = await trigger_corrective_if_needed(
        task_id="t2",
        orchestrator_result=res,
        config=CorrectiveTriggerConfig(aggregate_threshold=0.75, queue_name="qa:corrective:test"),
    )

    assert out.triggered is True
    assert out.reason == "threshold_not_met"
    assert out.payload is not None

    # Verify an item was pushed to our fake queue
    assert fake.calls
    qname, payload = fake.calls[0]
    assert qname == "qa:corrective:test"
    assert '"task_id": "t2"' in payload
