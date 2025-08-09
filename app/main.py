from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app import models
from app.config import apply_ollama_optimizations
from app.config_hot_reload import start_config_watcher_task
from app.config_loader import ConfigRegistry
from app.logging_config import init_logging
from app.metrics import metrics_endpoint, metrics_middleware
from app.models import preload_qwen_models
from app.routes.config import router as config_router


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

        # Start config hot-reload watcher per Task 2.4
        app.state.config_registry = ConfigRegistry()
        configs_dir = Path(__file__).resolve().parents[1] / "configs"
        watcher_task, stop_event = start_config_watcher_task(configs_dir, app.state.config_registry)
        app.state._config_watcher_task = watcher_task
        app.state._config_watcher_stop = stop_event
        try:
            yield
        finally:
            # Stop watcher gracefully
            stop_event.set()
            watcher_task.cancel()
            try:
                await watcher_task
            except Exception:
                pass

    app = FastAPI(title="GF-25 v3 Service", version="0.1.0", lifespan=lifespan)

    # Metrics middleware
    app.middleware("http")(metrics_middleware)

    # Config API
    app.include_router(config_router)

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
