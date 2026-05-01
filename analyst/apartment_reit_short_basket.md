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

> _ASSUMPTION (Wyatt's Claude default, 2026-05-01):_ Keep all 7 names
> in the basket; conviction-tilted weighting toward HCOL coastal exposure
> (EQR, AVB) which face the steepest renter-to-owner conversion math.
> Wyatt to confirm or trim. If forced to a 6-name basket, drop ESS
> (highest valuation, smallest margin of safety on multiple compression).

Default per-name weights (sum to 1.00) — see `analyst/short_baskets.yaml`
for the structured artifact Script 10/11b ingests.

| Ticker | Default weight | Conviction tier |
|---|--:|---|
| EQR | 0.20 | High (coastal urban concentration) |
| AVB | 0.18 | High (NEMA / coastal-urban same-store exposure) |
| MAA | 0.15 | Medium (Sun Belt; rent-decel risk if Sun Belt convert-to-own slows) |
| CPT | 0.15 | Medium (Sun Belt + DC; mixed) |
| UDR | 0.12 | Medium (diversified; least concentrated thesis) |
| ESS | 0.10 | Low (pure-CA coastal; tail risk on CA-specific regulation) |
| IRT | 0.10 | Low (Sun Belt secondary markets; smallest cap, highest beta) |

### Per-name notes (defaults — _ASSUMPTION_-flagged)

### EQR (Equity Residential)
- **Footprint:** coastal urban (NYC, Boston, SF, DC, Seattle, LA-area).
- **Why size first:** highest concentration in HCOL markets that lose marginal renters first when ownership becomes accessible. Same-store exposure to the cohorts JCHS flagged as already-priced-out (FTHB age 38, requires $126,700 income).
- **Risks:** WFH-driven urban-rental demand has held up better than 2020 expected; could be sticky if return-to-office slows again. Coastal supply growth has been minimal — short-term occupancy could remain firm.

### AVB (AvalonBay Communities)
- **Footprint:** New England coastal + DC/Baltimore + selected West Coast (Seattle, SF Bay, LA). Skews ~70% coastal HCOL.
- **Why size near EQR weight:** same coastal-renter-conversion exposure as EQR; better balance sheet (lower leverage), slightly more defensive on the multiple-compression leg but equally exposed on the renter-conversion leg.
- **Risks:** newer development pipeline could lease up at premium rents in late 2026 if supply pipeline empties. CapEx-heavy NEMA renovation cycle distorts FFO multiple reading.

### MAA (Mid-America Apartment Communities)
- **Footprint:** Sun Belt (Atlanta, Dallas, Charlotte, Tampa, Nashville, etc.). ~95% Sun Belt.
- **Why size lower:** the renter-to-owner conversion mechanism works in Sun Belt too, but Sun Belt single-family pricing is closer to affordability; the conversion has *already begun* in 2024-2025 (Sun Belt rent-growth went negative on RealPage / Apartment List indices) and a meaningful share of MAA's potential renter-converters has already converted. Less unrealized downside than EQR/AVB.
- **Risks:** Sun Belt multifamily completions through 2026 are still lapping; rent growth could re-accelerate H2 2026 if completions taper.

### CPT (Camden Property Trust)
- **Footprint:** Sun Belt + DC (Houston, Atlanta, DC suburbs, Tampa, Phoenix).
- **Why size near MAA:** similar Sun Belt thesis; DC adds a defensive overlay (federal-government-tenant base).
- **Risks:** Houston-energy concentration if oil-driven inflation persists; DC defensiveness limits upside on multiple compression but also limits downside.

### UDR (UDR, Inc.)
- **Footprint:** diversified — coastal (DC, NYC, Boston, SF, LA) + Sun Belt (Tampa, Charlotte, Nashville) + Pacific NW.
- **Why size lower:** the diversification dilutes the thesis. UDR is neither pure-coastal-renter-conversion (EQR/AVB) nor pure-Sun-Belt-rent-decel (MAA/CPT) — the basket effect is muted on each mechanism.
- **Risks:** highest geographic dispersion of any apartment REIT in the basket; idiosyncratic markets (Pacific NW, DC) have their own regulatory risk profile.

### ESS (Essex Property Trust)
- **Footprint:** California-only coastal (Bay Area, LA, San Diego).
- **Why smallest weight (or trim if forced to 6):** highest valuation multiple in the basket; CA-specific regulatory risk is binary and asymmetric — AB 1482 / rent-control extensions are tail-risk on the *long* side (limit downside on rents) but not symmetric tail-help on the short side. CA wildfire / climate-insurance crisis is a separate headline-noise channel that obscures the thesis read.
- **Risks:** CA migration outflow has *already* priced into ESS multiples through 2024; further outflow may not produce additional multiple compression.

### IRT (Independence Realty Trust)
- **Footprint:** Sun Belt + select Mountain West, smaller-tier cap (~$5B mcap vs $10-30B peers).
- **Why include despite ambiguity:** small-cap Sun Belt apartment exposure with the cleanest read on Sun Belt-specific renter-to-owner conversion (no coastal noise, no urban-renter dynamics). Higher beta to the thesis means it's the basket's "convexity" name on the directional read.
- **Why borderline:** smaller cap = wider bid-ask, less liquid borrow, and the rent-decel mechanism has already partly played out in IRT's footprint. Could be argued as Tier-3 long if Sun Belt convert-to-own normalizes faster than thesis assumes.
- _ASSUMPTION:_ Keep in basket at 10% weight; revisit after Q1 2026 10-Q if same-store rent growth has stabilized.

## 3. Sizing logic

The basket is sized by **conviction × Factor-1+5 sensitivity**:

- **Conviction tier** (above): high (EQR/AVB) > medium (MAA/CPT/UDR) > low (ESS/IRT).
- **Factor-1+5 sensitivity:** validated by Script 09's correlation rankings — apartment REITs should be *negatively* correlated with mortgage_rate_30yr (rate falls → renters convert → REIT underperforms). If a name is *positively* correlated (i.e., the rate-down move helps it), the short thesis is wrong about that name and weight should be reduced.

**Validation step (run weekly during basket maintenance):** check
`data/correlation_rankings.csv` for each basket member at the 5y window.
For a short thesis where rates falling produces apartment REIT
underperformance, the **expected sign of `pearson_r` vs
`mortgage_rate_30yr` is positive** (REIT prices and rates move in the
same direction; rates fall → REITs fall). If any member's `pearson_r`
is materially negative (< -0.20), flag for re-evaluation — the rate-
sensitivity is running opposite to thesis on that name.

**Sizing math** (against a target portfolio gross of 5%):

```
basket_gross = 5.0% of portfolio
per_name_size = basket_gross × default_weight
```

So for a $100M portfolio:
- EQR ~$1.0M short
- AVB ~$0.9M short
- MAA ~$0.75M short
- CPT ~$0.75M short
- UDR ~$0.6M short
- ESS ~$0.5M short
- IRT ~$0.5M short

Per-name single-position cap: 1.5% gross to bound idiosyncratic risk.

## 4. Entry / exit triggers

Defaults — Wyatt to revise.

- **Initial position (scale 25%):** start when 30yr falls below **5.5%
  sustained 60 days**. The recently-locked cohort (5%+ mortgages)
  begins crossing into willingness-to-transact at this level. Apartment-
  REIT renter-conversion narrative starts to take hold.
- **Half size (scale 50%):** when 30yr falls below **5.25% sustained 30
  days** OR when CME FedWatch 2026 cut probability rises above 50%.
- **Full size (100%):** when 30yr falls below **5.0% sustained 30 days**.
  At this level, the 4-5% locked-rate bucket begins releasing,
  unlocking ~5.4M new transaction inventory; renter conversion math
  shifts decisively.
- **Trim (scale to 25%):** if cap-rate spread to 10yr Treasury widens
  above **250 bps** (mean-reversion to historical mean has happened;
  multiple compression already largely priced).
- **Stop / unwind:** any of the following:
  - 30yr re-rises above **6.5% for 30 days** AND apartment REIT
    sector outperforms S&P by **10% over 60 days** (thesis broken on
    the rate-path side).
  - Sustained Sun Belt rent re-acceleration: any 3-month rolling MAA/
    CPT/IRT same-store rent growth > +3% YoY (supply-side reset).
  - Any major change in WFH policy at Tier-1 employers that
    materially increases urban-renter demand (e.g., federal RTO
    mandate going in opposite direction).

_ASSUMPTION:_ Triggers are conservative on entry (require sustained
moves, not single prints) and tight on stop (10% sector outperformance
is small enough to catch a thesis-break before max drawdown). Wyatt
may want to revise these to his risk-budget after first-trigger event.

## 5. Risk and counter-arguments

_The strongest version of the bear case on this short basket:_

- **WFH-anchored urban renting could prove stickier than thesis
  assumes.** EQR and AVB have already endured one cycle of return-to-
  office (2023-2024); a second WFH retrenchment in 2026 would
  re-strengthen urban renter retention. Watch: federal RTO mandates,
  major-employer return-to-office reversals.
- **Multifamily new-construction has slowed materially** (354k starts
  2024 vs 608k completions per JCHS 2025 p. 7). The supply pipeline
  empties through H2 2026 → 2027, which could let rent growth
  re-accelerate even as renter-conversion begins. **Sun Belt names
  (MAA/CPT/IRT) face this risk most acutely.**
- **Cap-rate compression in 2024-2025 has already partially priced
  this in.** Check current implied yields vs. NAREIT 5-year mean.
  Apartment REIT cap rates compressed ~75-100 bps from 2022 lows;
  if half of the multiple-compression has already happened, the
  short-side return is half what the central case implies.
- **Rate path doesn't deliver — Factor 1 weakens (FOMC hawkish,
  Warsh removes forward guidance).** If MBS spreads stay 200-220 bps
  and 30yr stalls at 6.0-6.5% through 2027, the renter-conversion
  catalyst doesn't fire. Apartment REITs continue to outperform on
  the involuntary-renter framing.
- **CA regulatory risk on ESS is asymmetric on the long side.** AB
  1482 / rent-cap extensions limit downside on rents (constrains
  thesis-positive read).

## 6. Cross-references

- `five_factor_framework.md` — Factor 1 (rate lock-in), Factor 5 (rent-own spread).
- `data/correlation_rankings.csv` (when Script 09 runs) — rate-sensitivity ranking will validate the basket.
- `data/sec_reit_homes.csv` — apartment REIT property count / occupancy snapshots when Betsy's per-REIT geo parser (Script 06c) lands.
