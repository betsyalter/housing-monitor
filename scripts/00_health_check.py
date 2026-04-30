"""Reads run_log; flags datasets that haven't ingested successfully recently.

Run hourly via cron / launchd. Staleness thresholds live in THRESHOLDS below.

Runbook:
  - Output goes to stdout (ok) or stderr (stale). Exit 0 = healthy, 1 = stale.
  - If alert_dispatcher is importable AND credentials are set, also pages.
  - To add a dataset: append (dataset_name, max_hours) to THRESHOLDS.
  - To silence transiently: comment out the row, commit on a branch.

The dataset name must match what ingest scripts pass to db.log_run().
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import db

# (dataset, max_hours_since_last_ok)
THRESHOLDS = [
    ("fred", 26),                # daily series, 2h slack for cron drift
    ("fhfa", 24 * 32),           # monthly cadence + slack
    ("fmp_prices", 26),
    ("sec_filings", 26),
]


def stale_datasets(now: dt.datetime | None = None) -> list[tuple[str, dt.datetime | None, int]]:
    now = now or dt.datetime.now()
    out: list[tuple[str, dt.datetime | None, int]] = []
    for dataset, max_hours in THRESHOLDS:
        last = db.last_successful_run(dataset)
        if last is None:
            out.append((dataset, None, max_hours))
            continue
        age_hours = (now - last).total_seconds() / 3600
        if age_hours > max_hours:
            out.append((dataset, last, max_hours))
    return out


def main() -> int:
    stale = stale_datasets()
    if not stale:
        print("ok — all datasets fresh")
        db.log_run("00_health_check.py", "health", "ok")
        return 0

    lines = ["STALE datasets detected:"]
    for dataset, last, max_hours in stale:
        if last is None:
            lines.append(f"  - {dataset}: never ran (threshold {max_hours}h)")
        else:
            lines.append(f"  - {dataset}: last ok {last.isoformat()} (threshold {max_hours}h)")
    msg = "\n".join(lines)
    print(msg, file=sys.stderr)
    db.log_run("00_health_check.py", "health", "stale", message=msg)

    try:
        from alert_dispatcher import send_alert_sync
        send_alert_sync(msg, priority="high")
    except Exception as e:
        print(f"  (alert not sent: {e})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
