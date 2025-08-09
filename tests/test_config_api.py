from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_get_config_success(tmp_path: Path):
    # Create a minimal configs dir with one valid config file
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "activities.yaml").write_text(
        """
analysis_type: activities
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
  system_prompt: sys
  user_prompt: user
validation_constraints:
  rules: [no meta]
performance_targets:
  throughput_target: "800+ per worker acceptable"
  success_rate_target: 0.95
qa_stages: [structural, content_quality, domain_expert]
        """,
        encoding="utf-8",
    )

    app = create_app()
    # Override configs path used by app by monkeypatching in place, via app.state after startup
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Reload from our tmp configs dir for this test
            app.state.config_registry.load_all_configs(cfg_dir)
            resp = await ac.get("/config/activities")
            assert resp.status_code == 200
            data = resp.json()
            assert data["analysis_type"] == "activities"
            assert data["model_configuration"]["model"] == "qwen2.5vl:32b"


@pytest.mark.asyncio
async def test_get_config_not_found(tmp_path: Path):
    # Empty configs dir
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Ensure registry exists but has no entries
            app.state.config_registry._configs.clear()
            resp = await ac.get("/config/unknown_type")
            assert resp.status_code == 422 or resp.status_code == 404
