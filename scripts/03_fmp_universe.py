import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"


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


def enrich_universe():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    base_cols = ['ticker', 'tier', 'subsector', 'directional']
    df = df[[c for c in base_cols if c in df.columns]]
    tickers = df['ticker'].dropna().unique().tolist()
    print(f"Loaded {len(tickers)} tickers from fmp_tickers.csv")

    profiles_all = []
    for i, ticker in enumerate(tickers):
        try:
            data = fmp_get("profile", {"symbol": ticker})
            if isinstance(data, list) and data:
                profiles_all.append(data[0])
        except Exception as e:
            print(f"  {ticker} failed: {e}")
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(tickers)} enriched")
        time.sleep(0.2)

    print(f"\nTotal profiles returned: {len(profiles_all)}")

    if not profiles_all:
        raise SystemExit("No profiles returned — aborting before overwriting CSV.")

    pdf = pd.DataFrame(profiles_all).rename(columns={'symbol': 'ticker'})
    keep_cols = ['ticker', 'companyName', 'marketCap', 'sector', 'industry',
                 'price', 'beta', 'averageVolume', 'country', 'exchange']
    pdf = pdf[[c for c in keep_cols if c in pdf.columns]]

    df = df.merge(pdf, on='ticker', how='left')
    df.to_csv(f"{DATA_DIR}/fmp_tickers.csv", index=False)

    print(f"\nEnriched universe saved: {len(df)} tickers -> {DATA_DIR}/fmp_tickers.csv")
    print("\nTier counts:")
    print(df.groupby('tier').size().to_string())
    print("\nSample:")
    print(df[['ticker', 'tier', 'subsector', 'companyName', 'marketCap', 'price']].head(10).to_string(index=False))


if __name__ == '__main__':
    enrich_universe()
