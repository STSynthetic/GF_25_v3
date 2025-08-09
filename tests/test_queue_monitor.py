import asyncio

import pytest

import app.queue.monitor as monitor_mod
from app.config_schema import AnalysisType, QAStage
from app.queue.monitor import QueueMonitor
from app.queue.queues import (
    analysis_queue_name,
    corrective_queue_name,
    management_manual_review_queue,
)


class FakeQueue:
    def __init__(self):
        self.store: dict[str, list[str]] = {}

    async def rpush(self, q: str, value: str) -> int:
        self.store.setdefault(q, []).append(value)
        return len(self.store[q])

    async def llen(self, q: str) -> int:
        return len(self.store.get(q, []))


@pytest.mark.asyncio
async def test_queue_monitor_alerts(monkeypatch):
    fake = FakeQueue()
    monkeypatch.setattr(monitor_mod, "get_client", lambda: asyncio.sleep(0, result=fake))

    # Seed some lengths
    q1 = analysis_queue_name(AnalysisType.AGES)
    q2 = corrective_queue_name(QAStage.STRUCTURAL, AnalysisType.AGES)
    q3 = management_manual_review_queue()

    # Populate queues: q1 has 2, q2 has 1, q3 has 0
    await fake.rpush(q1, "x")
    await fake.rpush(q1, "y")
    await fake.rpush(q2, "z")

    received = []

    def on_alert(alert):
        received.append(alert)

    mon = QueueMonitor(on_alert=on_alert)
    thresholds = {
        q1: (1, "warning"),  # expect alert since len=2 > 1
        q2: (2, "warning"),  # no alert since len=1 <= 2
        q3: (0, "critical"),  # no alert since len=0 == 0 (not greater)
    }

    alerts = await mon.check_alerts(thresholds)

    assert len(alerts) == 1
    assert alerts[0].queue == q1
    assert alerts[0].length == 2
    assert alerts[0].threshold == 1
    assert alerts[0].level == "warning"
    # Callback also received same alert
    assert len(received) == 1
    assert received[0].queue == q1
