"""pytest: make scripts/ importable, provide a tmp DuckDB fixture."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.duckdb"
    monkeypatch.setenv("HOUSING_DB", str(db_path))
    from lib import db
    importlib.reload(db)
    return db
