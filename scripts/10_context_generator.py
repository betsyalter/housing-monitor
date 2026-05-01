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
PERPLEXITY_WEEKLY_DIR = os.path.join(REPO_ROOT, "output", "perplexity", "weekly")


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


def _fmt_num(x, decimals=0, suffix="", prefix=""):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    if isinstance(x, (int, np.integer)):
        return f"{prefix}{x:,}{suffix}"
    return f"{prefix}{x:,.{decimals}f}{suffix}"


def _fmt_delta(x, decimals=2, suffix="", prefix=""):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    sign = "+" if x >= 0 else "-"
    return f"{sign}{prefix}{abs(x):,.{decimals}f}{suffix}"


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

def section_weekly_synthesis():
    """Surface the latest weekly Perplexity Computer output (analyst layer 3
    per docs/end_to_end_plan.md). Card-style display at top of dashboard:
    bottom line, factor scorecard, key risk, underappreciated catalyst."""
    state = {"name": "weekly_synthesis"}
    if not os.path.isdir(PERPLEXITY_WEEKLY_DIR):
        state["status"] = "missing"
        return _missing_block("Weekly Synthesis (Perplexity Computer)",
                              "no output/perplexity/weekly/ directory yet",
                              "wait for Wyatt's first weekly Perplexity run"), state

    json_files = sorted(glob.glob(os.path.join(PERPLEXITY_WEEKLY_DIR, "*.json")))
    if not json_files:
        state["status"] = "empty"
        return _missing_block("Weekly Synthesis (Perplexity Computer)",
                              "no weekly JSON outputs yet",
                              "wait for Wyatt's first weekly Perplexity run"), state

    latest_json_path = json_files[-1]
    try:
        with open(latest_json_path, encoding="utf-8") as f:
            wk = json.load(f)
    except Exception as e:
        state["status"] = f"error:{type(e).__name__}"
        return _missing_block("Weekly Synthesis (Perplexity Computer)",
                              f"could not parse {os.path.basename(latest_json_path)}: {e}",
                              "verify JSON is valid"), state

    state["status"] = "ok"
    report_date = wk.get("report_date", "unknown")
    md_path = latest_json_path.replace(".json", ".md")
    md_filename = os.path.basename(md_path)

    summary = wk.get("executive_summary", {}) or {}
    factor_scorecard = wk.get("factor_scorecard", []) or []
    key_risk = wk.get("key_risk", {}) or {}
    catalyst = wk.get("underappreciated_catalyst", {}) or {}
    stock_signals = wk.get("stock_signals", []) or []
    policy_events = wk.get("policy_events", []) or []

    body = f"## Weekly Synthesis — {report_date}\n\n"
    body += f"_Perplexity Computer synthesis layer. "
    body += f"[Read full report]({os.path.relpath(md_path, REPO_ROOT).replace(os.sep, '/')})._\n\n"

    if summary.get("bottom_line"):
        body += f"**Bottom line:** {summary['bottom_line']}\n\n"

    if summary.get("whats_new"):
        body += f"**What's new:** {summary['whats_new']}\n\n"

    if factor_scorecard:
        body += "### Factor scorecard\n\n"
        body += "| Factor | Strength | Direction | Signal |\n"
        body += "|--------|----------|:---------:|--------|\n"
        for f in factor_scorecard:
            label = f.get("name", str(f.get("factor", "?"))).replace("_", " ").title()
            strength = f.get("strength", "?")
            direction = f.get("direction", "?")
            arrow = {"+": "▲", "-": "▼", "0": "—", "mixed": "↔"}.get(direction, direction)
            signal = (f.get("signal", "") or "")[:200]
            body += f"| {label} | {strength} | {arrow} | {signal} |\n"
        body += "\n"

    if stock_signals:
        body += "### Analyst-flagged names\n\n"
        for s in stock_signals[:6]:
            ticker = s.get("ticker", "?")
            move = s.get("move_1w_pct")
            move_str = f"{move:+.1f}%" if isinstance(move, (int, float)) else "—"
            cause = (s.get("cause", "") or "")[:200]
            read = (s.get("thesis_read", "") or "")[:280]
            body += f"- **{ticker}** ({move_str} 1w) — *{cause}*\n"
            body += f"  - Read: {read}\n"
        body += "\n"

    if policy_events:
        body += "### Material policy events this week\n\n"
        for p in policy_events[:6]:
            event = (p.get("event", "") or "")[:160]
            date = p.get("date", "")
            direction = p.get("direction", "?")
            arrow = {"+": "▲", "-": "▼", "0": "—", "mixed": "↔"}.get(direction, direction)
            url = p.get("source", "") or ""
            body += f"- **{date}** {arrow} {event}"
            if url:
                body += f" — [source]({url})"
            body += "\n"
        body += "\n"

    if key_risk.get("summary"):
        body += f"### Key risk\n\n{key_risk['summary']}\n\n"

    if catalyst.get("summary"):
        body += f"### Underappreciated catalyst\n\n{catalyst['summary']}\n\n"

    state.update({
        "report_date": report_date,
        "report_path_md": os.path.relpath(md_path, REPO_ROOT).replace(os.sep, "/"),
        "executive_summary": summary,
        "factor_scorecard": factor_scorecard,
        "stock_signals": stock_signals,
        "policy_events": policy_events,
        "key_risk": key_risk,
        "underappreciated_catalyst": catalyst,
    })
    return body, state


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
    # Tuple: col, label, decimals, prefix, suffix, scale
    for col, label, decimals, prefix, suffix, scale in [
        ("mortgage_rate_30yr",       "30yr Mortgage Rate",         2, "",  "%",       1),
        ("mortgage_rate_15yr",       "15yr Mortgage Rate",         2, "",  "%",       1),
        ("existing_home_sales_saar", "Existing Home Sales (SAAR)", 0, "",  " k units", 0.001),
        ("existing_home_inventory",  "Active Listing Inventory",   0, "",  "",        1),
        ("new_home_sales",           "New Home Sales",             0, "",  " k units", 1),
        ("median_home_price",        "Median Home Price",          0, "$", "",        1),
        ("housing_starts_total",     "Housing Starts",             0, "",  " k units", 1),
        ("building_permits",         "Building Permits",           0, "",  " k units", 1),
        ("homeownership_rate",       "Homeownership Rate",         1, "",  "%",       1),
        ("case_shiller_national",    "Case-Shiller National",      1, "",  "",        1),
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

        # Cadence-aware delta: find the prior UNIQUE observation. Works
        # regardless of whether series is weekly, monthly, or quarterly —
        # avoids the "Δ vs 4w ago" trap where quarterly data shows the same
        # value (delta=0 or noise) because no new print happened in that window.
        unique_obs = sub.drop_duplicates(subset=[col]).sort_values('date')
        prior = unique_obs[unique_obs['date'] < latest['date']]
        delta = None
        prior_date_str = ""
        cadence_days = None
        if not prior.empty:
            prior_row = prior.iloc[-1]
            delta = (latest[col] - prior_row[col]) * scale
            prior_date_str = prior_row['date'].strftime("%Y-%m-%d")
            cadence_days = (latest['date'] - prior_row['date']).days
        delta_str = _fmt_delta(delta, decimals, suffix, prefix)

        # Show prior date in the cell when cadence is materially different
        # from "weekly-ish" — helps the reader read the delta correctly.
        cadence_label = ""
        if cadence_days is not None:
            if cadence_days >= 60:
                cadence_label = f" (vs {prior_date_str})"
            elif cadence_days >= 14:
                cadence_label = f" (vs {prior_date_str})"

        rows.append(
            f"| {label} | {_fmt_num(latest_val, decimals, suffix, prefix)} | "
            f"{delta_str}{cadence_label} | {latest_date} | {stale}d |"
        )
        json_rows.append({
            "metric": col, "label": label, "value": float(latest_val),
            "delta_vs_prior": float(delta) if delta is not None else None,
            "prior_date": prior_date_str,
            "cadence_days": cadence_days,
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


def section_correlations():
    """Read correlation_rankings.csv (output of Script 09); surface most rate-sensitive
    names in markdown, embed full rankings into JSON for the dashboard to consume."""
    df, status = _safe_read_csv(f"{DATA_DIR}/correlation_rankings.csv")
    state = {"name": "correlations", "status": status}
    if df is None:
        return _missing_block("Rate Sensitivity Rankings",
                              "correlation rankings not yet generated",
                              "run scripts/09_correlation_engine.py"), state

    body = "## Rate Sensitivity Rankings (5y trailing, monthly)\n\n"
    body += ("_Pearson r between monthly log-returns and monthly bps change in 30yr "
             "mortgage rate. Negative = stock falls when rates rise. Per Script 09._\n\n")

    rate_df = df[df["indicator"] == "mortgage_rate_30yr"].copy()
    if rate_df.empty:
        body += "_No 30yr-rate rankings available — possibly all tickers below min-obs threshold._\n"
        state["rankings_by_indicator"] = {}
        return body, state

    body += "**Most rate-sensitive longs (top 10 negative r):**\n\n"
    body += "| Rank | Ticker | Subsector | r | n |\n|-----:|--------|-----------|----:|---:|\n"
    bot = rate_df[rate_df["rank_side"] == "bottom"].sort_values("rank").head(10)
    for _, r in bot.iterrows():
        body += (f"| {int(r['rank'])} | {r['ticker']} | {r.get('subsector','')} | "
                 f"{r['pearson_r']:+.3f} | {int(r['n_obs'])} |\n")

    body += "\n**Rate-defensive (top 10 positive r):**\n\n"
    body += "| Rank | Ticker | Subsector | r | n |\n|-----:|--------|-----------|----:|---:|\n"
    top = rate_df[rate_df["rank_side"] == "top"].sort_values("rank").head(10)
    for _, r in top.iterrows():
        body += (f"| {int(r['rank'])} | {r['ticker']} | {r.get('subsector','')} | "
                 f"{r['pearson_r']:+.3f} | {int(r['n_obs'])} |\n")

    # Embed full rankings (all indicators, all ranks) into JSON for the dashboard
    rankings_by_indicator = {}
    for ind in df["indicator"].unique():
        rankings_by_indicator[ind] = df[df["indicator"] == ind].to_dict(orient="records")
    state["rankings_by_indicator"] = rankings_by_indicator
    state["indicators_with_rankings"] = sorted(df["indicator"].unique().tolist())

    return body, state


def section_news():
    """Top 5 high-signal news articles from last 24h. Compact summary."""
    df, status = _safe_read_csv(f"{DATA_DIR}/news_stream_log.csv")
    state = {"name": "news", "status": status}
    if df is None:
        return _missing_block("Recent High-Signal News (last 24h)",
                              "news stream log not yet generated",
                              "run scripts/14_news_poll.py (or wait for the 5-min cron)"), state

    df["detected_at"] = pd.to_datetime(df["detected_at"], errors="coerce", utc=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
    recent = df[df["detected_at"] >= cutoff]
    # Drop log-only and excluded; keep immediate + digest, dedupe on dedupe_key
    relevant = recent[recent["alert_priority"].isin(["immediate", "digest"])]
    relevant = relevant.drop_duplicates(subset=["dedupe_key"]).sort_values("score", ascending=False)

    body = "## Recent High-Signal News (last 24h)\n\n"

    n_imm = int((recent["alert_priority"] == "immediate").sum())
    n_dig = int((recent["alert_priority"] == "digest").sum())
    body += f"_{n_imm} immediate, {n_dig} digest-priority, "
    body += f"{int((recent['alert_priority'] == 'log').sum())} log-only since {cutoff.strftime('%Y-%m-%d %H:%M UTC')}._\n\n"

    if relevant.empty:
        body += "_No high-signal news in the last 24 hours._\n"
        state["count_immediate_24h"] = n_imm
        state["count_digest_24h"] = n_dig
        state["top_articles"] = []
        return body, state

    # Cap at 3 macro/policy + 2 ticker-specific per codex
    macro = relevant[relevant["stream"] == "topic"].head(3)
    ticker_news = relevant[relevant["stream"] == "ticker"].head(2)
    top = pd.concat([macro, ticker_news]).head(5)

    json_rows = []
    for _, r in top.iterrows():
        title = (r.get("title", "") or "")[:120]
        publisher = r.get("publisher", "") or "?"
        ticker = r.get("ticker", "") or "(macro)"
        score = int(r.get("score", 0))
        url = r.get("url", "") or ""
        priority = r.get("alert_priority", "")
        keywords = ((r.get("keyword_hits_high", "") or "").replace("|", ", ")
                   or (r.get("keyword_hits_medium", "") or "").replace("|", ", ")
                   or "—")
        body += f"- **[{score}] {ticker}** — [{title}]({url})\n"
        body += f"    {publisher} &middot; *{priority}* &middot; keywords: {keywords}\n"
        json_rows.append({
            "title": title, "ticker": ticker, "publisher": publisher,
            "url": url, "score": score, "priority": priority,
            "keywords": keywords, "published_at": r.get("published_at", ""),
        })

    state["count_immediate_24h"] = n_imm
    state["count_digest_24h"] = n_dig
    state["top_articles"] = json_rows
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


FOOTER = """## Five-Factor Framework

The full analyst write-up — rate lock-in, REIT absorption, second-home turnover, demographics ceiling, rent-own spread — lives in [`analyst/five_factor_framework.md`](analyst/five_factor_framework.md). The factor weights consumed by Script 09 / future scoring layers are in [`analyst/factor_weights.yaml`](analyst/factor_weights.yaml). Both are working drafts as of 2026-05-01; canonical weights pending.

## Apartment REIT Short Basket (Tier 4 thesis)
The short-on-unlock basket write-up lives in [`analyst/apartment_reit_short_basket.md`](analyst/apartment_reit_short_basket.md). Sizing + final basket members pending.

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
- **Anthropic Claude Haiku** — extracts homebuilder operational KPIs from 8-K Item 2.02 press releases
"""


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    md_parts = [f"# US Housing Monitor — Daily Context\n_Last updated: {generated_at}_\n"]
    states = []

    # Weekly synthesis at the top — sets the analytical frame before raw data
    for fn in [section_weekly_synthesis,
               section_macro, section_coiled_spring, section_homebuilders,
               section_reits, section_price_action, section_correlations,
               section_news, section_recent_8ks, section_insider]:
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
