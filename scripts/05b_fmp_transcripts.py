import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"
TRANS_DIR = os.path.join(DATA_DIR, "fmp_transcripts")
QUARTERS_BACK = 8  # last 2 years of calls
TIERS = [1, 2]


def fmp_get(endpoint, params=None):
    if params is None:
        params = {}
    params['apikey'] = FMP_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code == 429:
        print("Rate limited, waiting 60s...")
        time.sleep(60)
        return fmp_get(endpoint, params)
    r.raise_for_status()
    return r.json()


def list_available(ticker):
    data = fmp_get("earning-call-transcript-dates", {"symbol": ticker})
    if not isinstance(data, list):
        return []
    return data


def pull_transcript(ticker, year, quarter):
    path = os.path.join(TRANS_DIR, f"{ticker}_{year}Q{quarter}.txt")
    if os.path.exists(path):
        return "skipped"

    data = fmp_get("earning-call-transcript", {
        "symbol": ticker, "year": year, "quarter": quarter,
    })
    if not isinstance(data, list) or not data:
        return "empty"

    rec = data[0]
    content = rec.get("content", "")
    date = rec.get("date", "")
    if not content:
        return "empty"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {ticker} {year} Q{quarter} — {date}\n\n")
        f.write(content)
    return "ok"


def main():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    os.makedirs(TRANS_DIR, exist_ok=True)
    df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    df = df[df['tier'].isin(TIERS)]
    tickers = df['ticker'].dropna().unique().tolist()
    print(f"Pulling earnings transcripts for {len(tickers)} Tier 1+2 tickers (last {QUARTERS_BACK} quarters)")

    summary = {"ok": 0, "skipped": 0, "empty": 0, "no-list": 0, "error": 0}

    for i, ticker in enumerate(tickers):
        try:
            available = list_available(ticker)
            if not available:
                summary["no-list"] += 1
                continue
            for entry in available[:QUARTERS_BACK]:
                year = entry.get("fiscalYear")
                quarter = entry.get("quarter")
                if year is None or quarter is None:
                    continue
                try:
                    status = pull_transcript(ticker, year, quarter)
                    summary[status] += 1
                except Exception as e:
                    summary["error"] += 1
                    print(f"  {ticker} {year}Q{quarter} failed: {e}")
                time.sleep(0.15)
        except Exception as e:
            summary["error"] += 1
            print(f"  {ticker} list failed: {e}")

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(tickers)} tickers done — {summary}")

    print(f"\nDone. Summary: {summary}")
    print(f"Output dir: {TRANS_DIR}/")


if __name__ == '__main__':
    main()
