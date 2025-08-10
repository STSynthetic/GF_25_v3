from __future__ import annotations

import asyncio
from typing import Any

import httpx
from pydantic import BaseModel, Field, HttpUrl

from app.api.goflow_models import (
    Job,
    JobStatusUpdate,
    ReportRequest,
    ReportResponse,
    ResultPayload,
)

try:  # Optional retry support per [ASYNC-CORE]
    from tenacity import (  # type: ignore
        AsyncRetrying,
        RetryError,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential_jitter,
    )
except Exception:  # pragma: no cover - tests will not rely on real tenacity
    AsyncRetrying = None  # type: ignore
    RetryError = Exception  # type: ignore
    retry_if_exception_type = None  # type: ignore
    stop_after_attempt = None  # type: ignore
    wait_exponential_jitter = None  # type: ignore


class GoFlowConfig(BaseModel):
    base_url: HttpUrl = Field(description="GoFlow API base URL")
    api_key: str = Field(description="Bearer API key for GoFlow")
    timeout_seconds: float = Field(default=30.0, description="HTTP timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Max retry attempts for requests")


class GoFlowClient:
    """Async GoFlow API client with typed config and retry policy."""

    def __init__(self, cfg: GoFlowConfig) -> None:
        self.cfg = cfg
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> GoFlowClient:
        async with self._lock:
            if self._client is None:
                self._client = httpx.AsyncClient(
                    base_url=str(self.cfg.base_url),
                    timeout=self.cfg.timeout_seconds,
                    headers={
                        "Authorization": f"Bearer {self.cfg.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        async with self._lock:
            if self._client is not None:
                await self._client.aclose()
                self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized; use 'async with GoFlowClient(...)' context")
        return self._client

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        # Basic retry using tenacity if available
        if AsyncRetrying is None or self.cfg.max_retries <= 0:
            return await self.client.request(method, url, **kwargs)

        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self.cfg.max_retries),
            wait=wait_exponential_jitter(initial=0.2, max=2.0),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        ):
            with attempt:
                resp = await self.client.request(method, url, **kwargs)
                # Consider retry for 5xx
                if 500 <= resp.status_code < 600:
                    raise httpx.HTTPStatusError("server error", request=resp.request, response=resp)
                return resp

        # Should not reach here
        raise RuntimeError("Retry loop exited unexpectedly")

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._request("GET", path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def post(self, path: str, json: Dict[str, Any] | None = None) -> Dict[str, Any]:  # noqa: A002
        resp = await self._request("POST", path, json=json)
        resp.raise_for_status()
        return resp.json()

    # ---- Task 7.2: Job Acquisition and Status Management ----
    async def get_next_job(self) -> Job:
        """Fetch the next available job for this agent."""
        data = await self.get("/api/v1/agent/next-job")
        return Job.model_validate(data)

    async def update_project_status(
        self, project_id: str, update: JobStatusUpdate
    ) -> Dict[str, Any]:
        """Update processing status for a project (agent heartbeat/progress)."""
        path = f"/api/v1/agent/projects/{project_id}/status"
        return await self.post(path, json=update.model_dump())

    # ---- Task 7.3: Result Submission and Report Generation ----
    async def submit_analysis_result(self, payload: ResultPayload) -> Dict[str, Any]:
        """Submit analysis result for a specific project/media/analysis."""
        path = (
            f"/api/v1/agent/projects/{payload.project_id}/media/"
            f"{payload.media_id}/analysis/{payload.analysis_id}"
        )
        return await self.post(path, json=payload.model_dump())

    async def generate_project_report(self, req: ReportRequest) -> ReportResponse:
        """Trigger report generation for a project and return report info."""
        path = f"/api/v1/agent/projects/{req.project_id}/reports"
        data = await self.post(path, json=req.model_dump())
        return ReportResponse.model_validate(data)
