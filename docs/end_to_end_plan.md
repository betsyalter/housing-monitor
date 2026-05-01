# End-to-end plan: delivering on `docs/og_prompt.txt`

*Last updated: 2026-05-01.*

The original brief asked for three things:

1. A **dynamic, trackable dashboard** for 400+ housing-impacted tickers
2. A **very in-depth written report** ("much much more in depth")
3. **Ongoing intelligence** — policy/legislation scuttlebutt, real-time signal updates

These map to three layers, each with a different owner.

---

## Layer 1: Foundation (data + dashboard) — Engineering (Betsy)

**Status as of 2026-05-01: ~95% done.**

Built:

- Scripts 01–07: full data ingestion (FRED macro, FHFA distribution + coiled-spring scenarios, FMP universe enrichment, 5yr daily prices, quarterly financials, transcripts, insider trades, REIT 10-K Item 1+2+7 extraction, 8-K stream, LLM-extracted homebuilder operational KPIs)
- Script 09: correlation engine (262 tickers × 7 indicators × 3 windows = 5,467 pair-window observations)
- Script 10: daily context generator (markdown + JSON, fail-soft sections, freshness indicators)
- Script 11: 8-K alert dispatcher (HIGH per-event + MEDIUM digest, idempotent state)
- Script 11b: HTML dashboard at `https://betsyalter.github.io/housing-monitor/dashboard.html`
- Scripts 14 + 14b: news polling + sentiment + 4:15 PM ET digest, source-quality tiering
- 4 launchd cron jobs running on Mac mini

Remaining (~2 hours of work, ETA today):

- Observability watchdog (catches silent cron failures)
- Script 06c: per-REIT geo parser (state/MSA breakdown via Haiku extraction from existing 10-K text)
- Root `README.md`

**The dashboard is raw material the report sits on top of, not a substitute for the report.**

---

## Layer 2: Comprehensive deep-dive report — Wyatt

**Status as of 2026-05-01: NOT STARTED in prose form.**

Wyatt's Claude has landed *scaffolds* (`analyst/five_factor_framework.md`, `analyst/apartment_reit_short_basket.md`) — outline + decisions for Wyatt to fill in. Actual numbers, sizing, prose pending.

Per playbook Part 12, five sections:

1. **Structural map** — housing supply ecosystem
2. **Demand cohorts** — boomer / millennial / Gen Z mobility differentials
3. **Value chain** — where dollars flow when housing turns over
4. **Wave position** — where in the cycle we are now
5. **Stock scoring** — tier assignments + thesis exposure scores

Plus supplementary pieces:

- Five-factor framework prose (rate lock-in, REIT absorption, 2nd/3rd home turnover, demographics ceiling, rent-own spread)
- Harvard JCHS critique
- Apartment REIT short basket sizing
- Political economy section (administration unlock mechanics)

**Engineering cannot deliver this** — it's research + writing on top of the dashboard data.

**Realistic ETA: 1–2 weeks of Wyatt's writing time once he starts.**

---

## Layer 3: Ongoing intelligence — Wyatt running Perplexity Computer

**Why Perplexity, not Anthropic API:** Perplexity does live web search (X/Twitter, real estate forums, sell-side notes, congressional rumor mill, JCHS pre-prints) which Claude can't natively. Plus the Perplexity Pro subscription already exists — leverage existing tooling, no new costs.

Three scheduled tasks per playbook Part 10:

- **Weekly** (Mondays) — runs against the live `housing_context.json`, outputs policy signals + rate path update + stock alerts + risks / catalysts. Output lands as `analyst/perplexity_outputs/YYYY-WNN.md`.
- **Monthly** (22nd, NAR release day) — deeper dive against fresh FRED data.
- **Quarterly** — full structural refresh.

**Status:** Wyatt's Claude scaffolded `analyst/perplexity_tasks/weekly_housing_monitor.md`. First actual run hasn't happened yet.

---

## Tooling rule

- **Synthesis / "what's the call?" / web-search-needed → Perplexity Computer** (Wyatt's tool, runs against the live feed).
- **Structured data extraction (homebuilder KPIs, REIT geo breakdowns) → Anthropic API / Claude Haiku** (engineering tool, deterministic output).

Don't build a Claude-based synthesis script. Don't burn Anthropic credits on what Perplexity already does better.

---

## Calendar (proposed)

| Week | Engineering (Betsy) | Wyatt + Perplexity |
|------|---------------------|---------------------|
| **Week 1** (2026-05-01 →) | Watchdog, 06c, README. Hardening. | First weekly Perplexity run; finalize five-factor prose; size apartment short basket; **start deep dive report (Step 1: Structural map)** |
| **Week 2** | Standby for feature requests as report surfaces needs. | Deep dive Steps 2–3; first monthly NAR-day Perplexity run (May 22) |
| **Week 3** | Cosmetic polish; integrate report links into dashboard. | Deep dive Steps 4–5; first quarterly Perplexity run |
| **End of Week 3** | **Foundation hardened, dashboard polished.** | **Comprehensive deep-dive report delivered.** |

The full `og_prompt.txt` deliverable is **not complete until the deep-dive report is written**. The dashboard alone is foundation, not deliverable.
