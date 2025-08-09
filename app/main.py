from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import models
from app.config import apply_ollama_optimizations
from app.logging_config import init_logging
from app.metrics import metrics_endpoint, metrics_middleware
from app.models import preload_qwen_models


class HealthStatus(BaseModel):
    """Service health status response."""

    status: str = Field(description="Overall service status: 'ok' when healthy")
    service: str = Field(description="Service name identifier")
    version: str = Field(description="Service version string")


def create_app() -> FastAPI:
    # Initialize logging first
    init_logging()

    # [CORE-STD][OLLAMA-OPT] Apply Ollama env optimizations at startup
    apply_ollama_optimizations()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Preload required models asynchronously at startup per [MODEL-CONFIG]
        await preload_qwen_models()
        yield

    app = FastAPI(title="GF-25 v3 Service", version="0.1.0", lifespan=lifespan)

    # Metrics middleware
    app.middleware("http")(metrics_middleware)

    @app.get("/", tags=["root"])  # simple root for smoke-tests
    async def root() -> dict[str, str]:
        return {"message": "GF-25 v3 is running"}

    @app.get("/health", response_model=HealthStatus, tags=["health"])  # health endpoint
    async def health() -> HealthStatus:
        return HealthStatus(status="ok", service="gf-25-v3", version=app.version)

    # Expose Prometheus metrics
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return await metrics_endpoint()

    # Liveness probe
    @app.get("/live", tags=["health"], include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    # Readiness probe: checks Ollama availability quickly
    @app.get("/ready", tags=["health"], include_in_schema=False)
    async def ready() -> dict[str, str]:
        is_ready = await models.check_ollama_ready()
        return {"ready": "true" if is_ready else "false"}

    return app


app = create_app()
