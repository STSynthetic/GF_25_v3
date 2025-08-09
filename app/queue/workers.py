from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable

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


class ProcessingResult(BaseModel):
    task_id: str = Field(description="Processed task id")
    queue: str = Field(description="Queue name the task was pulled from")


ProcessFunc = Callable[[str, bytes], Awaitable[ProcessingResult | None]]


class WorkerCoordinator:
    def __init__(
        self,
        process_func: ProcessFunc,
        concurrency: int = 8,
        idle_backoff_s: float = 0.1,
    ) -> None:
        self.process_func = process_func
        self.semaphore = asyncio.Semaphore(concurrency)
        self.idle_backoff_s = idle_backoff_s
        self._stop_event = asyncio.Event()
        self._analysis_reg = QueueRegistry()
        self._corr_mgmt_reg = CorrectiveAndManagementRegistry()

    def build_round_robin_queues(self) -> deque[str]:
        rr: deque[str] = deque()
        # 21 analysis queues
        for t in AnalysisType:
            rr.append(analysis_queue_name(t))
        # corrective queues: 3 stages x 21
        for stage in (QAStage.STRUCTURAL, QAStage.CONTENT_QUALITY, QAStage.DOMAIN_EXPERT):
            for t in AnalysisType:
                rr.append(corrective_queue_name(stage, t))
        # management queues
        rr.append(management_manual_review_queue())
        rr.append(management_priority_processing_queue())
        rr.append(management_batch_completion_queue())
        return rr

    async def _try_dequeue_one(self, queue: str) -> tuple[str, bytes] | None:
        client = await get_client()
        raw = await client.lpop(queue)
        if raw is None:
            return None
        # redis-py returns bytes for raw value in real client
        if isinstance(raw, str):
            raw_bytes = raw.encode()
        else:
            raw_bytes = raw
        return queue, raw_bytes

    async def _worker_loop(self, rr: deque[str]) -> None:
        while not self._stop_event.is_set():
            # Acquire a slot
            async with self.semaphore:
                processed_any = False

                for _ in range(len(rr)):
                    queue = rr[0]
                    rr.rotate(-1)

                    got = await self._try_dequeue_one(queue)
                    if not got:
                        continue

                    processed_any = True
                    qname, payload = got
                    # Delegate actual processing to provided func
                    await self.process_func(qname, payload)

                if not processed_any:
                    await asyncio.sleep(self.idle_backoff_s)

    async def start(self) -> None:
        rr = self.build_round_robin_queues()
        # Run a single loop task; semaphore gates concurrent in-flight processing
        self._task = asyncio.create_task(self._worker_loop(rr))

    async def stop(self) -> None:
        self._stop_event.set()
        # Give loop a chance to exit
        await asyncio.sleep(self.idle_backoff_s)
        if hasattr(self, "_task"):
            await self._task
