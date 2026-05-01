"""One-shot patch: fix ASP rows in homebuilder_ops.csv that were stored in
thousands (459) instead of native USD (459000).

Wyatt's first Perplexity weekly report flagged: 'MHO ASP shows 459, MTH
ASP shows 373 — clearly truncated thousands.' Some press releases use
tabular columns labeled 'in thousands' and the original Script 07 prompt
didn't catch the convention. Updated prompt + sanity check now in place
for future runs; this script fixes existing rows.

Heuristic: any asp_dollars value 50 <= v < 5000 is almost certainly
truncated thousands. Scale up by 1000.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd

CSV_PATH = os.path.join(DATA_DIR, "homebuilder_ops.csv")

if not os.path.exists(CSV_PATH):
    raise SystemExit(f"{CSV_PATH} not found")

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} rows")

asp_mask = df["metric_name"] == "asp_dollars"
asp_df = df[asp_mask].copy()
print(f"asp_dollars rows: {len(asp_df)}")

# Find suspect rows
suspect_mask = (asp_df["metric_value"] >= 50) & (asp_df["metric_value"] < 5000)
suspect = asp_df[suspect_mask]
print(f"\nFound {len(suspect)} suspect asp_dollars rows (value 50-5000):")
print(suspect[["ticker", "fiscal_period", "metric_value", "accession_no"]].to_string(index=False))

if len(suspect) == 0:
    print("\nNo unit-truncation bugs to fix. Exiting.")
    sys.exit(0)

# Apply fix: scale by 1000
df.loc[asp_mask & (df["metric_value"] >= 50) & (df["metric_value"] < 5000), "metric_value"] *= 1000

# Save
df.to_csv(CSV_PATH, index=False)
print(f"\nFixed {len(suspect)} rows. CSV saved.")

# Verify
fixed = pd.read_csv(CSV_PATH)
asp_after = fixed[fixed["metric_name"] == "asp_dollars"]
print(f"\nNew ASP distribution:")
print(asp_after.groupby("ticker")["metric_value"].max().sort_values().to_string())
