from fastapi import FastAPI
from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Service health status response."""

    status: str = Field(description="Overall service status: 'ok' when healthy")
    service: str = Field(description="Service name identifier")
    version: str = Field(description="Service version string")


def create_app() -> FastAPI:
    app = FastAPI(title="GF-25 v3 Service", version="0.1.0")

    @app.get("/", tags=["root"])  # simple root for smoke-tests
    async def root() -> dict[str, str]:
        return {"message": "GF-25 v3 is running"}

    @app.get("/health", response_model=HealthStatus, tags=["health"])  # health endpoint
    async def health() -> HealthStatus:
        return HealthStatus(status="ok", service="gf-25-v3", version=app.version)

    return app


app = create_app()
