"""News alert dispatcher — reads news_stream_log.csv, sends emails.

Two modes:
- Default (no flag): send any unsent immediate-priority articles as
  per-event emails. Runs after every Script 14 poll.
- --digest:           send today's queued digest articles as one email.
  Triggered by launchd at 4:15 PM ET.

Idempotent: each row's email_status is updated in-place after a successful
send, preventing re-sends on subsequent runs. SMTP failures leave
email_status='none' so the row retries next run.
"""

import sys, os, csv, argparse
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
from datetime import datetime, timezone

from alert_dispatcher import send_email

LOG_CSV = os.path.join(DATA_DIR, "news_stream_log.csv")


def load_log():
    if not os.path.exists(LOG_CSV):
        return None
    return pd.read_csv(LOG_CSV)


def save_log(df):
    df.to_csv(LOG_CSV, index=False)


def format_immediate(row):
    title = (row["title"] or "")[:100]
    publisher = row["publisher"] or "?"
    site = row["site"] or ""
    ticker = row["ticker"] or "topic"
    score = int(row["score"])
    high = (row["keyword_hits_high"] or "").replace("|", ", ") or "—"
    medium = (row["keyword_hits_medium"] or "").replace("|", ", ") or "—"

    subject = f"[NEWS-HIGH] {ticker} | {title[:80]} ({publisher})"
    body = (
        f"{title}\n\n"
        f"Publisher: {publisher} ({site})\n"
        f"Published: {row['published_at']}\n"
        f"Score: {score}  Priority: {row['alert_priority']}\n"
        f"High-signal keywords: {high}\n"
        f"Medium-signal keywords: {medium}\n"
        f"Matched tickers: {row['matched_tickers'] or row['ticker'] or '—'}\n"
        f"\nURL: {row['url']}\n"
        f"\nExcerpt:\n{(row['text'] or '')[:600]}\n"
    )
    return subject, body


def format_digest(rows):
    n = len(rows)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"[NEWS-DIGEST] {n} medium-priority articles ({today})"

    # Sort by score desc within digest
    rows = sorted(rows, key=lambda r: -int(r["score"]))

    lines = [f"Today's medium-priority housing news ({n} articles, sorted by score):\n"]
    for r in rows:
        title = (r["title"] or "")[:100]
        publisher = r["publisher"] or "?"
        ticker = r["ticker"] or "—"
        score = int(r["score"])
        high = (r["keyword_hits_high"] or "").replace("|", ",") or "—"
        lines.append(f"\n[{score}] {ticker}: {title}")
        lines.append(f"  Source: {publisher}  Keywords: {high}")
        lines.append(f"  {r['url']}")
    return subject, "\n".join(lines)


def send_immediates(df):
    """Send per-event emails for rows with priority=immediate, status=none."""
    pending = df[(df["alert_priority"] == "immediate") &
                 (df["email_status"] == "none")]
    if pending.empty:
        print("No immediate-priority articles pending.")
        return df, 0, 0

    sent = 0
    failed = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for idx, row in pending.iterrows():
        try:
            subj, body = format_immediate(row)
            send_email(subj, body)
            df.loc[idx, "email_status"] = "sent_immediate"
            df.loc[idx, "email_sent_at_utc"] = now_iso
            sent += 1
            print(f"  [SENT] {row['ticker'] or 'topic'} — {row['title'][:60]}")
        except Exception as e:
            df.loc[idx, "email_status"] = "send_failed"
            failed += 1
            print(f"  [FAIL] {row.get('dedupe_key','?')} — {e}")

    return df, sent, failed


def send_digest(df):
    """Send today's queued digest articles as one email."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    pending = df[(df["alert_priority"] == "digest") &
                 (df["email_status"] == "none")]
    if pending.empty:
        print("No digest-priority articles to send.")
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
        print(f"  Digest send failed: {e} — none marked sent, will retry next run")
        return df, 0, len(pending)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", action="store_true",
                        help="Send digest of all pending digest-priority articles")
    args = parser.parse_args()

    df = load_log()
    if df is None or df.empty:
        print(f"No log at {LOG_CSV}. Run scripts/14_news_poll.py first.")
        return

    if args.digest:
        df, sent, failed = send_digest(df)
        print(f"\nDigest: {sent} articles sent, {failed} failed")
    else:
        df, sent, failed = send_immediates(df)
        print(f"\nImmediates: {sent} sent, {failed} failed")

    save_log(df)


if __name__ == "__main__":
    main()
