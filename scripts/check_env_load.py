"""Verify Settings loads .env: print the effective llm_provider."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402

print(settings.llm_provider)
