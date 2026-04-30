import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time
from datetime import date, timedelta

BASE = "https://financialmodelingprep.com/stable"
PRICES_DIR = os.path.join(DATA_DIR, "fmp_prices")
LOOKBACK_YEARS = 5


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


def latest_date_on_disk(ticker):
    path = os.path.join(PRICES_DIR, f"{ticker}.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if df.empty or 'date' not in df.columns:
            return None
        return pd.to_datetime(df['date']).max().date()
    except Exception:
        return None


def pull_ticker(ticker, default_from):
    last = latest_date_on_disk(ticker)
    start = (last + timedelta(days=1)) if last else default_from

    if start > date.today():
        return 0, "up-to-date"

    data = fmp_get("historical-price-eod-light", {
        "symbol": ticker,
        "from": start.isoformat(),
        "to": date.today().isoformat(),
    })
    if not isinstance(data, list) or not data:
        return 0, "no-data"

    new_df = pd.DataFrame(data)[['date', 'price', 'volume']]
    path = os.path.join(PRICES_DIR, f"{ticker}.csv")

    if os.path.exists(path):
        old_df = pd.read_csv(path)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date']).sort_values('date')
    else:
        combined = new_df.sort_values('date')

    combined.to_csv(path, index=False)
    return len(new_df), "ok"


def main():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    os.makedirs(PRICES_DIR, exist_ok=True)
    df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    tickers = df['ticker'].dropna().unique().tolist()
    print(f"Pulling prices for {len(tickers)} tickers into {PRICES_DIR}/")

    default_from = date.today() - timedelta(days=365 * LOOKBACK_YEARS)
    summary = {"ok": 0, "up-to-date": 0, "no-data": 0, "error": 0}
    new_rows_total = 0

    for i, ticker in enumerate(tickers):
        try:
            n, status = pull_ticker(ticker, default_from)
            summary[status] += 1
            new_rows_total += n
        except Exception as e:
            summary["error"] += 1
            print(f"  {ticker} failed: {e}")

        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(tickers)} done — {new_rows_total} new rows so far")
        time.sleep(0.2)

    print(f"\nDone. New rows written: {new_rows_total}")
    print(f"Status breakdown: {summary}")


if __name__ == '__main__':
    main()
