import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"
INSIDER_DIR = os.path.join(DATA_DIR, "fmp_insider")
LIMIT_PER_TICKER = 200  # most recent 200 transactions
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


def pull_ticker(ticker):
    data = fmp_get("insider-trading/search", {
        "symbol": ticker, "limit": LIMIT_PER_TICKER,
    })
    if not isinstance(data, list) or not data:
        return 0
    df = pd.DataFrame(data)
    if 'filingDate' in df.columns:
        df = df.sort_values('filingDate', ascending=False)
    path = os.path.join(INSIDER_DIR, f"{ticker}.csv")
    df.to_csv(path, index=False)
    return len(df)


def main():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    os.makedirs(INSIDER_DIR, exist_ok=True)
    df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    df = df[df['tier'].isin(TIERS)]
    tickers = df['ticker'].dropna().unique().tolist()
    print(f"Pulling insider trades for {len(tickers)} Tier 1+2 tickers (last {LIMIT_PER_TICKER} txns each)")

    total_rows = 0
    errors = 0
    empty = 0

    for i, ticker in enumerate(tickers):
        try:
            n = pull_ticker(ticker)
            total_rows += n
            if n == 0:
                empty += 1
        except Exception as e:
            errors += 1
            print(f"  {ticker} failed: {e}")
        time.sleep(0.15)

        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(tickers)} done — {total_rows} rows so far")

    print(f"\nDone. Total rows: {total_rows} across {len(tickers)} tickers")
    print(f"Empty (no insider trades): {empty}, Errors: {errors}")
    print(f"Output dir: {INSIDER_DIR}/")


if __name__ == '__main__':
    main()
