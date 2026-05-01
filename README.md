# Housing Monitor

Real-time monitoring + analytical pipeline for the US existing-home turnover thesis.

The brief: existing-home sales SAAR is bumping below 4M annually vs. a long-term 5M. The thesis is that this is part-cyclical (rate lock-in: ~95% of mortgages are below the current 30yr) and part-structural (REIT supply absorption, demographic shifts). When does turnover normalize? At what mortgage rate does the lock-in break? Which stocks benefit, which fade? See [`docs/og_prompt.txt`](docs/og_prompt.txt) for the original analyst brief.

**Live dashboard:** https://betsyalter.github.io/housing-monitor/dashboard.html

---

## Architecture

Three layers, three owners. See [`docs/end_to_end_plan.md`](docs/end_to_end_plan.md) for the full breakdown.

| Layer | What | Owner |
|---|---|---|
| **1. Foundation** — data + dashboard + alerts | Scripts 01–15, launchd cron, GitHub Pages dashboard | Engineering (Betsy) |
| **2. Deep-dive report** — comprehensive thesis writeup | 5-section report per playbook Part 12 | Wyatt |
| **3. Ongoing intelligence** — synthesis + web search | Perplexity Computer weekly / monthly / quarterly | Wyatt |

The dashboard is raw material the report sits on top of, not a substitute for the report. The full deliverable is **not complete until the deep-dive report is written.**

---

## Scripts

All in `scripts/`. Numbered roughly in execution order; bolded ones run on cron.

| # | Purpose | Output |
|---|---|---|
| **01** | FRED housing macro pull (mortgage rates, EHS, starts, permits, etc) | `data/fred_housing.csv` |
| **02** | FHFA mortgage rate distribution + coiled-spring scenarios | `data/fhfa_distribution.csv`, `data/coiled_spring_scenarios.csv` |
| 03 | FMP universe enrichment (262 actively-traded housing-impacted tickers) | `data/fmp_tickers.csv` |
| 04 | 5yr daily prices for full universe | `data/fmp_prices/{TICKER}.csv` |
| 05 | Quarterly financials (Tier 1+2) | `data/fmp_financials/...` |
| 05b | Earnings transcripts (Tier 1+2) | `data/fmp_transcripts/...` |
| 05c | Insider trades (Tier 1+2) | `data/fmp_insider/...` |
| 06 | SEC 10-K Item 1+2+7 extraction for 20 REITs | `data/sec_reit_homes.csv` + raw text |
| **06b** | Hourly SEC 8-K stream scan | `data/sec_stream_log.csv` |
| 07 | LLM-extracted homebuilder operational KPIs (17 builders × 8 quarters) | `data/homebuilder_ops.csv` |
| **09** | Correlation engine — universe returns vs FRED indicators | `data/correlation_matrix.csv`, `data/correlation_rankings.csv` |
| **10** | Daily context generator (markdown + JSON) | `housing_context.md`, `housing_context.json` |
| **11** | SEC 8-K alert dispatcher (HIGH per-event + MEDIUM digest) | emails |
| **11b** | HTML dashboard renderer (`dashboard.html` reads `housing_context.json`) | live page |
| **14** | FMP news polling, sentiment scoring, source-quality tiering | `data/news_stream_log.csv` |
| **14b** | News alert dispatcher (immediate per-event + 4:15 PM ET digest) | emails |
| **15** | Congress.gov bill tracker (housing-related federal legislation) | `data/congress_bill_log.csv` |
| **15b** | Congress alert dispatcher | emails |
| **watchdog** | Daily health check on cron pipeline + FRED freshness + API keys | email if red |

Plus `scripts/lib/coiled_spring.py` and `scripts/lib/yaml_config.py` (cherry-picked from Wyatt's scaffold; regression-tested by `tests/`).

---

## launchd jobs (Mac mini, all-day)

| Plist | When | Chains |
|---|---|---|
| `com.housing-monitor.hourly` | Every hour, 24/7 | 06b → 11 |
| `com.housing-monitor.news` | Every 5 min (script throttles internally outside market hours) | 14 → 14b |
| `com.housing-monitor.news-digest` | 1:15 PM PT (= 4:15 PM ET) | 14b --digest |
| `com.housing-monitor.legislative` | 3:15 PM PT (= 6:15 PM ET) | 15 → 15b |
| `com.housing-monitor.daily` | 6:00 AM PT | 10 + git push + watchdog |

See [`launchd/README.md`](launchd/README.md) for install steps.

---

## Setup

Prerequisites: Mac mini, Python 3.11+, conda env named `housing`.

1. Clone the repo:
   ```bash
   git clone https://github.com/betsyalter/housing-monitor.git
   cd housing-monitor
   ```

2. Install dependencies into the `housing` conda env:
   ```bash
   conda activate housing
   pip install -r requirements.txt
   ```

3. Create `~/.env` with the required API keys (see [`.env.example`](.env.example)):
   - `FMP_API_KEY` — Financial Modeling Prep
   - `SEC_API_KEY` — sec-api.io
   - `FRED_API_KEY` — FRED (St. Louis Fed)
   - `ANTHROPIC_API_KEY` — for Script 07 LLM extraction
   - `CONGRESS_API_KEY` — Congress.gov (free signup at api.congress.gov/sign-up)
   - `ALERT_EMAIL_FROM` / `ALERT_EMAIL_TO` / `ALERT_GMAIL_APP_PASSWORD` — Gmail SMTP
   - `GITHUB_TOKEN` — for daily auto-push (needs `repo` scope)

4. Initial backfill — run scripts 01 through 07 once each. After that, the cron jobs handle everything.

5. Install the launchd plists per [`launchd/README.md`](launchd/README.md).

---

## Repo layout

```
housing-monitor/
├── README.md                   # this file
├── housing_context.md          # daily report (auto-refreshed at 6 AM PT)
├── housing_context.json        # structured isomorph for dashboard.html
├── dashboard.html              # GitHub Pages dashboard (vendored Tabulator)
├── scripts/                    # all the Python + bash entry points
│   └── lib/                    # coiled_spring math, yaml_config helpers
├── data/                       # outputs (most gitignored — see .gitignore)
├── analyst/                    # Wyatt's domain — YAML configs + framework prose
│   ├── factor_weights.yaml
│   ├── coiled_spring_params.yaml
│   ├── ticker_overrides.yaml
│   ├── news_sources.yaml
│   ├── five_factor_framework.md           # working draft
│   ├── apartment_reit_short_basket.md     # working draft
│   └── perplexity_tasks/                  # weekly / monthly / quarterly task specs
├── output/perplexity/weekly/   # Perplexity Computer outputs (auto-generated)
├── docs/
│   ├── og_prompt.txt           # original analyst brief
│   ├── end_to_end_plan.md      # 3-layer architecture + delivery calendar
│   ├── coordination/           # Betsy ↔ Wyatt coordination notes
│   └── reports/                # third-party research drops (sell-side, Apollo, etc)
├── launchd/                    # plist files for the cron jobs
├── tests/                      # pytest — regression tests for coiled_spring + yaml
└── .github/workflows/ci.yml    # CI — runs tests on every push to main
```

---

## How alerts work

You'll get emails (Gmail) for:

- **8-K filings** within ~1 hour of being published — for 262-ticker universe, items 1.01 (material agreement), 2.01 (acq/disp), 4.02 (non-reliance), 5.02 (officer changes), 8.01 (other material). Tier-1 builders + mortgage / title / brokerage names get tighter triggering.
- **High-signal news** within ~5 min — Fed/FOMC/Powell/Warsh, FHFA/HUD/Fannie/Freddie, housing legislation keywords, bill-number references, NAR data drops. Source-quality tiering boosts trusted sources (Bloomberg/Reuters/Politico/HousingWire) and penalizes Zacks/SeekingAlpha/Motley Fool style aggregators.
- **Medium-signal news daily digest** at 4:15 PM ET — batch of the day's housing-relevant articles below the immediate threshold.
- **New federal bills** within 24h — same-day if introduced before 6:15 PM ET. Hard-promote rule fires for bills in House Financial Services / Senate Banking-Housing-Urban Affairs / Ways and Means / Senate Finance committees.
- **Watchdog alerts** — only when a cron job has silently failed or data has gone stale beyond expected cadence.

---

## Coordination

Two-person collaboration: Betsy (Person A — engineering) + Wyatt (Person B — analyst). Communication via Slack and the `codex` MCP. Coordination notes live in [`docs/coordination/`](docs/coordination/).

**Read-only files** (engineering writes, analyst consumes):
- `data/*.csv` — all the structured outputs
- `housing_context.{md,json}` — daily report
- `dashboard.html` — public dashboard

**Analyst-domain files** (Wyatt writes, engineering reads):
- `analyst/*.yaml` — factor weights, ticker overrides, news sources
- `analyst/*.md` — framework prose, basket sizing, perplexity task specs
- `output/perplexity/weekly/*` — auto-generated weekly synthesis runs

---

## Status

As of 2026-05-01:

- ✅ Foundation layer: data ingestion (01–07), correlations (09), daily report (10), 8-K alerts (11), HTML dashboard (11b), news pipeline (14/14b), Congress bill tracker (15/15b), watchdog, all 5 launchd jobs
- ✅ Tests passing in CI (12 tests, coiled_spring math + YAML validation)
- ⏳ Synthesis layer: first weekly Perplexity Computer run shipped (`output/perplexity/weekly/2026-05-04.{md,json}`); cadence ramping up
- ⏳ Deep-dive report: scaffolds landed in `analyst/`, prose pending — Wyatt's primary remaining workstream

---

## Quick links

- Live dashboard: https://betsyalter.github.io/housing-monitor/dashboard.html
- Latest daily report (markdown): [`housing_context.md`](housing_context.md)
- Latest weekly synthesis: [`output/perplexity/weekly/`](output/perplexity/weekly/) (newest by date)
- Original analyst brief: [`docs/og_prompt.txt`](docs/og_prompt.txt)
- End-to-end delivery plan: [`docs/end_to_end_plan.md`](docs/end_to_end_plan.md)
- Reference reports (Apollo deck + sell-side notes): [`docs/reports/`](docs/reports/)
