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


# -------------------- Corrective Queues (4.3) --------------------
from app.config_schema import QAStage  # noqa: E402


def corrective_queue_name(stage: QAStage, analysis_type: AnalysisType) -> str:
    return f"corrective:{stage.value}:{analysis_type.value}"


def management_manual_review_queue() -> str:
    return "mgmt:manual_review"


def management_priority_processing_queue() -> str:
    return "mgmt:priority_processing"


def management_batch_completion_queue() -> str:
    return "mgmt:batch_completion"


class CorrectiveQueueItem(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    analysis_type: AnalysisType = Field(description="Analysis type for correction")
    stage: QAStage = Field(description="Corrective stage to apply")
    original_output: str = Field(description="Original JSON output to correct")
    image_b64: str | None = Field(default=None, description="Optional base64 image data")
    meta: dict = Field(default_factory=dict, description="Additional metadata")


class ManagementQueueItem(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    reason: str = Field(description="Reason for management action")
    priority: int | None = Field(default=None, description="Optional priority score")
    batch_id: str | None = Field(default=None, description="Batch identifier if applicable")
    meta: dict = Field(default_factory=dict, description="Additional metadata")


@dataclass
class CorrectiveAndManagementRegistry:
    analysis_types: Iterable[AnalysisType] = tuple(AnalysisType)

    # Corrective
    async def enqueue_corrective(
        self,
        stage: QAStage,
        analysis_type: AnalysisType,
        item: CorrectiveQueueItem,
    ) -> int:
        client = await get_client()
        qname = corrective_queue_name(stage, analysis_type)
        payload = item.model_dump_json()
        return await client.rpush(qname, payload)

    async def dequeue_corrective(
        self,
        stage: QAStage,
        analysis_type: AnalysisType,
        timeout: int = 0,
    ) -> CorrectiveQueueItem | None:
        client = await get_client()
        q = corrective_queue_name(stage, analysis_type)
        if timeout > 0:
            res = await client.brpop(q, timeout=timeout)
            if res is None:
                return None
            _, raw = res
        else:
            raw = await client.lpop(q)
            if raw is None:
                return None
        return CorrectiveQueueItem.model_validate_json(raw)

    async def length_corrective(self, stage: QAStage, analysis_type: AnalysisType) -> int:
        client = await get_client()
        return await client.llen(corrective_queue_name(stage, analysis_type))

    # Management
    async def enqueue_manual_review(self, item: ManagementQueueItem) -> int:
        client = await get_client()
        return await client.rpush(management_manual_review_queue(), item.model_dump_json())

    async def dequeue_manual_review(self, timeout: int = 0) -> ManagementQueueItem | None:
        client = await get_client()
        q = management_manual_review_queue()
        if timeout > 0:
            res = await client.brpop(q, timeout=timeout)
            if res is None:
                return None
            _, raw = res
        else:
            raw = await client.lpop(q)
            if raw is None:
                return None
        return ManagementQueueItem.model_validate_json(raw)

    async def length_manual_review(self) -> int:
        client = await get_client()
        return await client.llen(management_manual_review_queue())

    async def enqueue_priority(self, item: ManagementQueueItem) -> int:
        client = await get_client()
        return await client.rpush(management_priority_processing_queue(), item.model_dump_json())

    async def dequeue_priority(self, timeout: int = 0) -> ManagementQueueItem | None:
        client = await get_client()
        q = management_priority_processing_queue()
        if timeout > 0:
            res = await client.brpop(q, timeout=timeout)
            if res is None:
                return None
            _, raw = res
        else:
            raw = await client.lpop(q)
            if raw is None:
                return None
        return ManagementQueueItem.model_validate_json(raw)

    async def length_priority(self) -> int:
        client = await get_client()
        return await client.llen(management_priority_processing_queue())

    async def enqueue_batch_completion(self, item: ManagementQueueItem) -> int:
        client = await get_client()
        return await client.rpush(management_batch_completion_queue(), item.model_dump_json())

    async def dequeue_batch_completion(self, timeout: int = 0) -> ManagementQueueItem | None:
        client = await get_client()
        q = management_batch_completion_queue()
        if timeout > 0:
            res = await client.brpop(q, timeout=timeout)
            if res is None:
                return None
            _, raw = res
        else:
            raw = await client.lpop(q)
            if raw is None:
                return None
        return ManagementQueueItem.model_validate_json(raw)

    async def length_batch_completion(self) -> int:
        client = await get_client()
        return await client.llen(management_batch_completion_queue())
