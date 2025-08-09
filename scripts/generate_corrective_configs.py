from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
# Ensure repository root is on sys.path so 'app' package is importable
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config_schema import AnalysisType  # noqa: E402

TEMPLATES_DIR = ROOT / "_project" / "templates"
STAGES_DIR = TEMPLATES_DIR / "corrective_stages"
BASE_TEMPLATE = TEMPLATES_DIR / "corrective_config.template.yaml"
OUTPUT_DIR = ROOT / "configs_corrective"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_corrective_config(analysis_type: AnalysisType) -> dict:
    base = load_yaml(BASE_TEMPLATE)
    structural = load_yaml(STAGES_DIR / "structural.yaml")
    content_quality = load_yaml(STAGES_DIR / "content_quality.yaml")
    domain_expert = load_yaml(STAGES_DIR / "domain_expert.yaml")

    name = analysis_type.value.replace("_", " ")

    base_meta = base.get("metadata", {})
    base_meta["name"] = f"{name} corrective"
    base_meta["analysis_type"] = analysis_type.value
    base["metadata"] = base_meta

    base["corrective_stages"] = {
        "structural": structural,
        "content_quality": content_quality,
        "domain_expert": domain_expert,
    }
    return base


def filename_for(analysis_type: AnalysisType) -> str:
    return f"{analysis_type.value}_corrective.yaml"


def validate_config_shape(cfg: dict) -> None:
    # Minimal structural validation for presence of keys
    if "metadata" not in cfg:
        raise ValueError("missing metadata block")
    if "corrective_stages" not in cfg:
        raise ValueError("missing corrective_stages block")
    stages = cfg["corrective_stages"]
    for key in ("structural", "content_quality", "domain_expert"):
        if key not in stages:
            raise ValueError(f"missing stage: {key}")
        stage = stages[key]
        for f in ("system_prompt", "user_prompt", "optimization_parameters"):
            if f not in stage:
                raise ValueError(f"stage '{key}' missing field: {f}")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for analysis_type in AnalysisType:
        cfg = build_corrective_config(analysis_type)
        validate_config_shape(cfg)
        out_path = OUTPUT_DIR / filename_for(analysis_type)
        out_path.write_text(
            yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        count += 1

    print(f"Generated {count} corrective configs into {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
