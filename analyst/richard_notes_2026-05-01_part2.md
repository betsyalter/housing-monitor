# Richard's Voice Notes — 2026-05-01 (Part 2)

**Status:** Active analyst memo (companion to `analyst/richard_notes_2026-05-01.md` — Part 1)
**Captured:** 2026-05-01
**Sources:** Richard's voice memos forwarded by Wyatt
**Treatment:** Each thread is mapped to (a) which factor in `five_factor_framework.md` it sharpens, (b) what evidence Richard offers, (c) what data we have to validate, (d) what changes in the weekly monitor going forward.

---

## Thread 1 — Apollo's "2.5M deficit" looks high; Richard's prior was 1.5M (now 3-3.5M)

### Richard's view (verbatim sense)
- Apollo's house view (Slok deck — `docs/reports/FILE_4211.pdf`) is that the U.S. is short ~2.5M homes vs. the trend household-formation curve.
- Richard's recollection of his 2006 work was a **1.5M *surplus*** at the housing bubble peak.
- His current scoring puts the deficit at 3-3.5M — but he wants the numbers stress-tested. Apollo's framing may be too aggressive.

### What we can say from data
- The deficit math is sensitive to (a) baseline household-formation rate assumed, (b) treatment of vacant-but-not-on-market units, (c) treatment of second/vacation homes, (d) demolitions/replacement assumption.
- Different respected sources land at different estimates. Range from [Up for Growth (2024 estimate)](https://upforgrowth.org/) of ~3.9M to Freddie Mac's ~3.7M to lower NAHB and Realtor.com figures around 1.5-2.5M. The variance is methodology, not data.
- **Implication:** present the deficit as a range with method-dependence, not a single number. The Apollo number should be cited with its assumption set explicitly.

### Action for the weekly
- Add a **"Deficit estimate dispersion"** sentence to the housing value-chain map intro: lead with Apollo's number, list the alternative methodologies (Up for Growth, Freddie, NAHB), and note the spread.
- Standing skepticism: when the deficit narrative is invoked to justify a thesis, check which methodology underpins it.

---

## Thread 2 — Residential Fixed Investment as % of GDP: peak / trough / normal

### Richard's view
- 2005-06 boom: residential investment hit "3-something %" of total economy.
- 2010-11 trough: collapsed to ~1.3% — "you can't go below that, you have to replace appliances and carpets."
- "Normal" should be ~2% — implying the U.S. has been **below normal** for a long stretch and the cumulative under-build is real.
- Richard wasn't sure where we are today; thought we were probably still below normal.

### What the data actually shows
| Period | Residential Fixed Investment / GDP | Source |
|---|---|---|
| Q4 2005 (boom peak) | 6.7% | [FRED A011RE1Q156NBEA](https://fred.stlouisfed.org/series/A011RE1Q156NBEA) |
| 2010-2011 trough | ~2.4% (annual avg) | [FRED A011RE1A156NBEA](https://fred.stlouisfed.org/series/A011RE1A156NBEA) |
| 2020-2021 pandemic boom | 4.8% (peak) | [FRED A011RE1Q156NBEA](https://fred.stlouisfed.org/series/A011RE1Q156NBEA) |
| 2025 (full year) | 3.9% | [FRED A011RE1A156NBEA](https://fred.stlouisfed.org/series/A011RE1A156NBEA) |
| Q4 2025 | 3.8% | [FRED A011RE1Q156NBEA](https://fred.stlouisfed.org/series/A011RE1Q156NBEA) |
| Q1 2026 | 3.7% | [FRED A011RE1Q156NBEA](https://fred.stlouisfed.org/series/A011RE1Q156NBEA) |

### Reconciliation
- Richard was **directionally right but quantitatively low** on his "normal." The historical pre-bubble normal (1980-2005 average) is closer to 4.5%, not 2%. The 2010-2011 trough was 2-3%, not 1.3%. The "carpet replacement floor" idea is useful but the actual floor is higher.
- **We are NOT below normal today.** Residential investment is running at 3.7-3.9% — modestly below the long-run average but well above the post-GFC trough and consistent with sustained build-rate.
- **Reconciles with the deficit story how?** The deficit is a *cumulative* claim — many years of below-trend completions. Even a mid-3% RFI/GDP run-rate today won't close the cumulative gap quickly. Annual flows ≠ cumulative stock.

### Action for the weekly
- Add Residential Fixed Investment as % of GDP to the macro delta table with 4w/13w/52w windows where the underlying series allows.
- Add cumulative-completions-vs-formation gap chart (NAHB / Census starts vs. household formation) as a recurring inventory-paradox subsection.

---

## Thread 3 — The "lagging rent" argument: averages bake in 5-7 year-old leases

### Richard's view
- Average tenancy is ~7 years. Rent indices that average across all leases bake in rents from leases signed years ago.
- The relevant signal for *current* market clearing is the **most recent** rent — what new tenants are paying today.
- His read: shelter inflation in CPI is structurally lagged, and the *real* current rent picture is much weaker. Ergo headline CPI overstates inflation, Fed easing is closer than the curve thinks, admin will push to juice the housing economy ahead of midterms / 2028.

### What the data actually shows
| Series | Latest reading | Source |
|---|---|---|
| BLS Standard Rent Index (continuing tenants) — Q2 2025 YoY | **+2.8%** | [BLS New Tenant Rent Index page](https://www.bls.gov/pir/new-tenant-rent.htm) |
| BLS New Tenant Rent Index (R-CPI-NTR) — Q2 2025 YoY | **−9.3%** | [BLS New Tenant Rent Index page](https://www.bls.gov/pir/new-tenant-rent.htm) |
| Apartment Q4 2025 effective rent change | **−1.3%** sequential | [Smart Apartment Data — Q4 2025 Multifamily Overview](https://smartapartmentdata.com/news/q4-2025-u-s-multifamily-market-national-overview) |
| Cleveland Fed rent inflation forecast | Above pre-pandemic until mid-2026; new vs. continuing-tenant gap ~5.5% | [Cleveland Fed (October 2024)](https://www.clevelandfed.org/collections/press-releases/2024/pr-20241016-model-predicts-rent-inflation-will-remain-elevated) |
| Census Q1 2026 rental vacancy rate | **7.3%** | [Census HVS Q1 2026](https://www.census.gov/housing/hvs/current/index.html) |
| RealPage Q4 2025 rent YoY | +1.5% | [Smart Apartment Data — Q4 2025 Multifamily Overview](https://smartapartmentdata.com/news/q4-2025-u-s-multifamily-market-national-overview) |

### Reconciliation
- **Richard's argument is empirically backed.** The gap between continuing-tenant (+2.8%) and new-tenant (−9.3%) is the largest in the published series. CPI shelter is dragged by the continuing-tenant cohort and lags the actual market by 12-18 months. The Cleveland Fed model explicitly quantifies the gap at ~5.5%.
- **Implication for macro chain (Q7 — oil → CPI → Fed → 30yr):** if you mark CPI shelter to new-tenant rents, headline CPI is materially lower today. Fed reaction function depends on which they emphasize. Powell has acknowledged the lag publicly.
- **Implication for apartment-REIT short basket (Factor 4):** new-tenant rents falling into rising vacancy (7.3% — highest since early 2010s) is the operational evidence the basket is right. Effective-rent decline -1.3% Q4 confirms.

### Action for the weekly
- Add a **"Lagging rent indicator"** standing line to the rent-own spread / apartment-REIT bridge section: report (1) BLS NTR latest YoY, (2) BLS All-Tenant Regressed (continuing) latest YoY, (3) Cleveland Fed model forecast, (4) Census HVS rental vacancy, (5) RealPage / Smart Apartment Data effective rent change.
- Tie this directly into the macro chain (Q7) section — flag whether CPI shelter is starting to converge to new-tenant data, which is the gating condition for faster Fed easing.

---

## Thread 4 — Admin policy/legislative workarounds for rate lock-in

### Richard's view
- The administration knows it can't push 30yr rates much lower with conventional policy levers. The political demand is to "do something about housing."
- Therefore look for **side-door** policies that restore transaction volume without needing rates to move.
- Categories he flagged:
  1. Tax credits for sellers (locked-in low-rate cohort) to monetize the rate gift before selling.
  2. Depreciation-style mechanisms to subsidize the rate spread.
  3. Mortgage assumption/portability mechanisms (let the buyer assume the seller's rate).
  4. First-time-homebuyer credits sized large enough to bridge the affordability gap.

### What's in policy_pipeline.md already
- §121 capital-gains exclusion expansion (Stop Penalizing Longtime Homeowners Act, [H.R. 1340](https://www.congress.gov/bill/119th-congress/house-bill/1340)) — already tracked.
- First-time-homebuyer credit ($25-50K range) — tracked.
- LLPA changes — tracked.
- Conforming loan limit increases — tracked.
- DPA (down-payment assistance) grants — tracked.
- 2-1 buydown subsidies (Treasury/HUD-funded) — tracked.

### What's missing / to add
- **Mortgage portability / assumption rules:** Currently FHA, VA, USDA loans are assumable; conventional GSE loans largely are not. A GSE rule change to allow conventional assumption would be the single biggest unlock for Factor 1. Watch FHFA / Treasury notices.
- **Targeted "lock-in tax credit"** — a credit to sellers conditional on listing, sized to make selling tax-equivalent to staying. No specific bill yet but this is the natural vehicle if the admin wants to be seen acting before midterms. **Watch trial balloons in Heritage / AEI Housing Center / Manhattan Institute.**
- **Depreciation expansion / §1031 widening** — primary residence is currently excluded from §1031; widening could affect investor demand.
- **State-level transfer-tax abatements** — beyond federal scope but affects the math.

### Action for the weekly
- Add **"Assumption / portability"** as an explicit watchlist line in policy_pipeline.md.
- Add **"Lock-in-targeted seller tax credit"** as a SCUTTLE bucket item to scan trial balloons for.
- When any item moves stage (rumor → floated → drafted → introduced → markup → passed), surface as TOP-OF-NOTIFICATION pre-Monday-open flag.

---

## Thread 5 — Mortgage insurance ecosystem: 4 publics + bank exposure

### Richard's view
- Five public mortgage insurers: MGIC, Radian, Essent, NMI Holdings, Enact (also Arch's MI segment, but Arch is a multi-line).
- "Great business right now because of low LTV." Embedded equity means default loss-given-default is structurally low.
- Banks holding seasoned mortgages don't worry much about NPL/REO because of the equity cushion — same dynamic, different layer.
- Trump-administration headline risk in Jan 2026: rumored MI premium cut wiped 4-6% off the names in a day before being walked back ([Longbridge — coverage of Jan 2026 MI selloff](https://longbridge.com/en/news/272453586)).

### What the data actually shows

| Insurer | Ticker | Insurance in Force | PMIERs cushion | 2024 NIW (industry context) |
|---|---|---|---|---|
| MGIC Investment | MGIC | (Q2 2025 IIF mid-200s $B range) | Strong | Industry leader in 2024 NIW |
| Radian Group | RDN | $276.7B (Q2 2025, all-time high) | $2.035B PMIERs excess at Q2 2025 | Top tier |
| Essent Group | ESNT | (similar scale) | Bermuda-affiliate cession | Q4 2024 NIW share gains |
| NMI Holdings | NMIH | $221.4B (FY 2025) | 70% PMIERs sufficiency | Smaller scale, fastest grower historically |
| Enact Holdings | ACT | (Genworth spin) | Bermuda affiliate | Mid-tier |

Industry: 2024 total NIW $298.9B; 2025 NIW $311B (+4% YoY) per [Milliman PMI Q4 2025 report](https://www.milliman.com/en/insight/pmi-market-trends-4q-2025). Total mortgage debt outstanding $14T per [NMI 10-K](https://ir.nationalmi.com/static-files/c854af6a-524b-4104-8070-fd6b4d2d3f0e). Market persistency: 84% (12 months ended June 30, 2025).

Trump admin Jan 2026 MI premium-cut event:
- Names sold off Jan 2026 on rumor: Radian -5.3%, NMI -5.65%, Essent -4.49%, MGIC -5.2% (per [Longbridge press coverage](https://longbridge.com/en/news/272453586)).
- Subsequent rebound when story walked back. Confirms the **headline-risk factor is live** for these names — every admin-aligned trial balloon on FHA / GSE pricing reads through MI premium.

### Why this fits the framework
- MI equity is **levered to refi and purchase volumes** (NIW), with a long-tail loss reserve based on insurance-in-force LTV. Given today's ~46% market-wide LTV, loss reserve releases have been a recurring earnings driver.
- This is a **2nd-derivative refi name set** — MI volume scales with both purchase originations (low-down-payment cohort) and refi volume (when refi'd loans get re-MI'd if LTV is still >80%).
- Bank exposure: large mortgage-bank books at WFC, JPM, USB, BAC have similar embedded equity cushion. NPL / REO concerns are blunted; loss-content on the book is the relevant metric, not the headline NPL ratio.

### Action for the weekly
- Add an **MI subsector** watchlist line under Stock-level signals: report MGIC, RDN, ESNT, NMIH, ACT moves and any new PMIERs / NIW data.
- Add **MI premium-cut / FHA MIP cut** to policy_pipeline.md as ON-TAPE-prone item — high binary risk to the names, often surfaces in trial-balloon form before Federal Register notice.
- Cross-reference to Q1 attribution: the credit-box factor (loosening MI / FHA terms = credit-box loosening) is a Q1 Factor 5 (or "credit availability" cross-cut) item.

---

## Thread 6 — Title insurance: FAF, FNF, STC

### Richard's view
- Three publics: First American Financial (FAF), Fidelity National Financial (FNF), Stewart Information Services (STC).
- 99.9% attach rate to home transactions — title is functionally mandatory for any financed transaction.
- 2019 FNF/STC merger blocked by FTC — concentration-of-power concern even with 3 majors.
- **Massive upside on EHS turnover recovery:** the title business is hyper-cyclical to transaction volume. Margin operating leverage is enormous because the cost base is sticky (title plant, branch network, escrow ops).

### What the data actually shows

| Insurer | Ticker | 2025 results | Margin |
|---|---|---|---|
| First American | FAF | Q4 2025 Title segment revenue $1.9B (+21% YoY); FY2025 total revenue $7.5B (+22% YoY); FY2025 net income $622M ($6.00 EPS); Title segment Q4 pretax margin 14.9% (vs 7.9% prior year) | [First American Q4 2025 release](https://www.firstam.com/news/2025/fourth-quarter-full-year-2025-results-20260211.html) |
| Fidelity National Financial | FNF | Q3 2025 Title revenue $2.265B (+8% YoY); Q3 2025 Title adjusted pretax margin 17.8% (vs 15.9% prior year); Q4 2025 Title segment adjusted margin 17.5%; FY2025 total revenue $14.5B (+7% YoY) | [BeyondSPX — FNF Q3 2025 analysis](https://www.beyondspx.com/quote/FNF/analysis/fidelity-national-financial-margin-expansion-meets-value-unlocking-as-technology-transforms-title-insurance-nyse-fnf), [Yahoo Finance — FNF FY 2025 results](https://finance.yahoo.com/news/fidelity-national-financial-fnf-reports-102605734.html) |
| Stewart | STC | Smaller scale; ~9% title margins per public coverage; trades 21x P/E reflecting smaller-scale higher-cost structure | [BeyondSPX — FNF analysis (comp section)](https://www.beyondspx.com/quote/FNF/analysis/fidelity-national-financial-margin-expansion-meets-value-unlocking-as-technology-transforms-title-insurance-nyse-fnf) |

Critical operating tells:
- FNF is achieving **17.5-17.8% title margin in a "low transactional environment"** ([BeyondSPX](https://www.beyondspx.com/quote/FNF/analysis/fidelity-national-financial-margin-expansion-meets-value-unlocking-as-technology-transforms-title-insurance-nyse-fnf)) — meaning operating leverage on a turnover recovery is massive. SoftPro / inHere / AI investments raised the floor.
- FAF's Q4 2025 title segment Q4 pretax margin near-doubled to 14.9% from 7.9% — same cyclical operating leverage story.
- Commercial title is in third-best year ever; office sector recovery would be added tailwind into 2026 ([BeyondSPX FNF analysis](https://www.beyondspx.com/quote/FNF/analysis/fidelity-national-financial-margin-expansion-meets-value-unlocking-as-technology-transforms-title-insurance-nyse-fnf)).

### Why this fits the framework
- Title is the **purest 2nd-derivative on Factor 1 (rate lock-in unlock)** — when rate-lock thaws and EHS run-rate moves from ~4M to ~5-5.5M (post-pandemic normalization), title volume scales 1:1 with closed orders. Margin operating leverage means EPS scales >1:1.
- It's also the **purest expression of the "supply unlock" coiled-spring upside** — every single thawed transaction generates a title order.
- Also commercial-title is a clean expression of office/CRE recovery if that develops.

### Position-sizing tell
- FNF dividend yield ~3.5% with 47% payout ratio plus the F&G distribution structural unlock — provides downside cushion. FAF gives more pure-play title exposure (less F&G annuity-business comingling). STC is high-beta on the cycle but smaller scale.

### Action for the weekly
- Add **Title insurance** subsector basket line to Stock-level signals: report FAF, FNF, STC moves; report any new orders-opened / closed / commercial revenue datapoints.
- Treat as a **2nd-order beneficiary** in the bottleneck → 2nd-order → 3rd-order cheat sheet keyed off Factor 1 (rate-lock unlock).
- When FNF / FAF report Q4 / Q1 results, include the orders-opened daily run-rate as a leading inflection signal.

---

## Thread 7 — Refi-cycle 2nd-derivative names

### Richard's view
- When the refi cycle inevitably restarts (rates falling enough to unlock the locked-in cohort), there are public names whose entire business model is levered to refi volume.
- Examples: Rocket Companies (RKT), United Wholesale Mortgage (UWMC), and the broader IMB (independent mortgage banker) channel.

### Public-market names to track
| Name | Ticker | Channel | Refi exposure |
|---|---|---|---|
| Rocket Companies | RKT | Retail | Pure-play, ~50%+ refi historically |
| UWM Holdings | UWMC | Wholesale | Wholesale leader, refi-heavy |
| Mr. Cooper | COOP | Servicing + retail | MSR runoff offsets refi gains; net neutral |
| LoanDepot | LDI | Retail | Smaller scale, refi-heavy |
| Guild Holdings | GHLD | Retail | Smaller; mixed |
| PennyMac Financial | PFSI | Correspondent + servicing | Diversified across channels |
| Mr. Cooper | COOP | Servicing | Net beneficiary of *both* directions |

### Cross-reference to MI / title threads
- Refi cycle restart = simultaneous tailwind to MI (NIW from new origination), title (orders opened), and origination platforms. The framework should treat these as a **correlated basket** keyed to the Factor 1 thaw.
- **Asymmetry:** Rocket / UWM are pure-play, high-beta, levered to gain-on-sale margin and volume. Mr. Cooper is hedged via servicing book runoff.

### Action for the weekly
- Add **Mortgage origination subsector** line to Stock-level signals: track RKT, UWMC, COOP, LDI as the refi-cycle 2nd-derivative basket.
- In the bottleneck → 2nd-order → 3rd-order cheat sheet, when the binding constraint is rate-lock (Factor 1), refi-cycle names belong in the **2nd-order beneficiary** column alongside title insurers.
- Track the channel-mix split (wholesale vs. retail; IMB vs. depository; refi vs. purchase) as a standing weekly section already in the spec.

---

## Cross-cut: integration into the weekly cadence

These six new analytical threads (Threads 1-7 above) generate the following **changes to the weekly monitor template**:

### New / refreshed standing sections
1. **Macro delta table** — add Residential Fixed Investment % GDP (4w/13w/52w windows)
2. **Inventory paradox section** — add Aggregate Equity Pulse subsection (ICE tappable, ATTOM equity-rich, withdrawals, HMBS issuance) ← from Thread 1 (deficit dispersion) + reverse-mortgage annex
3. **Rent-own spread / apartment-REIT bridge** — add Lagging Rent Indicator subsection (BLS NTR, BLS continuing, Cleveland Fed gap, Census HVS, RealPage/SAD)
4. **Stock-level signals** — add MI subsector (MGIC/RDN/ESNT/NMIH/ACT) + Title subsector (FAF/FNF/STC) + Origination subsector (RKT/UWMC/COOP/LDI)
5. **Bottleneck → 2nd-order → 3rd-order cheat sheet** — add Title and MI as standing 2nd-order beneficiaries when Factor 1 is binding constraint; add FOA as senior-equity-channel marker
6. **Macro chain (Q7)** — add CPI-shelter convergence flag against new-tenant rent

### New / refreshed policy-pipeline lines
- Mortgage portability / GSE assumption rules
- Lock-in-targeted seller tax credit (SCUTTLE bucket — scan Heritage / AEI / MI for trial balloons)
- HECM PLF / MIP / loan-limit changes
- HMBS 2.0 program developments
- MI premium cuts / FHA MIP cuts (binary headline-risk events)

### New JSON sidecar fields (proposed)
- `aggregate_equity_pulse`: { tappable_equity_t, equity_rich_pct, equity_withdrawals_q, hmbs_issuance_m }
- `lagging_rent_indicator`: { bls_ntr_yoy, bls_continuing_yoy, cleveland_fed_gap_bp, census_vacancy, realpage_effective_yoy }
- `mi_subsector_basket`: { mgic_pct, rdn_pct, esnt_pct, nmih_pct, act_pct, basket_avg }
- `title_subsector_basket`: { faf_pct, fnf_pct, stc_pct, basket_avg }
- `origination_subsector_basket`: { rkt_pct, uwmc_pct, coop_pct, ldi_pct, basket_avg }

---

## Open questions for Wyatt / Richard

1. **Deficit estimate dispersion** — should the weekly report a single-point deficit or a methodology-conditional range? Recommend range.
2. **MI premium-cut headline-risk** — should we pre-build a triggered-alert template for the next iteration?
3. **Title insurance position-sizing** — should the weekly track FAF/FNF/STC as a basket or pick one as the cleanest expression?
4. **Refi 2nd-derivative timing** — when do we start sizing exposure (Fed first cut? specific 30yr level? mortgage rate <6%?)
5. **Aggregate Equity Pulse** — promote to standalone Factor 6 in the framework, or keep as cross-cut?

---

## Sources

### Macro / data
- [FRED — Residential Fixed Investment % GDP (Quarterly)](https://fred.stlouisfed.org/series/A011RE1Q156NBEA)
- [FRED — Residential Fixed Investment % GDP (Annual)](https://fred.stlouisfed.org/series/A011RE1A156NBEA)
- [BLS — New Tenant Rent Index](https://www.bls.gov/pir/new-tenant-rent.htm)
- [Cleveland Fed — Rent inflation forecast (Oct 2024)](https://www.clevelandfed.org/collections/press-releases/2024/pr-20241016-model-predicts-rent-inflation-will-remain-elevated)
- [Census — Housing Vacancy Survey Q1 2026](https://www.census.gov/housing/hvs/current/index.html)
- [Smart Apartment Data — Q4 2025 Multifamily Overview](https://smartapartmentdata.com/news/q4-2025-u-s-multifamily-market-national-overview)
- [ICE Mortgage Monitor](https://www.icemortgagetechnology.com/about/news-releases)
- [ATTOM — Q4 2025 Equity & Underwater Report](https://www.attomdata.com/news/market-trends/home-equity-underwater/q4-2025-u-s-home-equity-and-underwater-report/)
- [Investopedia / ICE — Home Equity Withdrawals 3-Year High](https://www.investopedia.com/home-equity-withdrawals-hit-three-year-high-11923725)
- [FHFA — National Mortgage Database](https://www.fhfa.gov/data/dashboard/national-mortgage-database)

### Reverse mortgage / FOA
- [HousingWire — FOA tops HMBS market with 30%](https://www.housingwire.com/articles/foa-leads-2025-hmbs-market/)
- [Yahoo Finance — FOA Q4 2025 results](https://finance.yahoo.com/news/finance-america-reports-fourth-quarter-200500262.html)
- [Investing.com — FOA Q4 2025 earnings transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-finance-of-america-q4-2025-sees-robust-growth-93CH-4553202)

### Mortgage insurance
- [Milliman — PMI Q4 2025 trends](https://www.milliman.com/en/insight/pmi-market-trends-4q-2025)
- [S&P Global — U.S. PMI Sector View 2026](https://www.spglobal.com/ratings/en/regulatory/article/us-private-mortgage-insurance-sector-view-2026-strength-amid-rising-challenges-s101661481)
- [Longbridge — Coverage of Jan 2026 MI premium-cut headline event](https://longbridge.com/en/news/272453586)
- [USMI — PMI by the numbers](https://www.usmi.org/filter_data/pmi-by-the-numbers/)
- [NMI Holdings — 10-K (mortgage debt outstanding cite)](https://ir.nationalmi.com/static-files/c854af6a-524b-4104-8070-fd6b4d2d3f0e)
- [Porter's Five Forces — Radian competitive landscape (Q2 2025 IIF cite)](https://portersfiveforce.com/blogs/competitors/radian)

### Title insurance
- [First American — Q4 / FY 2025 results](https://www.firstam.com/news/2025/fourth-quarter-full-year-2025-results-20260211.html)
- [BeyondSPX — Fidelity National Financial Q3 2025 analysis](https://www.beyondspx.com/quote/FNF/analysis/fidelity-national-financial-margin-expansion-meets-value-unlocking-as-technology-transforms-title-insurance-nyse-fnf)
- [Yahoo Finance — FNF FY 2025 results](https://finance.yahoo.com/news/fidelity-national-financial-fnf-reports-102605734.html)

### Policy
- [Congress.gov — H.R. 1340 Stop Penalizing Longtime Homeowners Act](https://www.congress.gov/bill/119th-congress/house-bill/1340)
- [HUD — Mortgagee Letters](https://www.hud.gov/program_offices/housing/sfh/HOC/HML)
