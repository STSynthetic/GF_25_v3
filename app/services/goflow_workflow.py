from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

from app.api.goflow_client import GoFlowClient
from app.api.goflow_models import Job, JobStatusUpdate, ReportRequest, ResultPayload


class ProcessResult(BaseModel):
    """Output of the user-supplied processing function."""

    result: dict[str, Any] = Field(description="Structured analysis result data")
    meta: dict[str, Any] | None = Field(default=None, description="Optional metadata")


ProcessFn = Callable[[Job], Awaitable[ProcessResult]]


class GoFlowWorkflow:
    """Integrates GoFlow client into a single job lifecycle.

    Usage:
        async with GoFlowClient(cfg) as client:
            wf = GoFlowWorkflow(client)
            await wf.run_once(process_fn)
    """

    def __init__(self, client: GoFlowClient, *, logger: logging.Logger | None = None) -> None:
        self.client = client
        self.log = logger or logging.getLogger(__name__)

    async def run_once(self, process_fn: ProcessFn, *, generate_report: bool = True) -> bool:
        """Run a single job lifecycle.

        Returns True if a job was processed, False if no job was available.
        """
        # Acquire next job
        job: Job
        try:
            job = await self.client.get_next_job()
        except Exception as ex:
            # No job or fetch error should be surfaced to caller
            self.log.info("no job acquired or fetch failed: %s", ex)
            return False

        self.log.info("acquired job: %s", job.job_id)

        # Update status: in progress
        await self._safe_status_update(
            job.project_id, JobStatusUpdate(status="in_progress", progress=0.0)
        )

        try:
            # Process job via user provided function
            pr = await process_fn(job)
            # Submit result
            payload = ResultPayload(
                project_id=job.project_id,
                media_id=job.media_id,
                analysis_id=job.analysis_id,
                result=pr.result,
                meta=pr.meta,
            )
            await self.client.submit_analysis_result(payload)
            self.log.info("submitted result for job: %s", job.job_id)

            # Generate report if requested
            if generate_report:
                rep = await self.client.generate_project_report(
                    ReportRequest(project_id=job.project_id)
                )
                self.log.info("report requested: %s status=%s", rep.report_id, rep.status)

            # Final status: completed
            await self._safe_status_update(
                job.project_id, JobStatusUpdate(status="completed", progress=1.0)
            )
            return True
        except Exception as ex:  # pragma: no cover - exercised in tests via fake exception
            self.log.exception("job processing failed: %s", ex)
            await self._safe_status_update(
                job.project_id, JobStatusUpdate(status="failed", detail=str(ex))
            )
            return True

    async def _safe_status_update(self, project_id: str, update: JobStatusUpdate) -> None:
        try:
            await self.client.update_project_status(project_id, update)
        except Exception as ex:  # pragma: no cover
            self.log.warning("status update failed: %s", ex)
