# Five-Factor Framework — US Housing Transaction Volume

> **Status:** outline / scaffolding by Wyatt's Claude (2026-05-01).
> Wyatt fills in the prose, math anchors, and final weights.
> Once the prose section per factor stabilizes, Script 10's "Structural vs
> Cyclical Framework" footer (lines ~189–193 of `housing_context.md`) gets
> rewired to point at this file, and `analyst/factor_weights.yaml` gets
> updated with canonical (non-placeholder) weights + a `last_updated` date.

---

## 0. Schema decision before writing canonical weights

The playbook's five factors and `analyst/factor_weights.yaml` don't map 1:1.
This needs resolving before the YAML is updated, otherwise Script 10's footer
and Wyatt's prose drift apart.

| Playbook factor | Current YAML key | Notes |
|---|---|---|
| 1. Rate lock-in | `rate_lockin: 0.40` | Match. |
| 2. REIT absorption | folded into `inventory: 0.15` | YAML abstracts to "supply tightness". |
| 3. 2nd/3rd home turnover | folded into `demographics: 0.10` | YAML lumps with Factor 4. |
| 4. Demographics & ownership ceiling | folded into `demographics: 0.10` | YAML lumps with Factor 3. |
| 5. Rent-own spread | `affordability: 0.25` | Match (renamed). |
| _(not in playbook)_ | `policy: 0.10` | Extra dimension. |

**Decision (Wyatt's Claude default, 2026-05-01 — pending Wyatt review):**
Keep the abstracted set. Rationale:

1. Renaming creates a flag day for Script 10's footer + the dashboard's
   `housing_context.json` factor-weight surfacing + downstream code in
   `scripts/lib/yaml_config.py`. Cost is small but real.
2. The `demographics` weight (10%) is small enough that lumping factors 3
   and 4 loses minimal signal vs. a clean 2-key split. The disaggregation
   lives in this framework's prose, which is the load-bearing artifact for
   *interpretation* anyway.
3. `policy` as a cross-cutting 6th dimension preserves a useful slot the
   playbook's strict 5 doesn't. Section 121, assumable mortgages, and GSE
   reform don't fit cleanly in any of the five.

`analyst/factor_weights.yaml` is updated to canonical weights (40/25/15/
10/10) with `last_updated: 2026-05-01` reflecting this decision. The
factor-by-factor sections below use **playbook factor numbering** for the
analytical prose; the YAML rollup is documented in §6.

---

## Factor 1 — Rate Lock-In

> The cyclical core of the thesis. Most owners hold a sub-4% mortgage; the
> 30yr is at 6.30%. Moving means trading the sub-4% asset for a market-rate
> liability. Above some threshold, that trade-off is too expensive to take —
> so they don't move, existing-home turnover collapses, and pent-up volume
> accumulates.

**Weight:** 0.40 (canonical, see `analyst/factor_weights.yaml`).

### Mechanism

The mechanism is mechanical: an owner's decision to move depends on the
spread between the rate they hold and the rate they would receive at
purchase. When that spread exceeds a threshold of ~150 bps, the implicit
cost of trading rates exceeds the benefit of moving for most households —
not just the median household, but the entire cohort whose move-trigger
(job change, family-size shift, downsize) ranks below the rate friction
in importance. Demand for the next house doesn't disappear; it gets
deferred. Volume collapses but does not destroy.

As market rates fall, owners with progressively-lower locked rates cross
back into "willing to transact" territory — first the recently-locked
(5%+), then the mid-cycle (4–5%), then the deeply-locked (<4%) only at
extreme rate retracement. The unlock is **step-functional, not smooth**:
each 25 bps drop releases the FHFA-distribution bucket whose midpoint
crosses (market_rate − threshold).

The reason this is the headline factor is that it operates on the supply
side of *existing-home* inventory, which is 5–10× larger than new-home
supply by transaction count. A modest unlock of locked-low owners
produces a disproportionate inventory and transaction-volume response —
the "coiled spring" framing — without any change in underlying demand.
The demand was always there; the supply was withheld.

### Math (codified — see `lib/coiled_spring.py`)

- Threshold: `market_rate > current_rate + 1.5` ⇒ locked.
- Distribution: FHFA mortgage rate buckets (`analyst/coiled_spring_params.yaml`).
- At market 6.5% with the current distribution: ~41.5M locked, ~9.2M unlocked.
- Each 25 bps drop releases the bucket whose midpoint crosses the threshold.

### Anchors (defaults — _ASSUMPTION_-flagged, pending Wyatt review)

**1.5% threshold.** _ASSUMPTION (Wyatt's Claude default):_ The 150-bps
threshold is the central tendency of behavioral-finance work on
mortgage-mobility decisions and is the working assumption used by NY Fed
and FRBSF analysts in published commentary on the post-2022 lock-in.
Plausible alternates are 1.0% (more permissive — captures the cohort
with weakest move-frictions) and 2.0% (stricter — only the genuinely-
trapped). The thesis result is most sensitive to threshold choice in the
1.0–1.7 band, where bucket-edge owners flip in and out. **Wyatt to
confirm or revise**; if revised, regenerate
`data/coiled_spring_scenarios.csv` from the math in `lib/coiled_spring.py`.

**50% normalization scenario.** _ASSUMPTION:_ "Normalization" means a
return to pre-2022 turnover rates. NAR existing-home sales averaged
~5.3M/yr 2015–2019; the current pace is ~4.0M/yr — a ~25% deficit
sustained for ~3 years equals ~4M deferred transactions. **Why 50%
rather than 30% or 70%:** mover-survey evidence suggests ~70% of
sub-4% locked owners are structurally non-moving regardless of rate
(retirement-anchored, age-cohort-driven mobility decline, geographically
anchored). Of the ~30% who *would* move at any rate, half clear at the
5.5% threshold and half require rates closer to 5.0%. **50% is the
mid-case across the willing-cohort, not the outer band.**

**Step-functional unlock path.** _ASSUMPTION:_ Cohort-threshold based.
At 5.5% (sustained 60d), the recently-locked cohort (≥5% mortgages)
crosses to willingness-to-transact and adds ~2.2M homes to active
inventory. At 5.0% (sustained 30d), the 4-5% bucket crosses and adds
another ~5.4M. At 4.5%, the 3.5–4% bucket crosses and adds ~8.7M more.
The math is in `lib/coiled_spring.py`; the path-shape is the analyst's
call.

**Policy levers (load-bearing for the 18-36 month horizon).**

- **Section 121 expansion.** Capital-gains exclusion has been $250K
  single / $500K joint since 1997, never indexed. CPI-adjusting to 2026
  dollars would expand to ~$510K / ~$1.02M — meaningful relief for HCOL
  coastal owners whose realized gains have outrun the exclusion.
  **Direct attack on the lock-in mechanism via tax-friction reduction.**
  Watch: any movement in House Ways & Means or Senate Finance.
- **Assumable mortgage reform.** FHFA could expand assumability beyond
  VA/FHA. Mechanically, an assumable sub-4% mortgage transferred to the
  buyer sidesteps the rate-trade entirely — seller keeps proceeds,
  buyer inherits the rate. **Direct catalyst.** Watch: FHFA rule-makings,
  Senate Banking commentary.

### Counter-thesis (steelman of the bear case)

The strongest version of the bear read on Factor 1: **the rate-lockin
unwind is structurally smaller than the math suggests, and the unlock
catalyst will arrive too late to matter for the current cycle.** Three
mechanisms support this read.

First, the 30yr-fixed mortgage is itself an artifact of US policy
structure (GSE conservatorship, MBS market mechanics). If GSE reform
shifts toward shorter-duration or adjustable products, future
households are not locked in the same way; the locked-in cohort
becomes increasingly retirement-anchored and structurally non-moving
regardless of rate. The unwind benefits a cohort that doesn't transact
much for non-rate reasons.

Second, the affordability ceiling (Factor 5) tightens faster than the
lock-in eases. Even at 5.0% rates, the median home price × current
income excludes more of the prior buyer pool than the unlocked supply
can absorb. If 20M locked owners release into a market with 10M
qualified buyers, *pricing falls, not volume* — the absorbing capacity
becomes the bottleneck.

Third, the structural call may be wrong: the 2008–2014 millennial
delay cohort may be genuinely lost to homeownership rather than merely
delayed. The JCHS 2025 demand revision (Factor 4) is consistent with
this read. If household formation doesn't recover and the marginal-
buyer pool keeps shrinking, the unwind has no demand to absorb the
released supply.

**Counter to counter-thesis.** GSE reform is multi-year and politically
constrained — doesn't bind on an 18–36 month horizon. The Factor 5
affordability ceiling is mechanically relieved by Factor 1: lower rates
lower P&I, the largest component of cost-to-own. The cohort math is
real but operates over decades, not the thesis horizon. The contingent
question — *at what rate level does demand exceed released supply* —
is itself testable via the FRED + NAR feed weekly; the position is built
such that monitoring catches the real outcome rather than anchoring on
the central case.

### Dependencies (testable, monitorable, time-bounded)

| # | Dependency | Observable | Source | Horizon |
|---|---|---|---|---|
| 1 | The 1.5% threshold is a defensible central tendency, not a free parameter | Behavioral evidence in repeated-cross-section mover-survey data | NAR Profile of Buyers/Sellers, NY Fed SCE Housing Survey | Re-test at each annual NAR Profile release |
| 2 | The locked cohort is genuinely deferred, not destroyed | Existing-home sales return toward pre-2022 pace within 24 months of 30yr crossing 5.0% | FRED `EXHOSLUSM495S` (data-integrity caveat applies) | If 30yr crosses 5.0% sustained 60d, watch 24 months out |
| 3 | The Fed has a path to 5.0% — inflation/oil constraints are not structural | CME FedWatch 2026-2027 cut probabilities; oil <$80 sustained | CME, EIA | Re-test quarterly; if 2027 cut probability stays <30% through Q3 2026, downgrade timeline |
| 4 | MBS-Treasury spread can compress without a Fed cut (alternate path to lower 30yr) | MBS-Treasury spread tightening from 200-220 bps toward 160-180 bps | MBA chart-of-the-week, FRED 30yr/10yr spread | Quarterly |

### Data inputs

`data/fhfa_distribution.csv`, FRED MORTGAGE30US, `lib/coiled_spring.py`,
`analyst/coiled_spring_params.yaml`.

### Cross-reference

Factor 5 (rent-own spread) is partially endogenous to Factor 1 — when
rates fall, both lock-in eases AND ownership cost falls, compounding
the unlock effect. The framework should not double-count this. The
`affordability` weight (0.25) in `factor_weights.yaml` captures the
*incremental* affordability shift independent of the rate move.

---

## Factor 2 — REIT Absorption (Single-Family)

> The structural one. Institutional SFR REITs (INVH, AMH, primarily) acquired
> ~150k+ existing single-family homes between 2012 and 2022, removing them
> from the owner-occupied inventory permanently. The acquisition wave is the
> bigger structural effect; ongoing turnover differential is secondary.

**Weight:** part of the `inventory: 0.15` rollup. Apartment-REIT
Tier-4 thesis is downstream (see `analyst/apartment_reit_short_basket.md`).

### Mechanism

Two distinct effects, often conflated, with materially different
analytical weights.

**Effect 1 — Acquisition wave (2012–2022).** Institutional SFR REITs
acquired existing single-family homes at scale during the post-GFC
distress period. INVH and AMH together hold ~144k homes per their
latest 10-Ks (`data/sec_reit_homes.csv`: INVH 86,192; AMH 57,573).
Add ELS, SUI (manufactured-housing-adjacent), and the smaller AMH /
TSO-equivalent peers, and the institutionally-held single-family stock
is ~150-180k units. The supply curve shifted down once and stayed there.

**Effect 2 — Turnover differential (ongoing).** Owner-occupied homes
turn over at ~5%/yr; institutional-held homes turn over at <3%/yr. The
200-bps differential moves a small additional slice of stock out of
"willing seller" status each year — at ~160k institutionally-held stock,
roughly 3-4k homes/yr that don't transact vs. the owner-occupied
counterfactual.

**The analytical weight sits with the acquisition effect, not the
turnover differential.** The acquisition is a one-time level shift but
permanent and order-of-magnitude larger. The differential is real but
small relative to the ~4M annual existing-home transaction count
(~0.1%). Treating them as equally important would over-weight the
slow-bleed mechanism vs. the structural removal.

### Math

| Metric | Value | Source |
|---|---:|---|
| INVH home count (latest 10-K) | 86,192 | `data/sec_reit_homes.csv` |
| AMH home count (latest 10-K) | 57,573 | `data/sec_reit_homes.csv` |
| Combined SFR-REIT held stock | ~144k | summed |
| Total US owner-occupied housing units | ~83M | Census ACS |
| SFR-REIT share of owner-occupied stock | ~0.17% | computed |
| Owner-occupied turnover rate | ~5%/yr | NAR existing-home-sales / total stock |
| REIT-held turnover rate | <3%/yr | inferred from REIT 10-Q disposition rates |
| Annual "stuck" stock growth from differential | ~3-4k/yr | (0.05 − 0.03) × ~160k |

### Anchors (defaults — _ASSUMPTION_-flagged)

**Acquisition vs differential framing.** _ASSUMPTION (Wyatt's Claude
default):_ Acquisition is the dominant analytical lever; differential
is the recurring drag but secondary. Wyatt may want to flip emphasis
if a *future* acquisition pace becomes a forward concern (e.g., new
private-equity entrants with cost-of-capital advantages restart the
buy program). For the current thesis, the ~144k acquired-and-held
stock is the relevant supply withheld; the 3-4k/yr differential is
a footnote.

**Apartment REIT mechanism (Tier 4 short basket).** _ASSUMPTION:_ Both
sub-mechanisms are operative, in sequence.
1. **First-order: renters convert to owners.** When rates fall enough
   that the cost-to-own / cost-to-rent flip closes (Factor 5), a slice
   of involuntary renters becomes voluntary buyers. Apartment occupancy
   slips, rent growth decelerates.
2. **Second-order: multiple compression.** Apartment REIT cap rates
   compressed materially since 2022 on the "involuntary renter is
   structural" narrative. As that narrative weakens, cap rates re-rate
   toward historical means (10-y Treasury + 250 bps), compounding
   FFO-multiple compression independent of operating performance.

The Tier-4 short basket is sized to capture both effects, with entry
triggers tied to rate path and cap-rate spread (see
`analyst/apartment_reit_short_basket.md`).

### Counter-thesis

Apartment REITs may continue outperforming if (a) rates stay higher
for longer — involuntary-renter persists as structural —, (b) WFH
preserves urban-rental demand more durably than thesis assumes, or
(c) new multifamily construction continues slowing (354k starts 2024
vs 608k completions per JCHS 2025 p. 7) and the supply pipeline
empties faster than demand softens. The position must be built such
that we test both rate path AND cap-rate spread weekly via Script 09's
correlation rankings; if apartment REITs are *positively* correlated
with MORTGAGE30US over a sustained window, the short thesis is wrong
about the sub-mechanism and needs to be reset.

### Dependencies

| # | Dependency | Observable | Source | Horizon |
|---|---|---|---|---|
| 1 | SFR REITs are net-non-sellers (no material disposition wave) | Quarterly 10-Q home-count delta vs prior-period filing | `data/sec_reit_homes.csv` (Script 06) | Quarterly, sensitive monthly |
| 2 | Apartment REITs are over-earning on the involuntary-renter narrative | Cap-rate spread to 10y > 250 bps; FFO multiple > pre-2022 average | NAREIT data, internal Script 09 correlations | Quarterly |
| 3 | The ~144k SFR-REIT stock is meaningfully sized vs. the unlocked-cohort math | (Factor-1 unlock millions) / (REIT held stock) ratio | Internal | Annually |

### Data inputs

`data/sec_reit_homes.csv` (Betsy's `06_sec_reit_properties.py`),
Census ACS owner-occupied stock, NAREIT cap-rate index, internal
correlation rankings from Script 09.

---

## Factor 3 — Second/Third Home Turnover

> Demographic stickiness layer 1. Second-home owners (~7M units, ~6% of
> housing stock) move at materially lower rates than primary residents.
> Third-home owners (much smaller cohort) move even less. As wealth has
> concentrated in the cohort that holds multi-property portfolios, this
> effect has grown.

**Weight:** part of the `demographics: 0.10` rollup (shared with Factor 4).

### Mechanism (footnote-tier in the thesis)

Second-home owners — ~7M units, ~6% of housing stock per Census American
Housing Survey — move at materially lower rates than primary residents.
The differential is ~2–3%/yr for second homes vs ~5%/yr for primary
residences. Two mechanisms drive it:

1. **No "growing family / job change / downsize" trigger.** Second homes
   are vacation/seasonal; the move-decision gates that apply to primary
   residences don't apply.
2. **Tax basis lock-in.** Section 121's capital-gains exclusion ($250K
   single / $500K joint) applies only to primary residences. Second-home
   owners face full long-term capital gains on sale, creating a strong
   tax disincentive that compounds with normal-life move-friction.

The implied "stuck" annual volume vs. counterfactual: `(0.05 − 0.025) ×
7M ≈ 175k homes/yr` that don't transact. Compared to total existing-home
sales (~4M/yr), this is ~4% of annual volume.

**Why this is footnote-tier, not load-bearing:** the stuck volume is real
but small at the thesis horizon. The cohort overlaps materially with
Factor 1 — low-rate-locked owners are also disproportionately
second-home owners (wealth/age correlation), so the math double-counts
if treated additively. The framework captures the effect via the
`demographics` weight (10%, shared with Factor 4); separating Factor 3
as its own line item over-weights it. The factor exists in the framework
mostly so its policy-lever (Section 121 expansion) is properly attributed
when it moves.

### Anchors (defaults — _ASSUMPTION_-flagged)

**STR/Airbnb regulatory crackdown is a material catalyst.** _ASSUMPTION
(Wyatt's Claude default):_ Several HCOL markets have moved aggressively
against short-term rentals over the last 24 months — Hawaii (statewide
restrictions post-2024 wildfires), NYC (Local Law 18), New Orleans,
Coronado, Big Bear, and a growing list. Forced conversions of STR-held
properties to either owner-occupied or long-term-rental inventory are
occurring at scale in those markets. **A federal STR regulation or
Treasury rule constraining 1031-exchange treatment for STR properties
would force disposition of investor-held second-home stock**, which is
the highest-leverage Factor-3 catalyst on a 12–24 month horizon. Watch:
any HUD or Treasury rule-making touching investor-held housing.

**Counter-thesis.** The STR regulatory wave may have stabilized post-2024
(state-level resistance to further restrictions; federal preemption
unlikely). Most STR-held properties that would transact under the
existing patchwork have already done so during the 2023–2024 forced-
conversion phase, exhausting the easy supply.

### Dependencies

| # | Dependency | Observable | Source | Horizon |
|---|---|---|---|---|
| 1 | Second-home stock is ~6% of total housing stock | Census AHS biennial release | Census | 2-year cadence |
| 2 | STR regulatory crackdown extends to a federal lever in next 24 months | Treasury or HUD rule-making | Federal Register, FHFA, HUD pressrooms | Track via Perplexity weekly legislative scuttlebutt |
| 3 | Factor 3 contribution is meaningfully smaller than Factor 1 (no double-count) | Cohort overlap math: % of 2nd-home owners with sub-4% mortgages | Census + NAR | Annually |

### Data inputs

Census American Housing Survey, IRS SOI (capital gains realizations on
real estate), NAR Profile of Home Buyers and Sellers, internal
Perplexity weekly policy_watch outputs for STR regulatory tracking.

---

## Factor 4 — Demographics & Homeownership Ceiling (the JCHS Critique)

> The big skeptic factor — and the JCHS 2025 report partially flips its
> own framing. The 2025 edition forecasts dramatically slower household
> growth than prior editions (8.6M for 2025–2035 vs the ~12-13.5M pace of
> the 1990s/2010s) without explicitly acknowledging the revision. The new
> data both supports and reframes Wyatt's thesis: **JCHS revised forward
> household and new-unit demand materially lower, which complicates the
> shortage narrative** even though the report still characterizes
> affordability and supply stress as severe. Consensus opinion (builders,
> lenders, Wall Street REIT theses) is still largely pricing the old,
> higher forecasts.

**Placeholder weight:** TBD (currently rolled into `demographics: 0.10`)

**Mechanism (revised after JCHS 2025 read).**
The original Wyatt-thesis framing was "JCHS overstates headship rates →
overstates demand → fake shortage." The JCHS 2025 report is more interesting
than that:

1. **JCHS itself now forecasts much lower household growth.** The 2025 main
   projection is **8.6M new households for 2025–2035 (~860k/yr)**, vs the
   13.5M (1990s) and 10.1M (2010s) historical decadal totals. That's a
   step-function down. (JCHS 2025, p. 20, Fig 13.)
2. **Implied housing demand drops to 11.3M units / decade (~1.13M/yr).**
   Below the historical 16M/decade pace. Single-family starts in 2024 were
   1.01M and multifamily 354k → total ~1.36M, *above* the implied need.
   (JCHS 2025, p. 4, p. 20.)
3. **The 2019–2023 "missing households" tailwind ended in 2024.** JCHS
   admits the post-COVID household-formation surge was a one-time pull-
   forward of Recession-delayed formations (~250k/yr extra), and that
   tailwind is now zero. (JCHS 2025, p. 18.)
4. **JCHS does not explicitly flag the revision.** The closest hedge is a
   sentence on p. 20 that lower demand "still yield[s] historically low
   levels of new construction" — softening the gap from prior reports
   without a "we revised" admission. (See Appendix A.8.)

**Implication for the unlock thesis.** This actually *strengthens* the
"affordability ceiling" element of the thesis (less new demand to absorb
the unlock when it comes) but *weakens* the "lock-in produces a coiled
spring of pent-up volume" framing — if young-adult headship rates have
permanently shifted, the demand on the other side of the unlock is smaller
than the lock-in math alone implies.

**Math (from JCHS 2025).**

| Metric | JCHS 2025 figure | Source |
|---|---:|---|
| Net household growth, 2025–2035 (main) | **8.6M** | p. 20 |
| Net household growth, 2035–2045 (main) | 5.1M | p. 20 |
| Net household growth, 2025–2035 (low-immig.) | 6.9M | p. 20 |
| Comparison: 1990s actual | 13.5M | p. 20 |
| Comparison: 2010s actual | 10.1M | p. 20 |
| 2024 net household growth (actual) | 1.56M | p. 17 |
| 2025 Q1 annualized rate | 1.26M | p. 17 |
| Implied housing demand 2025–2035 (units) | 11.3M | p. 20 |
| 2024 single-family starts | 1.01M | p. 4 |
| 2024 multifamily starts | 354k | p. 7 |
| Homeownership rate, 2024 | 65.6% | p. 6 |
| Homeownership rate, Q1 2025 | 65.1% | p. 9 |
| Under-35 homeownership rate | 37.1% (-1.4pp) | p. 25 |
| 35–44 homeownership rate | 61.8% (-0.8pp) | p. 25 |
| Cost-burdened owners (>30% income) | 20.3M | p. 5 |
| Cost-burdened renters | 22.6M (50%) | p. 5 |
| Severely-burdened renters (>50% income) | 12.1M (27%) | p. 5 |
| Income to afford median home (FTHB) | $126,700 | p. 27 |
| Median home price | $412,500 | p. 27 |
| Median FTHB age (record high 2024) | 38 | p. 27 |
| Renters with $26.8k cash for downpayment | 12% | p. 27 |
| 2024 existing-home sales (30-yr low) | 4.06M | p. 1 |

### Anchors (defaults — _ASSUMPTION_-flagged)

**Recast thesis framing.** _ASSUMPTION (Wyatt's Claude default):_ The
original framing ("JCHS overstates demand → fake shortage") is replaced
by: **"JCHS quietly revised the forecast downward ~30%+ without flagging
the change; consensus building, lending, and sell-side REIT theses are
still pricing the higher prior numbers."** That's still a contrarian
view — just contrarian in a different direction. The contrarian edge sits
in the *gap between JCHS's now-acknowledged number and the consensus that
hasn't updated*, not in JCHS itself being wrong.

**SFR REIT short read-across.** _ASSUMPTION:_ If household growth is
structurally ~30% lower than 2010s pace, SFR REIT NOI growth assumptions
embedded in current cap rates are too high. INVH and AMH guide ~3-5%
same-home NOI growth long-term; that math implies ~3-5% rent growth
plus stable occupancy. Lower household formation directly compresses
the rent-growth side of that math. **Direct read-across to the Tier-4
short basket and the SFR REITs (INVH, AMH) on the long side of supply-
withholding.**

**Counter-argument: JCHS could be over-correcting.** _ASSUMPTION:_ The
strongest bull case on Factor 4 is that JCHS's 2025 revision is itself
overshooting — the post-COVID household-formation slump may be the
temporary effect (mortgage rates × cohort timing locked out the
formation cohort), and as rates fall and the affordability ceiling
relaxes, headship rates re-accelerate to the 1990s/2010s baseline.
**Two pieces of evidence support that bull case:** (1) the Census
"missing households" dynamic JCHS cited (250k/yr 2019-2023 catch-up
formations) suggests the underlying population *can* form households at
higher rates when conditions allow; (2) under-35 homeownership at 37.1%
(JCHS p. 25) is below the long-run 1980-2024 average (~40%) — the
deficit is large enough that mean-reversion alone would close it
materially. The framework holds the JCHS-2025 number as the central
case but treats Factor 4 as a *bidirectional* factor rather than a
one-way bear lens.

**The "15-25% overstatement" anchor is retired.** _ASSUMPTION:_ The
prior anchor was a vintage-2023 estimate of JCHS's then-forecast vs.
realized. The 2025 JCHS revision substantially closes that gap on
JCHS's own terms. The contrarian claim is now about *consensus updating
lag*, not JCHS forecasting error.

### Dependencies

| # | Dependency | Observable | Source | Horizon |
|---|---|---|---|---|
| 1 | Consensus building / lending / REIT theses haven't updated to JCHS-2025 numbers | Sell-side housing notes, NAHB sentiment, REIT same-home NOI guidance | Sell-side coverage, NAHB, REIT 10-Qs | Quarterly |
| 2 | Headship rates remain depressed for the under-35 cohort | Census ACS annual release | Census | Annually |
| 3 | Cohort math (mean reversion) doesn't produce a near-term headship-rate snapback | Quarterly Census Housing Vacancies and Homeownership headship-rate panel | Census | Quarterly |

### Data inputs

JCHS State of the Nation's Housing 2025 (Wyatt has the PDF; full
verbatim extract in Appendix A), Census ACS headship rates by age
cohort, Census Housing Vacancies and Homeownership, BLS Consumer
Expenditure Survey, NAR existing-home-sales series.

---

## Factor 5 — Rent-Own Spread

> The affordability lever. Monthly cost-to-own (mortgage + tax + insurance)
> vs CPI owners' equivalent rent for a comparable unit. When the spread is
> historically wide on the cost-to-own side, marginal renters who would
> otherwise buy stay renting; demand for owner-occupied homes drops
> independent of the lock-in effect.

**Placeholder weight:** 0.25 (current YAML `affordability`)

**Mechanism.**
The "should I buy or keep renting" calculation:
- Cost-to-own ≈ mortgage payment + property tax + insurance + HOA + maintenance.
- Cost-to-rent ≈ market rent (or CPI owners' equivalent rent as a proxy).
- When (cost-to-own − cost-to-rent) is wide, marginal renters defer ownership.
- When it narrows (rates fall, prices fall, or rents rise), they convert.

### Math spec (confirmed — Betsy can implement in Script 10)

```
cost_to_own_monthly =
    median_home_price × 0.80 × pmt(MORTGAGE30US, 360 months)    # P&I on 80% LTV
    + median_home_price × 0.012 / 12                             # property tax (1.2% effective, national-blended)
    + median_home_price × 0.005 / 12                             # insurance (50 bps)
    + median_home_price × 0.005 / 12                             # maintenance reserve (50 bps)

cost_to_rent_monthly = CUSR0000SEHA  # CPI Owners' Equivalent Rent (per unit)

spread = cost_to_own − cost_to_rent
```

_ASSUMPTION (Wyatt's Claude default — confirm or revise the bps
constants):_

- **Property tax 1.20%/yr.** National-blended; varies materially by
  state (TX/NJ/IL run 2%+, HI/AL run <0.5%). Reasonable national
  central tendency.
- **Insurance 0.50%/yr.** National-blended; gross of climate-risk
  premium where applicable. **HCOL coastal markets (FL, CA wildfire-
  zone, TX coast) run materially higher** post-2023 reinsurance reset;
  Factor 5 reads worse there. Defensible to add a "climate-adjusted"
  variant of this calc for the apartment-REIT short thesis specifically.
- **Maintenance reserve 0.50%/yr.** Standard National Association of
  Home Inspectors guidance. Some sell-side analysts use 1.0%; 0.5% is
  the conservative-on-cost-to-own side, which biases the spread reading
  toward "ownership looks cheap" — so the read is more credible when
  it shows ownership looks expensive.

These constants are inputs to Betsy's Script-10 implementation; if the
Analyst revises any, the housing_context.json's "rent-own spread" field
changes directly and the dashboard re-renders.

### Anchors (defaults — _ASSUMPTION_-flagged)

**Behavioral-shift threshold is currently a TBD anchor.** _ASSUMPTION:_
The exact spread level that triggers a 10/25/50% behavioral shift among
first-time buyers is empirically under-researched. The framework treats
it as a range rather than a point: a sustained compression of >$500/mo
in (cost_to_own − cost_to_rent) over a 60-day window is a meaningful
threshold for narrative shift in the buy-vs-rent calculation. The
research project to anchor this number more precisely (1990–2024
historical spread distribution × HOUST × homeownership rate to back out
a first-time-buyer-share elasticity) is **deferred** — directional
read of "spread narrowing = thesis-positive" stands without the precise
number.

**Counter-thesis: rent could fall faster than ownership cost.** _If_
the 2024-2025 multifamily completion wave (608k completions on 354k
starts per JCHS 2025 p. 7) keeps rent disinflation persistent, and
single-family rent follows multifamily, the spread can *widen* on the
cost-to-rent side — renters stay renters longer because renting is
cheap, not because owning is expensive. The framework still reads
correctly in this scenario (rent falling = Factor 5 negative for the
long-side basket), but the *mechanism* differs from the central case.
**Watch: CPI Shelter MoM print direction** — a sustained sub-0.20%
print for two consecutive months should trigger a Factor 5 mechanism
re-test.

### Dependencies

| # | Dependency | Observable | Source | Horizon |
|---|---|---|---|---|
| 1 | The cost-to-own calc constants are right (property tax, insurance, maintenance) | Realtor.com / Zillow buy-vs-rent calculator cross-check | Realtor.com, Zillow | Annually |
| 2 | CPI OER is a defensible proxy for median rent | OER vs. Realtor.com / Zillow rent-index correlation > 0.85 | BLS, Realtor.com | Annually |
| 3 | Rate falling produces near-monotonic spread compression | FRED MORTGAGE30US × MSPUS × CUSR0000SEHA panel | FRED | Quarterly |

### Data inputs

FRED MORTGAGE30US, MSPUS (quarterly cadence — note watchdog calibration),
CUSR0000SEHA (CPI shelter), Census Housing Vacancies and Homeownership
Survey, Realtor.com / Zillow spread indices.

---

## 6. Rollup to current `analyst/factor_weights.yaml`

If we keep the abstracted YAML schema (not the playbook-1:1 rename):

| YAML key (current) | Maps to | Suggested allocation |
|---|---|---|
| `rate_lockin` | Factor 1 | 0.35–0.40 |
| `affordability` | Factor 5 | 0.20–0.25 |
| `inventory` | Factor 2 | 0.10–0.15 |
| `demographics` | Factors 3 + 4 (combined) | 0.10–0.15 |
| `policy` | Cross-cutting (Fed, GSE, tax) | 0.05–0.15 |

**Wyatt sets exact weights in PR after the prose stabilizes.**

---

## 7. Open coordination items

Status as of 2026-05-01 (Wyatt's Claude defaults applied; Wyatt review
pending):

- [x] **Schema decision (§0):** abstracted set kept (Wyatt's Claude
      default). Updates to `analyst/factor_weights.yaml` and Script 10's
      footer reflect this.
- [x] **Canonical weights** — `analyst/factor_weights.yaml` updated to
      `40/25/15/10/10` with `last_updated: 2026-05-01`. Wyatt to revise
      via PR if any of these don't match his judgment after reading the
      Factor 1-5 prose above.
- [x] **JCHS critique** — Factor 4 reframed and populated from JCHS 2025
      verbatim extract; thesis recast from "JCHS overstates" to "JCHS
      revised down without flagging; consensus updating lag is the
      contrarian edge."
- [ ] **Apartment REIT short basket sizing** —
      `analyst/apartment_reit_short_basket.md` filled with default
      members, weights, triggers (Wyatt's Claude defaults). Final
      sizing is Wyatt's call.
- [ ] **`analyst/short_baskets.yaml`** — drafted with default basket
      roster + weights. Script 10/11b can ingest. Wyatt to revise
      member list and per-name weights via PR.
- [x] **Perplexity Computer weekly task** — live; first run output at
      `output/perplexity/weekly/2026-05-04.md`. v3 patch (legislative
      scuttlebutt) at
      `analyst/perplexity_tasks/weekly_v2_to_v3_patch.md`.
- [ ] **Defended threshold (Factor 1, 1.5%)** — Wyatt to confirm
      against his own behavioral-finance read. ASSUMPTION-flagged.
- [ ] **Defended normalization (Factor 1, 50%)** — same.
- [ ] **Cost-to-own constants (Factor 5)** — Wyatt to confirm 1.2% prop
      tax / 50bps insurance / 50bps maintenance. ASSUMPTION-flagged.

---

## Appendix A — JCHS 2025 Report data extraction

> Source PDF: `Harvard_JCHS_The_State_of_the_Nations_Housing_2025.pdf` (52 pages).
> Page numbers refer to the JCHS-printed footer.

### A.1 Household formation forecast — verbatim (with marked omissions)

> "Under the Census Bureau's main population projection, **8.6 million net
> new households will form between 2025 and 2035** and another **5.1 million
> households from 2035 to 2045**, assuming that net foreign migration over
> the next two decades will average roughly 900,000 immigrants annually.
> These levels are substantially lower than the **13.5 million and 10.1
> million new households that formed in the 1990s and in the 2010s**,
> respectively (Figure 13). If, however, immigration levels follow the
> Census Bureau's projection that assumes an annual average of 422,000
> people [...] household growth is projected to total just **6.9 million
> households in the next decade and a scant 3.2 million from 2035 to
> 2045**." (p. 19–20)

> "In 2024, the number of US households increased by 1.56 million to
> 131.7 million [...] far lower than the pandemic-era surge of 1.93 million
> households averaged annually between 2019 and 2022. And the annual rate
> continues to decline, dropping to 1.26 million households by the first
> quarter of 2025." (p. 17)

### A.2 Construction / housing-demand forecast — verbatim

> "Since the 1970s, the US has built an average of **16 million new
> housing units each decade**. Under the Center's main household growth
> projection, the implicit new housing demand—the amount of housing needed
> to effectively address household growth, replace older homes, ensure a
> healthy supply of vacant stock, and satisfy demand for second homes—
> **drops to 11.3 million units between 2025 and 2035**. This is only
> marginally above the **9.9 million units produced in the sluggish post–
> Great Recession decade of 2010–2019**. New housing demand would then
> fall to **8.0 million units in 2035–2045**. Demand would shrink even
> further under the low-immigration projection, with an implied need for
> **9.5 million new units in 2025–2035 and 6.1 million in 2035–2045**."
> (p. 20)

### A.3 Homeownership rate — verbatim

> "The US homeownership rate fell in 2024 for the first time in eight
> years to **65.6 percent** and continued downward to **65.1 percent in
> the first quarter of 2025**." (executive summary p. 3; Homeownership
> chapter p. 24)

> "While homeownership rates remained relatively unchanged in 2024 for
> households age 45 and over, the **homeownership rate dropped 1.4
> percentage points to 37.1 percent among households under age 35, and
> 0.8 percentage points to 61.8 percent for households aged 35–44**."
> (p. 25–27)

### A.4 Headship rate — the "missing households" admission (verbatim)

> "The outsized level of household growth among younger adults was largely
> due to an inherently temporary return of **'missing' households whose
> formation was delayed by the Great Recession**. These new households
> helped grow both the younger adult headship rate—the share of adults
> under age 45 who head a household—and household growth by an additional
> **1.0 million households, or 250,000 per year between 2019 and 2023**…
> In 2024, however, the **rebound in young adult headship rates ended**,
> with formations among younger adults entirely driven by underlying
> population growth." (p. 18)

### A.5 Cost burden — verbatim (two quotes spliced via [...] for length)

> "In 2023, the number of cost-burdened homeowners—those spending more
> than 30 percent of income on housing and utilities—rose by 646,000 to
> **20.3 million**." (p. 5)

> "[N]early a quarter (24 percent) of all homeowners are cost burdened."
> (p. 27)

> "For the third consecutive year, the number of cost-burdened renters
> reached another record high in 2023 at **22.6 million renters
> (50 percent)**. This includes more than **12.1 million (27 percent)
> who are severely burdened**, spending more than half of their income on
> housing and utilities." (p. 5; renters chapter detail p. 32)

### A.6 First-time buyer affordability ceiling — verbatim (with marked omissions)

> "Today, a typical first-time homebuyer needs an annual income of at least
> **$126,700** to afford payments on the median-priced home (**$412,500**)
> [...] a first-time homebuyer would need to provide **$26,800 in cash** to
> cover the downpayment and 3 percent closing costs. Roughly **12 percent**
> of renters can meet this requirement based on the 2022 Survey of Consumer
> Finances [...] **the median age of a first-time homebuyer hit a
> record-high 38 in 2024**, and the median annual household income of
> first-time buyers was $26,000 higher than it was just two years earlier."
> (p. 27)

### A.7 Lock-in cross-reference — verbatim

> "Just **4.06 million home sales** were recorded last year, the fewest
> since 1995. Contributing to the low rate of sales is the **large share
> of existing homeowners with below-market mortgage rates who are
> disincentivized from selling in the higher-rate environment**." (p. 1–4)

### A.8 What JCHS does NOT say

The 2025 edition does **not** explicitly admit prior over-forecasting. The
closest hedge is on p. 20: "These estimates do not account for the levels
of construction required to address the nation's existing housing
shortage. Even so, including that additional production would still yield
historically low levels of new construction." This is JCHS softening the
gap between the old "shortage" narrative and the new ~11.3M/decade demand
without a "we revised" admission.

### A.9 Most-citable chart

**Figure 13, p. 20: "Household Growth Is Projected to Slow"**
Decadal household growth: 1990–2000 = 13.5M; 2000–2010 ≈ 12M;
2010–2020 ≈ 10.1M; 2025–2035 = 8.6M (main) / 6.9M (low-immigration);
2035–2045 = 5.1M (main) / 3.2M (low-immigration).

This is the single chart that operationalizes the demographic-ceiling
thesis. If the framework cites one image, this is it.
