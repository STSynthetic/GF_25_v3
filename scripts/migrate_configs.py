#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"

ANALYSIS_TYPES = {
    "activities",
    "ages",
    "body_shapes",
    "captions",
    "category",
    "colors",
    "composition",
    "emotions",
    "ethnicity",
    "events",
    "gender",
    "lighting",
    "locations",
    "objects",
    "occlusions",
    "outfits",
    "relationships",
    "scene_description",
    "themes",
    "time_of_day",
    "weather",
}


def ensure_block(d: dict[str, Any], key: str, default: Any) -> dict[str, Any]:
    if key not in d or not isinstance(d[key], dict):
        d[key] = {}
    # only set defaults for missing keys to preserve existing values
    for k, v in default.items():
        d[key].setdefault(k, v)
    return d[key]


def main() -> int:
    if not CONFIG_DIR.exists():
        print(f"configs/ directory not found at {CONFIG_DIR}", file=sys.stderr)
        return 1

    updated = 0
    for yml in sorted(CONFIG_DIR.glob("*.yaml")):
        with yml.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        stem = yml.stem
        # Derive analysis_type from either existing key or filename
        analysis_type = data.get("analysis_type") or stem
        if analysis_type not in ANALYSIS_TYPES:
            # best-effort: some filenames may differ (e.g., scene_description)
            # keep existing value if present; otherwise leave as stem
            pass

        # Top-level required
        data.setdefault("analysis_type", analysis_type)
        data.setdefault("version", data.get("version", "1.0.0"))

        # metadata block (optional but recommended)
        metadata_defaults = {
            "name": analysis_type.replace("_", " ").title(),
            "version": data["version"],
            "description": f"Configuration for {analysis_type} analysis",
            "analysis_type": data["analysis_type"],
        }
        ensure_block(data, "metadata", metadata_defaults)

        # model_configuration
        mc_defaults = {
            "model": data.get("model_configuration", {}).get("model", "qwen2.5vl:32b"),
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "num_ctx": 32768,
            # Do not set num_predict/max_tokens by default; leave to pipeline sizing
        }
        ensure_block(data, "model_configuration", mc_defaults)

        # vision_optimization
        vo_defaults = {
            "max_edge_pixels": 1344,
            "preserve_aspect_ratio": True,
        }
        ensure_block(data, "vision_optimization", vo_defaults)

        # parallel_processing
        pp_defaults = {
            "max_concurrency": 8,
            "worker_count": 8,
            "batch_size": 1,
            "timeout_seconds": 60,
        }
        ensure_block(data, "parallel_processing", pp_defaults)

        # prompts
        pr_defaults = {
            "system_prompt": "# system prompt (externalized)",
            "user_prompt": "# user prompt template",
        }
        ensure_block(data, "prompts", pr_defaults)

        # validation_constraints
        vc_defaults = {
            "rules": [
                "no meta-descriptive language",
                "json output only",
            ],
            "output_format": "json",
            "required_fields": [],
            "data_types": {},
        }
        ensure_block(data, "validation_constraints", vc_defaults)

        # performance_targets
        pt_defaults = {
            "throughput_target": "800+ per worker acceptable",
            "success_rate_target": 0.95,
            "max_latency_ms": 2000,
            "min_accuracy": 0.9,
            "throughput_goals": [">= 800/worker sustained"],
        }
        ensure_block(data, "performance_targets", pt_defaults)

        # qa_stages list
        data.setdefault(
            "qa_stages",
            ["structural", "content_quality", "domain_expert"],
        )

        with yml.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        updated += 1
        print(f"updated {yml.relative_to(ROOT)}")

    print(f"Updated {updated} YAML config(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
