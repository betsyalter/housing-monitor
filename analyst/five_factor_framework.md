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

**Recommendation:** mirror the playbook 1:1. The current YAML double-counts
factors 3 and 4 inside one weight (`demographics`), which makes any future
re-weighting ambiguous. Renaming costs us: a one-line update in
`scripts/lib/yaml_config.py` (the validator) and a footer regeneration in
Script 10.

**Wyatt to decide:**
- [ ] Mirror playbook 1:1 (rename keys → `rate_lockin`, `reit_absorption`,
      `second_home_turnover`, `demographics_ceiling`, `rent_own_spread`,
      drop `policy` or keep as a 6th dimension).
- [ ] Keep the abstracted set (rate_lockin / affordability / inventory /
      demographics / policy) and document the rollups inside this file.

The factor-by-factor sections below are written under the **playbook 1:1
naming**. Translation back to the abstracted YAML is in §6.

---

## Factor 1 — Rate Lock-In

> The cyclical core of the thesis. Most owners hold a sub-4% mortgage; the
> 30yr is at 6.30%. Moving means trading the sub-4% asset for a market-rate
> liability. Above some threshold, that trade-off is too expensive to take —
> so they don't move, existing-home turnover collapses, and pent-up volume
> accumulates.

**Placeholder weight:** 0.40

**Mechanism (one paragraph, Wyatt to refine).**
Owners decide whether to move based on the spread between their current
mortgage rate and the prevailing 30yr rate available to them. When that
spread exceeds a threshold (~150–200 bps in the current model), the implicit
cost of trading rates exceeds the benefit of moving for most households.
Volume collapses. As market rates fall, owners with progressively-lower
locked rates cross back into "willing to transact" territory — first the
recently-locked (5%+), then the mid-cycle (4–5%), then the deeply-locked
(<4%) only at extreme rate retracement.

**Math (codified — see `lib/coiled_spring.py`).**
- Threshold: `market_rate > current_rate + 1.5` ⇒ locked.
- Distribution: FHFA mortgage rate buckets (`analyst/coiled_spring_params.yaml`).
- At market 6.5% with the current distribution: ~41.5M locked, ~9.2M unlocked.
- Each 25 bps drop releases the bucket whose midpoint crosses the threshold.

**Anchors needed (from Wyatt):**
- [ ] **Defend the 1.5% threshold.** Cite behavioral / mover-survey evidence
      or a published model. Plausible alternates: 1.0% (more permissive),
      2.0% (stricter). The choice is load-bearing.
- [ ] **Define "50% normalization."** Earlier framing (in Wyatt's notes)
      assumed half of locked owners eventually transact. Why 50%? Why not
      30% or 70%? An empirical anchor would be: pre-2022 turnover rate vs
      a normalized baseline. NAR existing-home sales 2015–2019 averaged
      ~5.3M/yr; today's pace is ~4.0M/yr — that's a ~25% deficit, suggesting
      ~50% normalization unlocks the deficit + some.
- [ ] **Interaction with policy levers.** Assumable mortgage reform
      (FHFA could expand assumability beyond VA/FHA), capital-gains exclusion
      expansion (currently $250k single / $500k joint, set in 1997, never
      indexed). Both increase the value of moving for locked owners. Wyatt
      to estimate sensitivity.

**Data inputs:**
`data/fhfa_distribution.csv`, FRED MORTGAGE30US, `lib/coiled_spring.py`,
`analyst/coiled_spring_params.yaml`.

**Cross-reference:** Factor 5 (rent-own spread) is partially endogenous to
Factor 1 — when rates fall, both lock-in eases AND ownership cost falls,
compounding the unlock effect. The framework should not double-count this.

---

## Factor 2 — REIT Absorption (Single-Family)

> The structural one. Institutional SFR REITs (INVH, AMH, primarily) acquired
> ~150k+ existing single-family homes between 2012 and 2022, removing them
> from the owner-occupied inventory permanently. The acquisition wave is the
> bigger structural effect; ongoing turnover differential is secondary.

**Placeholder weight:** TBD (currently rolled into `inventory: 0.15`)

**Mechanism.**
Two distinct effects, often conflated:
1. **Acquisition (2012–2022).** Permanent removal of N homes from
   owner-occupied stock. This shifted the supply curve down once.
2. **Turnover differential (ongoing).** Owner-occupied homes turn over at
   ~5%/yr; REIT-held homes turn over at <3%/yr. Each year of differential
   turnover moves a small additional slice of stock out of "willing seller"
   status.

The acquisition effect is order-of-magnitude larger than the differential.
But it's a one-time level shift — it doesn't grow over time. The
differential is the recurring drag.

**Math (Wyatt to fill).**
- [ ] Total SFR REIT-held stock as of latest 10-K (use `data/sec_reit_homes.csv`):
      INVH, AMH, ELS, SUI, INVS-equivalents. Sum, dedup overlap.
- [ ] What % of single-family owner-occupied stock does that represent?
      (US owner-occupied housing stock ~83M units → REIT share ~0.2%.)
- [ ] Turnover differential math: `(0.05 − 0.03) × stock_held` = annual
      "stuck" inventory growth. At ~150k stock × 2% diff = ~3k homes/year.
      That's small in absolute terms — argue whether it's signal or noise.

**Open questions for prose section:**
- Is the SFR REIT effect actually structural, or did the 2022 rate spike
  freeze their acquisitions and make them effectively net-zero / net-sellers?
  Check most recent 10-Q acquisition vs disposition counts.
- What's the right anchor for "stuck inventory" — gross homes held, or
  net of natural turnover? The math above uses gross.

**Data inputs:**
`data/sec_reit_homes.csv` (Betsy's `06_sec_reit_properties.py`),
American Community Survey owner-occupied stock, NAR median tenure stats.

---

## Factor 3 — Second/Third Home Turnover

> Demographic stickiness layer 1. Second-home owners (~7M units, ~6% of
> housing stock) move at materially lower rates than primary residents.
> Third-home owners (much smaller cohort) move even less. As wealth has
> concentrated in the cohort that holds multi-property portfolios, this
> effect has grown.

**Placeholder weight:** TBD (currently rolled into `demographics: 0.10`)

**Mechanism.**
Second-home turnover is ~2-3%/yr vs ~5%/yr for primary residences (Census
American Housing Survey, periodic). Two reasons:
1. Vacation/seasonal homes don't have a "growing family / job change /
   downsize" turnover trigger the way primary residences do.
2. Tax basis lock-in: capital-gains exclusion ($250k/$500k) only applies to
   primary residences, so 2nd-home owners face full long-term cap gains on
   sale → strong tax disincentive to sell.

**Math (Wyatt to fill).**
- [ ] Second-home stock from Census AHS (most recent edition).
- [ ] Implied annual "stuck" volume vs counterfactual primary-residence
      turnover: `(0.05 − 0.025) × second_home_stock`. At 7M × 2.5% diff ≈
      175k homes/yr that don't transact.
- [ ] Compare to total existing-home sales (~4M/yr) — this is ~4% of annual
      volume.

**Open questions:**
- Does this overlap with Factor 1 (rate lock-in) — i.e., is a lower-rate
  2nd-home owner double-locked? Probably yes; the math should subtract the
  Factor 1 contribution to avoid double-counting.

**Data inputs:**
Census American Housing Survey, IRS SOI (capital gains realizations on
real estate), NAR Profile of Home Buyers and Sellers.

---

## Factor 4 — Demographics & Homeownership Ceiling (the JCHS Critique)

> The big skeptic factor — and the JCHS 2025 report partially flips its
> own framing. The 2025 edition forecasts dramatically slower household
> growth than prior editions (8.6M for 2025–2035 vs the ~12-13.5M pace of
> the 1990s/2010s) without explicitly acknowledging the revision. The new
> data both supports and reframes Wyatt's thesis: JCHS has effectively
> walked back the "shortage" narrative, but consensus opinion (builders,
> lenders, Wall Street REIT theses) is still pricing the old forecasts.

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
   without a "we revised" admission. (See Appendix A item 7.)

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

**Anchors needed (from Wyatt):**
- [ ] **Decide whether to recast the thesis.** The original Wyatt framing
      ("JCHS overstates demand") doesn't quite fit the 2025 data. A more
      defensible framing is: *"JCHS quietly revised the demand forecast
      downward 30%+ but the broader shortage narrative hasn't caught up."*
      That's still a contrarian view; it's just contrarian in a different
      direction.
- [ ] **Implication for SFR REIT shorts (Factor 2 and Tier 4 basket).**
      If household growth is structurally lower, SFR REIT NOI growth
      assumptions are too high. This is a direct read-across.
- [ ] **Counter-argument to engage.** JCHS could be over-correcting in the
      opposite direction now — the post-COVID slump may be the temporary
      effect, and headship rates could mean-revert. What's the strongest
      version of that bull case?
- [ ] **Decide whether the original "15–25% overstatement" anchor still
      stands.** It's a vintage-2023 number; the 2025 JCHS revision
      arguably resolves it. Either delete the claim or recast as
      "historical overstatement, now corrected."

**Data inputs:**
JCHS State of the Nation's Housing 2025 (Wyatt has the PDF, see Appendix A
for the full extract), Census ACS headship rates by age cohort, BLS
Consumer Expenditure Survey, NAR existing-home-sales series.

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

**Math (specify exact calc — Wyatt to confirm).**
```
cost_to_own_monthly =
    median_home_price × 0.80 × pmt(MORTGAGE30US, 360 months)    # P&I on 80% LTV
    + median_home_price × 0.012 / 12                             # property tax (1.2% effective)
    + median_home_price × 0.005 / 12                             # insurance (50 bps)
    + median_home_price × 0.005 / 12                             # maintenance reserve

cost_to_rent_monthly = CUSR0000SEHA  # CPI owners' equivalent rent (per unit)

spread = cost_to_own − cost_to_rent
```

**Anchors needed (from Wyatt):**
- [ ] Historical spread distribution: 1990–2024. What's the threshold spread
      that triggers a 10% / 25% / 50% behavioral shift among first-time buyers?
- [ ] Use FRED HOUST × homeownership rate to back out the implied
      "first-time buyer share" elasticity to spread.
- [ ] Right-size the property tax / insurance / maintenance bps. The numbers
      above are placeholders.

**Data inputs:**
FRED MORTGAGE30US, MSPUS, CUSR0000SEHA (CPI shelter), Census HMS,
Realtor.com / Zillow spread indices.

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

- [ ] Decide schema (§0). Communicate to Betsy via Slack so she can wire
      Script 10's footer rewrite.
- [ ] When weights are finalized, PR `analyst/factor_weights.yaml` with
      canonical values + `last_updated: "YYYY-MM-DD"`.
- [ ] Apartment REIT short basket — see `analyst/apartment_reit_short_basket.md`
      for sample format and the format-options discussion.
- [ ] Perplexity Computer weekly task — kickoff timing TBD.
- [ ] JCHS critique — depth depends on whether 2025 report acknowledges
      prior over-forecasts. Subagent extraction in Appendix A.

---

## Appendix A — JCHS 2025 Report data extraction

> Source PDF: `Harvard_JCHS_The_State_of_the_Nations_Housing_2025.pdf` (52 pages).
> Page numbers refer to the JCHS-printed footer.

### A.1 Household formation forecast — verbatim

> "Under the Census Bureau's main population projection, **8.6 million net
> new households will form between 2025 and 2035** and another **5.1 million
> households from 2035 to 2045**, assuming that net foreign migration over
> the next two decades will average roughly 900,000 immigrants annually.
> These levels are substantially lower than the **13.5 million and 10.1
> million new households that formed in the 1990s and in the 2010s**,
> respectively (Figure 13). If, however, immigration levels follow the
> Census Bureau's projection that assumes an annual average of 422,000
> people… household growth is projected to total just **6.9 million
> households in the next decade and a scant 3.2 million from 2035 to
> 2045**." (p. 19–20)

> "In 2024, the number of US households increased by 1.56 million to
> 131.7 million… far lower than the pandemic-era surge of 1.93 million
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
> the first quarter of 2025**." (p. 6, p. 9)

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

### A.5 Cost burden — verbatim

> "In 2023, the number of cost-burdened homeowners—those spending more
> than 30 percent of income on housing and utilities—rose by 646,000 to
> **20.3 million**… nearly a quarter (24 percent) of all homeowners are
> cost burdened." (p. 5, p. 27)

> "For the third consecutive year, the number of cost-burdened renters
> reached another record high in 2023 at **22.6 million renters
> (50 percent)**. This includes more than **12.1 million (27 percent)
> who are severely burdened**, spending more than half of their income on
> housing and utilities." (p. 5, p. 32)

### A.6 First-time buyer affordability ceiling — verbatim

> "Today, a typical first-time homebuyer needs an annual income of at least
> **$126,700** to afford payments on the median-priced home (**$412,500**)
> … a first-time homebuyer would need to provide **$26,800 in cash** to
> cover the downpayment and 3 percent closing costs. Roughly **12 percent**
> of renters had this much in cash savings as of 2022… **the median age of
> a first-time homebuyer hit a record-high 38 in 2024**, and the median
> annual household income of first-time buyers was $26,000 higher than it
> was just two years earlier." (p. 27)

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
