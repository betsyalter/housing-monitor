"""Inspect EHS column to diagnose why Script 09 isn't producing correlations for it."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
import numpy as np

df = pd.read_csv(f"{DATA_DIR}/fred_housing.csv")
df["date"] = pd.to_datetime(df["date"])

print("=== Column existence ===")
print(f"existing_home_sales_saar in columns: {'existing_home_sales_saar' in df.columns}")
print(f"All FRED columns: {list(df.columns)}")

print("\n=== EHS data overview ===")
ehs = df[["date", "existing_home_sales_saar"]].dropna().sort_values("date")
print(f"Rows with EHS data: {len(ehs)}")
if len(ehs) > 0:
    print(f"Date range: {ehs['date'].min().date()} to {ehs['date'].max().date()}")
    print(f"Min/max value: {ehs['existing_home_sales_saar'].min():.0f} / {ehs['existing_home_sales_saar'].max():.0f}")
    print(f"\nFirst 3 rows:")
    print(ehs.head(3).to_string(index=False))
    print(f"\nLast 3 rows:")
    print(ehs.tail(3).to_string(index=False))

print("\n=== After monthly resample (resample('MS').last()) ===")
ehs_indexed = ehs.set_index("date")["existing_home_sales_saar"]
ehs_monthly = ehs_indexed.resample("MS").last()
print(f"Total months: {len(ehs_monthly)}")
print(f"Non-null months: {ehs_monthly.notna().sum()}")
print(f"Null months: {ehs_monthly.isna().sum()}")

print("\n=== After ffill(limit=2) ===")
ehs_filled = ehs_monthly.ffill(limit=2)
print(f"Non-null after ffill: {ehs_filled.notna().sum()}")

print("\n=== After log-diff transform ===")
ehs_logdiff = np.log(ehs_filled.replace({0: np.nan})).diff()
print(f"Non-null after logdiff: {ehs_logdiff.notna().sum()}")
print(f"Logdiff sample (last 12): \n{ehs_logdiff.tail(12)}")

print("\n=== Last 5y window ===")
cutoff = ehs_filled.index.max() - pd.DateOffset(years=5)
recent = ehs_logdiff.loc[ehs_logdiff.index >= cutoff]
print(f"Cutoff: {cutoff.date()}")
print(f"Rows in 5y window: {len(recent)}")
print(f"Non-null in 5y window: {recent.notna().sum()}")

print("\n=== Compare to housing_starts (which DID work) ===")
hs = df[["date", "housing_starts_total"]].dropna().sort_values("date").set_index("date")["housing_starts_total"]
hs_monthly = hs.resample("MS").last()
hs_logdiff = np.log(hs_monthly.replace({0: np.nan})).diff()
print(f"housing_starts non-null monthly: {hs_monthly.notna().sum()}")
print(f"housing_starts non-null logdiff: {hs_logdiff.notna().sum()}")
