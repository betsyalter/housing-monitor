"""Observability watchdog — daily health check on the cron pipeline.

Runs once a day (folded into run_daily.sh after Script 10). Checks:
  - Cron logs got entries in the last N hours
  - Stream logs (sec_stream, news_stream) got fresh rows
  - housing_context.md / .json are fresh
  - Each FRED column in fred_housing.csv has recent data
  - API key sanity (FMP, sec-api, Anthropic)

If anything's red, sends a single email with the failing checks. If
everything's green, no email — silent good days.

Designed to be the canary in the coal mine. Without this, a silently
dead pipeline would only get noticed when alerts mysteriously stop —
and "no alerts" is indistinguishable from "no events worth alerting on"
for weeks.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from config import (DATA_DIR, FMP_API_KEY, SEC_API_KEY, FRED_API_KEY,
                    ANTHROPIC_API_KEY)

import pandas as pd
import requests
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(REPO_ROOT, "logs")
CONTEXT_MD = os.path.join(REPO_ROOT, "housing_context.md")
CONTEXT_JSON = os.path.join(REPO_ROOT, "housing_context.json")
SEC_LOG = os.path.join(DATA_DIR, "sec_stream_log.csv")
NEWS_LOG = os.path.join(DATA_DIR, "news_stream_log.csv")
FRED_CSV = os.path.join(DATA_DIR, "fred_housing.csv")

from alert_dispatcher import send_email


def _hours_since_modified(path):
    if not os.path.exists(path):
        return None
    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    return (datetime.now(timezone.utc) - mtime).total_seconds() / 3600


def _hours_since_latest_row(csv_path, ts_col):
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path, usecols=[ts_col])
        if df.empty:
            return None
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
        latest = df[ts_col].max()
        if pd.isna(latest):
            return None
        return (pd.Timestamp.now(tz="UTC") - latest).total_seconds() / 3600
    except Exception:
        return None


def check_cron_logs():
    """Each launchd job's log file should have been written to recently."""
    expected = [
        ("logs/hourly.log", 2.0, "hourly cron (06b → 11)"),
        ("logs/news_poll.log", 0.5, "news poll cron (every 5 min)"),
        ("logs/daily.log", 26.0, "daily cron (6 AM ET)"),
    ]
    failures = []
    for rel, max_hours, label in expected:
        path = os.path.join(REPO_ROOT, rel)
        h = _hours_since_modified(path)
        if h is None:
            failures.append(f"❌ {label}: log file missing ({rel})")
        elif h > max_hours:
            failures.append(f"❌ {label}: log untouched for {h:.1f}h "
                            f"(threshold {max_hours}h)")
    return failures


def check_data_freshness():
    """Stream logs and dashboard outputs should be fresh."""
    failures = []
    # SEC stream — should refresh hourly
    h = _hours_since_latest_row(SEC_LOG, "filed_at")
    if h is None:
        failures.append("⚠ sec_stream_log.csv: missing or empty")
    # 8-K filings can have multi-day quiet periods; threshold relaxed to 72h
    elif h > 72:
        failures.append(f"⚠ sec_stream_log.csv: latest filing {h:.1f}h old "
                        "(possibly OK on quiet days)")

    # News stream — should refresh in market hours, more frequent than SEC
    h = _hours_since_latest_row(NEWS_LOG, "detected_at")
    if h is None:
        failures.append("❌ news_stream_log.csv: missing or empty")
    elif h > 6:
        failures.append(f"❌ news_stream_log.csv: no new rows in {h:.1f}h")

    # Daily report
    h = _hours_since_modified(CONTEXT_MD)
    if h is None:
        failures.append("❌ housing_context.md: file missing")
    elif h > 26:
        failures.append(f"❌ housing_context.md: not refreshed in {h:.1f}h "
                        "(daily cron at 6 AM ET should refresh nightly)")

    h = _hours_since_modified(CONTEXT_JSON)
    if h is None:
        failures.append("❌ housing_context.json: file missing")
    elif h > 26:
        failures.append(f"❌ housing_context.json: not refreshed in {h:.1f}h")

    return failures


def check_fred_freshness():
    """Each tracked FRED column should have data within its expected cadence."""
    if not os.path.exists(FRED_CSV):
        return ["❌ fred_housing.csv: missing"]
    try:
        df = pd.read_csv(FRED_CSV)
        df["date"] = pd.to_datetime(df["date"])
    except Exception as e:
        return [f"❌ fred_housing.csv: failed to parse ({e})"]

    failures = []
    # cadence per column (max staleness in days before flagging)
    cadence = {
        "mortgage_rate_30yr": 14,    # Freddie Mac weekly
        "existing_home_sales_saar": 60,  # NAR monthly + reporting lag
        "housing_starts_total": 60,
        "building_permits": 60,
        "median_home_price": 90,     # quarterly
        "case_shiller_national": 90, # 2-month lag
    }
    today = pd.Timestamp.now()
    for col, max_days in cadence.items():
        if col not in df.columns:
            failures.append(f"❌ FRED column '{col}' missing from CSV")
            continue
        sub = df[["date", col]].dropna()
        if sub.empty:
            failures.append(f"❌ FRED '{col}' is all NaN")
            continue
        latest = sub["date"].max()
        days = (today - latest).days
        if days > max_days:
            failures.append(f"⚠ FRED '{col}' latest is {latest.date()} "
                            f"({days}d old, threshold {max_days}d)")

    # Special check: existing_home_sales_saar coverage (we know this is broken)
    if "existing_home_sales_saar" in df.columns:
        ehs_count = df["existing_home_sales_saar"].notna().sum()
        if ehs_count < 24:
            failures.append(f"❌ FRED 'existing_home_sales_saar' has only "
                            f"{ehs_count} non-null obs (expected 25+ years; "
                            "Script 01 fix pending — see Slack to Wyatt)")

    return failures


def check_api_keys():
    """Quick sanity ping per API to confirm keys are still valid."""
    failures = []

    if not FMP_API_KEY:
        failures.append("❌ FMP_API_KEY missing from ~/.env")
    else:
        try:
            r = requests.get(
                f"https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey={FMP_API_KEY}",
                timeout=10)
            if r.status_code == 401:
                failures.append("❌ FMP_API_KEY invalid (401)")
            elif r.status_code == 429:
                failures.append("⚠ FMP rate-limited (429) — usually transient")
            elif r.status_code != 200:
                failures.append(f"⚠ FMP returned {r.status_code}")
        except Exception as e:
            failures.append(f"⚠ FMP unreachable: {type(e).__name__}")

    if not SEC_API_KEY:
        failures.append("❌ SEC_API_KEY missing from ~/.env")
    else:
        try:
            r = requests.post(
                f"https://api.sec-api.io?token={SEC_API_KEY}",
                json={"query": "formType:\"8-K\"", "from": "0", "size": "1"},
                timeout=10)
            if r.status_code != 200:
                failures.append(f"❌ sec-api returned {r.status_code}")
        except Exception as e:
            failures.append(f"⚠ sec-api unreachable: {type(e).__name__}")

    if not FRED_API_KEY:
        failures.append("⚠ FRED_API_KEY missing (Wyatt's Script 01 won't refresh)")

    if not ANTHROPIC_API_KEY:
        failures.append("⚠ ANTHROPIC_API_KEY missing (Script 07 quarterly "
                        "homebuilder-ops re-extraction won't work)")

    return failures


def main():
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    all_failures = []

    print(f"=== Housing-monitor watchdog @ {now_iso} ===\n")

    cron = check_cron_logs()
    print(f"Cron logs: {'✓ healthy' if not cron else f'{len(cron)} issues'}")
    for f in cron:
        print(f"  {f}")
    all_failures.extend(cron)

    data = check_data_freshness()
    print(f"\nData freshness: {'✓ healthy' if not data else f'{len(data)} issues'}")
    for f in data:
        print(f"  {f}")
    all_failures.extend(data)

    fred = check_fred_freshness()
    print(f"\nFRED columns: {'✓ healthy' if not fred else f'{len(fred)} issues'}")
    for f in fred:
        print(f"  {f}")
    all_failures.extend(fred)

    api = check_api_keys()
    print(f"\nAPI keys: {'✓ healthy' if not api else f'{len(api)} issues'}")
    for f in api:
        print(f"  {f}")
    all_failures.extend(api)

    if all_failures:
        # Send single summary email
        n_red = sum(1 for f in all_failures if f.startswith("❌"))
        n_yellow = sum(1 for f in all_failures if f.startswith("⚠"))
        subject = f"[HOUSING-WATCHDOG] {n_red} red, {n_yellow} yellow"
        body = (f"Watchdog ran at {now_iso} and found {len(all_failures)} issues:\n\n"
                + "\n".join(all_failures)
                + "\n\nLog: ~/housing_monitor/logs/daily.log")
        try:
            send_email(subject, body)
            print(f"\n📧 Watchdog email sent ({n_red} red, {n_yellow} yellow)")
        except Exception as e:
            print(f"\n[FAIL] Watchdog email failed: {e}")
    else:
        print("\n✓ All checks passed. No email sent (silent good days)")


if __name__ == "__main__":
    main()
