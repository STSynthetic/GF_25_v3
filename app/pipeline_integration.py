from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisConfig, AnalysisType

# Standard placeholder used across prompts per [CONFIG-MANAGEMENT]
PLACEHOLDER_BASE64_IMAGE = "{{BASE64_IMAGE_PLACEHOLDER}}"


@dataclass(frozen=True)
class PreparedRun:
    """Represents a fully prepared analysis run derived from configuration."""

    analysis_type: AnalysisType
    model_params: dict[str, Any]
    system_prompt: str
    user_prompt: str
    config_version: str


def render_prompt(template: str, placeholders: Mapping[str, str]) -> str:
    """Render a prompt template with simple key replacement.

    We intentionally keep templating minimal (string replace) to avoid
    introducing a runtime dependency; tests validate prompt presence.
    """
    rendered = template
    for key, value in placeholders.items():
        rendered = rendered.replace(key, value)
    return rendered


def model_params_from_config(cfg: AnalysisConfig) -> dict[str, Any]:
    """Translate AnalysisConfig.model_configuration to model param dict."""
    mc = cfg.model_configuration
    params: dict[str, Any] = {
        "model": mc.model,
        "temperature": mc.temperature,
        "top_p": mc.top_p,
        "top_k": mc.top_k,
        "num_ctx": mc.num_ctx,
    }
    # optional generation cap (num_predict) supported via alias in schema
    if mc.num_predict is not None:
        params["num_predict"] = mc.num_predict
    return params


def prepare_run(
    registry: ConfigRegistry,
    analysis_type: AnalysisType,
    *,
    base64_image: str,
    extra_placeholders: Mapping[str, str] | None = None,
) -> PreparedRun:
    """Prepare a run by resolving config, prompts, and model params.

    - Fetches the config from the registry
    - Renders prompts with BASE64 image placeholder and any extras
    - Builds model parameter dict to pass to the model runner
    """
    cfg = registry.get(analysis_type)

    placeholders: dict[str, str] = {
        PLACEHOLDER_BASE64_IMAGE: base64_image,
    }
    if extra_placeholders:
        placeholders.update(extra_placeholders)

    system_prompt = render_prompt(cfg.prompts.system_prompt, placeholders)
    user_prompt = render_prompt(cfg.prompts.user_prompt, placeholders)
    model_params = model_params_from_config(cfg)

    return PreparedRun(
        analysis_type=cfg.analysis_type,
        model_params=model_params,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        config_version=cfg.version,
    )
