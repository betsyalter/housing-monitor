"""Congress.gov bill alert dispatcher — reads congress_bill_log.csv, sends emails.

Mirrors 11 / 14b: per-event email for immediate-priority rows, digest
for medium. Idempotent via the email_status column (in-place update).
"""

import sys, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
from datetime import datetime, timezone

from alert_dispatcher import send_email

LOG_CSV = os.path.join(DATA_DIR, "congress_bill_log.csv")


def load_log():
    if not os.path.exists(LOG_CSV):
        return None
    return pd.read_csv(LOG_CSV)


def save_log(df):
    df.to_csv(LOG_CSV, index=False)


def format_immediate(row):
    bill_id = row.get("bill_id", "?")
    title = (row.get("title") or "")[:120]
    sponsor = row.get("sponsor_name", "") or ""
    party = row.get("sponsor_party", "") or ""
    state = row.get("sponsor_state", "") or ""
    sponsor_str = f"{sponsor} ({party}-{state})" if sponsor else "Unknown sponsor"
    event = row.get("event_type", "")
    action_date = row.get("latest_action_date", "") or ""
    action_text = (row.get("latest_action_text", "") or "")[:200]
    committees = row.get("committees", "") or "—"
    keywords = (row.get("keyword_hits", "") or "").replace("|", ", ") or "—"
    url = row.get("url", "") or ""

    event_label = "NEW BILL" if event == "new_bill" else "BILL ACTION"
    subject = f"[CONGRESS-{event_label}] {bill_id} — {title[:70]}"

    body = (
        f"{title}\n\n"
        f"Bill: {bill_id} ({row.get('bill_type','?')} {row.get('bill_number','?')})\n"
        f"Sponsor: {sponsor_str}\n"
        f"Introduced: {row.get('introduced_date','—')}\n"
        f"Latest action ({action_date}): {action_text}\n\n"
        f"Committees: {committees}\n"
        f"Policy area: {row.get('policy_area','') or '—'}\n"
        f"Keyword hits: {keywords}\n"
        f"Score: {row.get('score','?')}  Priority: {row.get('alert_priority','?')}\n\n"
        f"Bill page: {url}\n"
    )
    return subject, body


def format_digest(rows):
    n = len(rows)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"[CONGRESS-DIGEST] {n} medium-priority housing bills ({today})"

    rows = sorted(rows, key=lambda r: -int(r.get("score", 0) or 0))

    lines = [f"Today's medium-priority housing-related bill activity ({n} items):\n"]
    for r in rows:
        bill_id = r.get("bill_id", "?")
        title = (r.get("title") or "")[:120]
        sponsor = r.get("sponsor_name", "") or "?"
        action = (r.get("latest_action_text") or "")[:120]
        action_date = r.get("latest_action_date", "")
        score = int(r.get("score", 0) or 0)
        keywords = (r.get("keyword_hits", "") or "").replace("|", ",") or "—"
        url = r.get("url", "") or ""
        lines.append(f"\n[{score}] {bill_id} — {title}")
        lines.append(f"  Sponsor: {sponsor}")
        lines.append(f"  Latest action ({action_date}): {action}")
        lines.append(f"  Keywords: {keywords}")
        lines.append(f"  {url}")
    return subject, "\n".join(lines)


def send_immediates(df):
    pending = df[(df["alert_priority"] == "immediate") &
                 (df["email_status"] == "none")]
    if pending.empty:
        print("No immediate bills pending.")
        return df, 0, 0

    sent = failed = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for idx, row in pending.iterrows():
        try:
            subj, body = format_immediate(row)
            send_email(subj, body)
            df.loc[idx, "email_status"] = "sent_immediate"
            df.loc[idx, "email_sent_at_utc"] = now_iso
            sent += 1
            print(f"  [SENT] {row['bill_id']} — {row.get('event_type','')}")
        except Exception as e:
            df.loc[idx, "email_status"] = "send_failed"
            failed += 1
            print(f"  [FAIL] {row.get('bill_id','?')} — {e}")
    return df, sent, failed


def send_digest(df):
    pending = df[(df["alert_priority"] == "digest") &
                 (df["email_status"] == "none")]
    if pending.empty:
        print("No digest-priority bills.")
        return df, 0, 0

    rows = pending.to_dict(orient="records")
    try:
        subj, body = format_digest(rows)
        send_email(subj, body)
        now_iso = datetime.now(timezone.utc).isoformat()
        for idx in pending.index:
            df.loc[idx, "email_status"] = "sent_digest"
            df.loc[idx, "email_sent_at_utc"] = now_iso
        return df, len(pending), 0
    except Exception as e:
        print(f"  Digest send failed: {e} — none marked, will retry")
        return df, 0, len(pending)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", action="store_true",
                        help="Send digest of all pending digest-priority bills")
    args = parser.parse_args()

    df = load_log()
    if df is None or df.empty:
        print(f"No log at {LOG_CSV}. Run scripts/15_congress_bill_poll.py first.")
        return

    if args.digest:
        df, sent, failed = send_digest(df)
        print(f"\nDigest: {sent} bills sent, {failed} failed")
    else:
        df, sent, failed = send_immediates(df)
        print(f"\nImmediates: {sent} sent, {failed} failed")

    save_log(df)


if __name__ == "__main__":
    main()
