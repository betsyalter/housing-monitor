import requests
import os
import csv
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

FMP_API_KEY = os.environ['FMP_API_KEY']

# Load tickers from CSV
tickers_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'fmp_tickers.csv')
ALL_425_TICKERS = []
with open(tickers_csv) as f:
    reader = csv.DictReader(f)
    for row in reader:
        ALL_425_TICKERS.append(row['ticker'])

print(f"Loaded {len(ALL_425_TICKERS)} tickers. Validating against FMP...\n")

dead = []
active = []
errors = []

for i, ticker in enumerate(ALL_425_TICKERS):
    try:
        r = requests.get(
            f"https://financialmodelingprep.com/stable/profile?symbol={ticker}&apikey={FMP_API_KEY}",
            timeout=10
        )
        data = r.json()
        if not data or not isinstance(data, list) or len(data) == 0:
            dead.append(ticker)
            print(f"  DEAD/NOT FOUND: {ticker}")
        elif not data[0].get('isActivelyTrading', True):
            dead.append(f"{ticker} (inactive)")
            print(f"  INACTIVE: {ticker}")
        else:
            active.append(ticker)
        # Light rate limiting — FMP stable endpoint allows ~300 req/min
        time.sleep(0.2)
    except Exception as e:
        errors.append(f"{ticker}: {e}")
        print(f"  ERROR: {ticker} — {e}")

print(f"\n{'='*60}")
print(f"RESULTS: {len(active)} active, {len(dead)} dead/invalid, {len(errors)} errors")
print(f"\nDead/invalid tickers ({len(dead)}):")
for t in dead:
    print(f"  {t}")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
