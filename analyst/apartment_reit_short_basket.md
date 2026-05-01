# Apartment REIT Short Basket — Tier 4 Thesis

> **Status:** sample / scaffolding by Wyatt's Claude (2026-05-01).
> Demonstrates **Option A** of the format choice (markdown report).
> Wyatt fills in numbers, sizes the basket, picks the trade structure.
> See §0 for the format-options discussion.

---

## 0. Format options for this analysis (decide before filling in)

claude-a asked: markdown report, separate YAML, or embedded in `factor_weights.yaml` notes? Three options in priority order:

| Option | Where it lives | Pros | Cons |
|---|---|---|---|
| **A — Markdown report** (this file) | `analyst/apartment_reit_short_basket.md` | Best for narrative, citations, sizing rationale, charts. Reviewable as a PR. | Not machine-readable — Script 10 / 11b can't pull the basket members from it. |
| **B — Structured YAML** | `analyst/short_baskets.yaml` | Script 10 / 11b can ingest directly. Single source of truth for which tickers are in which basket and at what weight. | Constrained format; no narrative space. |
| **C — Embedded in `factor_weights.yaml`** | Existing analyst YAML | One file fewer. | Mixes orthogonal concerns (factor weights are aggregate; baskets are specific). Bloats the file. |

**Recommendation: A + B together.** A is the analyst write-up (this file). B is a small structured artifact downstream code can consume:

```yaml
# analyst/short_baskets.yaml — sample structure
last_updated: "2026-05-01"
baskets:
  apartment_reit_short:
    thesis: "Apartment REITs lose pricing power as rate-lockin unwinds and
             owner-occupied demand returns; cap-rate multiple compresses."
    members:
      - ticker: EQR
        weight: 0.20
        rationale: "Coastal urban; highest concentration in HCOL markets that lose marginal renters first."
      - ticker: AVB
        weight: 0.18
      - ticker: MAA
        weight: 0.15
      - ticker: CPT
        weight: 0.15
      - ticker: UDR
        weight: 0.12
      - ticker: ESS
        weight: 0.10
      - ticker: IRT
        weight: 0.10
    triggers:
      - "30yr below 5.5% sustained 60d → start scaling in"
      - "30yr below 5.0% sustained 30d → full size"
      - "Cap rate spread to 10yr above 250bps → trim (mean-reversion already happened)"
    risk_caps:
      max_basket_gross: 0.05  # 5% of portfolio
      max_single_name: 0.012  # 1.2% on any one
```

Reject C (mixing concerns).

The rest of this file is the Option A content.

---

## 1. Thesis (one paragraph)

The apartment REIT short is a "Factor 1 unwind" trade — when mortgage rate lock-in eases, marginal renters convert to owners, weakening apartment REITs' pricing power and tenant retention. Today's apartment REITs benefit from involuntarily-trapped renters: would-be first-time buyers priced out of ownership by the affordability ceiling (JCHS 2025: $126,700 income required for the median home, $26,800 cash needed, only 12% of renters can meet it). When rates fall enough to release that pent-up buying demand, occupancy and rent growth both compress; **whatever valuation premium the sector still carries from the 2022–2026 rate-lockup period is at risk** (Wyatt to source — implied cap-rate vs 10y, FFO multiple comparison vs pre-2022).

**Caveat from the JCHS 2025 read.** The "Factor 4 demographics" recast (see `five_factor_framework.md`) cuts the other way for apartment REITs — if structural household formation is materially lower than consensus, *both* owner and renter demand are weaker than the bull case assumes. The short thesis still works (apartment REITs face structural headwinds) but the unwind path is messier than a simple "rates fall, multiple compresses" story.

## 2. Basket members and rationale

Tier 4 in `data/fmp_tickers.csv` currently includes (per claude-a's note): EQR, AVB, MAA, CPT, UDR, ESS, plus IRT and others. Wyatt to confirm the exact roster and per-name weights.

Per-name notes (skeleton — fill in):

### EQR (Equity Residential)
- **Footprint:** coastal urban (NYC, Boston, SF, DC, Seattle, LA-area).
- **Why size first:** highest concentration in HCOL markets that lose marginal renters first when ownership becomes accessible.
- **Risks:** WFH-driven urban-rental demand has held up better than 2020 expected; could be sticky.

### AVB (AvalonBay Communities)
- _(Wyatt to fill)_

### MAA (Mid-America Apartment Communities)
- _(Wyatt to fill)_

### CPT (Camden Property Trust)
- _(Wyatt to fill)_

### UDR (UDR, Inc.)
- _(Wyatt to fill)_

### ESS (Essex Property Trust)
- _(Wyatt to fill)_

### IRT (Independence Realty Trust)
- _(Wyatt to fill — debatable whether this belongs vs leave as Tier 3 long)_

## 3. Sizing logic

_(Wyatt to fill — use Script 09's correlation rankings to validate that these names are negatively correlated with the lock-in unwind indicators; weight inversely proportional to existing thesis exposure if any positive correlation surfaces.)_

## 4. Entry / exit triggers

Skeleton — replace with Wyatt's actual triggers:
- **Initial position:** start scaling in when 30yr drops below 5.5% sustained 60d.
- **Full size:** when 30yr drops below 5.0% sustained 30d.
- **Trim:** if cap-rate spread to 10yr Treasury widens above 250bps (mean-reversion already happened, premium compressed).
- **Stop:** if 30yr re-rises above 6.5% for 30d AND apartment REIT sector outperforms S&P by 10% (thesis broken).

## 5. Risk and counter-arguments

_(Wyatt to fill — at minimum:)_
- WFH-anchored urban renting could prove sticky longer than thesis assumes.
- Multifamily new-construction has slowed materially (354k starts 2024 vs 608k completions; supply pipeline empties out → rent growth could re-accelerate before unwind).
- Cap-rate compression in 2024-2025 has already partially priced this in; check current implied yields.

## 6. Cross-references

- `five_factor_framework.md` — Factor 1 (rate lock-in), Factor 5 (rent-own spread).
- `data/correlation_rankings.csv` (when Script 09 runs) — rate-sensitivity ranking will validate the basket.
- `data/sec_reit_homes.csv` — apartment REIT property count / occupancy snapshots when Betsy's per-REIT geo parser (Script 06c) lands.
