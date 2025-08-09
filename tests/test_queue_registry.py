import asyncio

import pytest

import app.queue.queues as queues_mod
from app.config_schema import AnalysisType
from app.queue.queues import QueueItem, QueueRegistry, analysis_queue_name


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
        # simple non-blocking emulation ignoring timeout
        if q not in self.store or not self.store[q]:
            return None
        return (q, self.store[q].pop())

    async def llen(self, q: str) -> int:
        return len(self.store.get(q, []))


@pytest.mark.asyncio
async def test_registry_enqueue_dequeue_and_length(monkeypatch):
    # Use fake Redis client
    fake = FakeQueue()
    # Patch where it's used: the queues module imported get_client directly
    monkeypatch.setattr(queues_mod, "get_client", lambda: asyncio.sleep(0, result=fake))

    registry = QueueRegistry()
    qname = analysis_queue_name(AnalysisType.AGES)

    # Initially empty
    assert await registry.length(qname) == 0

    # Enqueue two items
    item1 = QueueItem(task_id="t1", payload={"k": 1})
    item2 = QueueItem(task_id="t2", payload={"k": 2})

    assert await registry.enqueue(qname, item1) == 1
    assert await registry.enqueue(qname, item2) == 2
    assert await registry.length(qname) == 2

    # Dequeue non-blocking -> FIFO: t1 then t2
    out1 = await registry.dequeue(qname)
    assert out1 and out1.task_id == "t1"
    out2 = await registry.dequeue(qname)
    assert out2 and out2.task_id == "t2"

    # Empty now
    assert await registry.dequeue(qname) is None
    assert await registry.length(qname) == 0
