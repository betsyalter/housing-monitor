# Richard's housing-thesis notes — 2026-05-01

> **Source.** Voice notes from Richard, captured by Wyatt 2026-05-01.
> **Purpose.** Capture Richard's threads, map each to the existing five-factor framework, flag what the framework already covers vs what's a new gap, and recommend follow-up research / data work.
> **Status.** Analyst note. Not a report. Intended to inform next iteration of `analyst/five_factor_framework.md`, `housing_context.json` schema, and the weekly monitor's standing sections.

---

## Executive read of Richard's notes

Richard is essentially proposing a **2006-style structural net-absorption analysis** as the foundational layer under our five-factor framework, plus three new analytical threads we don't currently track:

1. **Normalized turnover decomposition** — the difference between the "old normal" 5M EHS run-rate and today's ~4M is the central question. He wants to know how much of the gap is *structural* (REIT installed base, older homeowners, second/third homes in strong hands) vs *cyclical* (rate lock-in). That maps almost perfectly onto Q1 of the og_prompt seven anchor questions, but the structural-vs-cyclical decomposition is currently underspecified — we report Q1 attribution as factor weights, not as an absorption-math reconciliation.
2. **Installed-base segmentation** — how many of the ~94M single-family units are owned by REITs / second-and-third-home owners / older long-tenured owners (effectively dead inventory) vs the "live" turnover pool. We have not quantified this and the Apollo deck does not size it.
3. **The reverse-mortgage / household-wealth-trapped angle** — Richard's biggest fresh idea. ~$35-50T of homeowner equity held by an aging cohort that doesn't want to sell but increasingly needs cash. **FOA (Finance of America Companies)** is the public-market expression; reverse-mortgage securitization (HMBS) is the structural unlock mechanism. This is **completely absent from the current framework**.

The historical-net-absorption math (2003-06 oversupply → 2009-11 absorption → price stabilization) is a reasonable analytical scaffold and we should formalize it as a standing section. The household-formation × attach-rate × supply-flow construction Richard described is a cleaner read than what the framework currently does.

---

## Thread-by-thread mapping

### Thread 1 — Adjusted normalized turnover; what the new normal actually is

**Richard's claim.** Normal EHS used to be 5M/yr. Today ~4M and trending sideways. Need to reconcile: how much of the 1M gap is structural (older owners moving less, REIT-owned stock, second-home stock, strong-hands inventory) vs cyclical (rate lock-in). If new structural normal is 4.8M and the current 4M reflects 800K of rate-lock suppression, the coiled spring is real and ~20% volume uplift sits behind a cut to ~4.5%. If the new structural normal is ~3M and we're already there, there is no coiled spring at all.

**Existing framework coverage.**
- Q1 of og_prompt explicitly asks for the structural-vs-cyclical decomposition, and the report's §Q1 attribution table allocates % of the EHS gap across the five factors. ✅ But we attribute the gap to factor *weights*, not to a Richard-style reconciliation that nets out installed-base structural drift first.
- Coiled-spring §Q2 produces SAAR uplift at 25/50/100/150 bps. ✅ Useful but operates on the **current** EHS base; doesn't separate out the structural-normal anchor.
- Factor 3 (second/third home turnover) framework prose mentions ~2-3%/yr second-home turnover vs ~5%/yr primary turnover. ✅ But we don't multiply this by the installed-base segment sizes to back into total absorbable turnover.

**What's missing — concrete additions.**

1. **A standing "structural turnover anchor" calculation**, refreshed quarterly, that builds bottom-up:
   - Total US single-family stock: ~94M detached + ~7M attached = ~101M ([FRED ETOTALUSQ176N Q1 2026 = 149.0M total housing](https://fred.stlouisfed.org/series/ETOTALUSQ176N); ACS 1-unit share ~63% detached + 6% attached).
   - Owner-occupied SF: ~83-85M (homeownership rate 65.3% per [FRED RHORUSQ156N Q1 2026](https://fred.stlouisfed.org/series/RHORUSQ156N) × ~131M occupied units, biased toward SF).
   - **Less institutional SFR**: ~700K-1M (INVH 80K + AMH 60K + smaller institutional ≈ <1M; ABS-securitized issuance trackers can refine).
   - **Less long-tenured "dead" inventory** (median seller age now 64, median tenure ~10y per [NAR 2025 Profile of Home Buyers and Sellers](https://www.nar.realtor/magazine/real-estate-news/nar-2025-profile-of-home-buyers-sellers-reveals-market-extremes)): need an estimate of the share of the owner-occupied stock held by households 65+ with 15+ years of tenure. JCHS Harvard publishes age-of-homeowner data; pull and quantify.
   - **Less second/third homes**: ~5-8M depending on definition. Census ACS Table B25004 reports vacancy reasons including "seasonal/recreational/occasional use" (~3.8M) plus a portion of "for rent" + "sold/awaiting occupancy". Need to triangulate.
   - **= Live turnover pool** = the denominator that should multiply by the underlying age-adjusted attach rate.

2. **Age-adjusted natural turnover rate**. Older cohorts move materially less. NAR data: median seller age 64 vs ~50 a decade ago. Tenure ~10y now vs ~6 in early 2000s. **Apply age-bucket turnover rates** (e.g., 5-7% for 30-44 cohort; 4-5% for 45-59; 2-3% for 60+) to the population-weighted owner-occupied stock. This produces a *demographically-adjusted natural turnover rate* that's the right comparator — not the static "5M was normal" benchmark.

3. **Reconcile the 2.77% [Redfin national turnover rate](https://www.redfin.com/news/home-turnover-report-2025/) (lowest in 30+ years; ~28 of 1,000 homes changed hands in 2025) against the demographically-adjusted normal**. If the demographically-adjusted normal is 3.5%, the gap is ~0.7-0.8 percentage points × ~95M sellable units = 700K-800K of suppressed transactions. That's the actual coiled-spring magnitude in volume terms, not the framework's current spring-decompression output.

**Recommended deliverable.** Add a **§Structural Turnover Anchor** standing section to the weekly report:

```
Live turnover pool   = Owner-occupied SF
                     − institutional SFR
                     − long-tenured 65+ stock (>15y tenure)
                     − second/third homes
Age-adj nat turnover = Σ (age-bucket weight × age-bucket turnover rate)
Implied normal sales = live pool × age-adj nat turnover
Suppression          = implied normal − actual EHS
Decomp of suppression: rate-lock vs affordability vs other
```

This structurally answers Q1 of og_prompt better than the current weight-based attribution. Worth refactoring §Q1 around it. **Action: open issue in `betsyalter/housing-monitor` to scope this standing section + data sourcing.**

---

### Thread 2 — Multi vs single-family vs rental installed base; cohort age weights; second/third homes

**Richard's claim.** Apollo deck doesn't break out the **rental install base vs SF install base vs MF install base** by cohort age, and doesn't tell you what share of installed base is second/third home. He wants the segmentation.

**Existing framework coverage.**
- Apollo deck slides 31, 32 cover **median age of buyers/sellers** but not the installed-base age distribution. ⚠ Partial.
- Factor 3 explicitly addresses second/third home turnover in qualitative terms. ✅ But not quantified at the installed-base level.
- The framework's Layer 9 (apartment REITs) and Layer 10 (SFR REITs) of the value-chain map name tickers but don't anchor against the SF vs MF stock split. ⚠

**Numbers to pull and add.**
- Total SF (detached + attached): ~101M units ([Census Vintage 2024 housing units](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-total-housing-units.html); ACS 1-unit share).
- Total MF (2+ units): ~50M units (149M total minus ~101M SF minus ~7M manufactured).
- Owner-occupied vs renter-occupied: 65.3% / 34.7% per [FRED RHORUSQ156N Q1 2026](https://fred.stlouisfed.org/series/RHORUSQ156N).
- **Of the ~50M MF stock**: ~85% rental, ~15% condo/co-op (rough; refine via ACS).
- **Of the ~101M SF stock**: ~85% owner-occupied, ~12% SF-rental (institutional + mom-and-pop), ~3-5% second/seasonal.
- **Age distribution of owner-occupied SF**: NAR median seller age 64 implies the bulk of owner-occupied SF stock is held by 55+ households. JCHS Harvard "State of the Nation's Housing" annual report publishes age × tenure crosstabs — pull from their 2025 report.
- **Second/third home count**: Census ACS B25004 vacancy categories — "seasonal, recreational, or occasional use" is the primary tag. Latest 5-year ACS estimate is ~3.8M. NAR estimates higher (~5-7M) when you include investor-held SF. Triangulate.

**Recommended deliverable.** Add a **§Installed-Base Segmentation** standing section. Structure:

| Segment | Units (M) | % of total housing | % of SF | Age-of-owner skew | Turnover behavior |
|---|---|---|---|---|---|
| Owner-occupied SF, primary residence | ~80-83 | ~54% | ~80% | bimodal: 35-50 + 60+ | normal ~4-5%/yr structurally |
| SF rental (institutional + mom-and-pop) | ~12-15 | ~9% | ~12-15% | n/a | 0% — REIT/landlord doesn't sell |
| Second / seasonal / occasional SF | ~4-6 | ~3% | ~4-5% | 55+ skew | ~2-3%/yr |
| Owner-occupied condo / townhome / co-op | ~7-9 | ~5% | n/a | younger skew | ~3% (per Redfin condo turnover) |
| Renter-occupied MF | ~38-42 | ~28% | n/a | mostly 18-44 | high churn but not "turnover" in EHS sense |
| Manufactured | ~7 | ~5% | n/a | mixed | low |

The point is: the *live turnover pool* that maps to EHS is the first row. Everything else is structurally absent from the EHS denominator.

**Action.** Once segmented, run the weekly monitor's §Q1 attribution against the live turnover pool, not against total stock or total owner-occupied. This will materially shift the inferred "rate-lockin %" of the gap because we'll have already netted out the structural-absent layers.

---

### Thread 3 — Net cumulative supply absorption (the 2006 analytical scaffold)

**Richard's claim.** In 2006-07 he built a model of net excess supply: starts vs household formation × attach rate, integrated cumulatively. By 2007 ≥3M of excess supply needed to be absorbed. GFC stopped new supply; 2009-11 net absorption (formation > new starts) firmed the market in advance of price stabilization. Apollo deck doesn't speak to the 2009-2011 supply-side discipline shift (build-to-order vs spec).

**Existing framework coverage.**
- Apollo slide 68 anchors the "2.4M home deficit." ✅
- Factor 1 of the framework discusses lock-in but not the cumulative supply-absorption math. ⚠
- Builder land-book section in the weekly report covers owned-vs-optioned and JV walkaways. ✅ This is exactly Richard's "supply-side got more rational" point at the *current* state, but not as a multi-year cumulative.
- The Apollo deck does mention low inventory across price tiers (slides 50, 67-68) but not as a flow-vs-stock construction.

**What's missing — concrete additions.**

1. **A standing "cumulative net absorption" calculation** going back to 2003:
   - Annual housing starts (Census C20/C21)
   - Annual household formation (Census/ACS / JCHS)
   - Implicit demand = formation × attach rate (single-family vs rental, age-cohort weighted)
   - Net excess/deficit per year
   - Cumulative running balance
   - Compare to current state: are we still in cumulative deficit relative to the 2010-2015 floor? (Apollo's 2.4M deficit number is one expression of this.)

2. **Build-to-order vs spec ratio at Tier-1 builders** — Richard explicitly flags this as a supply-side discipline indicator missing from Apollo. This **is partially in our framework** via NVR's pure build-to-order model and the four-archetype Tier-1 read in this week's report (§Layer 6). But we should formalize the cohort-wide spec-vs-BTO mix as a standing metric.
   - Data source: 10-Q "homes under construction" disclosures broken out by spec vs sold. NVR is 100% sold; DHI/PHM/LEN/TOL each disclose spec inventory. Quantify quarterly.

3. **Lot walkaway and impairment tracking** as supply-discipline real-time tells. Already in framework but could be a standing chart.

**Recommended deliverable.** Add a **§Cumulative Supply Absorption Model** standing section, refreshed quarterly with cohort-level spec-vs-BTO mix.

---

### Thread 4 — Multi-family deflation as housing substitute

**Richard's claim.** Big multi-family build cycle 2021-23 → now deflation in apartment rents, widening the rent-vs-own affordability gap. Charts should pick that up.

**Existing framework coverage.**
- Apartment-REIT short basket (`analyst/apartment_reit_short_basket.md`) is the explicit framework expression. ✅
- §Apartment / multifamily basket read in the weekly report covers concession, lease trade-out, occupancy, Sun Belt vs Coastal. ✅
- §Rent-own spread + apartment-REIT bridge is required (Q4 of og_prompt). ✅
- **What's NOT in the report yet**: the specific *flow* of MF completions (which were heavily front-loaded into 2024-25 from 2021-22 starts) → rent deflation → demand-substitution math. We capture the symptom (concessions) but don't bridge it back to the supply-side cause (MF starts cycle).

**Recommended addition.** In §Apartment/MF basket read, add a 1-paragraph standing reminder that ties current concession data to the 2021-23 starts cohort timing. This is a 1-2 sentence thesis-grounding addition, not a section.

---

### Thread 5 — REIT absorption of excess supply (2009-12) as the prior-cycle anchor

**Richard's claim.** REITs bought homes at 30% discount to rental equivalent during 2009-12 — that's what sopped up excess supply. Apollo has the rent-vs-own price chart but doesn't credit the REIT institutional absorption as the mechanism.

**Existing framework coverage.**
- Factor 2 of the framework is REIT absorption — this is well-covered. ✅
- The weekly report has SFR/BTR basket read (INVH, AMH, etc.). ✅
- **What's NOT in the report**: the historical-anchor narrative — that REITs are now in a different position (HOLDING ~700K-1M units of installed base with no acquisition pace, vs being the marginal buyer 2010-2014). This shifts the marginal-buyer dynamic.

**Recommended addition.** In Factor 2 / SFR-basket read, distinguish between **REITs as acquirer (2010-2015)** vs **REITs as install-base holder (2020-present)**. The latter creates a structural tax on EHS supply (Richard's "strong hands" point) but doesn't generate marginal demand. This nuance matters for thesis interpretation.

---

### Thread 6 — Aggregate household equity / wealth trapped; reverse mortgages; FOA

**This is Richard's biggest gap-vs-framework thread.** Currently the framework does not address:
- Aggregate homeowner equity ($35-50T)
- The "trapped wealth" structural problem (older owners with no income, large equity, no want to sell)
- Reverse mortgage as the structural unlock mechanism
- FOA (Finance of America Companies) as the public-market expression

**Numbers.**
- US homeowner equity (mortgaged borrowers only): **$17.0T** at Q4 2025 per [Cotality / The Mortgage Reports](https://themortgagereports.com/108999/home-equity-gains). Average mortgaged borrower equity: $295K.
- Add equity for **non-mortgaged** owners (~40% of all owner-occupied per Census/ACS): the all-owner aggregate is roughly **$35-40T**.
- Per [ATTOM Q4 2025 home equity report](https://finance.yahoo.com/news/u-homeowner-equity-eases-slightly-175100711.html): **44.6% of mortgaged homes are equity-rich (LTV ≤50%)** — that's 28.4M mortgaged properties with very low leverage. Only **3.0% are seriously underwater** (LTV ≥125%).
- Total residential mortgage debt outstanding: ~$13T (Federal Reserve Z.1 / FRED). Total residential real estate value: ~$45-50T (FRED HOOREVLMHMV / Z.1).
- Implied aggregate LTV: ~28-30% — Richard's "well under 50%" intuition is correct.

**The structural unlock thesis.**

The aging-in-place cohort is the binding factor in Factor 3 (second/third home turnover) AND Factor 4 (demographics ceiling). Reverse mortgages are the only mechanism that **monetizes the equity without forcing the sale**. As the median seller age rises (now 64 per [NAR 2025 Profile](https://www.nar.realtor/magazine/real-estate-news/nar-2025-profile-of-home-buyers-sellers-reveals-market-extremes)), and 65+ households increasingly hit the income / longevity-of-savings wall, reverse mortgage origination should structurally accelerate.

This has TWO thesis-relevant implications:
1. **Reverse mortgage growth is *bearish* for EHS turnover** — every reverse-mortgage origination is a household that explicitly chose NOT to sell. So if Factor 1 (rate lock-in) decays via 30yr falling, but reverse-mortgage origination accelerates faster, the supply unlock is partially neutralized.
2. **Reverse mortgage growth is *bullish* for FOA and HMBS issuers/investors** — direct equity expression of the "trapped wealth" thesis.

**FOA (Finance of America Companies) — public-market expression.**

- **Current state.** FOA is the largest reverse-mortgage originator in the US. Issued $1.87B in HMBS in 2025 — **~30% market share** ([HousingWire / New View Advisors Jan 7 2026](https://www.housingwire.com/articles/foa-leads-2025-hmbs-market/)).
- **Financials (FY 2025).** Revenue $497M (+26% YoY); GAAP net income $110M (+175% YoY); adjusted net income $74M (+429% YoY); adjusted EBITDA $143M (+138% YoY). EPS $5.04 (basic). ([Investing.com Q4 2025 transcript summary](https://www.investing.com/news/transcripts/earnings-call-transcript-finance-of-america-q4-2025-sees-robust-growth-93CH-4553202)).
- **Capital structure.** Total equity $396M as of 12/31/25 (up from $316M); cash & equivalents $90M. Restructured 2024 unsecured debt into 2026/2029 secured tranches per [HousingWire June 2024](https://www.housingwire.com/articles/finance-of-america-announces-debt-restructuring-staving-off-2025-maturity-risk/). 2026/2027 maturity is the next stress event.
- **Strategic moves.** November 2025 announced acquisition of PHH Mortgage's HECM servicing portfolio from Onity Group ([Yahoo Finance Nov 18 2025](https://finance.yahoo.com/news/finance-america-acquire-reverse-mortgage-211500825.html)) — closes Q2 2026, materially expands servicing platform. December 2025 received $50M equity investment. February 2026 fully exited Blackstone legacy ownership.
- **Securitization platform.** FASST (Finance of America Structured Securities Trust) — multiple proprietary jumbo reverse-mortgage securitizations, e.g. [FASST 2025-PC2 ($215M, KBRA-rated)](https://www.kbra.com/publications/wqjQGrzQ).
- **Listing risk.** Russell de-listing risk and prior NYSE listing-standards notice (cured via 10:1 reverse split in 2024). Currently NYSE-listed.
- **Market cap.** ~$358M (Mar 2026 per Investing.com). Well below the $17T equity pool they're tapping into = high optionality if the "trapped wealth" unlock thesis plays out.

**Thesis-frame.** FOA is a **levered call on the demographic-aging × home-equity-monetization joint distribution**. Bull case: Boomer cohort needs $30-50K/yr supplementary income; HECM origination accelerates; FOA's 30% market share + servicing platform compounds; HMBS spreads tighten. Bear case: FOA's small balance sheet and 2026/2029 debt maturities create refinancing risk if HMBS market stress; the entire reverse-mortgage industry is regulatorily-fragile (FHA HECM rules can change abruptly); listing/liquidity risk persists. Both cases are real.

**Recommended deliverable.**

1. **Add `analyst/reverse_mortgage_thesis.md`** as a new framework annex, treating reverse mortgage as a Factor-1-and-Factor-3 cross-cut. Include FOA as the named public-market expression.
2. **Add `reverse_mortgage_pulse` standing subkey** to the weekly JSON sidecar — track HMBS issuance volume, FOA quarterly origination, and HECM regulatory developments.
3. **Add HECM/HMBS to the policy-pipeline mechanism watchlist** — FHA HECM rule changes, IRS reverse-mortgage tax-treatment changes, GSE involvement in HMBS, etc.
4. **Add FOA to the watchlist** — currently not in `data/fmp_tickers.csv` per the framework. Should be added to a new "Demographic-aging financials" subsector basket.
5. **Pull FOA 10-K + recent 10-Qs + investor materials** — needed for proper coverage. The Q4 2025 print summary above is from a transcript; we need the primary filings.

This is the most under-covered angle in the current framework relative to its thesis-importance.

---

### Thread 7 — Aggregate equity / LTV math as a macro-stability anchor

**Richard's claim.** Economy is on strong footing because $35-50T of equity is parked in housing with low LTV (~30% aggregate). Apollo cites LTV but not the aggregate dollar values — the latter is a stability-of-consumption argument and a potential consumption-via-equity-extraction tailwind.

**Existing framework coverage.**
- Not currently in framework. ⚠ NEW.

**Numbers (refer Thread 6).**
- Aggregate residential equity: $35-40T (all owners, mortgaged + non-mortgaged).
- Aggregate residential mortgage debt: ~$13T.
- Aggregate LTV: ~28-30%.
- Equity-rich (LTV ≤50%) share of mortgaged homes: 44.6%.
- Seriously underwater (LTV ≥125%): 3.0%.
- 2025 cash-out / equity-extraction volume: **$205B** ([Investopedia / ICE](https://www.investopedia.com/home-equity-withdrawals-hit-three-year-high-11923725)) — highest in 3 years; HELOC the dominant channel.

**Thesis-frame.** Two opposing reads:
1. *Bullish-consumption* — the $205B/yr extraction rate is sub-1% of aggregate equity; massive headroom for consumption support if savings-rate compresses. Reverse mortgages, HELOCs, cash-out refis are all underutilized.
2. *Bearish-housing-supply* — the same low-LTV / high-equity state is precisely what enables households to NOT sell; the Coiled-Spring math implicitly bakes in lock-in but not the *equity-side* reason that reinforces it. Owners with $300K of free equity and no income don't need to sell — they can borrow against it.

**Recommended deliverable.** Add a **§Aggregate Equity & Extraction Pulse** to the weekly report as a quarterly-updated standing section (data is quarterly anyway via Cotality / ICE / Z.1). Tie it to both Factor 1 (lock-in reinforcement) and to consumption macro reads.

---

### Thread 8 — Median age of homebuyer (already in Apollo, but worth flagging)

**Richard's claim implicit.** "70 year-olds aren't buying new houses." Demographics ceiling is real.

**Existing framework coverage.**
- Apollo slides 31, 32: median age of homebuyers 59 (was 31 in 1981); first-time buyer 40 (was 30 in 2008). ✅
- Recent NAR 2025 Profile: first-time buyer 40 (record); repeat buyer 62; seller 64 ([NAR Nov 2025](https://www.nar.realtor/magazine/real-estate-news/nar-2025-profile-of-home-buyers-sellers-reveals-market-extremes)). ✅
- Note Redfin's analysis publishes different (younger) numbers — first-time buyer 35, repeat 47 per [Redfin Feb 2026](https://www.redfin.com/news/median-homebuying-age-2025/). Methodology-dependent. NAR uses survey of recent buyers; Redfin uses Census deeds-data inferences. Use both as a confidence range.
- 49% of 2025 buyers were 60+. [NAR research / Facebook post Jan 2026](https://www.facebook.com/narresearchgroup/).

**No action needed** — this thread is already well-covered.

---

## Synthesis — what changes in the framework

### Already in framework, but worth tightening (Threads 1, 4, 5, 8)
- §Q1 attribution should add a **structural-turnover-anchor reconciliation step** before allocating gap to factors.
- Apartment REIT bridge should add **flow-supply timing context** (2021-23 starts cohort).
- Factor 2 (REIT absorption) should distinguish **acquirer-mode vs install-base-holder-mode**.

### NEW additions to the framework (Threads 2, 3, 6, 7)
1. **§Installed-Base Segmentation** — quantified, refreshed quarterly. Adds clarity to Q1 / Factor 3 reads.
2. **§Cumulative Supply Absorption Model** — multi-year flow-vs-stock construction; quarterly refresh.
3. **`analyst/reverse_mortgage_thesis.md`** — new framework annex; FOA as public-market expression; HECM/HMBS as the structural unlock mechanism; integrated into Factor 1 + Factor 3 cross-reads.
4. **§Aggregate Equity & Extraction Pulse** — quarterly standing section; ties household-wealth to consumption macro.

### NEW data/code work
- Pull JCHS Harvard "State of the Nation's Housing" 2025 for age × tenure crosstabs.
- Pull Census ACS B25004 (vacancy categories) for second-home / seasonal stock count.
- Add FOA + reverse-mortgage subsector basket to `data/fmp_tickers.csv`.
- Add HMBS issuance + FOA origination pulse fields to `housing_context.json` schema.
- Add HECM/HMBS regulatory items to `analyst/news_sources.yaml` policy-pipeline watchlist.

### NEW report sections (standing)
- **Structural Turnover Anchor** (quarterly refresh)
- **Installed-Base Segmentation** (quarterly refresh)
- **Cumulative Supply Absorption** (quarterly refresh)
- **Aggregate Equity & Extraction Pulse** (quarterly refresh)
- **Reverse Mortgage Pulse** (weekly — HMBS issuance is monthly, FOA news is event-driven)

---

## Suggested next steps (ranked by thesis-importance × effort-to-add)

| # | Action | Impact | Effort | Priority |
|--:|---|:--:|:--:|:--:|
| 1 | Spin up `analyst/reverse_mortgage_thesis.md` + add FOA to ticker universe | **High** | Low | DO FIRST |
| 2 | Add §Aggregate Equity & Extraction Pulse to weekly report (quarterly data; just a 1-paragraph add) | High | Low | DO FIRST |
| 3 | Build Installed-Base Segmentation table (one-time effort, then quarterly refresh) | High | Med | Next |
| 4 | Build Cumulative Supply Absorption Model (multi-decade dataset construction) | High | High | After #1-3 |
| 5 | Refactor §Q1 around structural-turnover-anchor reconciliation | Med-High | Med | After #3 |
| 6 | Add HMBS / HECM to policy-pipeline mechanism watchlist | Med | Low | DO FIRST (cheap) |
| 7 | Pull FOA 10-K + recent 10-Qs as reference materials in `docs/reports/` | Med | Low | DO FIRST |

**Items 1, 2, 6, 7 are all low-effort and all DO FIRST**. They unlock the FOA / reverse-mortgage thesis and add the household-wealth macro layer immediately. Items 3-5 are deeper structural framework rebuilds that should be staged over the next 2-4 weeks.

---

## Citations consolidated

- Total US housing units, Q1 2026: 149.0M [FRED ETOTALUSQ176N](https://fred.stlouisfed.org/series/ETOTALUSQ176N)
- US homeownership rate, Q1 2026: 65.3% [FRED RHORUSQ156N](https://fred.stlouisfed.org/series/RHORUSQ156N)
- Census Vintage 2024 housing units file: [Census](https://www.census.gov/data/datasets/time-series/demo/popest/2020s-total-housing-units.html)
- 2024 single-family completions ~1.0M; 2024 new-home median price $420K, average $515K: [Census Highlights of 2024 Characteristics of New Housing](https://www.census.gov/construction/chars/highlights.html)
- US national turnover rate 2025 = 2.77% (lowest in 30+ years): [Redfin](https://www.redfin.com/news/home-turnover-report-2025/)
- 2025 EHS 4.06M (tied 2024, just below 2023): [FastCompany / Cotality–ResiClub](https://www.fastcompany.com/91516789/housing-market-resale-turnover-is-near-a-4-decade-low-heres-how-agents-say-the-industry-is-shifting)
- NAR 2025 Profile of Home Buyers and Sellers: median first-time buyer 40, repeat 62, seller 64 [NAR](https://www.nar.realtor/magazine/real-estate-news/nar-2025-profile-of-home-buyers-sellers-reveals-market-extremes)
- Redfin alternative read: median first-time 35, repeat 47 [Redfin](https://www.redfin.com/news/median-homebuying-age-2025/)
- US homeowner equity (mortgaged), Q4 2025: $17.0T [Cotality / The Mortgage Reports](https://themortgagereports.com/108999/home-equity-gains)
- ATTOM Q4 2025: 44.6% equity-rich, 3.0% seriously underwater [ATTOM/Yahoo](https://finance.yahoo.com/news/u-homeowner-equity-eases-slightly-175100711.html)
- 2025 home-equity withdrawals: $205B [Investopedia / ICE](https://www.investopedia.com/home-equity-withdrawals-hit-three-year-high-11923725)
- FOA 30% HMBS market share 2025: [HousingWire / New View Advisors Jan 7 2026](https://www.housingwire.com/articles/foa-leads-2025-hmbs-market/)
- FOA debt restructuring 2024: [HousingWire June 26 2024](https://www.housingwire.com/articles/finance-of-america-announces-debt-restructuring-staving-off-2025-maturity-risk/)
- FOA acquires PHH HECM servicing Nov 2025: [Yahoo Finance Nov 18 2025](https://finance.yahoo.com/news/finance-america-acquire-reverse-mortgage-211500825.html)
- FOA Q4/FY2025 results: [Yahoo Finance Mar 10 2026](https://finance.yahoo.com/news/finance-america-reports-fourth-quarter-200500262.html)
- FOA Q4 2025 transcript summary: [Investing.com Mar 2026](https://www.investing.com/news/transcripts/earnings-call-transcript-finance-of-america-q4-2025-sees-robust-growth-93CH-4553202)
- FASST 2025-PC2 ($215M, KBRA-rated): [KBRA May 2025](https://www.kbra.com/publications/wqjQGrzQ)
- 2024 household formation 1.4M (941K owner / 463K renter): [NAR research / Facebook Jan 2026](https://www.facebook.com/narresearchgroup/posts/-1316196563869012/)
- Federal Reserve 2024 Economic Well-Being report (homeownership by age): [FRB Dec 2025](https://www.federalreserve.gov/publications/2025-economic-well-being-of-us-households-in-2024-housing.htm)
