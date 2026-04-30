"""Idempotent: create housing.duckdb, run schema migrations, seed run_log.

Run on first setup or after schema changes. Safe to run multiple times.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import db


def main() -> int:
    print(f"Bootstrapping {db.DB_PATH}")
    with db.connect() as conn:
        db.init_schema(conn)
        existing = conn.execute("SELECT COUNT(*) FROM run_log").fetchone()[0]
    db.log_run("00_bootstrap.py", "bootstrap", "ok", message="schema initialized")
    print(f"  schema initialized — run_log had {existing} prior rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
