from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisConfig, AnalysisType

router = APIRouter(prefix="/config", tags=["config"])


def get_registry(request: Request) -> ConfigRegistry:
    reg = getattr(request.app.state, "config_registry", None)
    if reg is None:
        raise HTTPException(status_code=503, detail="Configuration registry not initialized")
    return reg


@router.get("/{analysis_type}", response_model=AnalysisConfig)
async def get_analysis_config(
    analysis_type: AnalysisType,
    registry: ConfigRegistry = Depends(get_registry),  # noqa: B008 - FastAPI DI pattern
) -> AnalysisConfig:
    try:
        return registry.get(analysis_type)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown analysis type: {analysis_type}",
        ) from exc
