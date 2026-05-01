# Step 5 — Stock Scoring

> _Status: 2026-05-01. Default-driven first draft. ASSUMPTION-flagged
> on scoring methodology and per-ticker conviction. Output table is
> illustrative; the canonical scored output regenerates from
> `data/correlation_rankings.csv` × `analyst/factor_weights.yaml`._

This section ties everything to specific names. The structural map
(Step 1) cataloged who captures dollars; the value chain (Step 3)
quantified how much; the wave position (Step 4) located when the
catalyst fires. Step 5 produces a thesis-exposure score per ticker
that ranks the universe for position-building.

---

## Methodology — Hybrid factor-weighted aggregate score

_ASSUMPTION (Wyatt's Claude default):_ Use a hybrid approach: factor-
weighted aggregate score validated against Lynch category and Profile/
Archetype [per Investment Research Training Manual v5.0]. Pure
quantitative scoring (correlation-only) misses structural calls;
pure judgment scoring loses systematic discipline. The hybrid:

```
thesis_exposure_score(ticker) =
    w1 × neg(corr(ticker, mortgage_rate_30yr))    # Factor 1
  + w5 × affordability_signal(ticker)              # Factor 5  
  + w2 × inventory_signal(ticker)                  # Factor 2
  + wd × cohort_signal(ticker)                     # Factors 3+4 combined
  + wp × policy_signal(ticker)                     # Cross-cut

where:
  w1 = 0.40 (rate_lockin weight from factor_weights.yaml)
  w5 = 0.25 (affordability)
  w2 = 0.15 (inventory)  
  wd = 0.10 (demographics)
  wp = 0.10 (policy)

Score range: -1 (pure short-thesis aligned) to +1 (pure long-thesis aligned)
```

Each component is a discrete signal (mostly per-subsector classification
based on Step 1's structural map):

- `corr(ticker, mortgage_rate_30yr)` — pearson_r from Script 09's
  correlation_rankings.csv at 5y window.
- `affordability_signal(ticker)` — discrete: -1, 0, +1 based on
  whether the name is a Layer-1/2/5/6 long (volume-beta), Layer-4
  short (apartment REIT), or other.
- `inventory_signal(ticker)` — discrete: -1 (apartment REIT), 0
  (most), +1 (SFR REIT or builder if framing supply emergence).
- `cohort_signal(ticker)` — discrete: penalty for entry-level / FHA-
  cohort exposed names (LGIH/CCS specifically given Q1 2026 cancel
  data); +1 for diversified-buyer-cohort names.
- `policy_signal(ticker)` — discrete based on policy-lever exposure:
  +1 for names that benefit from Section 121 / assumable mortgage
  reform; -1 for names penalized by tariffs on building inputs;
  0 for neutral.

After computing, **validate against Lynch category** [Manual L2095]:
- A name scored as +0.7+ (high long conviction) but classified as
  Cyclical (Lynch) without an inning-2-4 market position is a flag
  to discount conviction.
- A name scored as -0.7+ (high short conviction) but classified as
  Stalwart (Lynch) is a flag — Stalwarts rarely deserve the high
  short-conviction multiplier.

Then **validate against Profile/Archetype** [Manual Part III]:
- Profile 1 (Cyclical Distress with Misperceived Quality): elevated
  long score; the manual lists this as the highest-conviction long
  setup [Manual L1672-1820].
- Profile 7 (Business Model Change): NVR's option-the-land model
  [Manual L1799-1819] is the canonical example. Highest weight on
  builders with sustained Profile-7 attributes.
- Short Archetype B (Structural Decline): the framework distinguishes
  this from cyclical decline. Short-conviction names should be
  Archetype B candidates, not Archetype F (Peak-Cycle Component
  Supplier) — apartment REITs are closer to F than B, which lowers
  the short-conviction multiplier.

---

## Top long-side scored names

_Illustrative — based on Script 09 outputs at 2026-05-01._

| Ticker | Layer | Tier | Pearson r vs MORTGAGE30US | Inferred Score | Rationale |
|---|---|---|---:|---:|---|
| **STC** (Stewart Information) | 5 — Title | 1 | -0.65 | **+0.65** | Pure-play volume beta; low capex; high operating leverage |
| **RKT** (Rocket Companies) | 2 — Mortgage | 1 | -0.64 | **+0.62** | Largest originator with capacity to capture refi wave |
| **FAF** (First American Financial) | 5 — Title | 1 | -0.63 | **+0.63** | Title insurance leader; cleanest Factor-1 long exposure |
| **PFSI** (PennyMac Financial) | 2 — Mortgage | 1 | -0.60 | **+0.58** | Mortgage origination + servicing; lower idiosyncratic noise |
| **MTH** (Meritage Homes) | 3 — Builder | 1 | -0.58 | **+0.55** | Tier-1 builder; recent QoQ orders +14%; mid-Sun-Belt mix |
| **NVR** (NVR Inc.) | 3 — Builder | 1 | -0.58 | **+0.60** | Profile 7 (option-the-land) [Manual L1799]; structural quality bumps score |
| **CCS** (Century Communities) | 3 — Builder | 1-2 | -0.57 | **+0.40** | Tier 1-2 builder with -12% net orders; Factor 4 risk discount |
| **DHI** (D.R. Horton) | 3 — Builder | 1 | -0.57 | **+0.55** | Largest by volume; defensively positioned |
| **MHO** (M/I Homes) | 3 — Builder | 1 | -0.56 | **+0.52** | Tier-1 builder; +22% net orders QoQ |
| **KBH** (KB Home) | 3 — Builder | 1 | -0.56 | **+0.50** | Entry-level mix; some Factor 4 risk |
| **PHM** (Pulte) | 3 — Builder | 1 | -0.55 | **+0.55** | High ASP exposure ($542K avg); affluent move-up cohort |
| **BZH** (Beazer) | 3 — Builder | 1 | -0.55 | **+0.45** | Tier-1 with rising cancel rate (13.5%); sizing discount |
| **GRBK** (Green Brick) | 3 — Builder | 1 | -0.54 | **+0.50** | Smaller-cap builder; high beta |
| **TMHC** (Taylor Morrison) | 3 — Builder | 1 | — | **+0.55** | Move-up positioning; defensive |
| **HD** (Home Depot) | 6 — Aftermarket | 1 | — | **+0.30** | Diversified; mover-cohort lift is incremental, not load-bearing |
| **LOW** (Lowe's) | 6 — Aftermarket | 1 | — | **+0.30** | Same as HD |
| **W** (Wayfair) | 6 — Furnishings | 2 | — | **+0.45** | Mover-cohort beta higher than HD/LOW |
| **WHR** (Whirlpool) | 6 — Appliances | 2 | — | **+0.35** | Mid-beta; replacement cycle component |

The pure-play volume-beta names (title insurance, mortgage origination)
sit at the top — score +0.55 to +0.65. Builders cluster in the +0.45
to +0.60 band with idiosyncratic discounts (BZH/CCS for cancel-rate
issues; entry-level builders for Factor 4 ceiling exposure).

---

## High-conviction short-side scored names

| Ticker | Layer | Tier | Pearson r vs MORTGAGE30US | Inferred Score | Rationale |
|---|---|---|---:|---:|---|
| **EQR** (Equity Residential) | 4 — Apartment | 4 | (correlation est.: weakly positive — confirmed thesis-positive on rate-down) | **−0.65** | Coastal urban; conviction-tilted basket; see basket file |
| **AVB** (AvalonBay) | 4 — Apartment | 4 | — | **−0.60** | NEMA / coastal urban; balance-sheet defensive |
| **MAA** (Mid-America) | 4 — Apartment | 4 | — | **−0.45** | Sun Belt; partial conversion already |
| **CPT** (Camden) | 4 — Apartment | 4 | — | **−0.45** | Sun Belt + DC defensive |
| **UDR** | 4 — Apartment | 4 | — | **−0.35** | Diversified; thesis dilution |
| **ESS** (Essex) | 4 — Apartment | 4 | — | **−0.35** | CA-only; regulatory tail risk |
| **IRT** (Independence Realty) | 4 — Apartment | 4 | — | **−0.40** | Sun Belt small-cap; high beta |

The apartment REIT short basket sits in the -0.35 to -0.65 band, with
EQR/AVB at the highest conviction (coastal urban renter-conversion
cleanest). Per the apartment REIT basket file, weighting is conviction-
tilted to match.

---

## Edge cases requiring manual judgment

| Ticker | Issue | Default scoring | Recommended action |
|---|---|---|---|
| **SUI** (Sun Communities — manufactured housing REIT) | -0.62 corr to MORTGAGE30US (high) but apartment-adjacent (would normally be short basket) | Score: ~+0.30 (mixed; demographic-wave-positive on rate-down) | _ASSUMPTION:_ Treat as long; low conviction; mark as "thesis-complex" — Wyatt may want to reclassify |
| **LGIH** (LGI Homes) | Tier-1 builder with 45.6% Q1 2026 cancel rate; affordability ceiling clearly biting | Default Factor 4 discount: -0.20 vs other builders | Score: ~+0.30 (long-thesis with Factor 4 risk); revisit Q2 |
| **UWMC** (United Wholesale Mortgage) | Heavy insider selling (Mat Ishbia $38M+ in April); supply overhang on the stock | Default insider-selling discount: -0.15 | Score: ~+0.45 (long-thesis, insider-supply discount); RKT/PFSI positioned cleaner |
| **LDI** (loanDepot) | Material balance-sheet stress signaled by April 30 8-K | Factor 4 + balance-sheet risk: -0.30 | Score: ~+0.10 (low conviction; possible binary outcome — survive vs fail) |
| **VTR / WELL** (Senior Housing REITs) | Demographic-wave-positive but thesis-orthogonal | Score: +0.25 (lower-conviction long; long via different mechanism) | Long, but in a separate "demographic wave" book, not the unlock book |
| **OPEN** (Opendoor) | iBuyer with inventory carry; Layer 1 brokerage but with inventory risk | Score: ~+0.15 (mixed; high beta to volume but balance-sheet-heavy) | Pass or low-weight long |

These are the names where pure formula-driven scoring underweights or
overweights conviction. Wyatt's quarterly review should focus on these
edges.

---

## Tier definitions (default — _ASSUMPTION_-flagged)

The 262-ticker universe carries Tier 1-5 labels in `data/fmp_tickers.csv`.
The default tier definitions:

| Tier | Definition | Position style |
|---|---|---|
| **Tier 1** | Highest-conviction long names; pure-play housing exposure (>70% revenue from housing); strong balance sheet | Core long positions; up to 1.5% gross per name |
| **Tier 2** | High-conviction long; substantial housing exposure (40-70% revenue); some idiosyncratic risk | Swing long positions; up to 1.0% gross per name |
| **Tier 3** | Lower-conviction long or specialized exposure; moderate housing tilt | Long basket positions; 0.25-0.50% gross |
| **Tier 4** | Apartment REITs (Tier-4 short basket); designated short for unlock thesis | Short basket; sized via short_baskets.yaml |
| **Tier 5** | Macro / context tickers; not core thesis positions | Pass or correlation-only |

_ASSUMPTION:_ These tier definitions are inherited from the playbook
universe. Wyatt may want to re-tier specific names after Step 5
scoring (e.g., LGIH from Tier 1 to Tier 2 given Factor 4 risk; CCS
similarly). Re-tiering is a PR-driven update to `data/fmp_tickers.csv`.

---

## Position-building sequence (consolidated from Step 3 lag structure)

| Tranche | Trigger | Names |
|---|---|---|
| **1** (T-0 to T+12 weeks of rate-path inflection) | 30yr below 5.5% sustained 60d | Pure-play volume beta: STC, FAF, FNF, RKT, UWMC, PFSI |
| **2** (T+12 to T+30 weeks) | Pending home sales > 4.4M sustained 2 mo | Tier-1 builders: NVR, DHI, LEN, PHM, MTH, MHO, TMHC |
| **3** (T+24 to T+50 weeks) | Builder closings inflect + HD/LOW comps confirm | Aftermarket: HD, LOW, W, RH, WHR, GNRC |
| **4** (T+30 to T+100 weeks) | Apartment REIT same-store rent decel confirmed | Short basket scaling per `analyst/short_baskets.yaml` triggers |

---

## Open questions for Wyatt's revision

- _ASSUMPTION:_ Hybrid scoring formula above weights Factor 1 at 40%
  via `factor_weights.yaml`. If schema changes (Factor 4 broken out
  separately), the formula needs re-deriving.
- _ASSUMPTION:_ Edge-case treatment for LGIH/CCS — the cancel-rate
  signal is recent (Q1 2026 print). If Q2 2026 cancel rates revert,
  the Factor 4 discount should be removed.
- _ASSUMPTION:_ Insider-selling penalty for UWMC. Wyatt may have a
  view on whether the Ishbia selling is 10b5-1 (mechanical) vs
  signal-bearing.
- _ASSUMPTION:_ SUI / Manufactured Housing classification. Could
  argue these should be in a "demographic wave" book rather than
  unlock-thesis book.
- _ASSUMPTION:_ Tier reassignments based on Step 5 scoring. Specific
  names (LGIH, CCS, IRT) where the scoring suggests a tier change
  are flagged in the edge-cases table above.

The illustrative scores in this section are starting points; the
canonical scored universe regenerates from `data/correlation_rankings.csv`
× `analyst/factor_weights.yaml` × the edge-case adjustments. Engineering
can productionize this scoring logic as Script 09b (per claude-a's
"Script 09 is pure measurement; thesis exposure score deferred to
09b or 10").
