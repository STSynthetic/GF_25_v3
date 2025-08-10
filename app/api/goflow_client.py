from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import logging
import httpx
from pydantic import BaseModel, Field, HttpUrl

from app.api.goflow_models import (
    Job,
    JobStatusUpdate,
    ReportRequest,
    ReportResponse,
    ResultPayload,
)
from app.api.goflow_errors import (
    GoFlowAuthError,
    GoFlowClientError,
    GoFlowError,
    GoFlowNotFound,
    GoFlowRetryableError,
    GoFlowServerError,
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
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._log = logging.getLogger(__name__)

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
        # Tenacity-based retry path
        if AsyncRetrying is not None and self.cfg.max_retries > 0:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(self.cfg.max_retries),
                wait=wait_exponential_jitter(initial=0.2, max=2.0),
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ReadTimeout, GoFlowRetryableError)
                ),
            ):
                with attempt:
                    resp = await self.client.request(method, url, **kwargs)
                    if 500 <= resp.status_code < 600:
                        self._log.warning(
                            "server 5xx on %s %s -> %s", method, url, resp.status_code
                        )
                        raise GoFlowServerError(f"server error {resp.status_code}")
                    self._raise_for_status_map(resp)
                    return resp

            raise RuntimeError("Retry loop exited unexpectedly")

        # Fallback retry when tenacity is unavailable
        attempts = max(1, self.cfg.max_retries or 1)
        last_exc: Optional[Exception] = None
        for i in range(attempts):
            try:
                resp = await self.client.request(method, url, **kwargs)
                if 500 <= resp.status_code < 600:
                    self._log.warning(
                        "server 5xx on %s %s attempt %d/%d -> %s",
                        method,
                        url,
                        i + 1,
                        attempts,
                        resp.status_code,
                    )
                    last_exc = GoFlowServerError(f"server error {resp.status_code}")
                    await asyncio.sleep(min(2**i * 0.2, 2.0))
                    continue
                self._raise_for_status_map(resp)
                return resp
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                self._log.warning(
                    "network error on %s %s attempt %d/%d: %s",
                    method,
                    url,
                    i + 1,
                    attempts,
                    e,
                )
                last_exc = GoFlowRetryableError(str(e))
                await asyncio.sleep(min(2**i * 0.2, 2.0))
                continue
        assert last_exc is not None
        raise last_exc

    def _raise_for_status_map(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        code = resp.status_code
        if code in (401, 403):
            raise GoFlowAuthError(f"auth error {code}")
        if code == 404:
            raise GoFlowNotFound("not found")
        if 400 <= code < 500:
            raise GoFlowClientError(f"client error {code}")
        if 500 <= code < 600:
            raise GoFlowServerError(f"server error {code}")
        raise GoFlowError(f"unexpected status {code}")

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
