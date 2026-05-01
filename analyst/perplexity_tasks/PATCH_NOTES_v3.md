# Weekly Housing Monitor — Spec Patch Notes v3 (apply before next run)

> Applied 2026-05-01. Supersedes v1 (initial spec) and v2
> (post-first-run audit, four fixes). Adds depth standard from
> the data-center industry market-map benchmark (form, not content)
> and standing admin/legislative intel mandate. Re-anchored to the
> seven structural questions in `docs/og_prompt.txt`. Source of
> truth on `main` always wins; this file documents what changed.

## Carry-over from v2 (still in force)

1. No length cap. Length is quality-driven; write what substance warrants.
2. Named-person attributions need a primary-source URL or `[unsourced]` inline.
3. §7 schema is a minimum, not a maximum.
4. Framework SHA must be retrieved (`gh api ... --jq .sha`), never invented.

---

## v3 anchor: the seven questions in `docs/og_prompt.txt`

Every report must read like an answer to these questions, updated
with this week's evidence. The data-center benchmark sets the
*depth* standard; the questions below set the *content* standard.

1. **Q1 — Structural vs cyclical decomposition of the EHS collapse.**
   Existing-home sales SAAR ~4M vs the 5M long-run norm. How much
   of the 1M gap is cyclical (rate lock-in) vs structural (REIT
   absorption, 2nd/3rd-home holding, demographic ceiling, rent-own
   spread)? This is the central question; every weekly report must
   carry an updated decomposition (table with % attribution to
   each of the five factors), even if the attribution moves only
   marginally week-to-week. Movements >5pp QoQ are themselves a
   reportable signal.

2. **Q2 — The coiled-spring math.** What 30yr mortgage rate threshold
   unlocks materially-stuck inventory? At today's rate, what %
   locked, what SAAR uplift at each 25bp / 50bp / 100bp / 150bp
   step lower? Report the live unlock-curve every week. Cross
   these thresholds, you're in a different regime — the report
   must say so.

3. **Q3 — Inventory paradox.** Inventory rising is *good* for sales
   velocity (paradoxically — opposite of 2005-2007). The report
   must distinguish "inventory rising because supply unlocking
   (bullish)" vs "inventory rising because demand collapsing
   (bearish)" using months-of-supply, price-cut share, days-on-market,
   list-to-sale spread, and new-listings flow.

4. **Q4 — Rent-own spread direction.** Rents are the lagging
   deflationary print, with offsets from oil / shelter CPI / wage
   growth. Track the spread weekly; flag inflection. Bridge to
   apartment REIT short basket explicitly.

5. **Q5 — The 400+ ticker downstream cascade.** Map the trade by
   bottleneck, name 2nd-order and 3rd-order beneficiaries by ticker.
   The data-center deck's "second/third-order beneficiary cheat
   sheet" is the form — a housing version, refreshed weekly to
   reflect *this* week's binding constraint, is the requirement.

6. **Q6 — Political economy / legislative unlock.** "Getting housing
   moving again is probably extremely important for the incumbent
   admin to try to get their voter approval count up prior to either
   midterms or 2028." The Admin & Legislative Pipeline section
   (Change 5 below) is the standing scope.

7. **Q7 — Macro path-dependence.** Oil → CPI → Fed path → mortgage
   rates is the chain. Iran-driven oil makes the Fed stuck; if oil
   eases (or if structural deflation shows through despite oil), Fed
   gets room. Track the chain weekly; specifically flag any oil /
   CPI / Fed-personnel surprise that changes the path.

---

## Change 5 — Standing Admin & Legislative Pipeline section (mandatory)

Principal directive (Wyatt, 2026-05-01): "I strongly suspect the
admin may try to do legislative actions to jumpstart the housing
market in spite of currently high mortgage rates. We should be
staying up on anything that might be coming down the pike
legislatively, hopefully detecting what's going on before it
splashes all over the tape."

Required scope each weekly run:

- Trailing 7 days, scour: whitehouse.gov, OMB/DPC press, executive
  orders (federalregister.gov), Treasury, HUD, FHFA, CFPB, USDA-RD,
  OCC/FDIC/Fed regulator releases, GSE conservator actions
  (Fannie/Freddie capital framework, conservatorship-release
  signals), congress.gov (House Financial Services + Senate Banking
  schedules, hearings, draft markups), DC trade press promoted to
  TRUSTED in `analyst/news_sources.yaml`: Politico Pro Housing,
  Punchbowl News, Roll Call, The Hill, HousingWire, Inman,
  Inside Mortgage Finance, MBA, NAHB official, Bloomberg Government,
  Axios Pro Housing. Trial balloons from admin-aligned policy shops
  (Heritage, AEI Housing Center, Manhattan Institute).
- Bucket findings: **ON-TAPE** (announced) / **IN-MOTION**
  (drafted/leaked/floated) / **SCUTTLE** (single-source rumor with
  named originator). Each item must record: date, URL, originator,
  mechanism, affected factor (rate-lockin / supply / demand /
  credit-box / tax), stage (rumor → floated → drafted → introduced
  → markup → passed → signed/effective), thesis-impact direction
  (+/0/−), confidence (Confirmed / Reported / Plausible /
  Speculative).
- Flag anything that could land before next Monday market open.
- Maintain a running log at `output/perplexity/policy_pipeline.md`
  — append-only, never overwrite, mark stage transitions with
  timestamps. Weekly section is curated read; log is durable record.

Mechanisms specifically to watch (housing-unlock policy levers):

- GSE conservatorship release / capital framework changes; Fannie/Freddie privatization mechanics
- LLPA (loan-level pricing adjustment) modifications
- FHA mortgage insurance premium cuts / FHA loan limit increases
- Conforming loan limit increases above the standard FHFA formula
- Mortgage interest deduction expansion / restoration of pre-TCJA caps
- First-time homebuyer tax credit (per 2024 platform proposals — $25K-$50K)
- Down-payment assistance grants (federally funded)
- Treasury/HUD-funded 2-1 or 3-2-1 buydown subsidies
- §121 capital gains exclusion expansion ($250K/$500K limits unchanged since 1997, badly nominal-eroded)
- §1031 like-kind exchange rules
- Opportunity Zone reauthorization / expansion
- LIHTC (Low Income Housing Tax Credit) expansion
- HUD/USDA-RD rural housing program expansion
- Federal land transfers for housing supply (admin rhetoric on BLM/USFS land)
- IRS/Treasury rulings on rental depreciation, REIT structure changes
- CFPB enforcement-posture shifts that loosen credit
- Bank regulator (OCC/FDIC/Fed) capital relief that frees mortgage origination
- QM (Qualified Mortgage) rule amendments
- Agency-MBS purchase resumption (Fed balance sheet)
- VantageScore 4.0 / FICO 10T full implementation timeline
- DTI / LTV regulatory ceiling changes

---

## Change 6 — Data-center-deck depth standard, ported to housing

Reference: `data-center-industry-market-map.pdf`. The benchmark sets
the *form*; the housing content is original. Apply these techniques.

### 6a. Layered value-chain map (required section, refreshed weekly)

Every report must contain a **Housing Value Chain Map** that segments
the housing supply/demand stack into named layers, with named
tickers, and identifies the **binding constraint this week**. The
data-center deck's central insight is that bottlenecks migrate —
GPUs → packaging → transformers → grid. The housing equivalent is
the same idea: rates → credit box → builder margin → land cost →
labor → insurance → buyer income — and each migration creates a
different set of winners and losers.

Suggested layers (extend / contract as warranted; full universe in
`data/fmp_tickers.csv`):

1. **Rate complex & MBS funding plumbing** — UST curve, MBS-Treasury OAS, primary-secondary spread, OIS-implied Fed path, agency-MBS gross issuance vs runoff, FHLB advance volume, Ginnie servicer liquidity, dollar-roll specialness.
2. **Mortgage origination layer** — UWMC, RKT, LDI, COOP, PFSI, GHLD; channel mix (wholesale vs retail, IMB vs depository), refi vs purchase, MBA pipeline depth, capacity vs demand.
3. **Existing-home transaction layer** — RMAX, COMP, EXPI, HOUS, ZG, RDFN, OPEN; volume, listing flow, cancel/relist, agent count, commission compression post-NAR settlement.
4. **New-home production (homebuilders)** — Tier-1 (DHI, LEN, NVR, PHM, TOL) + secondary (LGIH, MTH, MHO, TPH, KBH, BZH, MDC, GRBK, CCS, IBP, SKY, CVCO, LSEA, HOV); ASP, orders, cancel rate, gross margin, owned-vs-optioned land book, JV/option strategy, community count, SG&A, incentive load.
5. **Building products & materials** — BLDR, BCC, EXP, SUM, MLM, VMC, MAS, FBHS, LII, AOS, WHR, WSO, FAST, PGTI, JELD, AMWD, IBP, TREX, AZEK; volume/ASP split, lumber/cement, tariff exposure, repair-remodel mix.
6. **Title, mortgage insurance, settlement services** — FAF, FNF, STC, ESNT, MTG, NMIH, RDN, ACT; revenue per closing, defect rates, claims trend.
7. **Apartment / multifamily REITs (the involuntary-renter beneficiaries)** — EQR, AVB, MAA, CPT, UDR, ESS, IRT, AIRC, NXRT, BRT; concession rate, lease trade-out, occupancy, supply absorption, Sun Belt vs Coastal divergence.
8. **SFR / build-to-rent (the supply-absorption story)** — INVH, AMH, ROIC, Tricon (private), Pretium / Roofstock SFR ABS issuance.
9. **Manufactured / specialty / 55+** — SUI, ELS, UMH, CVCO, SKY, LSEA.
10. **Senior housing & medical** — WELL, VTR, SBRA, CTRE, NHI.
11. **Insurance, climate, tax cost-of-ownership** — Florida/California insurer exits, NFIP reauthorization, FEMA flood maps, reinsurance pricing, state-level reassessment cycles, prop-tax-as-share-of-PITI.
12. **Mortgage REITs / agency / non-agency credit** — NLY, AGNC, TWO, PMT — for the funding-side read.

The text must explicitly name the **binding constraint this week**
and explain what shifted vs prior weeks. Layer-by-layer numeric
anchors (one citable data point per layer minimum) are required.

### 6b. Per-name vignettes — backlog/order-book numerics

Like the data-center deck does for Vertiv ($15B backlog), Caterpillar
($51B +71% YoY), GE Vernova (83 GW on order), each named stock
signal must include:

- **Backlog or pipeline number** (units / $ / community count) with QoQ trajectory
- **Cohort positioning** (vs Tier-1 peers) — share gain/loss on the relevant operating metric
- **Specific moat or fragility statement** (one-line, citable) — e.g., NVR's option-only land model; LGIH's FHA buyer concentration; UWMC's wholesale-channel dependence
- **Insider / capital-allocation overlay** (buybacks, JV writedowns, lot walkaways, secondary offerings, inside-sale clusters)
- **Counter-read** — the specific bull or bear case opposing your read, with why our read still wins (or whether it's a coin flip)

### 6c. Bottleneck → 2nd-order → 3rd-order cheat sheet (required section)

Every report ends with a housing-specific decomposition table of the
*current binding constraint* into beneficiary tiers. Refresh
weekly to match this week's binding constraint — never boilerplate.

Schema example (illustrative — fill fresh each week):

| Bottleneck | 2nd-Order Beneficiary | 3rd-Order Spillover |
|---|---|---|
| Rate lock-in releases | Volume builders (DHI, LEN), originators (UWMC, RKT) | Title (FNF, FAF), MI (ESNT, MTG), brokerage tech (ZG, COMP) |
| FHA MIP cut | LGIH, MTH (FHA-heavy) | NMIH, RDN, MTG; subprime-adjacent originators |
| GSE LLPA cut | Originators with high LMI mix (UWMC) | Builders with FHA-eligible inventory; servicers |
| Conforming loan limit ↑ | Move-up market (TOL, NVR) | Title, jumbo originators |
| §121 cap raise | Move-up + downsizer flows | RMAX, real-estate services, title |
| Insurance backstop / NFIP | Coastal-exposed builders | FL/CA insurance brokers |
| Federal land transfers | Western/SW builders (LGIH, MTH) | Site-development EPC |
| MBS-Treasury spread tightening | Mortgage REITs (NLY, AGNC) | Servicers (COOP, PFSI), originators |
| Insurance unaffordability | Manufactured (SUI, CVCO, ELS) | Inland-shift builders, MH lenders |
| Builder-incentive exhaustion | NVR, TOL (low-incentive history) | Tier-2 share donors → Tier-1 |

The table is *the analytical synthesis* — it converts the binding
constraint into a watch list and is where most of the alpha lives.

### 6d. Three-risk explicit framing (required, replaces v1 single-risk)

Like the data-center deck's three explicit risks, each report closes
with **three concrete risks**, each with:

- Falsifiable threshold metric ("if 30yr crosses 7.25%" / "if cohort
  cancel rate exceeds 28%" / "if HPI YoY turns negative")
- Mechanism (which factor breaks)
- Specific watch trigger (which release / filing / data point
  would confirm)

### 6e. Bottleneck-migration narrative (required paragraph)

The data-center deck's most replicable insight: bottleneck migrates.
Each weekly report must include an explicit paragraph naming where
the binding constraint has migrated *to* and *from* over the last
few weeks. Examples of housing-bottleneck migration: rates → credit
box (2024); credit box → land/lot supply (mid-2024); lot supply →
buyer income/affordability (2025); affordability → insurance cost
(coastal, 2025-26). State the current location; trace where it came
from.

---

## Change 7 — Required sections (expanded list)

Required (minimum, may extend):

- Executive summary (3 bullets)
- **Bottom line / binding constraint this week** (one paragraph)
- **Bottleneck-migration paragraph** (where the constraint moved to/from)
- Factor scorecard (with confidence column — Change 8)
- **Five-factor attribution table** (Q1: % of EHS gap attributed to each factor, with WoW delta)
- Macro delta vs trailing 4w / 13w / 52w baselines (Change 10)
- Coiled-spring status with full unlock-curve table (Q2)
- **Rate complex & MBS funding read** (UST curve / MBS-Treasury / OIS / Ginnie / FHLB / dollar-roll)
- **Inventory paradox read** (Q3 — distinguish supply-unlock vs demand-collapse)
- **Rent-own spread + apartment-REIT bridge** (Q4)
- **Housing value chain map** (Change 6a — layered, with binding constraint)
- Stock-level signals (multi-paragraph each, with backlog/cohort/moat/insider/counter — Change 6b)
- Homebuilder cohort table + most-surprising-data-point analysis
- **Builder land-book read** (owned vs optioned ratios, JV writedowns, lot walkaways, impairments)
- **Mortgage origination channel mix** (wholesale vs retail, IMB vs depository, refi vs purchase)
- **Existing-home supply micro-read** (Realtor.com active listings WoW, Redfin new-listings WoW, price-cut share, DOM, list-to-sale spread)
- Subsector basket dispersion analysis
- **Apartment / multifamily basket read** (concession rate, lease trade-out, occupancy, Sun Belt vs Coastal)
- **SFR / BTR basket read** (institutional-SFR REITs + ABS issuance, REIT acquisition pace)
- Correlation rankings — name-level thesis exposure validation
- **Insurance & climate update** (when material)
- Material policy / legislative events (each with date, factor, direction, source URL)
- **Admin & Legislative Pipeline** (Change 5 — on-tape / in-motion / scuttle, pre-Monday-open flags)
- **Sell-side rolling tracker** (initiations / upgrades / downgrades / PT changes on Tier-1 builders, originators, REITs, title)
- **Earnings calendar — forward 2 weeks** (what's reporting + consensus EPS/rev + key KPI watch-items)
- **Macro chain check (Q7)** (oil → CPI → Fed path → 30yr mortgage; flag any link break)
- **Three risks** (Change 6d — each falsifiable threshold + mechanism + watch trigger)
- Underappreciated catalyst (multi-paragraph, evidence threshold = ≥1 citable data point AND ≥1 citable consensus that misses it; with time-to-tape tag — Change 9)
- **Second/third-order beneficiary cheat sheet** (Change 6c — refreshed table)
- **Cross-asset confirmation panel** (HG copper, lumber futures, crude, DXY, USTs, IG/HY credit; does the housing read agree?)
- **"What we got wrong last week"** (look back at last week's risk + catalyst + factor scores; did thresholds get hit; did catalyst materialize)
- What would change my mind this week (4-6 specific data points)
- Data integrity flags
- Sources (full URL list)

---

## Change 8 — Confidence-weighted factor scoring

Factor scorecard: signal | strength | direction | **confidence**
(high/med/low). Propagate to JSON sidecar
`factor_scorecard[].confidence`.

## Change 9 — Time-to-tape tag

Every catalyst, risk, and admin-pipeline item carries: **this week
/ this month / this quarter / longer**. Forces specificity.

## Change 10 — 4w / 13w / 52w deltas

Macro delta table now shows three windows. 4w = inflection; 13w =
mean-reversion; 52w = regime drift.

## Change 11 — Reference-report awareness

When `docs/reports/` contains third-party research, read
`docs/reports/README.md` first. **Use the data, not the analyst
conclusions.** Specifically (per 2026-05-01 push):

- **Apollo deck (Slok, FILE_4211.pdf)**: empirical anchors for the
  structural map — 95% 30yr fixed, >50% locked sub-4%, 2.4M home
  deficit, median buyer age 59 (vs 31 in 1981), first-time buyer
  age 40 (vs 30 in 2008), median sales price $403K, "fastest
  Fed-driven slowdown on record." Cite slide #s. These calibrate
  Q1 / Q2 / Q3.
- **DHI sell-side (5 notes)**: use BTIG / Wells / Morningstar
  order/backlog/cancel commentary to calibrate `homebuilder_ops.csv`
  Q1 2026 data for DHI specifically. Note explicit deviations from
  Street consensus as reportable signals. **Do not adopt Street
  conclusions** — our read is the value-add; their data is the
  cross-check.
- **Coverage gaps**: no equivalent for LEN, NVR, PHM, TOL, or the
  apartment REIT basket. Note in data integrity flags when
  references are absent.

---

## Why these eleven (now total)

The first run produced ~4,500 words of substantively excellent
analysis but was structurally narrow against the seven questions in
`og_prompt.txt`. The Apollo deck shows the empirical depth available
for housing; the data-center benchmark shows what *form* depth takes
when properly executed (layered value chain, sized flows, per-name
backlog vignettes, three explicit risks, 2nd/3rd-order beneficiary
table, bottleneck migration narrative). The v3 patches port that
form to housing while making each of the seven `og_prompt.txt`
questions a recurring section that gets refreshed every Monday.

The Admin & Legislative Pipeline section + running
`policy_pipeline.md` log is the highest-leverage addition. Housing
legislation is a low-base-rate, high-impact event. Detection
*before* the tape reaction is the entire alpha.
