import copy
import os

import pytest

from app.config import apply_ollama_optimizations, ollama_optimization_vars


@pytest.mark.parametrize(
    "key, value",
    list(ollama_optimization_vars.items()),
)
def test_apply_ollama_optimizations_overwrites_env(
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: str,
) -> None:
    # Backup current env and ensure a conflicting value exists
    original = copy.deepcopy(os.environ)
    try:
        monkeypatch.setenv(key, "DIFFERENT")
        apply_ollama_optimizations()
        assert os.environ[key] == value
    finally:
        # Restore original environment
        for k in list(os.environ.keys()):
            if k not in original:
                del os.environ[k]
        for k, v in original.items():
            os.environ[k] = v
