"""Generate the daily housing-monitor context report.

Outputs two files at repo root:
- housing_context.md  — human-readable markdown (served by GitHub Pages)
- housing_context.json — structured isomorph for downstream tooling

Each dynamic section reads its upstream CSV, marks freshness, and fails soft.
Critical distinction: "upstream script hasn't run" vs "no recent activity"
shows up explicitly in the section status so stale data isn't masked.
"""

import sys, os, glob, json
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(REPO_ROOT, "housing_context.md")
OUT_JSON = os.path.join(REPO_ROOT, "housing_context.json")
PRICES_DIR = os.path.join(DATA_DIR, "fmp_prices")
INSIDER_DIR = os.path.join(DATA_DIR, "fmp_insider")


# ── helpers ────────────────────────────────────────────────────────────────

def _safe_read_csv(path, **kw):
    if not os.path.exists(path):
        return None, "missing"
    try:
        df = pd.read_csv(path, **kw)
        if df.empty:
            return None, "empty"
        return df, "ok"
    except Exception as e:
        return None, f"error:{type(e).__name__}"


def _fmt_num(x, decimals=0, suffix=""):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    if isinstance(x, (int, np.integer)):
        return f"{x:,}{suffix}"
    return f"{x:,.{decimals}f}{suffix}"


def _fmt_delta(x, decimals=2, suffix=""):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.{decimals}f}{suffix}"


def _days_stale(date_or_iso):
    if pd.isna(date_or_iso):
        return None
    ts = pd.to_datetime(date_or_iso, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    now = pd.Timestamp.now(tz="UTC")
    return int((now - ts).days)


def _missing_block(title, missing_what, hint):
    return (
        f"## {title}\n\n"
        f"_⚠ {missing_what}_  \n"
        f"_Hint: {hint}_\n"
    )


# ── sections ───────────────────────────────────────────────────────────────

def section_macro():
    df, status = _safe_read_csv(f"{DATA_DIR}/fred_housing.csv")
    state = {"name": "macro", "status": status}
    if df is None:
        return _missing_block("Macro Snapshot",
                              "FRED data unavailable",
                              "run scripts/01_fred_pull.py"), state

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    rows = []
    json_rows = []
    latest_observed = None
    for col, label, decimals, suffix, scale in [
        ("mortgage_rate_30yr", "30yr Mortgage Rate", 2, "%", 1),
        ("mortgage_rate_15yr", "15yr Mortgage Rate", 2, "%", 1),
        ("existing_home_sales_saar", "Existing Home Sales (SAAR)", 0, "k units", 1),
        ("existing_home_inventory", "Active Listing Inventory", 0, "", 1),
        ("new_home_sales", "New Home Sales", 0, "k units", 1),
        ("median_home_price", "Median Home Price", 0, " USD", 1),
        ("housing_starts_total", "Housing Starts", 0, "k units", 1),
        ("building_permits", "Building Permits", 0, "k units", 1),
        ("homeownership_rate", "Homeownership Rate", 1, "%", 1),
        ("case_shiller_national", "Case-Shiller National", 1, "", 1),
    ]:
        if col not in df.columns:
            continue
        sub = df[['date', col]].dropna()
        if sub.empty:
            continue
        latest = sub.iloc[-1]
        latest_val = latest[col] * scale
        latest_date = latest['date'].strftime("%Y-%m-%d")
        stale = _days_stale(latest['date'])
        latest_observed = max(latest_observed, latest['date']) if latest_observed else latest['date']

        four_wk_ago = latest['date'] - timedelta(days=28)
        prior = sub[sub['date'] <= four_wk_ago]
        delta = None
        if not prior.empty:
            delta = (latest[col] - prior.iloc[-1][col]) * scale
        delta_str = _fmt_delta(delta, decimals, suffix.strip().replace("k units", "k").replace(" USD", ""))

        rows.append(
            f"| {label} | {_fmt_num(latest_val, decimals, suffix)} | {delta_str} | {latest_date} | {stale}d |"
        )
        json_rows.append({
            "metric": col, "label": label, "value": float(latest_val),
            "delta_4w": float(delta) if delta is not None else None,
            "as_of": latest_date, "days_stale": stale,
        })

    state["latest_observed"] = latest_observed.strftime("%Y-%m-%d") if latest_observed else None
    state["metrics"] = json_rows

    body = "## Macro Snapshot\n\n"
    body += "| Metric | Latest | Δ vs ~4w ago | As of | Stale |\n"
    body += "|--------|-------:|-------------:|-------|------:|\n"
    body += "\n".join(rows) + "\n"
    return body, state


def section_coiled_spring():
    fhfa, fhfa_status = _safe_read_csv(f"{DATA_DIR}/fhfa_distribution.csv")
    scenarios, scen_status = _safe_read_csv(f"{DATA_DIR}/coiled_spring_scenarios.csv")
    fred, fred_status = _safe_read_csv(f"{DATA_DIR}/fred_housing.csv")
    state = {"name": "coiled_spring",
             "status": "ok" if all(s == "ok" for s in [fhfa_status, scen_status, fred_status]) else "missing_inputs",
             "inputs": {"fhfa": fhfa_status, "scenarios": scen_status, "fred": fred_status}}

    if fhfa is None or scenarios is None or fred is None:
        return _missing_block("Coiled Spring Status",
                              "lock-in distribution or scenarios unavailable",
                              "run scripts/02_fhfa.py"), state

    fred['date'] = pd.to_datetime(fred['date'])
    rate_series = fred[['date', 'mortgage_rate_30yr']].dropna().sort_values('date')
    if rate_series.empty:
        return _missing_block("Coiled Spring Status",
                              "30yr rate unavailable in FRED data",
                              "verify scripts/01_fred_pull.py output"), state
    current_rate = rate_series.iloc[-1]['mortgage_rate_30yr']

    locked_below_pct = float(fhfa[fhfa['approx_midpoint_rate'] < current_rate]['pct_of_outstanding'].sum())
    locked_below_m = float(fhfa[fhfa['approx_midpoint_rate'] < current_rate]['est_homes_millions'].sum())

    state.update({
        "current_30yr_rate": float(current_rate),
        "pct_locked_below_current": locked_below_pct,
        "locked_below_millions": locked_below_m,
        "scenarios": scenarios.to_dict(orient="records"),
    })

    body = "## Coiled Spring Status\n\n"
    body += f"**Current 30yr rate:** {current_rate:.2f}%  \n"
    body += f"**% of mortgages locked below current rate:** {locked_below_pct*100:.1f}%  \n"
    body += f"**Total locked-low homeowners:** ~{locked_below_m:.1f}M\n\n"
    body += "**Unlock scenarios:**\n\n"
    body += "| Scenario Rate | Locked (M) | Newly Unlocked (M) | Est. SAAR Uplift (k units) |\n"
    body += "|--------------:|-----------:|-------------------:|---------------------------:|\n"
    for _, row in scenarios.iterrows():
        body += (f"| {row['scenario_rate']:.2f}% | {row['locked_millions']:.1f} | "
                 f"{row['unlocked_vs_today_millions']:.1f} | {row['estimated_saar_uplift_k']:,.0f} |\n")
    return body, state


def section_homebuilders():
    df, status = _safe_read_csv(f"{DATA_DIR}/homebuilder_ops.csv")
    state = {"name": "homebuilders", "status": status}
    if df is None:
        return _missing_block("Homebuilder Pulse",
                              "homebuilder operational KPIs not yet collected",
                              "run scripts/07_homebuilder_ops.py"), state

    df['period_end_date'] = pd.to_datetime(df['period_end_date'], errors='coerce')

    wide = df.pivot_table(
        index=['ticker', 'period_end_date', 'fiscal_period'],
        columns='metric_name', values='metric_value', aggfunc='first',
    ).reset_index()

    rows = []
    json_rows = []
    for ticker in sorted(wide['ticker'].unique()):
        sub = wide[wide['ticker'] == ticker].sort_values('period_end_date')
        if sub.empty:
            continue
        latest = sub.iloc[-1]
        prior = sub.iloc[-2] if len(sub) >= 2 else None

        def chg(col):
            if prior is None:
                return ""
            lv, pv = latest.get(col), prior.get(col)
            if pd.isna(lv) or pd.isna(pv) or pv == 0:
                return ""
            return f"{(lv-pv)/pv*100:+.0f}%"

        rows.append(
            f"| {ticker} | {latest.get('fiscal_period','')} | "
            f"{_fmt_num(latest.get('net_orders_units'))} | {chg('net_orders_units')} | "
            f"{_fmt_num(latest.get('backlog_units'))} | {chg('backlog_units')} | "
            f"{_fmt_num(latest.get('cancellation_rate_pct'),1,'%')} | "
            f"{_fmt_num(latest.get('closings_units'))} | "
            f"${_fmt_num(latest.get('asp_dollars'))} | "
            f"{_fmt_num(latest.get('community_count'))} |"
        )
        json_rows.append({
            "ticker": ticker,
            "fiscal_period": latest.get('fiscal_period'),
            "period_end_date": latest['period_end_date'].strftime("%Y-%m-%d") if pd.notna(latest['period_end_date']) else None,
            "metrics": {k: (None if pd.isna(latest.get(k)) else float(latest.get(k)))
                        for k in ["net_orders_units","cancellation_rate_pct","backlog_units",
                                  "community_count","closings_units","asp_dollars","gross_margin_pct"]},
            "qoq_pct": {k: chg(k) for k in ["net_orders_units","backlog_units","closings_units","asp_dollars"]},
        })

    state["builders"] = json_rows

    body = "## Homebuilder Pulse\n\n"
    body += "Latest reported quarter per builder. ΔQ = quarter-over-quarter change.\n\n"
    body += "| Ticker | Period | Orders | ΔQ | Backlog | ΔQ | Cancel% | Closings | ASP | Comms |\n"
    body += "|--------|--------|-------:|---:|--------:|---:|--------:|---------:|----:|------:|\n"
    body += "\n".join(rows) + "\n"
    return body, state


def section_reits():
    df, status = _safe_read_csv(f"{DATA_DIR}/sec_reit_homes.csv")
    state = {"name": "reits", "status": status}
    if df is None:
        return _missing_block("REIT Supply Snapshot",
                              "REIT property data unavailable",
                              "run scripts/06_sec_reit_properties.py"), state

    rows = []
    json_rows = []
    for _, r in df.sort_values('ticker').iterrows():
        rows.append(
            f"| {r['ticker']} | {r.get('filing_date','')} | "
            f"{_fmt_num(r.get('home_count'))} | "
            f"${_fmt_num(r.get('avg_monthly_rent'),0)} | "
            f"{_fmt_num(r.get('occupancy_pct'),1,'%')} |"
        )
        json_rows.append({k: (None if pd.isna(r.get(k)) else r.get(k))
                          for k in ["ticker","filing_date","home_count","avg_monthly_rent","occupancy_pct"]})

    state["reits"] = json_rows

    body = "## REIT Supply Snapshot\n\n"
    body += "_⚠ home_count is best-effort regex parsing of 10-K Item 2/7. Verify before relying on for material decisions. Geographic breakdown is not yet parsed (Script 06c TODO)._\n\n"
    body += "| Ticker | Filing Date | Home Count | Avg Rent | Occupancy |\n"
    body += "|--------|-------------|-----------:|---------:|----------:|\n"
    body += "\n".join(rows) + "\n"
    return body, state


def section_price_action():
    universe, u_status = _safe_read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    state = {"name": "price_action", "status": u_status}
    if universe is None or not os.path.isdir(PRICES_DIR):
        return _missing_block("Price Action",
                              "ticker universe or price files unavailable",
                              "run scripts/03_fmp_universe.py and scripts/04_fmp_prices.py"), state

    rows = []
    for path in glob.glob(os.path.join(PRICES_DIR, "*.csv")):
        ticker = os.path.basename(path).replace(".csv", "")
        try:
            p = pd.read_csv(path)
            if p.empty or 'price' not in p.columns:
                continue
            p['date'] = pd.to_datetime(p['date'])
            p = p.sort_values('date')
            if len(p) < 6:
                continue
            latest = p['price'].iloc[-1]
            week_ago = p['price'].iloc[-6] if len(p) >= 6 else p['price'].iloc[0]
            month_ago = p['price'].iloc[-22] if len(p) >= 22 else p['price'].iloc[0]
            rows.append({
                "ticker": ticker,
                "price": float(latest),
                "ret_1w": (latest / week_ago - 1) * 100 if week_ago else np.nan,
                "ret_1m": (latest / month_ago - 1) * 100 if month_ago else np.nan,
            })
        except Exception:
            continue

    if not rows:
        return _missing_block("Price Action",
                              "no price files have at least 6 rows yet",
                              "verify scripts/04_fmp_prices.py completed"), state

    pdf = pd.DataFrame(rows).merge(
        universe[['ticker', 'tier', 'subsector', 'directional']], on='ticker', how='left'
    )

    body = "## Price Action — Universe\n\n"

    body += "**Top 5 (1-week return):**\n\n"
    top = pdf.nlargest(5, 'ret_1w')
    body += "| Ticker | Subsector | Price | 1w | 1m |\n|--------|-----------|------:|----:|----:|\n"
    for _, r in top.iterrows():
        body += f"| {r['ticker']} | {r.get('subsector','')} | ${r['price']:.2f} | {_fmt_delta(r['ret_1w'],1,'%')} | {_fmt_delta(r['ret_1m'],1,'%')} |\n"

    body += "\n**Bottom 5 (1-week return):**\n\n"
    bot = pdf.nsmallest(5, 'ret_1w')
    body += "| Ticker | Subsector | Price | 1w | 1m |\n|--------|-----------|------:|----:|----:|\n"
    for _, r in bot.iterrows():
        body += f"| {r['ticker']} | {r.get('subsector','')} | ${r['price']:.2f} | {_fmt_delta(r['ret_1w'],1,'%')} | {_fmt_delta(r['ret_1m'],1,'%')} |\n"

    # Subsector basket breakout — answers "how is the market trading the unlock thesis today?"
    body += "\n**Thesis basket performance (median return):**\n\n"
    body += "| Basket | n | Median 1w | Median 1m |\n|--------|--:|----------:|----------:|\n"
    baskets = [
        ("Homebuilders (T1)", pdf[pdf['subsector'] == 'Homebuilders']),
        ("SFR REITs (Short on unlock)", pdf[pdf['subsector'] == 'SFR REITs']),
        ("Apartment REITs (Short on unlock)", pdf[pdf['subsector'] == 'Apartment REITs']),
        ("Mortgage Originators (T1)", pdf[pdf['subsector'] == 'Mortgage Originators']),
        ("Title Insurance (T1)", pdf[pdf['subsector'] == 'Title Insurance']),
        ("RE Brokerages (T1)", pdf[pdf['subsector'] == 'RE Brokerages']),
        ("Building Products (T2)", pdf[pdf['subsector'] == 'Building Products']),
        ("Long basket (all tiers)", pdf[pdf['directional'] == 'Long']),
        ("Short-on-unlock basket", pdf[pdf['directional'] == 'Short on unlock']),
    ]
    json_baskets = []
    for label, grp in baskets:
        if grp.empty:
            continue
        m1w = grp['ret_1w'].median()
        m1m = grp['ret_1m'].median()
        body += f"| {label} | {len(grp)} | {_fmt_delta(m1w,2,'%')} | {_fmt_delta(m1m,2,'%')} |\n"
        json_baskets.append({"basket": label, "n": int(len(grp)),
                             "median_1w_pct": float(m1w) if not pd.isna(m1w) else None,
                             "median_1m_pct": float(m1m) if not pd.isna(m1m) else None})

    body += "\n**Tier basket performance:**\n\n"
    body += "| Tier | n | Median 1w | Median 1m |\n|------|--:|----------:|----------:|\n"
    for tier, grp in pdf.groupby('tier'):
        body += f"| {tier} | {len(grp)} | {_fmt_delta(grp['ret_1w'].median(),2,'%')} | {_fmt_delta(grp['ret_1m'].median(),2,'%')} |\n"

    state["top_5_1w"] = top.to_dict(orient="records")
    state["bottom_5_1w"] = bot.to_dict(orient="records")
    state["subsector_baskets"] = json_baskets
    state["n_universe_priced"] = len(pdf)

    return body, state


def section_recent_8ks():
    df, status = _safe_read_csv(f"{DATA_DIR}/sec_stream_log.csv")
    state = {"name": "recent_8ks", "status": status}
    if df is None:
        return _missing_block("Recent Material 8-K Filings",
                              "8-K stream log not yet generated",
                              "run scripts/06b_sec_8k_scan.py (preferably on a launchd timer)"), state

    df['filed_at'] = pd.to_datetime(df['filed_at'], errors='coerce', utc=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
    recent = df[df['filed_at'] >= cutoff].sort_values('filed_at', ascending=False)

    body = "## Recent Material 8-K Filings (last 7 days)\n\n"
    if recent.empty:
        body += f"_No material 8-K activity from the universe since {cutoff.strftime('%Y-%m-%d')}._\n"
        state["filings"] = []
        state["count_7d"] = 0
        return body, state

    json_rows = []
    for _, r in recent.head(20).iterrows():
        date = r['filed_at'].strftime("%Y-%m-%d")
        ticker = r.get('ticker', '?')
        items = r.get('item_codes', '')
        title = (r.get('title', '') or '')[:120]
        url = r.get('filing_url', '') or ''
        body += f"- **{date}** [{ticker}] items `{items}` — [{title}]({url})\n"
        json_rows.append({"date": date, "ticker": ticker, "items": items, "title": title, "url": url})

    state["filings"] = json_rows
    state["count_7d"] = int(len(recent))
    return body, state


def section_insider():
    universe, u_status = _safe_read_csv(f"{DATA_DIR}/fmp_tickers.csv")
    state = {"name": "insider", "status": u_status}
    if universe is None or not os.path.isdir(INSIDER_DIR):
        return _missing_block("Insider Activity",
                              "insider trade files unavailable",
                              "run scripts/05c_fmp_insider.py"), state

    tier1 = set(universe[universe['tier'] == 1]['ticker'].dropna().astype(str))
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)

    rows = []
    for ticker in tier1:
        path = os.path.join(INSIDER_DIR, f"{ticker}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
            df['filingDate'] = pd.to_datetime(df.get('filingDate'), errors='coerce', utc=True)
            recent = df[df['filingDate'] >= cutoff]
            for _, r in recent.iterrows():
                rows.append({
                    "ticker": ticker,
                    "date": r['filingDate'].strftime("%Y-%m-%d") if pd.notna(r['filingDate']) else "?",
                    "name": r.get('reportingName', ''),
                    "type": r.get('typeOfOwner', ''),
                    "txn": r.get('acquisitionOrDisposition', ''),
                    "shares": float(r.get('securitiesTransacted', 0) or 0),
                    "price": float(r.get('price', 0) or 0),
                })
        except Exception:
            continue

    body = "## Insider Activity — Tier 1 (last 30 days)\n\n"
    if not rows:
        body += "_No Tier 1 insider activity in the last 30 days._\n"
        state["transactions"] = []
        return body, state

    df = pd.DataFrame(rows)
    df['value'] = df['shares'].abs() * df['price'].abs()
    df = df.nlargest(15, 'value')

    body += "Top 15 by transaction value:\n\n"
    body += "| Date | Ticker | Insider | Role | A/D | Shares | Price |\n"
    body += "|------|--------|---------|------|-----|-------:|------:|\n"
    for _, r in df.iterrows():
        body += (f"| {r['date']} | {r['ticker']} | {r['name']} | {r['type']} | "
                 f"{r['txn']} | {_fmt_num(r['shares'])} | "
                 f"${_fmt_num(r['price'],2)} |\n")

    state["transactions"] = df.to_dict(orient="records")
    return body, state


FOOTER = """## Structural vs Cyclical Framework

**Cyclical** (rate-driven, reversible): rate lock-in (most mortgaged owners are below current 30yr); affordability (ownership-vs-rent spread at historic highs); Fed constrained by oil/inflation outlook.

**Structural** (demographic/supply, slower to reverse): SFR REITs absorbed existing-home supply and are not sellers; homeownership ceiling (younger cohorts shifting to renting); 2nd/3rd-home owners turn over less frequently than primary.

## Unlock Trigger Checklist
- [ ] 30yr drops below 5.5% (partial unlock, ~13M homes incremental)
- [ ] 30yr drops below 5.0% (significant unlock, ~21M homes)
- [ ] Legislation: capital-gains exclusion expansion, assumable mortgage reform
- [ ] Oil falls sustained below $70/bbl → Fed rate-cut path opens

## Data Sources
- **FRED** — mortgage rates, sales, inventory, starts, permits
- **FMP** — prices, financials, transcripts, insider trades for 262-ticker universe
- **sec-api.io** — 10-K Item 1+2+7 for REITs, 8-K stream
- **FHFA** — mortgage rate distribution
- **Anthropic Claude Haiku** — extracts homebuilder operational KPIs from earnings press releases
"""


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    md_parts = [f"# US Housing Monitor — Daily Context\n_Last updated: {generated_at}_\n"]
    states = []

    for fn in [section_macro, section_coiled_spring, section_homebuilders,
               section_reits, section_price_action, section_recent_8ks, section_insider]:
        try:
            md, state = fn()
            md_parts.append(md)
            states.append(state)
        except Exception as e:
            md_parts.append(f"## {fn.__name__}\n\n_⚠ exception: {type(e).__name__}: {e}_\n")
            states.append({"name": fn.__name__, "status": f"exception:{type(e).__name__}", "error": str(e)})

    md_parts.append(FOOTER)

    # --- markdown ---
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_parts))

    # --- json (isomorphic) ---
    payload = {
        "generated_at": generated_at,
        "section_status": {s["name"]: s.get("status") for s in states},
        "sections": {s["name"]: s for s in states},
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"Wrote {OUT_MD} ({os.path.getsize(OUT_MD):,} bytes)")
    print(f"Wrote {OUT_JSON} ({os.path.getsize(OUT_JSON):,} bytes)")
    print("\nSection status:")
    for s in states:
        print(f"  {s['name']:20s} {s.get('status', 'unknown')}")


if __name__ == "__main__":
    main()
