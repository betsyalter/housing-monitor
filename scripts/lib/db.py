"""DuckDB spine. Owns the connection, schema, and run_log heartbeat.

Every ingest writes to housing.duckdb via this module. Every model reads from
it. Health checks scan run_log to detect stale ingestion.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import os
from pathlib import Path
from typing import Iterator, Optional

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.environ.get("HOUSING_DB") or REPO_ROOT / "data" / "housing.duckdb")
SNAPSHOTS_DIR = REPO_ROOT / "data" / "snapshots"

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS run_log (
        script TEXT NOT NULL,
        dataset TEXT NOT NULL,
        status TEXT NOT NULL,
        rows BIGINT,
        message TEXT,
        ran_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fred (
        series_id TEXT NOT NULL,
        obs_date DATE NOT NULL,
        value DOUBLE,
        ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (series_id, obs_date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fhfa_distribution (
        rate_bucket TEXT PRIMARY KEY,
        pct_of_outstanding DOUBLE NOT NULL,
        approx_midpoint_rate DOUBLE NOT NULL,
        est_homes_millions DOUBLE NOT NULL,
        ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tickers (
        symbol TEXT PRIMARY KEY,
        tier INTEGER,
        subsector TEXT,
        directional TEXT,
        company_name TEXT,
        sector TEXT,
        industry TEXT,
        market_cap DOUBLE,
        exchange TEXT,
        notes TEXT,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


@contextlib.contextmanager
def connect(read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH), read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    for stmt in SCHEMA:
        conn.execute(stmt)


def log_run(
    script: str,
    dataset: str,
    status: str,
    rows: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    with connect() as conn:
        init_schema(conn)
        conn.execute(
            "INSERT INTO run_log (script, dataset, status, rows, message) VALUES (?, ?, ?, ?, ?)",
            [script, dataset, status, rows, message],
        )


def last_successful_run(dataset: str) -> Optional[dt.datetime]:
    with connect(read_only=True) as conn:
        row = conn.execute(
            "SELECT MAX(ran_at) FROM run_log WHERE dataset = ? AND status = 'ok'",
            [dataset],
        ).fetchone()
    return row[0] if row and row[0] else None


def export_snapshot(table: str) -> Path:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOTS_DIR / f"{table}.parquet"
    with connect(read_only=True) as conn:
        conn.execute(f"COPY {table} TO '{out.as_posix()}' (FORMAT PARQUET)")
    return out
