from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.config_schema import AnalysisType
from app.queue.redis_client import get_client


def analysis_queue_name(analysis_type: AnalysisType) -> str:
    return f"analysis:{analysis_type.value}"


class QueueItem(BaseModel):
    """Base queue item schema (extend later for corrective/management)."""

    task_id: str = Field(description="Unique task identifier")
    payload: dict = Field(default_factory=dict, description="Arbitrary payload blob")


@dataclass
class QueueRegistry:
    """Registry for analysis queues."""

    analysis_types: Iterable[AnalysisType] = tuple(AnalysisType)

    def all_analysis_queue_names(self) -> list[str]:
        return [analysis_queue_name(t) for t in self.analysis_types]

    async def enqueue(self, queue: str, item: QueueItem) -> int:
        """Push an item to a queue (tail). Returns new length."""
        client = await get_client()
        # Use RPUSH to enqueue at tail
        return await client.rpush(queue, item.model_dump_json())

    async def dequeue(self, queue: str, timeout: int = 0) -> QueueItem | None:
        """Pop an item from a queue (blocking when timeout>0)."""
        client = await get_client()
        if timeout > 0:
            # BRPOP returns (queue, value) or None
            res = await client.brpop(queue, timeout=timeout)
            if res is None:
                return None
            _, raw = res
        else:
            raw = await client.lpop(queue)
            if raw is None:
                return None
        return QueueItem.model_validate_json(raw)

    async def length(self, queue: str) -> int:
        client = await get_client()
        return await client.llen(queue)
