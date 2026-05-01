# Comprehensive Housing Thesis Report

> _Status: 2026-05-01. Default-driven first draft by Wyatt's Claude.
> All judgment calls flagged inline as `_ASSUMPTION_`. Wyatt edits in
> place; commits via PR override defaults._

The deep-dive report that completes `docs/og_prompt.txt`. Voice
intends standard equity research clinical/declarative tone; the
analytical scaffolding (factor framework, training-manual methodology)
lives in supporting files. **Note (per codex audit 2026-05-01):** the
report does use internal labels like "Factor 1" and "Tier 4" in
reader-facing prose because the document is treated as
internal-research, not external sell-side-quality publication. If
this is later distributed externally, those references should be
translated to plain equity-research phrasing per the Output
Discipline standard.

## Sections (read in order)

| # | File | Focus |
|---|---|---|
| 1 | [`01_structural_map.md`](01_structural_map.md) | Housing supply ecosystem; mapping of 262-ticker universe to functional roles |
| 2 | [`02_demand_cohorts.md`](02_demand_cohorts.md) | Generational mobility differentials; JCHS-anchored cohort decomposition |
| 3 | [`03_value_chain.md`](03_value_chain.md) | Dollar flow through a housing transaction; per-subsector beta to volume normalization |
| 4 | [`04_wave_position.md`](04_wave_position.md) | Where in the cycle we are now; inning marker call |
| 5 | [`05_stock_scoring.md`](05_stock_scoring.md) | Tier assignments, thesis-exposure scoring methodology, named-ticker output |
| 6 | [`06_political_economy.md`](06_political_economy.md) | Administration unlock mechanics; legislative levers ranked by leverage |

## Sources of truth this report cites

- **Framework:** [`analyst/five_factor_framework.md`](../five_factor_framework.md)
- **Apartment REIT basket:** [`analyst/apartment_reit_short_basket.md`](../apartment_reit_short_basket.md)
- **Factor weights:** [`analyst/factor_weights.yaml`](../factor_weights.yaml)
- **JCHS 2025 verbatim extract:** Appendix A of the framework file
- **Live data feed:** `housing_context.json` (refreshed daily)
- **Correlation rankings:** `data/correlation_rankings.csv`
- **Methodology backbone:** Investment Research Training Manual v5.0
  (RBF Capital). Internal scaffolding; never cited in deliverable
  vocabulary, only behind-the-scenes.

## What this report deliberately does not include

- **Trade recommendations.** The output surfaces signal; the principal
  positions [Manual L40-48].
- **Forward valuation models per ticker.** Per-ticker DCF/multiple work
  is downstream of stock-scoring (Step 5); not in the report's scope.
- **Real-time positioning.** The report is a thesis snapshot;
  positioning lives in the principal's PMS, not in markdown.

## What's missing (next pass)

- Per-ticker valuation work (post-Step 5).
- Updated factor weights once Wyatt revises the placeholder defaults.
- Apartment REIT basket sizing once Wyatt confirms member roster.
- Quarterly refresh cadence (monthly NAR-day Perplexity outputs are the
  forward inputs).
