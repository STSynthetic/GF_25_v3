from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from app.config_schema import AnalysisType, QAStage
from app.queue.queues import (
    CorrectiveAndManagementRegistry,
    QueueRegistry,
    analysis_queue_name,
    corrective_queue_name,
    management_batch_completion_queue,
    management_manual_review_queue,
    management_priority_processing_queue,
)
from app.queue.redis_client import get_client


class Alert(BaseModel):
    queue: str = Field(description="Queue name")
    length: int = Field(ge=0, description="Observed queue length")
    threshold: int = Field(gt=0, description="Threshold that was exceeded")
    level: str = Field(description="Alert level, e.g., warning or critical")


AlertCallback = Callable[[Alert], None]


class QueueMonitor:
    def __init__(self, on_alert: AlertCallback | None = None) -> None:
        self._analysis_reg = QueueRegistry()
        self._corr_mgmt_reg = CorrectiveAndManagementRegistry()
        self._on_alert = on_alert

    def all_queue_names(self) -> list[str]:
        names: list[str] = []
        # Analysis
        for t in AnalysisType:
            names.append(analysis_queue_name(t))
        # Corrective (3 x 21)
        for stage in (QAStage.STRUCTURAL, QAStage.CONTENT_QUALITY, QAStage.DOMAIN_EXPERT):
            for t in AnalysisType:
                names.append(corrective_queue_name(stage, t))
        # Management (3)
        names.append(management_manual_review_queue())
        names.append(management_priority_processing_queue())
        names.append(management_batch_completion_queue())
        return names

    async def sample_lengths(self) -> dict[str, int]:
        client = await get_client()
        lengths: dict[str, int] = {}
        for q in self.all_queue_names():
            lengths[q] = await client.llen(q)
        return lengths

    async def check_alerts(self, thresholds: dict[str, tuple[int, str]]) -> list[Alert]:
        """
        thresholds: mapping of queue name -> (threshold_value, level)
        Returns list of alerts and emits via callback if provided.
        """
        lengths = await self.sample_lengths()
        alerts: list[Alert] = []
        for q, (limit, level) in thresholds.items():
            val = lengths.get(q, 0)
            if val > limit:
                alert = Alert(queue=q, length=val, threshold=limit, level=level)
                alerts.append(alert)
                if self._on_alert:
                    self._on_alert(alert)
        return alerts
