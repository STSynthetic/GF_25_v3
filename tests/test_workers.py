import asyncio

import pytest

import app.queue.workers as workers_mod
from app.config_schema import AnalysisType, QAStage
from app.queue.queues import analysis_queue_name, corrective_queue_name
from app.queue.workers import WorkerCoordinator


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


@pytest.mark.asyncio
async def test_worker_coordinator_round_robin_processing(monkeypatch):
    fake = FakeQueue()

    # Monkeypatch redis client getter used inside WorkerCoordinator
    monkeypatch.setattr(workers_mod, "get_client", lambda: asyncio.sleep(0, result=fake))

    # Preload items across multiple queues
    q_analysis1 = analysis_queue_name(AnalysisType.AGES)
    q_analysis2 = analysis_queue_name(AnalysisType.THEMES)
    q_corrective = corrective_queue_name(QAStage.STRUCTURAL, AnalysisType.AGES)

    await fake.rpush(q_analysis1, '{"task_id": "a1"}')
    await fake.rpush(q_analysis2, '{"task_id": "a2"}')
    await fake.rpush(q_corrective, '{"task_id": "c1"}')

    processed = []

    async def process_func(q: str, payload: bytes):
        # Minimal processing: record and return
        processed.append((q, payload.decode()))
        return None

    coord = WorkerCoordinator(process_func=process_func, concurrency=8, idle_backoff_s=0.01)

    await coord.start()
    # Allow some time for processing
    await asyncio.sleep(0.1)
    await coord.stop()

    # Validate that items from multiple queues were processed
    queues_seen = {q for q, _ in processed}
    assert q_analysis1 in queues_seen
    assert q_analysis2 in queues_seen
    assert q_corrective in queues_seen
    assert len(processed) == 3
