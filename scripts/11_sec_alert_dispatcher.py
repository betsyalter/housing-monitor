"""Read sec_stream_log.csv, classify each new 8-K, send emails.

Designed to run hourly via launchd. Maintains its own state in
data/alert_state.json so re-runs don't re-alert.

Priority classification (per coordination with codex):
- HIGH (per-event email):
    Item 4.02 (non-reliance on prior financials) — anywhere in universe
    Item 1.03 (bankruptcy)                       — anywhere
    Item 2.01 (acquisition/disposition)          — Tier 1
    Item 5.02 (officer departures)               — Tier 1
    Item 1.01 (material agreement)               — Tier 1 + keyword match
                (merger, acquisition, sale, asset purchase, strategic alternative,
                 joint venture)
- MEDIUM (digest, one email per run):
    Item 2.02 (earnings)                         — Tier 1+2
    Item 8.01 (other material)                   — Tier 1
    Item 1.01 (material agreement)               — Tier 1 without keyword match
- LOW (skip):
    everything else 06b lets through

Failure modes:
- SMTP transient → log, do not mark accession as seen → retries next run
- First run (empty state) → alert only on last 24h, mark older as seen-but-not-sent
- Missing CSV → exit cleanly
- Digest is one transaction: if SMTP fails on the digest, none of its
  component accessions are marked seen
"""

import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
from datetime import datetime, timezone, timedelta

from alert_dispatcher import send_email

LOG_CSV = os.path.join(DATA_DIR, "sec_stream_log.csv")
STATE_PATH = os.path.join(DATA_DIR, "alert_state.json")

TIER1_SUBSECTORS = {
    "Homebuilders", "Mortgage Originators", "Title Insurance",
    "RE Brokerages", "Land Developers",
}
TIER12_SUBSECTORS = TIER1_SUBSECTORS | {
    "SFR REITs", "Home Improvement", "Moving/Storage", "Home Furnishings",
    "Appliances", "Building Products",
}

KEYWORD_PROMOTE_101 = re.compile(
    r"\b(merger|acquisition|acquir(e|ed|ing)|sale|asset\s+purchase|"
    r"strategic\s+alternative|joint\s+venture|divest|spin[- ]?off)\b",
    re.IGNORECASE,
)

SEEN_TTL_DAYS = 30
FIRST_RUN_LOOKBACK_HOURS = 24


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"last_run_utc": None, "seen_accessions": {}}
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"WARN: could not read alert_state.json ({e}). Starting fresh.")
        return {"last_run_utc": None, "seen_accessions": {}}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def prune_seen(seen_accessions, now):
    cutoff = now - timedelta(days=SEEN_TTL_DAYS)
    return {
        a: ts for a, ts in seen_accessions.items()
        if pd.to_datetime(ts, utc=True) >= cutoff
    }


def load_universe():
    """Returns ticker → subsector dict for tier classification."""
    path = os.path.join(DATA_DIR, "fmp_tickers.csv")
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    out = {}
    for _, r in df.iterrows():
        ticker = str(r.get("ticker", "")).strip()
        sub = str(r.get("subsector", "")).strip()
        if ticker:
            out[ticker] = sub
    return out


def classify(row, universe):
    """Return ('high'|'medium'|'low', reason)."""
    items = str(row.get("item_codes", "") or "")
    item_set = set(filter(None, items.split("|")))
    ticker = str(row.get("ticker", "") or "").upper()
    subsector = universe.get(ticker, "")
    title_excerpt = str(row.get("title", "") or "") + " " + str(row.get("excerpt", "") or "")

    # HIGH: universal (anywhere in universe)
    if "4.02" in item_set:
        return "high", "Item 4.02 — non-reliance on prior financials"
    if "1.03" in item_set:
        return "high", "Item 1.03 — bankruptcy"

    in_t1 = subsector in TIER1_SUBSECTORS
    in_t12 = subsector in TIER12_SUBSECTORS

    # HIGH: Tier 1
    if in_t1 and "2.01" in item_set:
        return "high", "Item 2.01 — acquisition/disposition (Tier 1)"
    if in_t1 and "5.02" in item_set:
        return "high", "Item 5.02 — officer departure (Tier 1)"
    if in_t1 and "1.01" in item_set and KEYWORD_PROMOTE_101.search(title_excerpt):
        return "high", "Item 1.01 — material agreement w/ M&A keywords (Tier 1)"

    # MEDIUM
    if in_t12 and "2.02" in item_set:
        return "medium", "Item 2.02 — earnings (Tier 1+2)"
    if in_t1 and "8.01" in item_set:
        return "medium", "Item 8.01 — other material (Tier 1)"
    if in_t1 and "1.01" in item_set:
        return "medium", "Item 1.01 — material agreement (Tier 1, routine)"

    return "low", ""


def _filed_str(row):
    """Coerce row['filed_at'] (pandas Timestamp or str) into ISO string."""
    v = row.get("filed_at", "")
    if pd.isna(v):
        return ""
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d %H:%M %Z").strip()
    return str(v)


def _filed_date(row):
    v = row.get("filed_at", "")
    if pd.isna(v):
        return ""
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10]


def format_high_email(row, reason):
    ticker = row.get("ticker", "?")
    items = row.get("item_codes", "")
    title = (row.get("title", "") or "")[:60]
    company = row.get("company_name", "")
    filed_at = _filed_str(row)
    excerpt = (row.get("excerpt", "") or "")[:600]
    primary = row.get("primary_doc_url", "")
    filing = row.get("filing_url", "")
    raw_path = row.get("raw_text_path", "")

    subject = f"[HOUSING-HIGH] {ticker} 8-K Item {items} — {title}"
    body = (
        f"{ticker} — {company}\n"
        f"Filed: {filed_at}\n"
        f"Items: {items}\n"
        f"Trigger: {reason}\n\n"
        f"Primary doc: {primary}\n"
        f"Filing index: {filing}\n"
        f"Raw text saved at: {raw_path}\n\n"
        f"Excerpt:\n{excerpt}\n"
    )
    return subject, body


def format_digest_email(rows_with_reasons):
    n = len(rows_with_reasons)
    subject = f"[HOUSING-DIGEST] {n} medium-priority filings"
    lines = ["Medium-priority 8-K filings since last run:\n"]
    for row, reason in rows_with_reasons:
        ticker = row.get("ticker", "?")
        items = row.get("item_codes", "")
        title = (row.get("title", "") or "")[:80]
        filed_at = _filed_date(row)
        primary = row.get("primary_doc_url", "")
        lines.append(f"• {filed_at} [{ticker}] items {items} — {title}")
        lines.append(f"    Trigger: {reason}")
        lines.append(f"    Doc: {primary}\n")
    return subject, "\n".join(lines)


def main():
    if not os.path.exists(LOG_CSV):
        print(f"No log yet at {LOG_CSV}. Run scripts/06b_sec_8k_scan.py first.")
        return

    df = pd.read_csv(LOG_CSV)
    if df.empty:
        print("Stream log is empty. Nothing to dispatch.")
        return

    df["filed_at"] = pd.to_datetime(df["filed_at"], errors="coerce", utc=True)
    df = df.sort_values("filed_at")

    state = load_state()
    seen = state.get("seen_accessions", {})
    now = datetime.now(timezone.utc)
    seen = prune_seen(seen, now)

    first_run = state.get("last_run_utc") is None
    if first_run:
        cutoff = now - timedelta(hours=FIRST_RUN_LOOKBACK_HOURS)
        print(f"FIRST RUN: only alerting on filings since {cutoff.isoformat()}")
        # Mark older filings as seen-but-not-sent so we don't spam later
        for _, row in df.iterrows():
            acc = str(row.get("accession_no", "") or "")
            if not acc:
                continue
            if pd.notna(row["filed_at"]) and row["filed_at"] < cutoff:
                seen[acc] = now.isoformat()

    universe = load_universe()
    if not universe:
        print("WARN: fmp_tickers.csv unavailable — Tier classification will skip all rows.")

    high_events = []
    medium_events = []

    for _, row in df.iterrows():
        acc = str(row.get("accession_no", "") or "")
        if not acc or acc in seen:
            continue
        priority, reason = classify(row, universe)
        if priority == "low":
            seen[acc] = now.isoformat()  # mark seen so we don't reclassify next run
            continue
        if priority == "high":
            high_events.append((acc, row, reason))
        else:
            medium_events.append((acc, row, reason))

    print(f"To dispatch: {len(high_events)} HIGH per-event, {len(medium_events)} MEDIUM in digest")

    # ── Send HIGH per-event ─────────────────────────────────────────────
    high_sent = 0
    high_failed = 0
    for acc, row, reason in high_events:
        try:
            subj, body = format_high_email(row, reason)
            send_email(subj, body)
            seen[acc] = now.isoformat()
            high_sent += 1
            print(f"  [HIGH sent] {acc} — {row.get('ticker','?')} — {reason}")
        except Exception as e:
            high_failed += 1
            print(f"  [HIGH FAIL] {acc} — {e} — will retry next run")

    # ── Send MEDIUM digest (one email, all-or-nothing) ──────────────────
    medium_sent = 0
    medium_failed = 0
    if medium_events:
        rows_with_reasons = [(row, reason) for _, row, reason in medium_events]
        try:
            subj, body = format_digest_email(rows_with_reasons)
            send_email(subj, body)
            for acc, _, _ in medium_events:
                seen[acc] = now.isoformat()
            medium_sent = len(medium_events)
            print(f"  [DIGEST sent] {medium_sent} filings")
        except Exception as e:
            medium_failed = len(medium_events)
            print(f"  [DIGEST FAIL] {e} — will retry whole batch next run")

    # ── Persist state ───────────────────────────────────────────────────
    state["last_run_utc"] = now.isoformat()
    state["seen_accessions"] = seen
    save_state(state)

    print(f"\nSummary: HIGH sent={high_sent} fail={high_failed} | "
          f"MEDIUM sent={medium_sent} fail={medium_failed}")
    print(f"State persisted to {STATE_PATH}")
    print(f"Tracking {len(seen)} seen accessions ({SEEN_TTL_DAYS}-day TTL)")


if __name__ == "__main__":
    main()
