import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package is importable during tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
