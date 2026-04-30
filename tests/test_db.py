from __future__ import annotations


def test_bootstrap_creates_schema(temp_db):
    db = temp_db
    with db.connect() as conn:
        db.init_schema(conn)
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert {"run_log", "fred", "fhfa_distribution", "tickers"} <= tables


def test_log_run_writes_row(temp_db):
    db = temp_db
    with db.connect() as conn:
        db.init_schema(conn)
    db.log_run("test_script.py", "fred", "ok", rows=42)
    with db.connect(read_only=True) as conn:
        row = conn.execute(
            "SELECT script, dataset, status, rows FROM run_log WHERE script = 'test_script.py'"
        ).fetchone()
    assert row == ("test_script.py", "fred", "ok", 42)


def test_last_successful_run(temp_db):
    db = temp_db
    with db.connect() as conn:
        db.init_schema(conn)
    db.log_run("01_fred_pull.py", "fred", "ok", rows=100)
    assert db.last_successful_run("fred") is not None
    assert db.last_successful_run("does_not_exist") is None


def test_init_schema_is_idempotent(temp_db):
    db = temp_db
    with db.connect() as conn:
        db.init_schema(conn)
        db.init_schema(conn)
        db.init_schema(conn)
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert "run_log" in tables
