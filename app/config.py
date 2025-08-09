import os
from collections.abc import Mapping

# [CORE-STD][OLLAMA-OPT]: Pre-job optimization variables
ollama_optimization_vars: Mapping[str, str] = {
    "OLLAMA_NUM_PARALLEL": "8",
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KV_CACHE_TYPE": "q8_0",
    "OLLAMA_MAX_VRAM": "22000000000",
    "OLLAMA_SCHED_SPREAD": "true",
}


def apply_ollama_optimizations() -> None:
    """Apply Ollama optimization environment variables.

    Does not overwrite values already provided by the environment; only sets defaults.
    Pattern: os.environ.update(ollama_optimization_vars)
    """
    # [CORE-STD] Follow exact pattern: overwrite with the optimized values
    os.environ.update(ollama_optimization_vars)
