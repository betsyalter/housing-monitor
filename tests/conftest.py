"""pytest: make scripts/ importable so tests can `from lib.coiled_spring import ...`"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
