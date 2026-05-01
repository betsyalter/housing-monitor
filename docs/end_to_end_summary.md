# Housing Monitor — End-to-End Summary

*How the build delivers on `docs/og_prompt.txt`. Last updated 2026-05-01.*

---

## What the brief asked for

Read literally, the original prompt asked five things:

1. **Disentangle the structural-vs-cyclical drivers** of existing-home turnover bumping below 4M vs the 5M long-term — specifically across five factors: rate lock-in, REIT supply absorption, 2nd/3rd home stickiness, demographics/homeownership ceiling, rent-own spread.
2. **Identify the "coiled spring"** — at what mortgage rate does the lock-in break and turnover normalize.
3. **Track 400+ stocks** that have downstream exposure to that turnover.
4. **A live, dynamic dashboard** of the data — *"much much more in depth"* than a static report.
5. **Real-time policy/legislative scuttlebutt** — *"the moment we hear anything about such legislation would be the immediate signal."*

Plus an in-depth written report ("dashboard is delivered with a report to go with it").

Split across three layers, each with a different owner, built backwards from those asks.

---

## Layer 1 — Foundation (Betsy / engineering)

The dashboard is the empirical scaffolding. Without it, the report is unfounded; without the report, the dashboard is just numbers. The engineering job: every empirical claim the report wants to make is *checkable in one place*, *daily refreshed*, and *alert-driven so signal doesn't get missed.*

**Maps to brief items 2, 3, 4, 5.**

| Brief ask | What we built |
|---|---|
| Coiled-spring rate threshold (item 2) | Script 02 pulls the FHFA mortgage rate distribution and computes scenario tables — at 5.5% / 5.0% / 4.5%, what % of stuck mortgages cross "in-the-money to refi" and what fraction of inventory unlocks. Math lives in `scripts/lib/coiled_spring.py`, params in `analyst/coiled_spring_params.yaml`, regression tests in `tests/`. |
| 400+ ticker universe (item 3) | Script 03 enriches against FMP — landed at 262 actively-traded names spanning homebuilders, building products, mortgage/title/brokerage, single-family REITs, multifamily REITs, suppliers, lenders. Script 04 pulls 5yr daily prices for all of them. Script 09 runs the correlation engine — 262 tickers × 7 FRED indicators × 3 windows = ~5,500 pair-windows showing which tickers are most rate-sensitive, most EHS-sensitive, most starts-sensitive. |
| Dynamic dashboard (item 4) | Script 10 generates `housing_context.{md,json}` daily at 6 AM PT. Script 11b renders to `dashboard.html` (vendored Tabulator, no CDN). GitHub Pages auto-publish via daily cron + git push. Live at `https://betsyalter.github.io/housing-monitor/dashboard.html`. |
| Real-time legislative + policy scuttlebutt (item 5) | Three independent alert streams, all running on launchd cron on the Mac mini: <br>• **8-K filings** (06b → 11) — every hour, sec-api.io stream filtered to the 262 universe, classified by item type. <br>• **News** (14 → 14b) — every 5 min, FMP news + source-quality tiering (Bloomberg/Reuters/Politico/HousingWire = TRUSTED; Zacks/SeekingAlpha = penalized; congress.gov/whitehouse.gov/treasury.gov = TRUSTED), Fed/FHFA/HUD/legislation keywords + bill-number regex, immediate emails for high-signal + 4:15 PM ET digest for medium. <br>• **Congress bills** (15 → 15b) — daily 6:15 PM ET, polls Congress.gov for new bills + committee actions, hard-promotes anything in House Financial Services / Senate Banking / Ways & Means / Senate Finance to immediate. **This is the literal answer to *"the moment we hear anything about such legislation would be the immediate signal"* — bills now reach you the same day they're introduced.** |
| REIT supply absorption (factor 2 of item 1) | Script 06 extracts SEC 10-K Item 1 / 2 / 7 for 20 single-family REITs (INVH, AMH, etc), captures owned-home count, geographic concentration, occupancy. Maps the supply they've taken off the existing-home market. |
| Builder operational KPIs (cohort layer) | Script 07 runs Anthropic Haiku against earnings transcripts to extract quarterly orders / backlog / cancel rate / ASP / community count for 17 Tier-1+2 builders × 8 quarters. This is what the sell-side notes Wyatt curated map back to. |

Plus a watchdog (catches silent cron failures + stale data) and a daily auto-push that keeps the GitHub Pages dashboard live.

---

## Layer 2 — Comprehensive report (Wyatt)

**Maps to brief item 1** — the deep-dive prose disentangling the five factors.

The dashboard alone doesn't answer *"how much is REITs vs 2nd-homes vs demographics vs rate-lockin."* That's a research-and-writing job. The framework lives in `analyst/`:

- **Five-factor framework** (`analyst/five_factor_framework.md`) — scaffolded by Wyatt's Claude, prose pending. Each factor gets its own section that pulls directly from the dashboard data:
  - Factor 1 (rate lock-in) → coiled-spring scenarios from Script 02
  - Factor 2 (REITs) → REIT geo footprint from Script 06
  - Factor 3 (2nd/3rd homes) → FRED indicators from Script 01
  - Factor 4 (demographics) → Apollo deck slides 31–32 (median buyer age 59, was 31 in 1981)
  - Factor 5 (rent-own spread) → rent CPI vs ownership-cost data from FRED
- **Apartment REIT short basket** (`analyst/apartment_reit_short_basket.md`) — sizing for EQR, AVB, MAA, CPT, UDR, ESS as the disconfirming-trade leg. Logic: if existing-home turnover normalizes, the rent-as-substitute-for-buying thesis weakens, and the apartment REITs that benefited from the lock-in unwind.
- **Sell-side reference materials** (`docs/reports/`) — 19 PDFs across four Tier-1 builder archetypes (DHI volume / TOL luxury / NVR build-to-order / PHM mix-shift) plus the Apollo macro deck. Calibration points — what the Street is saying — that the framework cross-checks against, not a substitute for the framework.

**Status:** scaffolds landed, prose pending. This is the deliverable that's still owed.

---

## Layer 3 — Ongoing intelligence (Wyatt + Perplexity Computer)

**Maps to brief item 5 plus "make it dynamic and trackable"** — the re-evaluation cadence the brief implied when it asked for "dynamic" tracking.

Three scheduled Perplexity runs:

- **Weekly** — re-reads the live `housing_context.json`, web-searches policy signals, outputs factor scorecard + bottom line + analyst-flagged names + policy events.
- **Monthly** (22nd, NAR release day) — deeper dive against fresh FRED + NAR data.
- **Quarterly** — full structural refresh of the five-factor weights.

First weekly run shipped: `output/perplexity/weekly/2026-05-04.{md,json}`. The dashboard reads this JSON and renders the synthesis card at the top — analyst conclusions live above the raw data, not buried below.

**Why Perplexity not Claude API:** web-search and live X/Twitter / sell-side-rumor mill are native to Perplexity, not Claude. Engineering doesn't try to replicate it.

---

## How it actually works in operation

A typical day, end-to-end:

- **6:00 AM PT** — daily cron runs Script 10 → regenerates `housing_context.{md,json}` from yesterday's data → git push → GitHub Pages updates → dashboard goes live with overnight FRED prints, latest correlation rankings, latest synthesis card.
- **All day, every hour** — 8-K stream scan; if any of the 262 universe tickers files an 8-K item 1.01 / 2.01 / 4.02 / 5.02 / 8.01, email within ~1 hour of the filing.
- **All day, every 5 min market hours** — news poll. Fed / FHFA / HUD / NAR / housing-legislation / bill-number references cross the immediate threshold; everything else queues for the 4:15 PM ET digest.
- **6:15 PM ET** — Congress.gov bill poll. Anything new in House Financial Services / Senate Banking / Ways & Means / Senate Finance hard-promotes to immediate email.
- **Mondays** — Wyatt fires the weekly Perplexity task → output drops into `output/perplexity/weekly/` → next morning's daily cron pulls it into the dashboard synthesis card.
- **22nd of each month** — Perplexity monthly NAR-release-day run.
- **Quarterly** — full structural refresh.

The thesis question — *"at what mortgage rate, under what legislative scenario, does the lock-in break"* — gets re-asked weekly against fresh data. The "immediate signal" requirement is *literally* the three alert streams. The framework that interprets all of it is Wyatt's report, currently scaffolded and pending prose.

---

## What's still owed

One deliverable: **Wyatt's deep-dive report prose** (Layer 2). Scaffolds are landed, the data the prose references is in the dashboard, the sell-side calibration points are in `docs/reports/`. ETA: 1–2 weeks of Wyatt's writing time once he starts.

Until that lands, the brief isn't fully delivered — the dashboard is foundation, not deliverable.

---

## Quick links

- Live dashboard: https://betsyalter.github.io/housing-monitor/dashboard.html
- Original brief: [`docs/og_prompt.txt`](og_prompt.txt)
- Architecture / delivery calendar: [`docs/end_to_end_plan.md`](end_to_end_plan.md)
- Reference reports (Apollo deck + sell-side notes): [`docs/reports/`](reports/)
- Latest weekly synthesis: [`output/perplexity/weekly/`](../output/perplexity/weekly/) (newest by date)
- Analyst framework + scaffolds: [`analyst/`](../analyst/)
