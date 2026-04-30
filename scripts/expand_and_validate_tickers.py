import requests
import os
import csv
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

FMP_API_KEY = os.environ['FMP_API_KEY']
BASE = "https://financialmodelingprep.com/stable"
TICKERS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'fmp_tickers.csv')

def fmp_get(endpoint, params=None):
    if params is None:
        params = {}
    params['apikey'] = FMP_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code == 429:
        print("  Rate limited — waiting 60s...")
        time.sleep(60)
        return fmp_get(endpoint, params)
    r.raise_for_status()
    return r.json()

# ── Step 1: Load existing manual tickers ─────────────────────────
existing = {}
with open(TICKERS_CSV) as f:
    for row in csv.DictReader(f):
        existing[row['ticker']] = row

print(f"Loaded {len(existing)} manually curated tickers.")

# ── Step 2: Run FMP screeners ─────────────────────────────────────
screener_queries = [
    {"sector": "Real Estate", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 500},
    {"industry": "Residential Construction", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 200},
    {"industry": "Home Improvement Retail", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 100},
    {"industry": "Building Products & Equipment", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 200},
    {"industry": "Mortgage Finance", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 100},
    {"industry": "Insurance—Property & Casualty", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 100},
    {"industry": "Lumber & Wood Production", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 100},
    {"industry": "Specialty Retail", "sector": "Consumer Cyclical", "exchangeShortName": "NYSE,NASDAQ,AMEX", "limit": 200},
]

screener_additions = {}
for i, query in enumerate(screener_queries):
    label = query.get('industry', query.get('sector', ''))
    print(f"  Screener {i+1}/{len(screener_queries)}: {label}...")
    try:
        results = fmp_get("stock-screener", query)
        added = 0
        for item in results:
            ticker = item.get('symbol', '').upper()
            if ticker and ticker not in existing and ticker not in screener_additions:
                screener_additions[ticker] = {
                    'ticker': ticker,
                    'tier': 5,
                    'subsector': f"Screener: {label}",
                    'directional': 'review_needed'
                }
                added += 1
        print(f"    → {added} new tickers added (total screener additions so far: {len(screener_additions)})")
        time.sleep(0.5)
    except Exception as e:
        print(f"    ERROR: {e}")

print(f"\nScreener added {len(screener_additions)} new tickers to the {len(existing)} manual ones.")
print(f"Total to validate: {len(existing) + len(screener_additions)}")

# ── Step 3: Validate ALL tickers against FMP profile ─────────────
all_tickers = list(existing.keys()) + list(screener_additions.keys())
print(f"\nValidating {len(all_tickers)} tickers against FMP...\n")

dead = []
active_existing = []
active_new = []

for i, ticker in enumerate(all_tickers):
    if i % 50 == 0 and i > 0:
        print(f"  ... {i}/{len(all_tickers)} checked")
    try:
        r = requests.get(
            f"{BASE}/profile?symbol={ticker}&apikey={FMP_API_KEY}",
            timeout=10
        )
        data = r.json()
        if not data or not isinstance(data, list) or len(data) == 0:
            dead.append((ticker, 'not_found'))
            print(f"  DEAD: {ticker}")
        elif not data[0].get('isActivelyTrading', True):
            dead.append((ticker, 'inactive'))
            print(f"  INACTIVE: {ticker}")
        else:
            if ticker in existing:
                active_existing.append(ticker)
            else:
                active_new.append(ticker)
        time.sleep(0.2)
    except Exception as e:
        print(f"  ERROR: {ticker} — {e}")

# ── Step 4: Write clean validated CSV ────────────────────────────
dead_set = {t for t, _ in dead}

output_rows = []
# Existing manual tickers that are active
for ticker, row in existing.items():
    if ticker not in dead_set:
        output_rows.append(row)

# New screener tickers that are active — enrich with profile data
print(f"\nEnriching {len(active_new)} new active screener tickers with profile data...")
for ticker in active_new:
    try:
        r = requests.get(f"{BASE}/profile?symbol={ticker}&apikey={FMP_API_KEY}", timeout=10)
        profile = r.json()
        if profile and isinstance(profile, list) and len(profile) > 0:
            p = profile[0]
            output_rows.append({
                'ticker': ticker,
                'tier': 5,
                'subsector': f"{p.get('sector','')}: {p.get('industry','')}",
                'directional': 'review_needed'
            })
        time.sleep(0.15)
    except:
        output_rows.append(screener_additions[ticker])

with open(TICKERS_CSV, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['ticker', 'tier', 'subsector', 'directional'])
    writer.writeheader()
    writer.writerows(output_rows)

# ── Step 5: Print summary ─────────────────────────────────────────
print(f"\n{'='*60}")
print(f"FINAL RESULTS")
print(f"{'='*60}")
print(f"Manual tickers active:   {len(active_existing)}")
print(f"Screener tickers active: {len(active_new)}")
print(f"Total active in CSV:     {len(output_rows)}")
print(f"Dead/invalid removed:    {len(dead_set)}")
print(f"\nDead tickers ({len(dead)}):")
for t, reason in sorted(dead):
    print(f"  {t} ({reason})")
