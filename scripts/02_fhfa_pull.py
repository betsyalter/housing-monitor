import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, FRED_API_KEY

import requests
import pandas as pd
from datetime import datetime

FHFA_URLS = {
    'rate_distribution': 'https://www.fhfa.gov/sites/default/files/2025-01/MIRS_ARM_FRM_Combined.xlsx',
    'mirs_backup':       'https://www.fhfa.gov/sites/default/files/2025-04/MIRS_ARM_FRM_Combined.xlsx',
}

def pull_fhfa_distribution():
    for name, url in FHFA_URLS.items():
        try:
            print(f"Trying FHFA URL: {url}")
            r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                filepath = f"{DATA_DIR}/fhfa_{name}.xlsx"
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  ✓ Saved to {filepath}")
                df = pd.read_excel(filepath, sheet_name=0, skiprows=5)
                df.to_csv(f"{DATA_DIR}/fhfa_{name}.csv", index=False)
                print(f"  ✓ Converted to CSV")
                return df
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    return None

def build_lock_in_distribution():
    """
    FHFA NMDB Q4 2024 published distribution of outstanding mortgage rates.
    Source: https://www.fhfa.gov/news/news-release/fhfa-releases-data-visualization-dashboard
    Update quarterly when FHFA publishes new data.
    """
    distribution = pd.DataFrame({
        'rate_bucket':         ['<3%','3-3.5%','3.5-4%','4-4.5%','4.5-5%','5-5.5%','5.5-6%','6-6.5%','>6.5%'],
        'pct_of_outstanding':  [0.219, 0.178,   0.172,   0.141,   0.107,   0.044,   0.032,   0.058,   0.049],
        'approx_midpoint_rate':[2.5,   3.25,    3.75,    4.25,    4.75,    5.25,    5.75,    6.25,    7.0],
        'est_homes_millions':  [0,     0,       0,       0,       0,       0,       0,       0,       0],
    })
    total_mortgaged = 50.8  # million (FHFA NMDB)
    distribution['est_homes_millions'] = distribution['pct_of_outstanding'] * total_mortgaged
    distribution.to_csv(f"{DATA_DIR}/fhfa_distribution.csv", index=False)
    print(f"\nLock-in distribution saved:")
    print(distribution.to_string(index=False))
    return distribution

def calculate_coiled_spring(current_30yr_rate, distribution_df, threshold_bps=150):
    threshold = threshold_bps / 100
    print(f"\n=== COILED SPRING MODEL ===")
    print(f"Current 30yr rate: {current_30yr_rate:.2f}%")
    print(f"Lock-in threshold: {threshold_bps}bps above locked rate\n")

    results = []
    for _, row in distribution_df.iterrows():
        locked_rate = row['approx_midpoint_rate']
        homes       = row['est_homes_millions']
        spread      = current_30yr_rate - locked_rate
        is_locked   = spread > threshold
        results.append({
            'rate_bucket':           row['rate_bucket'],
            'midpoint_rate':         locked_rate,
            'homes_millions':        homes,
            'spread_to_current':     spread,
            'is_locked':             is_locked,
            'locked_homes_millions': homes if is_locked else 0,
        })

    results_df  = pd.DataFrame(results)
    total_locked = results_df['locked_homes_millions'].sum()
    print(f"Total locked homeowners at {current_30yr_rate:.2f}%: {total_locked:.1f}M")
    print(f"  ({total_locked/50.8*100:.0f}% of all mortgaged homeowners)")

    scenarios = [6.5, 6.25, 6.0, 5.75, 5.5, 5.25, 5.0, 4.75, 4.5]
    print(f"\nUnlock scenarios (threshold={threshold_bps}bps):")
    print(f"{'Rate':>8} | {'Still Locked':>14} | {'Unlocked vs Today':>18} | {'Est SAAR Uplift':>16}")
    print("-" * 65)

    scenario_results = []
    for rate in scenarios:
        locked_at_rate = sum(
            row['est_homes_millions']
            for _, row in distribution_df.iterrows()
            if (rate - row['approx_midpoint_rate']) > threshold
        )
        unlocked_vs_today = total_locked - locked_at_rate
        saar_uplift       = unlocked_vs_today * 0.28 * 1000  # thousands of units
        scenario_results.append({
            'scenario_rate':                rate,
            'locked_millions':              locked_at_rate,
            'unlocked_vs_today_millions':   unlocked_vs_today,
            'estimated_saar_uplift_k':      saar_uplift,
        })
        print(f"{rate:>7.2f}% | {locked_at_rate:>11.1f}M | {unlocked_vs_today:>+14.1f}M | {saar_uplift:>+13.0f}k")

    scenario_df = pd.DataFrame(scenario_results)
    scenario_df.to_csv(f"{DATA_DIR}/coiled_spring_scenarios.csv", index=False)
    return results_df, scenario_df

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting FHFA pull...")
    os.makedirs(DATA_DIR, exist_ok=True)
    pull_fhfa_distribution()
    dist_df = build_lock_in_distribution()
    fred_df = pd.read_csv(f"{DATA_DIR}/fred_housing.csv")
    current_rate = pd.to_numeric(fred_df['mortgage_rate_30yr'], errors='coerce').dropna().iloc[-1]
    print(f"\nCurrent 30yr rate from FRED: {current_rate:.2f}%")
    locked_df, scenarios_df = calculate_coiled_spring(current_rate, dist_df, threshold_bps=150)
    print(f"\n✅ Done. CSVs saved to {DATA_DIR}")
