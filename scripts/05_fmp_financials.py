import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"
FIN_DIR = os.path.join(DATA_DIR, "fmp_financials")
QUARTERS = 20  # 5 years
TIERS = [1, 2]

STATEMENTS = {
    "income": "income-statement",
    "balance": "balance-sheet-statement",
    "cashflow": "cashflow-statement",
}


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


def pull_statement(ticker, label, endpoint):
    data = fmp_get(endpoint, {
        "symbol": ticker,
        "period": "quarter",
        "limit": QUARTERS,
    })
    if not isinstance(data, list) or not data:
        return 0
    df = pd.DataFrame(data).sort_values('date')
    path = os.path.join(FIN_DIR, f"{ticker}_{label}.csv")
    df.to_csv(path, index=False)
    return len(df)


def main():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    os.makedirs(FIN_DIR, exist_ok=True)
    df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    df = df[df['tier'].isin(TIERS)]
    tickers = df['ticker'].dropna().unique().tolist()
    print(f"Pulling {QUARTERS}-quarter financials for {len(tickers)} Tier 1+2 tickers")
    print(f"Output dir: {FIN_DIR}/")

    summary = {label: 0 for label in STATEMENTS}
    errors = []

    for i, ticker in enumerate(tickers):
        for label, endpoint in STATEMENTS.items():
            try:
                n = pull_statement(ticker, label, endpoint)
                summary[label] += n
            except Exception as e:
                errors.append((ticker, label, str(e)))
                print(f"  {ticker} {label} failed: {e}")
            time.sleep(0.15)

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(tickers)} tickers done")

    print(f"\nDone. Rows written per statement: {summary}")
    if errors:
        print(f"Errors: {len(errors)}")
        for t, lbl, e in errors[:10]:
            print(f"  {t} {lbl}: {e}")


if __name__ == '__main__':
    main()
