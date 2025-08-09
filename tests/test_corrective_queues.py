import asyncio

import pytest

import app.queue.queues as queues_mod
from app.config_schema import AnalysisType, QAStage
from app.queue.queues import (
    CorrectiveAndManagementRegistry,
    CorrectiveQueueItem,
)


class FakeQueue:
    def __init__(self):
        self.store: dict[str, list[str]] = {}

    async def rpush(self, q: str, value: str) -> int:
        self.store.setdefault(q, []).append(value)
        return len(self.store[q])

    async def lpop(self, q: str):
        if q not in self.store or not self.store[q]:
            return None
        return self.store[q].pop(0)

    async def brpop(self, q: str, timeout: int = 0):
        if q not in self.store or not self.store[q]:
            return None
        return (q, self.store[q].pop())

    async def llen(self, q: str) -> int:
        return len(self.store.get(q, []))


@pytest.mark.asyncio
async def test_corrective_enqueue_dequeue_and_length(monkeypatch):
    fake = FakeQueue()
    monkeypatch.setattr(queues_mod, "get_client", lambda: asyncio.sleep(0, result=fake))

    reg = CorrectiveAndManagementRegistry()

    assert await reg.length_corrective(QAStage.STRUCTURAL, AnalysisType.AGES) == 0

    item = CorrectiveQueueItem(
        task_id="t1",
        analysis_type=AnalysisType.AGES,
        stage=QAStage.STRUCTURAL,
        original_output="{}",
    )

    assert await reg.enqueue_corrective(QAStage.STRUCTURAL, AnalysisType.AGES, item) == 1
    assert await reg.length_corrective(QAStage.STRUCTURAL, AnalysisType.AGES) == 1

    out = await reg.dequeue_corrective(QAStage.STRUCTURAL, AnalysisType.AGES)
    assert out and out.task_id == "t1"
    assert await reg.length_corrective(QAStage.STRUCTURAL, AnalysisType.AGES) == 0
