#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ANALYSIS_TYPES = [
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
]

TEMPLATE = """analysis_type: {atype}
version: "1.0.0"
model_configuration:
  model: qwen2.5vl:32b
  temperature: 0.1
  top_p: 0.9
  top_k: 40
  num_ctx: 32768
vision_optimization:
  max_edge_pixels: 1344
  preserve_aspect_ratio: true
parallel_processing:
  max_concurrency: 8
prompts:
  system_prompt: |
    # system prompt for {atype} analysis (externalized)
  user_prompt: |
    # user prompt template for {atype} analysis (externalized)
validation_constraints:
  rules:
    - no meta-descriptive language
    - json output only
performance_targets:
  throughput_target: "800+ per worker acceptable"
  success_rate_target: 0.95
qa_stages:
  - structural
  - content_quality
  - domain_expert
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    configs_dir = root / "configs"
    os.makedirs(configs_dir, exist_ok=True)

    for at in ANALYSIS_TYPES:
        path = configs_dir / f"{at}.yaml"
        if not path.exists():
            path.write_text(TEMPLATE.format(atype=at), encoding="utf-8")
        else:
            # Overwrite to keep templates in sync
            path.write_text(TEMPLATE.format(atype=at), encoding="utf-8")


if __name__ == "__main__":
    main()
