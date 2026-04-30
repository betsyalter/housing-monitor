# US Housing Deep Dive: Complete End-to-End Execution Playbook
*Two-person build guide. Person A = Data Engineer / Pipeline Lead. Person B = Research Analyst / Perplexity Computer Lead. Every command, every script, every prompt is written out in full.*

***
## Part 0: Before Either Person Touches Code
### Critical Architectural Decision: Perplexity Computer ≠ Sonar API
Perplexity Computer (perplexity.ai/computer) is a UI-based autonomous agent that browses the web, reads files at URLs, executes multi-step tasks, and runs sub-agents — it is NOT an API you POST to programmatically. The correct Mac mini → Perplexity Computer integration is:[^1][^2]

1. Mac mini generates structured context files (Markdown + JSON)
2. Mac mini pushes those files to a publicly accessible URL (GitHub Pages)
3. You give Perplexity Computer a task prompt that begins: *"Go to [URL] and read the latest housing data, then do the following..."*
4. Perplexity Computer browses to your URL, reads the context as grounding, and executes the analytical task[^2]

This means the Mac mini is the data layer and Perplexity Computer is the intelligence layer. They communicate via a URL, not an API call.
### API Keys to Acquire Before Starting
Both people need these before any code is written. Collect all keys into a shared password manager entry.

**Person A collects:**

| Key | Where to Get It | Cost | Time |
|-----|----------------|------|------|
| FRED API key | fred.stlouisfed.org → My Account → API Keys | Free | 5 min |
| FMP API key | site.financialmodelingprep.com → Dashboard → API Keys | Paid (Ultimate plan) | 5 min |
| sec-api.io key | sec-api.io → Sign Up → Dashboard | Paid subscription | 5 min |
| GitHub personal access token | github.com → Settings → Developer Settings → Personal Access Tokens → Classic → Generate | Free | 5 min |

**Person B collects:**

| Key | Where to Get It | Cost | Time |
|-----|----------------|------|------|
| Capital IQ credentials | S&P Global Support Center (login required) → Python SDK download page | CIQ subscription | Contact S&P rep |
| Perplexity Max subscription | perplexity.ai → Settings → Subscription | $200/month or $167/month annual | 5 min |

**Shared environment file** — once collected, Person A creates a single `.env` file that lives on both Mac minis and is NEVER committed to git:

```bash
# /housing_monitor/.env
FRED_API_KEY=your_fred_key_here
FMP_API_KEY=your_fmp_key_here
SEC_API_KEY=your_sec_api_key_here
CIQ_USERNAME=your_ciq_username
CIQ_PASSWORD=your_ciq_password
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=yourusername/housing-monitor
```

***
## Part 1: Person A — Mac Mini Environment Setup (Day 1, ~3 hours)
### Step 1.1: Verify Python Version
Open Terminal on the Mac mini. Run:

```bash
python3 --version
```

If the output is below Python 3.11, install the latest via Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
python3 --version  # should now show 3.11.x
```
### Step 1.2: Create the Project Directory Structure
```bash
mkdir -p ~/housing_monitor/{data,scripts,output,public,logs}
cd ~/housing_monitor
```

The final directory layout will be:

```
~/housing_monitor/
├── .env                        # API keys — NEVER commit
├── .gitignore                  # excludes .env and data/
├── data/
│   ├── fred_data.csv           # all FRED time series
│   ├── fhfa_distribution.csv   # mortgage rate distribution
│   ├── fmp_tickers.csv         # 400+ ticker universe
│   ├── fmp_prices/             # per-ticker price history CSVs
│   ├── fmp_financials/         # per-ticker income statements
│   ├── sec_reit_homes.csv      # INVH/AMH homes owned time series
│   ├── ciq_segments.csv        # Capital IQ segment revenue
│   ├── ciq_homebuilder_ops.csv # community count, backlog, etc.
│   └── last_run.json           # stores prior run's values for delta
├── scripts/
│   ├── 01_fred_pull.py
│   ├── 02_fhfa_pull.py
│   ├── 03_fmp_universe.py
│   ├── 04_fmp_prices.py
│   ├── 05_fmp_financials.py
│   ├── 06_sec_reit.py
│   ├── 07_ciq_pull.py
│   ├── 08_coiled_spring_model.py
│   ├── 09_correlation_engine.py
│   ├── 10_context_generator.py
│   ├── 11_dashboard_generator.py
│   └── run_all.sh
├── output/
│   └── housing_dashboard.html
├── public/                     # what gets pushed to GitHub Pages
│   ├── housing_context.md      # what Perplexity Computer reads
│   ├── housing_data.json       # what the dashboard reads
│   └── index.html              # the dashboard itself
└── logs/
    └── housing_monitor.log
```
### Step 1.3: Create the Python Virtual Environment
```bash
cd ~/housing_monitor
python3 -m venv .venv
source .venv/bin/activate

# Confirm you're in the venv
which python  # should show ~/housing_monitor/.venv/bin/python
```
### Step 1.4: Install All Dependencies
```bash
pip install --upgrade pip

pip install \
  fredapi \
  requests \
  pandas \
  numpy \
  plotly \
  schedule \
  python-dotenv \
  sec-api \
  dlt \
  "dlt[duckdb]" \
  duckdb \
  gitpython \
  pyarrow \
  openpyxl

# Capital IQ SDK — requires manual download from S&P Global Support Center
# Once downloaded (spgmiciq-3.0.0.tar.gz):
pip install spgmiciq-3.0.0.tar.gz
# Or if wheel file:
pip install spgmiciq-3.0.0-py3-none-any.whl
```

Create `requirements.txt` for reproducibility:

```bash
pip freeze > requirements.txt
```
### Step 1.5: Set Up Environment Variable Loading
Create `~/housing_monitor/scripts/config.py` — this file is imported by every other script:

```python
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

FRED_API_KEY    = os.environ['FRED_API_KEY']
FMP_API_KEY     = os.environ['FMP_API_KEY']
SEC_API_KEY     = os.environ['SEC_API_KEY']
CIQ_USERNAME    = os.environ['CIQ_USERNAME']
CIQ_PASSWORD    = os.environ['CIQ_PASSWORD']
GITHUB_TOKEN    = os.environ['GITHUB_TOKEN']
GITHUB_REPO     = os.environ['GITHUB_REPO']

DATA_DIR    = os.path.join(os.path.dirname(__file__), '..', 'data')
PUBLIC_DIR  = os.path.join(os.path.dirname(__file__), '..', 'public')
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), '..', 'output')
LOGS_DIR    = os.path.join(os.path.dirname(__file__), '..', 'logs')
```
### Step 1.6: Set Up GitHub Repository for Data Feed Hosting
```bash
# Create the repo on GitHub first (github.com → New Repository → housing-monitor → Public)
# Then from Mac mini:

cd ~/housing_monitor
git init
git remote add origin https://github.com/YOURUSERNAME/housing-monitor.git

# Create .gitignore
cat > .gitignore << 'EOF'
.env
.venv/
data/
logs/
__pycache__/
*.pyc
.DS_Store
EOF

# Create initial public/ files
echo "# Housing Monitor" > public/README.md
echo "{}" > public/housing_data.json
echo "# Initializing..." > public/housing_context.md

git add public/ .gitignore requirements.txt scripts/
git commit -m "Initial housing monitor setup"
git branch -M main
git push -u origin main
```

Enable GitHub Pages: Go to github.com/YOURUSERNAME/housing-monitor → Settings → Pages → Source: Deploy from branch → Branch: main → Folder: /public → Save.

Your feed URL will be: `https://YOURUSERNAME.github.io/housing-monitor/housing_context.md`

**Give Person B this URL immediately.** They need it before they can write any Perplexity Computer tasks.

***
## Part 2: Person A — Script 01: FRED Data Pipeline (Day 2, ~2 hours)
Create `~/housing_monitor/scripts/01_fred_pull.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FRED_API_KEY, DATA_DIR

import pandas as pd
import fredapi
from datetime import datetime

fred = fredapi.Fred(api_key=FRED_API_KEY)

# Every Bloomberg series from your screens, mapped to FRED equivalents
SERIES = {
    # Core housing turnover
    'existing_home_sales_saar':   'EXHOSLUSM495S',   # ETSLTOTL — 3.98M
    'for_sale_inventory':         'HOSINVUSM495N',   # ETSLHAFS — 1.36M
    'months_supply':              'HOSSUPUSM673N',   # months of supply
    'median_sales_price':         'HOSMEDUSM052N',   # median existing home price
    
    # New home supply  
    'new_home_sales_saar':        'HSN1F',           # NHSLTOT equivalent — new 1-fam homes sold
    'housing_starts_total':       'HOUST',           # total housing starts
    'housing_starts_single_fam':  'HOUSTMW',        # single-family starts
    
    # Rates and financing
    'mortgage_rate_30yr':         'MORTGAGE30US',    # 30yr fixed (Freddie Mac PMMS, weekly)
    'mortgage_rate_15yr':         'MORTGAGE15US',    # 15yr fixed
    
    # Affordability (maps to HOMECOMP in Bloomberg)
    'affordability_composite':    'FIXHAI',          # NAR composite affordability index
    'affordability_first_time':   'FIXMHAI',         # first-time buyer affordability
    
    # Homeownership (maps to USH HOME)
    'homeownership_rate':         'RHORUSQ156N',     # US homeownership rate, quarterly
    
    # Rents (lagging indicator — your original prompt mentions rents coming down)
    'cpi_rent_primary':           'CUSR0000SEHA',    # CPI rent of primary residence
    'cpi_owners_equiv_rent':      'CUSR0000SEHC',    # owners' equivalent rent
    
    # Macro context
    'fed_funds_rate':             'FEDFUNDS',
    'wti_crude_oil':              'DCOILWTICO',      # oil price — the inflation wildcard
    'ten_yr_breakeven_inflation': 'T10YIE',          # market's inflation expectation
    'sp500':                      'SP500',
    
    # New home cost inputs
    'lumber_ppi':                 'WPU0811',         # lumber price — upstream for homebuilders
    'construction_labor_cost':    'PCU2362312362310', # construction labor PPI
}

def pull_all_series():
    results = {}
    errors = []
    
    for name, series_id in SERIES.items():
        try:
            s = fred.get_series(series_id, observation_start='2000-01-01')
            s.name = name
            results[name] = s
            print(f"  ✓ {name} ({series_id}): {len(s)} observations, last={s.index[-1].date()}, value={s.iloc[-1]:.3f}")
        except Exception as e:
            errors.append(f"  ✗ {name} ({series_id}): {e}")
    
    if errors:
        print("\nFailed series:")
        for e in errors: print(e)
    
    # Combine into wide DataFrame
    df = pd.DataFrame(results)
    df.index.name = 'date'
    df.to_csv(f"{DATA_DIR}/fred_data.csv")
    print(f"\nSaved {len(df.columns)} series × {len(df)} observations → {DATA_DIR}/fred_data.csv")
    return df

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting FRED pull...")
    df = pull_all_series()
    
    # Print latest values for quick sanity check
    latest = df.iloc[-1].dropna()
    print("\n=== LATEST VALUES ===")
    for col, val in latest.items():
        print(f"  {col}: {val:.3f}")
```

Run it:

```bash
cd ~/housing_monitor
source .venv/bin/activate
python scripts/01_fred_pull.py
```

Expected output confirms all 20+ series pulled. If `MORTGAGE30US` shows something around 6.8%, `EXHOSLUSM495S` around 3,980 (thousand), and `HOSINVUSM495N` around 1.36 — your Bloomberg data from your screens is confirmed.

***
## Part 3: Person A — Script 02: FHFA Mortgage Rate Distribution (Day 2, ~1 hour)
This is the **most important input for the coiled spring model** — the distribution of outstanding mortgage rates tells you exactly how many homeowners are rate-locked at each threshold.[^3]

Create `~/housing_monitor/scripts/02_fhfa_pull.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import requests
import pandas as pd
from datetime import datetime

# FHFA National Mortgage Database — public CSV downloads
# Updated quarterly. No API key required.
# Dashboard: https://www.fhfa.gov/data/nmdb

FHFA_URLS = {
    # Outstanding mortgage rate distribution by rate bucket (% of total mortgages)
    # This is the key "lock-in" dataset — shows % of mortgages at each rate range
    'rate_distribution': 
        'https://www.fhfa.gov/sites/default/files/2025-01/MIRS_ARM_FRM_Combined.xlsx',
    
    # If the above URL changes (FHFA updates URLs quarterly), find current at:
    # https://www.fhfa.gov/data/mirs — Monthly Interest Rate Survey
    'mirs_backup':
        'https://www.fhfa.gov/sites/default/files/2025-04/MIRS_ARM_FRM_Combined.xlsx',
}

# Alternative: NY Fed Household Debt and Credit data — also shows mortgage origination rates
# This gives us the distribution of WHEN mortgages were originated and at what rate
NY_FED_URL = 'https://www.newyorkfed.org/medialibrary/interactives/householdcredit/data/xls/HHD_C_Report_2025Q3.xlsx'

def pull_fhfa_distribution():
    """
    Download FHFA monthly interest rate survey data.
    This shows the distribution of interest rates on newly originated mortgages over time.
    Combined with outstanding balance data, we can infer the rate distribution of locked holders.
    """
    for name, url in FHFA_URLS.items():
        try:
            print(f"Trying FHFA URL: {url}")
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                filepath = f"{DATA_DIR}/fhfa_{name}.xlsx"
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  ✓ Saved to {filepath}")
                
                # Parse the Excel file
                df = pd.read_excel(filepath, sheet_name=0, skiprows=5)
                df.to_csv(f"{DATA_DIR}/fhfa_{name}.csv", index=False)
                print(f"  ✓ Converted to CSV")
                return df
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    return None

def build_lock_in_distribution():
    """
    Build the rate lock-in distribution from public data.
    
    Method: We know from FHFA NMDB data (published Jan 2025) that:
    - 21.9% of outstanding mortgages have rates below 3%
    - ~35% are between 3-4%
    - ~25% are between 4-5%
    - ~4% are between 5-6%
    - ~14% are at 6%+
    
    Source: FHFA NMDB Outstanding Residential Mortgage Statistics Q1 2024
    https://www.fhfa.gov/news/news-release/fhfa-releases-data-visualization-dashboard-for-nmdb
    
    We update this quarterly when FHFA publishes new data.
    """
    
    # Hardcoded from FHFA NMDB Q4 2024 publication
    # Update these when FHFA publishes Q1 2025 data
    distribution = pd.DataFrame({
        'rate_bucket': ['<3%', '3-3.5%', '3.5-4%', '4-4.5%', '4.5-5%', '5-5.5%', '5.5-6%', '6-6.5%', '>6.5%'],
        'pct_of_outstanding': [0.219, 0.178, 0.172, 0.141, 0.107, 0.044, 0.032, 0.058, 0.049],
        'approx_midpoint_rate': [2.5, 3.25, 3.75, 4.25, 4.75, 5.25, 5.75, 6.25, 7.0],
        'est_homes_millions': [0, 0, 0, 0, 0, 0, 0, 0, 0]  # will calculate below
    })
    
    # Total single-family mortgaged homes ~50.8M (FHFA NMDB)
    total_mortgaged = 50.8  # million
    distribution['est_homes_millions'] = distribution['pct_of_outstanding'] * total_mortgaged
    
    distribution.to_csv(f"{DATA_DIR}/fhfa_distribution.csv", index=False)
    print(f"\nLock-in distribution saved:")
    print(distribution.to_string(index=False))
    return distribution

def calculate_coiled_spring(current_30yr_rate, distribution_df, threshold_bps=150):
    """
    For a given current 30-year mortgage rate, calculate:
    - How many homeowners are 'locked in' (current rate - their rate > threshold)
    - How many would 'unlock' if rates fell to each scenario level
    
    The threshold of 150bps is the empirically observed spread above which 
    homeowners strongly resist moving. Below 100bps spread, mobility normalizes.
    """
    threshold = threshold_bps / 100  # convert to percentage points
    
    print(f"\n=== COILED SPRING MODEL ===")
    print(f"Current 30yr rate: {current_30yr_rate:.2f}%")
    print(f"Lock-in threshold: {threshold_bps}bps above locked rate")
    print()
    
    results = []
    for _, row in distribution_df.iterrows():
        locked_rate = row['approx_midpoint_rate']
        homes = row['est_homes_millions']
        spread = current_30yr_rate - locked_rate
        is_locked = spread > threshold
        
        results.append({
            'rate_bucket': row['rate_bucket'],
            'midpoint_rate': locked_rate,
            'homes_millions': homes,
            'spread_to_current': spread,
            'is_locked': is_locked,
            'locked_homes_millions': homes if is_locked else 0
        })
    
    results_df = pd.DataFrame(results)
    total_locked = results_df['locked_homes_millions'].sum()
    
    print(f"Total locked homeowners at {current_30yr_rate:.2f}%: {total_locked:.1f}M")
    print(f"  ({total_locked/50.8*100:.0f}% of all mortgaged homeowners)")
    
    # Now calculate unlock at each scenario rate
    scenarios = [6.5, 6.25, 6.0, 5.75, 5.5, 5.25, 5.0, 4.75, 4.5]
    print(f"\nUnlock scenarios (threshold={threshold_bps}bps):")
    print(f"{'Rate':>8} | {'Still Locked':>14} | {'Unlocked vs Today':>18} | {'SAAR Uplift Est.':>17}")
    print("-" * 65)
    
    scenario_results = []
    for rate in scenarios:
        locked_at_rate = sum(
            row['homes_millions'] 
            for _, row in distribution_df.iterrows()
            if (rate - row['approx_midpoint_rate']) > threshold
        )
        unlocked_vs_today = total_locked - locked_at_rate
        
        # Each 1M unlocked homeowners adds roughly 200-350k to SAAR
        # (not all will sell immediately; assume 25% turnover of unlocked stock per year)
        saar_uplift = unlocked_vs_today * 0.28 * 1000  # in thousands
        
        scenario_results.append({
            'scenario_rate': rate,
            'locked_millions': locked_at_rate,
            'unlocked_vs_today_millions': unlocked_vs_today,
            'estimated_saar_uplift_k': saar_uplift
        })
        
        print(f"{rate:>7.2f}% | {locked_at_rate:>11.1f}M | {unlocked_vs_today:>+14.1f}M | {saar_uplift:>+13.0f}k SAAR")
    
    scenario_df = pd.DataFrame(scenario_results)
    scenario_df.to_csv(f"{DATA_DIR}/coiled_spring_scenarios.csv", index=False)
    return results_df, scenario_df

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting FHFA pull...")
    pull_fhfa_distribution()
    dist_df = build_lock_in_distribution()
    
    # Get current 30yr rate from FRED data
    fred_df = pd.read_csv(f"{DATA_DIR}/fred_data.csv", index_col='date', parse_dates=True)
    current_rate = fred_df['mortgage_rate_30yr'].dropna().iloc[-1]
    
    locked_df, scenarios_df = calculate_coiled_spring(current_rate, dist_df, threshold_bps=150)
```

Run it:

```bash
python scripts/02_fhfa_pull.py
```

***
## Part 4: Person A — Script 03+04+05: FMP Pipeline (Day 3, ~4 hours)
The current FMP stable API base URL is `https://financialmodelingprep.com/stable/`. Authentication is `?apikey=YOUR_KEY` on every request. All responses are JSON arrays.[^4]
### Script 03: Build the 400+ Ticker Universe
Create `~/housing_monitor/scripts/03_fmp_universe.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"

def fmp_get(endpoint, params=None):
    """Single FMP API call with error handling and rate limit respect."""
    if params is None:
        params = {}
    params['apikey'] = FMP_API_KEY
    url = f"{BASE}/{endpoint}"
    r = requests.get(url, params=params, timeout=30)
    if r.status_code == 429:
        print("  Rate limited — waiting 60s...")
        time.sleep(60)
        return fmp_get(endpoint, params)
    r.raise_for_status()
    return r.json()

# --- TIER 1: Direct / Highest beta to existing home turnover ---

TIER1_MANUAL = {
    # Homebuilders
    'NVR': ('Homebuilder', 1, 'long'), 'DHI': ('Homebuilder', 1, 'long'),
    'LEN': ('Homebuilder', 1, 'long'), 'PHM': ('Homebuilder', 1, 'long'),
    'TOL': ('Homebuilder', 1, 'long'), 'KBH': ('Homebuilder', 1, 'long'),
    'MDC': ('Homebuilder', 1, 'long'), 'TMHC': ('Homebuilder', 1, 'long'),
    'GRBK': ('Homebuilder', 1, 'long'), 'MTH': ('Homebuilder', 1, 'long'),
    'MHO': ('Homebuilder', 1, 'long'), 'SKY': ('Homebuilder', 1, 'long'),
    
    # Mortgage originators/servicers
    'RKT': ('Mortgage', 1, 'long'), 'UWMC': ('Mortgage', 1, 'long'),
    'PFSI': ('Mortgage', 1, 'long'), 'COOP': ('Mortgage', 1, 'long'),
    'LDI': ('Mortgage', 1, 'long'), 'GHLD': ('Mortgage', 1, 'long'),
    
    # Title and closing
    'FNF': ('Title', 1, 'long'), 'FAF': ('Title', 1, 'long'),
    'STC': ('Title', 1, 'long'), 'WD': ('Title', 1, 'long'),
    
    # Real estate brokerages and platforms
    'RDFN': ('RE Brokerage', 1, 'long'), 'Z': ('RE Platform', 1, 'long'),
    'ZG': ('RE Platform', 1, 'long'), 'OPEN': ('iBuyer', 1, 'long'),
    'COMP': ('RE Brokerage', 1, 'long'), 'EXPI': ('RE Brokerage', 1, 'long'),
}

TIER2_MANUAL = {
    # SFR REITs — direct supply absorbers — complex (short on unlock, long on rental demand)
    'INVH': ('SFR REIT', 2, 'short_on_unlock'), 
    'AMH':  ('SFR REIT', 2, 'short_on_unlock'),
    
    # Home improvement retail — highest indirect sensitivity
    'HD':  ('Home Improvement', 2, 'long'), 
    'LOW': ('Home Improvement', 2, 'long'),
    'FND': ('Flooring', 2, 'long'),
    'LL':  ('Flooring', 2, 'long'),
    
    # Moving and storage — direct transaction signal
    'UHAL': ('Moving/Storage', 2, 'long'), 'CUBE': ('Storage', 2, 'long'),
    'EXR':  ('Storage', 2, 'long'),  'LSI': ('Storage', 2, 'long'),
    'PSA':  ('Storage', 2, 'long'),
    
    # Home furnishings — "new mover" purchases
    'RH':  ('Home Furnishings', 2, 'long'), 'WSM': ('Home Furnishings', 2, 'long'),
    'ARHS': ('Home Furnishings', 2, 'long'),
    
    # Appliances
    'WHR': ('Appliances', 2, 'long'), 'MASCO': ('Building Products', 2, 'long'),
    'FBHS': ('Building Products', 2, 'long'),
    
    # Building materials
    'BLDR': ('Building Materials', 2, 'long'), 'IBP': ('Insulation', 2, 'long'),
    'TREX': ('Composite Decking', 2, 'long'), 'OC': ('Insulation', 2, 'long'),
    'AWI': ('Ceiling/Flooring', 2, 'long'), 'APOG': ('Glass/Windows', 2, 'long'),
    'PGTI': ('Windows/Doors', 2, 'long'), 'AZEK': ('Building Products', 2, 'long'),
    'BECN': ('Roofing/Siding', 2, 'long'), 'GMS': ('Wallboard', 2, 'long'),
    'SITE': ('Landscaping', 2, 'long'),
}

TIER3_MANUAL = {
    # Lumber
    'WY': ('Lumber/Timberland', 3, 'long'), 'RYN': ('Timberland', 3, 'long'),
    'PCH': ('Timberland', 3, 'long'), 'LP': ('Lumber', 3, 'long'),
    'UFPI': ('Wood Products', 3, 'long'),
    
    # Paint and coatings
    'SHW': ('Paint', 3, 'long'), 'RPM': ('Paint/Coatings', 3, 'long'),
    'PPG': ('Coatings', 3, 'long'), 'AXTA': ('Coatings', 3, 'long'),
    
    # HVAC
    'LII': ('HVAC', 3, 'long'), 'CARR': ('HVAC', 3, 'long'),
    'TT': ('HVAC', 3, 'long'), 'AOS': ('Water Heaters', 3, 'long'),
    'MHK': ('Flooring/HVAC', 3, 'long'),
    
    # Home security/smart home
    'ADT': ('Home Security', 3, 'long'), 'REZI': ('Smart Home', 3, 'long'),
    'GNRC': ('Home Power', 3, 'long'),
    
    # Financials with housing exposure
    'WFC': ('Bank/Mortgage', 3, 'long'), 'JPM': ('Bank/Mortgage', 3, 'long'),
    'BAC': ('Bank/Mortgage', 3, 'long'), 'USB': ('Bank/Mortgage', 3, 'long'),
    'KEY': ('Bank/Mortgage', 3, 'long'), 'FITB': ('Bank/Mortgage', 3, 'long'),
    'RF': ('Bank/Mortgage', 3, 'long'),
    
    # Insurance
    'ALL': ('Property Insurance', 3, 'long'), 'TRV': ('Property Insurance', 3, 'long'),
    'HIG': ('Property Insurance', 3, 'long'),
    
    # Private mortgage insurance
    'ESNT': ('PMI', 3, 'complex'), 'MTG': ('PMI', 3, 'complex'),
    'RDN': ('PMI', 3, 'complex'), 'NMIH': ('PMI', 3, 'complex'),
}

TIER4_SHORT_HEDGE = {
    # Apartment REITs — benefit from rental demand, HURT by homeownership unlock
    'EQR': ('Apartment REIT', 4, 'short_on_unlock'),
    'AVB': ('Apartment REIT', 4, 'short_on_unlock'),
    'MAA': ('Apartment REIT', 4, 'short_on_unlock'),
    'CPT': ('Apartment REIT', 4, 'short_on_unlock'),
    'UDR': ('Apartment REIT', 4, 'short_on_unlock'),
    'NMR': ('Apartment REIT', 4, 'short_on_unlock'),
    'ESS': ('Apartment REIT', 4, 'short_on_unlock'),
    'AIV': ('Apartment REIT', 4, 'short_on_unlock'),
}

def build_full_universe():
    all_tickers = {}
    all_tickers.update(TIER1_MANUAL)
    all_tickers.update(TIER2_MANUAL)
    all_tickers.update(TIER3_MANUAL)
    all_tickers.update(TIER4_SHORT_HEDGE)
    
    # Also pull from FMP screener to catch any we missed
    print("Pulling FMP screener — Real Estate sector...")
    re_screen = fmp_get("stock-screener", {"sector": "Real Estate", "exchange": "NYSE,NASDAQ", "limit": 200})
    time.sleep(0.5)
    
    print("Pulling FMP screener — Consumer Discretionary / Home Improvement...")
    cd_screen = fmp_get("stock-screener", {"sector": "Consumer Discretionary", "industry": "Home Improvement Retail", "limit": 100})
    time.sleep(0.5)
    
    print("Pulling FMP screener — Homebuilding industry...")
    hb_screen = fmp_get("stock-screener", {"industry": "Residential Construction", "limit": 100})
    time.sleep(0.5)
    
    # Add any screener results not already in our manual list
    screener_additions = 0
    for item in (re_screen + cd_screen + hb_screen):
        ticker = item.get('symbol', '')
        if ticker and ticker not in all_tickers:
            all_tickers[ticker] = ('Screener Result', 4, 'review_needed')
            screener_additions += 1
    
    print(f"\nAdded {screener_additions} tickers from FMP screener")
    
    # Enrich with FMP profile data (name, market cap, sector, industry)
    print(f"\nEnriching {len(all_tickers)} tickers with FMP profiles...")
    rows = []
    ticker_list = list(all_tickers.keys())
    
    # Process in batches of 10 to respect rate limits
    for i in range(0, len(ticker_list), 10):
        batch = ticker_list[i:i+10]
        symbols = ','.join(batch)
        try:
            profiles = fmp_get("profile", {"symbol": symbols})
            for p in profiles:
                ticker = p.get('symbol', '')
                if ticker in all_tickers:
                    subsector, tier, direction = all_tickers[ticker]
                    rows.append({
                        'ticker': ticker,
                        'company_name': p.get('companyName', ''),
                        'sector': p.get('sector', ''),
                        'industry': p.get('industry', ''),
                        'subsector_custom': subsector,
                        'sensitivity_tier': tier,
                        'directional_flag': direction,
                        'market_cap': p.get('mktCap', 0),
                        'description': p.get('description', '')[:200],
                    })
            print(f"  Batch {i//10 + 1}: enriched {len(batch)} tickers")
            time.sleep(0.3)
        except Exception as e:
            print(f"  Batch {i//10 + 1} failed: {e}")
            for ticker in batch:
                subsector, tier, direction = all_tickers[ticker]
                rows.append({'ticker': ticker, 'subsector_custom': subsector, 
                             'sensitivity_tier': tier, 'directional_flag': direction})
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['sensitivity_tier', 'market_cap'], ascending=[True, False])
    df.to_csv(f"{DATA_DIR}/fmp_tickers.csv", index=False)
    print(f"\nSaved {len(df)} tickers to {DATA_DIR}/fmp_tickers.csv")
    print(f"\nTier breakdown:")
    print(df.groupby('sensitivity_tier').size().to_string())
    return df

if __name__ == '__main__':
    universe_df = build_full_universe()
```
### Script 04: Batch Price History Pull
Create `~/housing_monitor/scripts/04_fmp_prices.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time
import os

BASE = "https://financialmodelingprep.com/stable"

def fmp_get(endpoint, params=None):
    if params is None: params = {}
    params['apikey'] = FMP_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code == 429:
        time.sleep(60)
        return fmp_get(endpoint, params)
    r.raise_for_status()
    return r.json()

def pull_price_history(ticker, start='2015-01-01'):
    """Pull full daily OHLCV for one ticker."""
    try:
        data = fmp_get(f"historical-price-full", {
            "symbol": ticker, 
            "from": start,
            "serietype": "line"
        })
        if not data or 'historical' not in data:
            return None
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').set_index('date')
        return df[['close', 'volume']]
    except Exception as e:
        print(f"  ✗ {ticker}: {e}")
        return None

def pull_all_prices():
    """Pull price history for all tickers in the universe."""
    tickers_df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    tickers = tickers_df['ticker'].dropna().unique().tolist()
    
    prices_dir = f"{DATA_DIR}/fmp_prices"
    os.makedirs(prices_dir, exist_ok=True)
    
    # Check which already exist (allows resuming if interrupted)
    existing = set(f.replace('.csv', '') for f in os.listdir(prices_dir))
    to_pull = [t for t in tickers if t not in existing]
    
    print(f"Pulling prices for {len(to_pull)} tickers ({len(existing)} already cached)...")
    
    for i, ticker in enumerate(to_pull):
        df = pull_price_history(ticker)
        if df is not None and len(df) > 100:
            df.to_csv(f"{prices_dir}/{ticker}.csv")
            print(f"  [{i+1}/{len(to_pull)}] ✓ {ticker}: {len(df)} days")
        else:
            print(f"  [{i+1}/{len(to_pull)}] ✗ {ticker}: insufficient data")
        
        time.sleep(0.25)  # ~4 requests/second — well within Ultimate plan limits
    
    print(f"\nPrice pull complete. {len(os.listdir(prices_dir))} tickers cached.")

if __name__ == '__main__':
    pull_all_prices()
```
### Script 05: Quarterly Financial Statements
Create `~/housing_monitor/scripts/05_fmp_financials.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import pandas as pd
import time

BASE = "https://financialmodelingprep.com/stable"

def fmp_get(endpoint, params=None):
    if params is None: params = {}
    params['apikey'] = FMP_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code == 429:
        time.sleep(60)
        return fmp_get(endpoint, params)
    r.raise_for_status()
    return r.json()

# Tier 1 and high-priority Tier 2 tickers for deep financial pulls
PRIORITY_TICKERS = [
    # Homebuilders — need: revenue, community count, backlog, gross margin
    'DHI', 'LEN', 'PHM', 'NVR', 'TOL', 'KBH', 'MDC', 'MTH', 'TMHC', 'GRBK', 'MHO',
    # Mortgage
    'RKT', 'UWMC', 'PFSI', 'COOP',
    # Title
    'FNF', 'FAF', 'STC',
    # Brokerages
    'RDFN', 'Z', 'COMP',
    # SFR REITs — critical for Factor 2 (REIT absorption)
    'INVH', 'AMH',
    # Home improvement
    'HD', 'LOW', 'FND',
    # Storage/moving — transaction velocity signal
    'UHAL', 'EXR', 'CUBE', 'PSA',
]

def pull_income_statements(ticker):
    data = fmp_get("income-statement", {"symbol": ticker, "period": "quarter", "limit": 20})
    if not data: return None
    df = pd.DataFrame(data)
    df['ticker'] = ticker
    return df

def pull_key_metrics(ticker):
    """For REITs: gets FFO, AFFO, and per-share metrics."""
    data = fmp_get("key-metrics", {"symbol": ticker, "period": "quarter", "limit": 20})
    if not data: return None
    df = pd.DataFrame(data)
    df['ticker'] = ticker
    return df

def pull_analyst_estimates(ticker):
    """Consensus estimates — used in event study (beat/miss analysis)."""
    data = fmp_get("analyst-estimates", {"symbol": ticker, "period": "quarter", "limit": 20})
    if not data: return None
    df = pd.DataFrame(data)
    df['ticker'] = ticker
    return df

def pull_all_financials():
    income_all, metrics_all, estimates_all = [], [], []
    
    for i, ticker in enumerate(PRIORITY_TICKERS):
        print(f"  [{i+1}/{len(PRIORITY_TICKERS)}] {ticker}...")
        
        income = pull_income_statements(ticker)
        if income is not None: income_all.append(income)
        time.sleep(0.3)
        
        metrics = pull_key_metrics(ticker)
        if metrics is not None: metrics_all.append(metrics)
        time.sleep(0.3)
        
        estimates = pull_analyst_estimates(ticker)
        if estimates is not None: estimates_all.append(estimates)
        time.sleep(0.3)
    
    if income_all:
        pd.concat(income_all).to_csv(f"{DATA_DIR}/fmp_income_statements.csv", index=False)
        print(f"Income statements saved.")
    if metrics_all:
        pd.concat(metrics_all).to_csv(f"{DATA_DIR}/fmp_key_metrics.csv", index=False)
        print(f"Key metrics saved.")
    if estimates_all:
        pd.concat(estimates_all).to_csv(f"{DATA_DIR}/fmp_estimates.csv", index=False)
        print(f"Analyst estimates saved.")

if __name__ == '__main__':
    pull_all_financials()
```

***
## Part 5: Person A — Script 06: sec-api.io REIT Property Extraction (Day 4, ~3 hours)
This script extracts Item 2 (Properties) from INVH and AMH 10-K filings to build the time series of homes owned — the core input for **Factor 2 (REIT absorption)** from the original prompt.[^5][^6][^7]

Create `~/housing_monitor/scripts/06_sec_reit.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY, DATA_DIR

from sec_api import QueryApi, ExtractorApi
import pandas as pd
import re
import json
from datetime import datetime

queryApi = QueryApi(api_key=SEC_API_KEY)
extractorApi = ExtractorApi(api_key=SEC_API_KEY)

# SFR REITs to track — these are the companies that have "gobbled up supply" per original prompt
SFR_REITS = {
    'INVH': 'Invitation Homes',
    'AMH':  'American Homes 4 Rent',
    # Tricon Residential went private — we track via legacy filings
    # Progress Residential is private — no EDGAR filings
}

def get_10k_filings(ticker, from_year=2017):
    """Get all 10-K filings for a ticker since from_year."""
    query = {
        "query": f"formType:\"10-K\" AND ticker:{ticker} AND filedAt:[{from_year}-01-01 TO 2026-12-31]",
        "from": "0",
        "size": "20",
        "sort": [{"filedAt": {"order": "asc"}}]
    }
    result = queryApi.get_filings(query)
    return result.get('filings', [])

def extract_homes_owned(filing_url, ticker):
    """
    Extract Item 2 (Properties) from a 10-K filing.
    Parse the number of single-family homes owned from the text.
    """
    try:
        # Get Item 2 in plain text
        text = extractorApi.get_section(filing_url, "2", "text")
        
        # Pattern match for home counts — each REIT phrases this differently
        patterns = [
            r'(\d{2,3},\d{3})\s+(?:single-family|single family)\s+homes',
            r'portfolio of\s+(\d{2,3},\d{3})\s+homes',
            r'owned\s+(\d{2,3},\d{3})\s+(?:single-family|single family)',
            r'approximately\s+(\d{2,3},\d{3})\s+homes',
            r'(\d{2,3},\d{3})\s+(?:properties|homes)\s+(?:as of|at)',
            r'total of\s+(\d{2,3},\d{3})\s+(?:single-family|homes)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')
                return int(count_str)
        
        # If no match, return None and log for manual review
        print(f"    Could not parse home count from {ticker} filing")
        return None
        
    except Exception as e:
        print(f"    Extraction error: {e}")
        return None

def build_reit_homes_timeseries():
    """Build time series of total homes owned by SFR REITs."""
    results = []
    
    for ticker, name in SFR_REITS.items():
        print(f"\nProcessing {name} ({ticker})...")
        filings = get_10k_filings(ticker)
        print(f"  Found {len(filings)} 10-K filings")
        
        for filing in filings:
            filed_at = filing.get('filedAt', '')[:10]
            period = filing.get('periodOfReport', '')
            filing_url = filing.get('linkToFilingDetails', '')
            
            print(f"  Processing {period} filing...")
            homes = extract_homes_owned(filing_url, ticker)
            
            results.append({
                'ticker': ticker,
                'company': name,
                'period': period,
                'filed_at': filed_at,
                'homes_owned': homes,
                'filing_url': filing_url
            })
            
            if homes:
                print(f"    ✓ {period}: {homes:,} homes")
    
    df = pd.DataFrame(results)
    df = df.sort_values(['ticker', 'period'])
    df.to_csv(f"{DATA_DIR}/sec_reit_homes.csv", index=False)
    
    print(f"\n=== SFR REIT HOMES OWNED (TIME SERIES) ===")
    print(df.dropna(subset=['homes_owned'])[['ticker', 'period', 'homes_owned']].to_string(index=False))
    return df

def setup_8k_alert_monitor():
    """
    Set up a search query for real-time 8-K alerts.
    This query finds 8-K filings from housing-sensitive companies mentioning key terms.
    Run this daily to catch policy signals early.
    """
    
    # Tickers to monitor for housing policy signals
    housing_tickers = "DHI LEN PHM NVR TOL INVH AMH RKT FNF FAF RDFN Z HD LOW"
    
    query = {
        "query": f"formType:\"8-K\" AND ticker:({housing_tickers}) AND filedAt:[{{TODAY}} TO {{TODAY}}]",
        "from": "0",
        "size": "50",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    # Search for today's 8-Ks
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    query["query"] = f"formType:\"8-K\" AND ticker:({housing_tickers}) AND filedAt:[{today} TO {today}]"
    
    result = queryApi.get_filings(query)
    filings_today = result.get('filings', [])
    
    alerts = []
    for filing in filings_today:
        # Get Item 7.01 (Reg FD) and 8.01 (Other Events) — most likely to contain policy commentary
        items = filing.get('items', [])
        
        alert = {
            'ticker': filing.get('ticker', ''),
            'company': filing.get('companyName', ''),
            'filed_at': filing.get('filedAt', '')[:16],
            'items': ', '.join(items),
            'url': filing.get('linkToFilingDetails', '')
        }
        alerts.append(alert)
        print(f"  8-K ALERT: {alert['ticker']} — {alert['items']} — {alert['filed_at']}")
    
    if not alerts:
        print(f"  No 8-K alerts for {today}")
    
    return pd.DataFrame(alerts)

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting sec-api.io pull...")
    reit_df = build_reit_homes_timeseries()
    
    print(f"\n[{datetime.now()}] Running daily 8-K alert scan...")
    alerts_df = setup_8k_alert_monitor()
    
    if not alerts_df.empty:
        alerts_df.to_csv(f"{DATA_DIR}/sec_8k_alerts_today.csv", index=False)
        print(f"Alerts saved — {len(alerts_df)} filings today")
```

***
## Part 6: Person A — Script 07: Capital IQ Deep Pull (Day 5, ~3 hours)
The Capital IQ SDK real module name is `spgmi_api_sdk.ciq.services` and the class is `SDKDataServices(username, password)`. Note: the PyPI `SPGMICIQ` package is a placeholder — the actual SDK must be downloaded from the S&P Global Support Center and installed from the downloaded file.[^8]

Create `~/housing_monitor/scripts/07_ciq_pull.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import CIQ_USERNAME, CIQ_PASSWORD, DATA_DIR

from spgmi_api_sdk.ciq.services import SDKDataServices
import pandas as pd
from datetime import datetime

spg = SDKDataServices(CIQ_USERNAME, CIQ_PASSWORD)

# --- PRIORITY TICKERS FOR CIQ DEEP PULL ---
# Use CIQ for Tier 1+2 only — too expensive to run on all 400+

HOMEBUILDERS = ["DHI", "LEN", "PHM", "NVR", "TOL", "KBH", "MDC", "MTH", "TMHC", "GRBK"]
SFR_REITS = ["INVH", "AMH"]
MORTGAGE = ["RKT", "UWMC", "PFSI", "COOP"]
TITLE = ["FNF", "FAF", "STC"]
HOME_IMPROVEMENT = ["HD", "LOW", "FND", "LL"]
APARTMENT_REITS = ["EQR", "AVB", "MAA", "CPT", "UDR"]  # the short/hedge basket

ALL_PRIORITY = HOMEBUILDERS + SFR_REITS + MORTGAGE + TITLE + HOME_IMPROVEMENT + APARTMENT_REITS

def pull_financials_historical():
    """Pull 5 years of quarterly income statement data."""
    print("Pulling historical financials (quarterly, 20 periods)...")
    
    try:
        df = spg.get_financials(
            identifiers=ALL_PRIORITY,
            period_type="IQ_FQ-20"  # last 20 quarters
        )
        df.to_csv(f"{DATA_DIR}/ciq_financials_quarterly.csv")
        print(f"  ✓ Saved quarterly financials for {len(ALL_PRIORITY)} tickers")
        return df
    except Exception as e:
        print(f"  ✗ CIQ financials error: {e}")
        return None

def pull_estimates():
    """Consensus analyst estimates — forward-looking EPS, revenue, EBITDA."""
    print("Pulling analyst estimates...")
    
    try:
        df = spg.get_estimates(identifiers=ALL_PRIORITY)
        # Output includes: analyst recommendations, target price, forward P/E,
        # forward EPS, forward revenue, forward EBITDA
        df.to_csv(f"{DATA_DIR}/ciq_estimates.csv")
        print(f"  ✓ Saved estimates")
        return df
    except Exception as e:
        print(f"  ✗ CIQ estimates error: {e}")
        return None

def pull_multiples():
    """Key valuation multiples for each ticker."""
    print("Pulling valuation multiples...")
    
    try:
        df = spg.get_multiples(identifiers=ALL_PRIORITY)
        # Output: P/E, P/Book, TEV/EBITDA, P/Sales
        df.to_csv(f"{DATA_DIR}/ciq_multiples.csv")
        print(f"  ✓ Saved multiples")
        return df
    except Exception as e:
        print(f"  ✗ CIQ multiples error: {e}")
        return None

def pull_key_developments():
    """
    Latest activity for each Tier 1 ticker — this is the policy signal hunter.
    CIQ aggregates news, filings, and press releases into 'key developments.'
    Especially valuable for catching homebuilder commentary on market conditions.
    """
    print("Pulling key developments (policy signal scan)...")
    
    for ticker in HOMEBUILDERS[:5]:  # Start with top 5 builders for cost control
        try:
            response = spg.get_latest_activity(identifiers=[ticker])
            docs, events, key_devs = response
            
            if not key_devs.empty:
                # Look for housing-market-relevant key developments
                housing_keywords = ['mortgage', 'interest rate', 'affordability', 
                                   'demand', 'orders', 'cancellation', 'backlog']
                
                for _, row in key_devs.iterrows():
                    headline = str(row.get('headline', '')).lower()
                    if any(kw in headline for kw in housing_keywords):
                        print(f"  🔔 SIGNAL [{ticker}]: {row.get('headline', '')[:100]}")
        
        except Exception as e:
            print(f"  ✗ {ticker} key developments: {e}")

def pull_homebuilder_operational_kpis():
    """
    Homebuilder-specific KPIs not in GAAP statements.
    These are the operational metrics that lead financials by 1-2 quarters.
    
    Key metrics to extract:
    - Net new orders (leading indicator of revenue)
    - Cancellation rate (consumer confidence signal)
    - Community count (capacity constraint)
    - Backlog units and value (visible future revenue)
    - Average selling price (mix and affordability signal)
    """
    print("\nPulling homebuilder operational KPIs via CIQ...")
    
    # CIQ mnemonic codes for homebuilder KPIs
    # These are SNL Real Estate / homebuilder-specific data items
    homebuilder_mnemonics = [
        "IQ_HOMEBLDR_NET_NEW_ORDERS",    # Net new orders (units)
        "IQ_HOMEBLDR_CANCEL_RATE",        # Cancellation rate (%)
        "IQ_HOMEBLDR_COMMUNITY_COUNT",    # Active selling communities
        "IQ_HOMEBLDR_BACKLOG_UNITS",      # Backlog (units)
        "IQ_HOMEBLDR_BACKLOG_VALUE",      # Backlog (dollar value)
        "IQ_HOMEBLDR_HOMES_CLOSED",       # Closings (units)
        "IQ_HOMEBLDR_AVG_SELLING_PRICE",  # Average selling price
    ]
    
    try:
        df = spg.get_financials_historical(
            identifiers=HOMEBUILDERS,
            mnemonics=homebuilder_mnemonics,
            properties={"periodType": "IQ_FQ-20"}
        )
        df.to_csv(f"{DATA_DIR}/ciq_homebuilder_ops.csv")
        print(f"  ✓ Saved homebuilder operational KPIs")
        return df
    except Exception as e:
        print(f"  ✗ Homebuilder KPI error: {e}")
        print("  Note: Exact mnemonic names may vary — check CIQ Python SDK User Guide")
        return None

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting Capital IQ pull...")
    pull_financials_historical()
    pull_estimates()
    pull_multiples()
    pull_homebuilder_operational_kpis()
    pull_key_developments()
    print(f"[{datetime.now()}] Capital IQ pull complete.")
```

***
## Part 7: Person A — Script 08: Correlation Engine (Day 5, ~2 hours)
This scores every ticker in the universe by its statistical relationship to housing turnover — the quantitative backbone of the tier sensitivity matrix from the original prompt.

Create `~/housing_monitor/scripts/09_correlation_engine.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
import numpy as np
from datetime import datetime

def build_correlation_matrix():
    """
    For each of the 400+ tickers, compute:
    1. Correlation of monthly returns vs. EXHOSLUSM495S YoY change
    2. Correlation of monthly returns vs. MORTGAGE30US
    3. Average return around NAR release dates (event study)
    """
    
    # Load FRED data — existing home sales SAAR (monthly)
    fred_df = pd.read_csv(f"{DATA_DIR}/fred_data.csv", index_col='date', parse_dates=True)
    saar = fred_df['existing_home_sales_saar'].dropna()
    saar_yoy = saar.pct_change(12)  # year-over-year change
    mortgage = fred_df['mortgage_rate_30yr'].dropna()
    mortgage_mom = mortgage.diff()  # month-over-month change in rate
    
    # Load ticker universe
    tickers_df = pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    
    prices_dir = f"{DATA_DIR}/fmp_prices"
    results = []
    
    for _, row in tickers_df.iterrows():
        ticker = row['ticker']
        price_file = f"{prices_dir}/{ticker}.csv"
        
        if not os.path.exists(price_file):
            continue
        
        try:
            prices = pd.read_csv(price_file, index_col='date', parse_dates=True)['close']
            monthly_returns = prices.resample('ME').last().pct_change()
            
            # Align dates
            common_saar = saar_yoy.reindex(monthly_returns.index, method='ffill')
            common_mortgage = mortgage_mom.resample('ME').last().reindex(monthly_returns.index, method='ffill')
            
            valid = monthly_returns.dropna()
            valid_saar = common_saar.reindex(valid.index).dropna()
            valid_mortgage = common_mortgage.reindex(valid.index).dropna()
            
            # Compute correlations
            corr_saar = valid.corr(valid_saar) if len(valid_saar) > 24 else np.nan
            corr_mortgage = valid.corr(valid_mortgage) if len(valid_mortgage) > 24 else np.nan
            
            # Annualized volatility
            ann_vol = valid.std() * np.sqrt(12)
            
            # Average return in months when SAAR beats/misses by >5%
            # (simplified event study — full version needs exact NAR release dates)
            saar_beat_months = saar_yoy[saar_yoy > 0.05].index
            beat_returns = monthly_returns.reindex(saar_beat_months).mean()
            miss_returns = monthly_returns.reindex(saar_yoy[saar_yoy < -0.05].index).mean()
            
            results.append({
                'ticker': ticker,
                'company_name': row.get('company_name', ''),
                'sensitivity_tier': row.get('sensitivity_tier', ''),
                'subsector_custom': row.get('subsector_custom', ''),
                'directional_flag': row.get('directional_flag', ''),
                'corr_vs_saar_yoy': round(corr_saar, 3) if not np.isnan(corr_saar) else None,
                'corr_vs_mortgage_rate_chg': round(corr_mortgage, 3) if not np.isnan(corr_mortgage) else None,
                'avg_return_on_saar_beat': round(beat_returns * 100, 2) if not np.isnan(beat_returns) else None,
                'avg_return_on_saar_miss': round(miss_returns * 100, 2) if not np.isnan(miss_returns) else None,
                'annualized_vol': round(ann_vol * 100, 1) if not np.isnan(ann_vol) else None,
                'data_months': len(valid),
            })
            
        except Exception as e:
            pass
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(['sensitivity_tier', 'corr_vs_saar_yoy'], 
                                         ascending=[True, False])
    results_df.to_csv(f"{DATA_DIR}/correlation_matrix.csv", index=False)
    
    print(f"\n=== CORRELATION MATRIX (TOP 20 by SAAR correlation) ===")
    top20 = results_df.nlargest(20, 'corr_vs_saar_yoy')[
        ['ticker', 'subsector_custom', 'sensitivity_tier', 
         'corr_vs_saar_yoy', 'avg_return_on_saar_beat']
    ]
    print(top20.to_string(index=False))
    return results_df

if __name__ == '__main__':
    build_correlation_matrix()
```

***
## Part 8: Person A — Script 10: Context Generator (Day 6, ~2 hours)
This is the bridge between the Mac mini and Perplexity Computer. It takes all the processed data and writes `housing_context.md` — the file Perplexity Computer will read as its grounding context.

Create `~/housing_monitor/scripts/10_context_generator.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR, PUBLIC_DIR

import pandas as pd
import json
from datetime import datetime, date

def load_latest_fred():
    df = pd.read_csv(f"{DATA_DIR}/fred_data.csv", index_col='date', parse_dates=True)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    return df, latest, prev

def load_coiled_spring():
    try:
        return pd.read_csv(f"{DATA_DIR}/coiled_spring_scenarios.csv")
    except:
        return None

def load_five_factor_attribution():
    """
    Returns the current five-factor attribution.
    Initially hardcoded from research; updated quarterly via Perplexity Computer task.
    """
    return {
        'rate_lock_in': {
            'units_lost_k': 420,
            'pct_of_gap': 42,
            'description': 'Homeowners with sub-5% mortgages locked in by rate differential >150bps',
            'latest_data': 'FHFA NMDB Q4 2024: 50.8M outstanding mortgages tracked'
        },
        'sfr_reit_absorption': {
            'units_lost_k': 180,
            'pct_of_gap': 18,
            'description': 'SFR REITs (INVH, AMH, etc.) absorbed ~450-550k homes from for-sale market; turnover <5%/yr',
            'latest_data': 'sec-api.io 10-K extraction: INVH ~84k homes, AMH ~59k homes as of latest 10-K'
        },
        'second_third_home_lock_in': {
            'units_lost_k': 120,
            'pct_of_gap': 12,
            'description': '2nd/3rd homes turn over less frequently; post-COVID surge in vacation ownership depressed supply',
            'latest_data': 'Census American Housing Survey; ~6-7M second homes nationally'
        },
        'demographics_ceiling': {
            'units_lost_k': 160,
            'pct_of_gap': 16,
            'description': '25-34 cohort homeownership trending lower; renter-by-choice preference increasing at margin',
            'latest_data': 'Census homeownership by age: 25-34 cohort at structural plateau vs 1994 baseline'
        },
        'affordability_rent_own_spread': {
            'units_lost_k': 120,
            'pct_of_gap': 12,
            'description': 'Monthly cost to own vs rent at historic spread; rent deflation beginning to narrow but oil-driven inflation delays Fed',
            'latest_data': 'HOMECOMP 109.10 as of Q4 2025; CPI rent trending down as lagging indicator'
        }
    }

def generate_context_markdown(fred_latest, fred_prev, fred_df, spring_df, factors):
    """Generate the housing_context.md file that Perplexity Computer reads."""
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M PDT')
    
    # Calculate deltas
    def delta(col, fmt='.2f'):
        curr = fred_latest.get(col, float('nan'))
        prev_val = fred_prev.get(col, float('nan'))
        if pd.isna(curr) or pd.isna(prev_val):
            return 'N/A', 'N/A', 'N/A'
        d = curr - prev_val
        return format(curr, fmt), format(d, '+' + fmt), '▲' if d > 0 else '▼'
    
    saar_curr, saar_delta, saar_dir = delta('existing_home_sales_saar', '.0f')
    inv_curr, inv_delta, inv_dir = delta('for_sale_inventory', '.3f')
    rate_curr, rate_delta, rate_dir = delta('mortgage_rate_30yr', '.2f')
    afford_curr, afford_delta, afford_dir = delta('affordability_composite', '.1f')
    own_curr, own_delta, own_dir = delta('homeownership_rate', '.1f')
    oil_curr, oil_delta, oil_dir = delta('wti_crude_oil', '.2f')
    
    # Total gap
    gap_k = 5000 - float(saar_curr.replace(',','')) if saar_curr != 'N/A' else 1000
    factor_total = sum(f['units_lost_k'] for f in factors.values())
    
    md = f"""# US Housing Market Intelligence Feed
**Generated:** {now} | **Next NAR Release:** Check NAR.realtor for exact date

---

## Core Metrics (Latest Available)

| Metric | Current | Change | Bloomberg Ticker | Normal Range |
|--------|---------|--------|-----------------|-------------|
| **Existing Home Sales SAAR** | {saar_curr}k {saar_dir} | {saar_delta}k | ETSLTOTL | ~5,000k |
| **For-Sale Inventory** | {inv_curr}M units {inv_dir} | {inv_delta}M | ETSLHAFS | ~2.0M |
| **30-Year Mortgage Rate** | {rate_curr}% {rate_dir} | {rate_delta}% | MORTGAGE30US | ~5.0-5.5% unlock |
| **Housing Affordability Index** | {afford_curr} {afford_dir} | {afford_delta} | HOMECOMP | 100=balanced |
| **Homeownership Rate** | {own_curr}% {own_dir} | {own_delta}ppt | USH HOME | ~63-66% |
| **WTI Crude Oil** | ${oil_curr} {oil_dir} | ${oil_delta} | DCOILWTICO | Fed inflation factor |

> **The Gap:** Current SAAR of {saar_curr}k vs. normalized 5,000k = **{gap_k:.0f}k unit deficit**

---

## Five-Factor Attribution Model
*Structural vs. cyclical decomposition of the ~1M unit gap from 5M normalized SAAR*

| Factor | Units Lost (est.) | % of Gap | Key Dynamic |
|--------|-----------------|---------|------------|
"""
    
    for factor_name, data in factors.items():
        label = factor_name.replace('_', ' ').title()
        md += f"| **{label}** | ~{data['units_lost_k']}k | {data['pct_of_gap']}% | {data['description'][:80]}... |\n"
    
    md += f"""
*Total attributed: ~{factor_total}k | Residual/unattributed: ~{max(0, int(gap_k)-factor_total)}k*

---

## Coiled Spring Model — Rate Unlock Scenarios
*At what mortgage rate do locked homeowners begin to move? Threshold: 150bps spread above locked rate*
*Source: FHFA NMDB Q4 2024 — 50.8M outstanding mortgages*

"""
    
    if spring_df is not None:
        md += "| Scenario Rate | Homes Still Locked | Unlocked vs. Today | Est. SAAR Uplift |\n"
        md += "|--------------|-------------------|-------------------|------------------|\n"
        for _, row in spring_df.iterrows():
            md += f"| **{row['scenario_rate']:.2f}%** | {row['locked_millions']:.1f}M | {row['unlocked_vs_today_millions']:+.1f}M | {row['estimated_saar_uplift_k']:+.0f}k |\n"
    
    md += f"""

---

## Macro Context — The Unlock Chain

**The Fed is stuck:** Oil at ${oil_curr}/bbl creates persistent headline inflation that prevents rate cuts.
Per the original analytical framework: "The Fed is stuck as long as oil prices are so high with Iran,
on the inflationary outlook." The administration must resolve oil before Fed can meaningfully cut.

**Structural deflation offset:** Rents are coming down (lagging indicator — CPI rent trending down).
When oil resolves, the disinflationary backdrop could allow faster Fed action than market expects.

**Political incentive:** Administration has strong motivation to unlock housing before 2028.
Key lever: legislative/regulatory action that doesn't require Fed (FHA limits, GSE policy,
capital gains exclusion expansion, mortgage portability/assumability legislation).

**Inventory paradox:** Rising inventory ({inv_curr}M) is a GOOD sign — unlike 2005-2007 distressed buildup,
current inventory rise = sellers gaining confidence = precursor to velocity normalization.

---

## Policy Signal Monitor
*Updated by Perplexity Computer weekly synthesis task*

[PERPLEXITY COMPUTER UPDATES THIS SECTION — DO NOT EDIT MANUALLY]

---

## Data Freshness
| Dataset | Last Updated | Source | Update Frequency |
|---------|-------------|--------|-----------------|
| FRED core series | {now[:10]} | St. Louis Fed API | Daily |
| FHFA rate distribution | Q4 2024 | FHFA NMDB | Quarterly |
| SFR REIT homes owned | Per latest 10-K | sec-api.io | Annual (10-K) |
| 400+ ticker prices | {now[:10]} | FMP Stable API | Daily |
| CIQ segment data | Per latest quarter | Capital IQ SDK | Quarterly |
| Five-factor attribution | Q4 2025 | Analyst model | Quarterly (via Perplexity) |

---
*This file is machine-generated by the Mac mini housing monitor pipeline.*
*To trigger a Perplexity Computer analysis, use the task prompts in the task library.*
"""
    return md

def generate_dashboard_json(fred_latest, fred_prev, spring_df, factors):
    """Generate housing_data.json for dashboard rendering."""
    
    def safe_float(val):
        try:
            return float(val) if not pd.isna(val) else None
        except:
            return None
    
    data = {
        "generated_at": datetime.now().isoformat(),
        "metrics": {
            "existing_home_sales_saar_k": safe_float(fred_latest.get('existing_home_sales_saar')),
            "for_sale_inventory_m": safe_float(fred_latest.get('for_sale_inventory')),
            "mortgage_rate_30yr": safe_float(fred_latest.get('mortgage_rate_30yr')),
            "affordability_index": safe_float(fred_latest.get('affordability_composite')),
            "homeownership_rate": safe_float(fred_latest.get('homeownership_rate')),
            "wti_crude": safe_float(fred_latest.get('wti_crude_oil')),
            "cpi_rent_yoy": None,  # calculated separately
        },
        "coiled_spring": spring_df.to_dict('records') if spring_df is not None else [],
        "five_factors": factors,
        "gap_from_norm_k": 5000 - (safe_float(fred_latest.get('existing_home_sales_saar')) or 0),
        "policy_signals": []  # populated by Perplexity Computer task output
    }
    return data

if __name__ == '__main__':
    print(f"[{datetime.now()}] Generating context files...")
    
    fred_df, fred_latest, fred_prev = load_latest_fred()
    spring_df = load_coiled_spring()
    factors = load_five_factor_attribution()
    
    # Generate Markdown (for Perplexity Computer)
    md = generate_context_markdown(fred_latest, fred_prev, fred_df, spring_df, factors)
    md_path = f"{PUBLIC_DIR}/housing_context.md"
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(md_path, 'w') as f:
        f.write(md)
    print(f"  ✓ housing_context.md written ({len(md)} chars)")
    
    # Generate JSON (for dashboard)
    data = generate_dashboard_json(fred_latest, fred_prev, spring_df, factors)
    json_path = f"{PUBLIC_DIR}/housing_data.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ housing_data.json written")
    
    print(f"\nFiles ready to push to GitHub Pages.")
```

***
## Part 9: Person A — GitHub Auto-Push and Cron Setup (Day 6, ~1 hour)
Create `~/housing_monitor/scripts/push_to_github.py`:

```python
import subprocess
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import PUBLIC_DIR
from datetime import datetime

def push_to_github():
    repo_dir = os.path.join(os.path.dirname(__file__), '..')
    
    commands = [
        ['git', '-C', repo_dir, 'add', 'public/housing_context.md', 'public/housing_data.json'],
        ['git', '-C', repo_dir, 'commit', '-m', f'Auto-update {datetime.now().strftime("%Y-%m-%d %H:%M")}'],
        ['git', '-C', repo_dir, 'push', 'origin', 'main'],
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if 'nothing to commit' in result.stdout:
                print("  No changes to push.")
                return
            print(f"  Git error: {result.stderr}")
            return
    
    print(f"  ✓ Pushed to GitHub Pages at {datetime.now()}")

if __name__ == '__main__':
    push_to_github()
```

Create the master runner `~/housing_monitor/scripts/run_all.sh`:

```bash
#!/bin/bash
set -e

LOG_FILE="$HOME/housing_monitor/logs/housing_monitor.log"
VENV="$HOME/housing_monitor/.venv/bin/python"
SCRIPTS="$HOME/housing_monitor/scripts"

echo "[$(date)] === HOUSING MONITOR RUN STARTING ===" >> "$LOG_FILE"

cd "$HOME/housing_monitor"
source .venv/bin/activate

# Run each script, log output
$VENV $SCRIPTS/01_fred_pull.py >> "$LOG_FILE" 2>&1 && echo "[$(date)] FRED: OK" >> "$LOG_FILE"
$VENV $SCRIPTS/02_fhfa_pull.py >> "$LOG_FILE" 2>&1 && echo "[$(date)] FHFA: OK" >> "$LOG_FILE"
# 03+04+05 run weekly, not daily (too many API calls for daily)
$VENV $SCRIPTS/10_context_generator.py >> "$LOG_FILE" 2>&1 && echo "[$(date)] Context: OK" >> "$LOG_FILE"
$VENV $SCRIPTS/push_to_github.py >> "$LOG_FILE" 2>&1 && echo "[$(date)] GitHub push: OK" >> "$LOG_FILE"
$VENV $SCRIPTS/06_sec_reit.py >> "$LOG_FILE" 2>&1 && echo "[$(date)] 8-K alerts: OK" >> "$LOG_FILE"

echo "[$(date)] === RUN COMPLETE ===" >> "$LOG_FILE"
```

Set up cron jobs. Open crontab:

```bash
crontab -e
```

Add these lines:

```cron
# Daily: FRED + FHFA + context push (runs at 7:30 AM every day)
30 7 * * * /bin/bash /Users/YOURUSERNAME/housing_monitor/scripts/run_all.sh

# Weekly: Full data refresh (runs Monday 6:00 AM)
0 6 * * 1 /Users/YOURUSERNAME/housing_monitor/.venv/bin/python /Users/YOURUSERNAME/housing_monitor/scripts/03_fmp_universe.py
30 6 * * 1 /Users/YOURUSERNAME/housing_monitor/.venv/bin/python /Users/YOURUSERNAME/housing_monitor/scripts/04_fmp_prices.py
0 7 * * 1 /Users/YOURUSERNAME/housing_monitor/.venv/bin/python /Users/YOURUSERNAME/housing_monitor/scripts/09_correlation_engine.py

# Monthly (1st of month, 8:00 AM): CIQ pull + full financial refresh
0 8 1 * * /Users/YOURUSERNAME/housing_monitor/.venv/bin/python /Users/YOURUSERNAME/housing_monitor/scripts/05_fmp_financials.py
30 8 1 * * /Users/YOURUSERNAME/housing_monitor/.venv/bin/python /Users/YOURUSERNAME/housing_monitor/scripts/07_ciq_pull.py

# On NAR release days (manually update this with NAR release schedule):
# NAR releases existing home sales around the 22nd of each month
# 0 10 22 * * /bin/bash /Users/YOURUSERNAME/housing_monitor/scripts/run_all.sh
```

***
## Part 10: Person B — Perplexity Computer Setup and Task Library (Day 3, concurrent with Person A Day 3)
### Step B.1: Confirm Your Feed URL is Live
Before writing any Perplexity Computer tasks, verify the URL Person A set up is accessible. In a regular browser, navigate to:

```
https://YOURUSERNAME.github.io/housing-monitor/housing_context.md
```

You should see the markdown file rendering. If you see a 404, GitHub Pages may take up to 10 minutes to activate after the first push — check github.com/YOURUSERNAME/housing-monitor → Settings → Pages for status.
### Step B.2: The Perplexity Computer Interface
Go to perplexity.ai/computer. Perplexity Computer accepts multi-step tasks in natural language. It can browse URLs, read file contents, search the web, and write output files you download. There is no API or webhook — you type or paste the task, click run, and it executes autonomously.

**The key insight:** Because it can browse to your GitHub Pages URL, your Mac mini data feed becomes its "live context injection." Every task should start: *"Go to [URL] and read the current housing data feed. Use it as your quantitative foundation for the following task..."*
### Step B.3: The Weekly Monitor Task
Copy this exactly into Perplexity Computer every Monday morning (or set it as a recurring task if the Computer recurring-tasks feature is available in your subscription):

```
TASK: US Housing Market Weekly Intelligence Update

STEP 1 — READ DATA FEED
Go to https://YOURUSERNAME.github.io/housing-monitor/housing_context.md
Read the entire file. Note the current values for: SAAR, inventory, 30-year mortgage rate, 
affordability index, homeownership rate, oil price, and all coiled spring scenario outputs.

STEP 2 — POLICY SIGNAL SCAN (search the web)
Search for any of the following from the last 7 days:
a) Federal legislation mentioning "housing affordability" OR "mortgage rate relief" OR 
   "first-time homebuyer tax credit" OR "capital gains home exclusion" OR "assumable mortgage"
b) Administration (White House, HUD, Treasury, FHFA) statements on housing market
c) Congressional bills introduced related to housing supply, homeownership, or mortgage reform
d) Federal Reserve officials commenting on housing market or rate path implications for housing
e) NAR (National Association of Realtors) or NAHB press releases from this week

For each finding: state (1) what was announced, (2) by whom, (3) date, 
(4) URL/source, (5) relevance to existing home sales unlock on a scale of 1-5.

STEP 3 — RATE PATH UPDATE
Search for: latest Fed funds futures pricing, any FOMC member speeches from this week, 
and the current 30-year mortgage rate vs. last week. 
Answer: Has the probability of a rate cut before year-end increased or decreased vs. 
last week? What is the most likely path to mortgage rates at 5.5% and when?

STEP 4 — STOCK SIGNAL SCAN
For these specific tickers: DHI, LEN, PHM, NVR, RDFN, Z, INVH, AMH, FNF, FAF, HD, LOW
Search for: any analyst upgrades/downgrades this week, earnings pre-announcements, 
guidance changes, or CEO/CFO commentary on housing market conditions.

STEP 5 — GENERATE OUTPUT
Write a structured markdown update with these exact sections:
## Policy Signals This Week
## Rate Path Update  
## Stock-Level Alerts
## One Key Risk Not in the Model
## One Underappreciated Catalyst

Save the output as a file I can download. Title: "Housing_Weekly_[DATE].md"
```
### Step B.4: The Monthly Deep Dive Task (Run on NAR Release Day)
```
TASK: US Housing Market Monthly Deep Dive — NAR Release Analysis

STEP 1 — READ DATA FEED
Go to https://YOURUSERNAME.github.io/housing-monitor/housing_context.md
Record all current metric values.

STEP 2 — NAR RELEASE ANALYSIS
Search for the latest NAR existing home sales release (just published). Find:
- Actual SAAR vs. prior month vs. consensus estimate
- Inventory level vs. prior month (months supply)
- Median price vs. prior year
- Geographic breakdown (which regions leading/lagging)
- NAR chief economist Lawrence Yun's specific commentary — quote him directly

STEP 3 — FIVE-FACTOR UPDATE
Based on today's data, update the five-factor attribution model from the data feed.
For each factor, state whether it improved, worsened, or stayed the same and why:
1. Rate lock-in factor: Did inventory of sub-5% mortgages change? Any new FHFA data?
2. SFR REIT absorption: Did INVH or AMH announce any change in acquisition pace?
3. 2nd/3rd home factor: Any new data from NAR or Census on vacation home ownership?
4. Demographics factor: Any new Census or NAR data on 25-34 homeownership rates?
5. Affordability/rent-own spread: How did the rent-own spread move this month?

STEP 4 — COILED SPRING CALIBRATION
Using the current 30-year mortgage rate from the data feed:
- At the current rate, how many homeowners remain locked in (per FHFA distribution)?
- What would need to happen in the next 6 months to reach 5.5%? 
  (inflation data needed, oil price threshold, Fed meeting dates)
- Give a probability-weighted SAAR projection for 12 months out across three scenarios

STEP 5 — HARVARD JCHS CHECK
Search for the most recent Harvard Joint Center for Housing Studies publication.
Compare their household formation forecast (specifically 25-34 cohort) to:
- Actual Census data on household formation for the same period
- Actual homeownership rate for 25-34 cohort (latest Census)
Are they still overestimating family creation rates? By how much?

STEP 6 — STOCK REACTIONS
For each of the following, find today's price change and any analyst commentary:
Tier 1: DHI, LEN, PHM, NVR, TOL, RKT, FNF, FAF, RDFN, Z
Tier 2: INVH, AMH, HD, LOW, UHAL, EXR
Short basket: EQR, AVB, MAA

Which ticker had the biggest unexpected move vs. its sensitivity tier prediction?

STEP 7 — OUTPUT
Write a full monthly housing intelligence report (target 1500-2000 words) with:
- Executive summary (5 bullet points)
- Factor-by-factor update
- Scenario update (base/bull/bear at 6.5%/5.5%/5.0% rates)
- Top 5 stock-specific observations
- Policy catalyst watch list

Save as "Housing_Monthly_[MONTH]_[YEAR].md"
```
### Step B.5: The Quarterly Structural Task
```
TASK: US Housing Market Quarterly Deep Dive — Full Report Update

STEP 1 — READ DATA FEED
Go to https://YOURUSERNAME.github.io/housing-monitor/housing_context.md
This is your quantitative foundation. Every number you cite must come from here 
or be independently sourced and cited.

STEP 2 — STRUCTURAL vs. CYCLICAL FRAMEWORK UPDATE
The original analytical question: of the ~1M unit gap between current SAAR (~3.98M) 
and the normalized 5M, how much is structural vs cyclical?

Search for and synthesize the latest research on each factor:

FACTOR 1 — RATE LOCK-IN (estimated 40-50% of gap):
- Latest FHFA National Mortgage Database publication on outstanding mortgage rate distribution
- Any new NY Fed research on the "lock-in effect" — cite specific paper if published
- How has the distribution shifted since the prior quarter?
- What is the empirically supported "unlock threshold" in basis points?
  (Literature: Fuster & Willen 2017 suggested 100-150bps; any updates?)

FACTOR 2 — SFR REIT ABSORPTION (estimated 15-20% of gap):
- Latest total single-family homes owned by institutional investors (INVH, AMH, Tricon legacy)
- Search for any NBER, Atlanta Fed, or academic research on institutional SFR impact on supply
- Has INVH or AMH changed acquisition guidance in their most recent earnings call?
- Any new legislative proposals specifically targeting institutional SFR ownership?

FACTOR 3 — 2ND/3RD HOME LOCK-IN (estimated 10-15% of gap):
- Latest American Housing Survey data if newly published (Census, biennial)
- Any NAR data on vacation home ownership rates vs. pre-COVID
- Are 2nd home owners also rate-locked to the same degree as primary residence owners?

FACTOR 4 — DEMOGRAPHICS (estimated 15% of gap):
- Latest Census homeownership rate by age cohort (25-34, 35-44, 45-54)
- Latest Harvard JCHS State of the Nation's Housing report — what are their new projections?
- Cite their specific household formation forecast and compare to actual Census data
- Is the rent-by-choice trend among 25-34s accelerating, decelerating, or stable?

FACTOR 5 — AFFORDABILITY/RENT-OWN SPREAD (estimated 10-12% of gap):
- Calculate current monthly cost: 30yr mortgage on median home price vs. median rent
- How does this compare to historical averages (2000, 2005, 2015)?
- Rent deflation: is CPI shelter finally reflecting market rent declines?
- If rent-own spread normalizes, what is the demand uplift?

STEP 3 — POLICY CATALYST INVENTORY
List ALL currently active or proposed legislative/regulatory mechanisms that could 
unlock the housing market without requiring a rate cut:
1. Capital gains exclusion expansion (Section 121) — any legislation introduced?
2. Mortgage assumability/portability — any active bills?
3. FHA loan limit changes
4. GSE conforming loan limit changes
5. Down payment assistance programs
6. Property tax portability (state-level, e.g., Prop 19 in CA)
7. Any other creative mechanisms identified in the last quarter

For each: status (proposed/committee/passed), estimated impact on SAAR if enacted, 
and political probability.

STEP 4 — TICKER UNIVERSE REFRESH
For each sensitivity tier, identify:
- Any new companies that should be added since last quarter
- Any companies that have changed tier (e.g., a company sold its housing segment)
- The 10 "most coiled" stocks — highest correlation to SAAR AND currently near 52-week low

STEP 5 — SCENARIO ANALYSIS UPDATE
Update the three-scenario model:
- BASE CASE: current rate path, no major policy change
- BULL CASE: oil drops to $60, Fed cuts 50bps by year-end, legislation introduced
- BEAR CASE: oil stays elevated, Fed on hold through 2027, no policy action

For each scenario: projected SAAR in 12 months, in 24 months; top 3 stock winners; top 3 losers.

STEP 6 — OUTPUT
Write a complete quarterly deep dive report (target 3000-4000 words).
Match the depth and structure of professional sell-side housing research reports.
Include all citations with URLs.
Save as "Housing_Quarterly_Deep_Dive_[QUARTER]_[YEAR].md"
```

***
## Part 11: Person B — The Analytical Framework (Week 1-2, concurrent)
While Person A builds the data pipelines, Person B builds the analytical logic that the Python models and Perplexity Computer tasks will execute.
### The Five-Factor Quantitative Framework
**Factor 1 — Rate Lock-In: The Threshold Model**

The empirically supported spread threshold above which homeowners strongly resist moving is 150–200 basis points (based on Fuster & Willen research and FHFA analysis). At current 30-yr rate of ~6.82%:

- Owners with rates <3% (21.9% of ~50.8M = 11.1M homes): spread = ~380bps → locked
- Owners at 3-4% (35% = 17.8M homes): spread = ~280bps → locked
- Owners at 4-5% (25% = 12.7M homes): spread = ~120bps → borderline/partially locked
- Owners at 5-6% (7.6% = 3.9M homes): spread = ~20bps → NOT locked
- Owners at 6%+ (14.3% = 7.3M homes): spread = negative → NOT locked

This means ~40M homeowners are meaningfully locked. Even a modest 50% normalization of turnover rate for locked owners (from ~4%/yr to ~2%/yr) = ~800k units/year lost from the market.

**Person B builds this into a written section that explains the math.** Person A codes it (Script 02).

**Factor 2 — REIT Absorption: The Supply Removal Model**

The key metric is not how many homes REITs own — it is the **turnover differential**:
- Owner-occupied normal turnover: ~5%/yr (before rate lock = ~2.5M homes/yr from total ~50M)
- REIT-owned turnover: currently <3%/yr (REITs prefer to hold and rent; selling is a last resort)
- If REITs own ~500k homes at 2% turnover instead of 5%: differential = 15k units/yr removed
- This is a smaller number than intuition suggests — Person B should document this finding clearly

**The more important REIT signal from the original prompt:** REITs purchasing aggressively from 2012-2022 directly *removed* those homes from the for-sale market at time of purchase. That stock is now locked in the rental pool and only returns at REIT disposal rates.

**Factor 4 — The Harvard JCHS Critique**

Person B pulls the Harvard JCHS State of the Nation's Housing report annually. The original prompt notes: *"they overindex on family creation forecasts."* The specific critique to make:

1. JCHS household formation forecast for 25-34 cohort (typically 1.2-1.4M new households/year)
2. Actual Census household formation for the same cohort (typically 10-20% below forecast)
3. JCHS homeownership assumption for new households (typically 30-35% immediately buy)
4. Actual conversion rate (closer to 15-20% based on trailing data)

This means JCHS systematically overstates the demand pull for new housing by ~15-25%, which flows through to their new construction forecasts that feel too aggressive.
### The Rent-Own Spread Chart (Person B Specifies, Person A Codes)
Person B defines the exact calculation. Person A implements it in Python:

- **Monthly cost to own** = (median existing home price × 0.20 down → 80% LTV × 30yr PMT at MORTGAGE30US) + insurance (~$150/mo) + property tax (~0.9%/yr ÷ 12)
- **Monthly cost to rent** = CPI owners' equivalent rent component, converted to dollar amount using median rent data
- Plot both series back to 2000 on one chart, with the spread highlighted
- Mark 2005-2007 peak spread (housing too cheap vs. renting — led to bubble)
- Mark 2022-2025 spread (housing too expensive vs. renting — led to lock-in)
- Current spread direction — narrowing as rents fall, but slowly

***
## Part 12: Master Run-All and Division of Labor — Week-by-Week
### Week 1
| Day | Person A | Person B |
|-----|----------|----------|
| Mon | Environment setup (Steps 1.1-1.6) | Collect CIQ credentials from S&P rep; set up Perplexity Max |
| Tue | Script 01 (FRED pull) — run and verify data | Write five-factor analytical framework definitions |
| Wed | Script 02 (FHFA + coiled spring model) | Write Harvard JCHS critique methodology; identify which JCHS report to pull |
| Thu | Script 03 (FMP universe build) | Draft Perplexity Computer task prompts (all three) |
| Fri | Scripts 04+05 (FMP prices + financials) | Test weekly task prompt in Perplexity Computer once URL is live |
### Week 2
| Day | Person A | Person B |
|-----|----------|----------|
| Mon | Script 06 (sec-api REIT extraction) | Run first full weekly Perplexity Computer task; refine prompts |
| Tue | Script 07 (CIQ pull) — troubleshoot auth | Build the rent-own spread analysis spec |
| Wed | Script 09 (correlation engine) | Run monthly deep dive task; review output quality |
| Thu | Script 10 (context generator) | Draft the Structural Map section of the report |
| Fri | GitHub push + cron setup | Run first full Perplexity Computer quarterly task |
### Week 3
| Day | Person A | Person B |
|-----|----------|----------|
| Mon | Script 11 (HTML dashboard build) | Write Steps 1-3 of report (structural map, demand cohorts, value chain) |
| Tue | Dashboard: coiled spring slider | Write Steps 4-5 (wave position, stock scoring) |
| Wed | Dashboard: ticker heat map | Finalize tier assignments from correlation matrix |
| Thu | Full end-to-end test: Mac mini → GitHub → Perplexity Computer | Short/hedge section (apartment REIT analysis) |
| Fri | Dashboard QA + cron final test | Political economy section (administration unlock mechanics) |
### Week 4
| Day | Person A | Person B |
|-----|----------|----------|
| Mon | CIQ deep pull + homebuilder ops KPIs | Integrate CIQ data into factor 2 quantitative model |
| Tue | Simulate NAR release day: run pipeline manually | Run monthly Perplexity Computer task against simulated release |
| Wed | Final cron QA | Report final draft review |
| Thu | Document all scripts for maintenance | Perplexity Computer task library finalization |
| Fri | **Joint: Full system demo run** | **Joint: First complete report + dashboard review** |

***
## Appendix: The Original Prompt's Questions → Where Each Answer Lives
| Question from Original Prompt | Data Source | Python Script | Report Section |
|-------------------------------|------------|---------------|----------------|
| "How much is attributable to rate lock-in?" | FHFA NMDB | Script 02 | Factor 1 |
| "REIT absorbing supply" | sec-api.io 10-K | Script 06 | Factor 2 |
| "2nd/3rd homes don't turnover" | Census AHS | Script 02 (hardcoded) | Factor 3 |
| "Demographics, ownership ceiling" | FRED RHORUSQ156N + Census | Script 01 + 07 | Factor 4 |
| "Rent-own spread" | FRED CPI + mortgage calc | Scripts 01+02 | Factor 5 |
| "Harvard overindexing on family creation" | JCHS annual report | Perplexity Computer Q task | Report Step 1 |
| "400+ stocks impacted" | FMP screener + sec-api | Scripts 03+04+09 | Ticker Matrix |
| "Coiled spring at XYZ rates" | FHFA + FRED | Script 02 | Dashboard Gauge |
| "Policy signal — moment we hear legislation" | sec-api 8-K + Perplexity weekly | Script 06 + Computer | Policy Feed |
| "Rents coming down, lagging indicator" | FRED CUSR0000SEHA | Script 01 | Dashboard Module |
| "Oil as inflation wildcard" | FRED DCOILWTICO | Script 01 | Dashboard Flag |
| "Administration political incentive" | Perplexity Computer | Computer quarterly | Report Section |
| "Fed stuck on oil/Iran" | FRED T10YIE + Computer | Script 01 + Computer | Dashboard + Report |
| "Inventory rising = good sign (unlike 2005-2007)" | FRED HOSINVUSM673N | Script 01 | Dashboard Module |
| "Near a trough? Coiled spring?" | All above combined | Model output | Scenario Table |

---

## References

1. [Perplexity announces "Computer," an AI agent that assigns work to ...](https://arstechnica.com/ai/2026/02/perplexity-announces-computer-an-ai-agent-that-assigns-work-to-other-ai-agents/) - Perplexity has introduced “Computer,” a new tool that allows users to assign tasks and see them carr...

2. [Perplexity Computer for Developers: API Access, Integrations, and ...](https://sparkco.ai/blog/perplexity-computer-for-developers-api-access-integrations-and-limitations) - Developer guide to Perplexity Computer: in-depth coverage of API access, authentication, endpoints, ...

3. [FHFA Releases Data Visualization Dashboard for NMDB ...](https://www.fhfa.gov/news/news-release/fhfa-releases-data-visualization-dashboard-for-nmdb-outstanding-residential-mortgage-statistics) - Today's release describes outstanding residential mortgage debt at the end of the first quarter of 2...

4. [Financial Modeling Prep Python API Docs | dltHub](https://dlthub.com/context/source/financial-modeling-prep) - Build a Financial Modeling Prep-to-database pipeline in Python using dlt with AI Workbench support f...

5. [SEC EDGAR Filings API](https://sec-api.io) - SEC API is your gateway to search the latest SEC filings and access all corporate documents from the...

6. [Content Extraction API - Introduction, Endpoint, Authentication](https://sec-api.io/docs/sec-filings-item-extraction-api) - The Extractor API extracts any text section from 10-Q, 10-K and 8-K SEC filings, and returns the ext...

7. [SEC EDGAR Filing Search API](https://sec-api.io/docs/query-api) - The Query API allows searching and filtering all 18+ million filings and exhibits published on the S...

8. [SPGMICIQ · PyPI](https://pypi.org/project/SPGMICIQ/) - S&P Capital API clients can now access these SDKs to integrate end-of-day and time-series Financial ...

