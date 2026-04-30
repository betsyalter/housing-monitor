import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FRED_API_KEY, DATA_DIR

import requests
import pandas as pd

SERIES = {
    'MORTGAGE30US':    'mortgage_rate_30yr',
    'MORTGAGE15US':    'mortgage_rate_15yr',
    'ACTLISCOUUS':     'existing_home_inventory',
    'EXHOSLUSM495S':   'existing_home_sales_saar',
    'HSN1F':            'new_home_sales',
    'MSPUS':           'median_home_price',
    'HOUST':           'housing_starts_total',
    'PERMIT':          'building_permits',
    'RHORUSQ156N':     'homeownership_rate',
    'CSUSHPISA':       'case_shiller_national',
    'CUUR0000SAH1':    'cpi_shelter',
    'CUSR0000SEHA':    'cpi_rent',
}

BASE = 'https://api.stlouisfed.org/fred/series/observations'

def fetch_series(series_id: str, name: str):
    r = requests.get(BASE, params={
        'series_id':         series_id,
        'api_key':           FRED_API_KEY,
        'file_type':         'json',
        'observation_start': '2000-01-01',
        'sort_order':        'asc',
    }, timeout=15)
    r.raise_for_status()
    obs = r.json().get('observations', [])
    df = pd.DataFrame(obs)[['date', 'value']]
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.columns = ['date', name]
    return df

def run():
    os.makedirs(DATA_DIR, exist_ok=True)
    combined = None
    for series_id, name in SERIES.items():
        print(f"  Fetching {series_id} ({name})...")
        try:
            df = fetch_series(series_id, name)
            combined = df if combined is None else pd.merge(combined, df, on='date', how='outer')
        except Exception as e:
            print(f"  ⚠️  Skipped {series_id}: {e}")
    
    combined.sort_values('date', inplace=True)
    out = f'{DATA_DIR}/fred_housing.csv'
    combined.to_csv(out, index=False)
    print(f"\n✅ Saved {len(combined)} rows to {out}")
    print(combined.tail(3).to_string())

if __name__ == '__main__':
    run()
