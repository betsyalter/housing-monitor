# Step 1 — Structural Map of the US Housing Ecosystem

> _Status: 2026-05-01. Default-driven first draft. ASSUMPTION-flagged
> on subsector tier groupings; Wyatt revises via PR._

The 262-ticker universe in `data/fmp_tickers.csv` was assembled around
a single transaction: a US homeowner sells their primary residence to a
buyer who finances, insures, builds, brokers, moves, and improves that
home. Every ticker in the universe captures dollars at one or more
points in the lifecycle of that transaction. The structural map below
groups those tickers by *role*, not by GICS sector — sector
classifications obscure the housing-cycle mechanism because a "Title
Insurance" name (FAF, FNF) and a "Specialty Insurance" name
(travelers, etc.) are sector-cousins in GICS but housing-thesis
strangers.

The map has eight functional layers, plus a cross-cutting policy/
regulatory layer that sits above them all.

---

## Layer 1 — Demand origination and brokerage

Where the buyer-seller match happens. Compensation is volume-linked,
nearly all of it.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Real estate brokers (full service) | RMAX, RDFN, COMP, EXPI, OPEN | 1 | Very high — commission per closed transaction |
| Real estate platforms / data | Z, ZG | 2 | High — ad revenue + leads |
| Real estate brokerage adjacencies | DOMA, AHCO | 3 | Medium |

**Mechanism.** The brokerage layer captures 5-6% of every existing-home
transaction as commission, split between buyer's and seller's agents.
Industry economics are *binary* on the transaction count: zero
transactions, zero revenue. There is no "stable subscription" cushion.
This makes the brokerage layer the highest-beta read on Factor 1
unwind — a 25% volume increase translates almost linearly to a 25%
revenue increase, with operating-leverage amplification.

The brokerage layer is also where the most rapid consolidation is
visible. RMAX's April 2026 takeout by Real Brokerage [Investors.com,
2026-04-27] is one signal in a longer trend toward fewer, larger
platforms — the unlock environment rewards scale (ad spend, lead
matching, agent network effects).

---

## Layer 2 — Mortgage origination and servicing

Where the financing happens.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Mortgage origination (top 5) | RKT, UWMC, PFSI, COOP, LDI | 1 | Very high — gain-on-sale per loan + refi cycle leverage |
| Servicing (rights / MSR) | NMRK, MR | 2 | Medium — counter-cyclical via MSR amortization |
| Wholesale / GSE-adjacent | EFC, NLY, AGNC | 3-4 | Moderate; primarily MBS investment |

**Mechanism.** Origination revenue is $2-8k per loan (~50-200 bps of
loan amount). The 2024-2025 environment has been brutal on origination
volume — most of the book is purchase, not refi, and purchase volume
is itself rate-suppressed. **The originators are the dual-beneficiary
on the unlock:** rate falling drives both purchase volume (via Factor
1) AND refi volume (the existing locked-low cohort can refi the rate
they hold, even without moving). The refi component is independent of
the lock-in mechanism — refi happens whenever the new rate is
materially below the existing rate, which is most of the locked
cohort.

LDI's April 30 8-K [SEC filings] showing the 1.01 + 1.02 + 2.03
refinancing-under-duress combination flags that not all originators
will survive to capture the refi wave when it comes; balance-sheet
strength becomes a sorting mechanism within the layer.

---

## Layer 3 — Construction and homebuilding

Where new supply gets created.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Tier-1 homebuilders | DHI, LEN, NVR, PHM, KBH, TOL | 1 | High — new and existing markets are partial substitutes |
| Tier-2 homebuilders | MTH, TMHC, MHO, GRBK, BZH, CCS, DFH | 1-2 | High |
| Manufactured housing | CVCO, SKY, LGIH (entry-level) | 1-2 | High — entry-level cohort proxy |
| Building products | BLDR, MAS, FBHS, AOS, OC, JELD | 2 | Medium — capital-intensive, high cyclical leverage |
| Lumber and wood | WY, LPX, BCC, RYAM | 2-3 | Medium-high |
| HVAC and mechanical | LII, WAT, TT (Trane) | 2 | Medium — split between new construction and replacement |
| Paint and coatings | SHW, PPG, RPM | 2-3 | Lower — replacement-heavy |

**Mechanism.** New construction is *partial substitute* for existing
homes — when existing-home supply is constrained (the lock-in
environment), some demand spillover goes to new homes. The 2023-2025
period has seen builders capture this spillover via aggressive
incentives (rate buy-downs, closing-cost subsidies). When existing-
home volume normalizes, the substitute effect reverses: builders lose
their pricing-power buffer, but absolute new-home volume can still
grow if total transaction volume expands.

The mid-2026 builder cohort signal (orders +14-37% QoQ, closings -17
to -34% QoQ) [`output/perplexity/weekly/2026-05-04.md`] is consistent
with the pre-recognition phase: order intake is forming around the
unlock thesis, but conversion-to-closing is still gated by the
affordability ceiling. **The diagonal between order growth and
closing throughput is the cleanest builder-cohort signal of the
cycle's inflection point.**

---

## Layer 4 — Asset holding (REITs and institutional)

Where ownership of the housing stock concentrates beyond the
owner-occupied base.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Single-Family Rental REITs | INVH, AMH | 3 | Negative (short on unlock — supply re-emerges if dispositions accelerate) |
| Apartment REITs (HCOL coastal) | EQR, AVB, ESS | 4 | Negative (Tier 4 short basket — see basket file) |
| Apartment REITs (Sun Belt + diversified) | MAA, CPT, UDR, IRT | 4 | Negative |
| Manufactured Housing REITs | ELS, SUI, UMH | 3 | Mixed — defensive on rate-down; thesis-complex |
| Healthcare / Senior Housing | VTR, WELL | 5 | Demographic-wave-positive (boomer aging into 75+) |

**Mechanism.** SFR REITs withhold supply (Factor 2 acquisition wave;
see framework). Apartment REITs over-earn on the involuntary-renter
narrative (Factor 2 second-order; Factor 5 endogenous). Manufactured
housing and senior housing operate on different demographic-wave
mechanics and are thesis-orthogonal — they're in the universe for
correlation-cross-check completeness, not for thesis-positioning.

The asset-holding layer is the thesis's pure short-side: short-on-
unlock baskets sit here exclusively. Long-side of the unlock thesis
sits in Layers 1-3 + 5-7.

---

## Layer 5 — Title and transaction services

Where the closing-day services live.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Title insurance (top 4) | FAF, FNF, STC, ORI | 1 | Very high — premium per closed transaction |
| Closing services / e-mortgage | DOC, BLNDA | 2-3 | High |

**Mechanism.** Title insurers earn 0.5-1% of home price per closing
($2-4k per $400k home). Like brokerage, the revenue is binary on
transactions. Title insurers have tighter operating leverage than
brokers because the cost base is more variable (claims expense scales
with policy count, not just headcount), but the volume sensitivity is
similar.

STC's -0.65 Pearson correlation to mortgage_rate_30yr [Script 09
output] is the cleanest "Factor 1 long" signal in the universe;
title-insurance subsector is one of the highest-conviction layers
when the unlock catalyst fires.

---

## Layer 6 — Aftermarket and improvement

Where the *post-transaction* dollars flow.

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Home improvement retail | HD, LOW | 1 | Medium — mover-cohort spend is ~10-15% of total |
| Furnishings | W, RH, RST, LZB, LEG, SNBR | 2 | Medium-high |
| Appliances | WHR, GNRC | 2 | Medium |
| HVAC service | WSO, LII | 2 | Medium |
| Pool / outdoor | POOL, LESL, SITE | 2-3 | Lower beta to housing volume; weather-correlated |
| Flooring and fixtures | LL, FND, MHK | 3 | Medium |
| Garage / storage / lawn | GRMN, LSI, UHAL | 3-4 | Lower |

**Mechanism.** A typical mover spends $10-15k on furnishings,
appliances, and improvements within 90 days of closing [NAR Profile
of Home Buyers and Sellers]. The aftermarket layer captures this
"move-trigger" spend disproportionately. Home improvement retail is
the largest single channel; furnishings and appliances are close
behind.

The aftermarket layer's beta is lower than Layers 1, 2, 5 because the
mover-cohort spend is a fraction of total revenue (HD/LOW have large
DIY and pro-contractor channels independent of housing-transaction
volume). But on the margin, the mover spend is the *growth lever* —
HD/LOW comp performance during transaction-volume normalization
periods has historically tracked the +200-300 bps incremental that
the mover cohort brings.

---

## Layer 7 — Insurance and risk transfer

| Subsector role | Representative tickers | Tier | Beta to existing-home volume |
|---|---|---|---|
| Property and casualty (homeowner-heavy) | ALL, TRV, PGR | 3 | Lower — premium grows with stock, not transactions |
| Reinsurance | RNR, EVER, RGA | 3 | Lower |
| Mortgage insurance (PMI) | MTG, ESNT, RDN, ACT | 2 | High — linked to mortgage origination volume |

**Mechanism.** PMI is the highest-beta sub-layer here (it's mechanically
tied to LTV-driven loan origination), but the broader P&C insurance
layer is lower-beta because the policy-in-force base is the housing
*stock*, which is structural, not the transaction *flow*. Climate-
risk-driven premium hardening in coastal Florida and California is its
own mechanism, tangentially relevant to apartment-REIT-short Factor-5
dynamics in those markets.

---

## Layer 8 — Adjacent / second-order

| Subsector role | Representative tickers | Tier | Beta |
|---|---|---|---|
| Moving / storage | UHAL, LSI, EXR, CUBE | 3 | Medium |
| Specialty retail (housing-adjacent) | TGT, COST | 5 | Low (broad consumer exposure) |
| Construction materials (cement, aggregate) | EXP, MLM, USCR, CX | 3 | Lower |

These are the second-order names — exposure to housing volume but
materially diluted by other revenue drivers. Generally Tier 3-5.
Useful for portfolio context (subsector-correlation hedging) but not
for thesis-driver positioning.

---

## Cross-cutting Layer — Policy and regulatory

Sits above all eight functional layers. Operates through:

- **Section 121** capital gains exclusion (sellers' tax friction)
- **Assumable mortgage reform** (rate-lockin direct attack)
- **GSE conservatorship structure** (mortgage rate transmission channel)
- **FHFA / HUD rule-makings** (qualifiable-buyer pool)
- **Treasury / FOMC** (the rate path itself)
- **Tariffs on building materials** (Layer 3 cost-side input)

The policy layer doesn't have its own "tickers" but moves the relative
attractiveness of every other layer. See `06_political_economy.md`
for a ranked reading of which policy lever has highest leverage on the
thesis horizon.

---

## How the layers interact (the thesis transmission)

Per Investment Research Training Manual v5.0 (L817), each transmission
channel must be modeled separately because each lags differently:

```
Factor 1 (rate falls)
  → Mortgage rate transmits 1-2 weeks (Layer 2: refi volume up first)
  → Brokerage activity 4-8 weeks (Layer 1: pending-home-sales rises)
  → Title insurance 8-12 weeks (Layer 5: closings convert)
  → Builders' orders 8-16 weeks (Layer 3: pre-existing backlog clears
    + new orders form)
  → Builders' closings 6-12 months later (Layer 3 again)
  → Aftermarket spend 3-6 months after closing (Layer 6)
  → Insurance / PMI 6-12 months (Layer 7, lagging origination)
  → REIT NOI signal 12-24 months (Layer 4 — slowest lag, but largest
    multiple-compression effect when narrative shifts)
```

This is the layered transmission. The implication: **Layers 1, 2, 5
move first** (within 1-3 months of the rate-path inflection); Layer 3
moves at 3-12 months; Layer 6 moves at 6-12 months; Layer 4 (the
short side) moves last but largest. Position-building sequences
follow the lag structure.

---

## Universe summary as input to Step 5 (Stock Scoring)

The 262-ticker universe distributes across the layers approximately:

| Layer | Ticker count (rough) | Typical thesis positioning |
|---|--:|---|
| 1 — Brokerage | 8-10 | Long (high beta) |
| 2 — Mortgage origination | 12-15 | Long (high beta + refi component) |
| 3 — Construction | 50-60 | Long (Tier 1-2 builders + suppliers) |
| 4 — Asset holding | 35-40 | Mixed (SFR long; apartment short basket) |
| 5 — Title / transaction services | 6-8 | Long (high beta) |
| 6 — Aftermarket / improvement | 60-70 | Long (medium beta) |
| 7 — Insurance | 10-15 | Lower beta; selective |
| 8 — Adjacent / second-order | 20-30 | Pass / context |

**Step 5 will rank-aggregate these into thesis-exposure scores using
Script 09 correlations weighted by factor weights, validated against
Lynch category and Profile/Archetype.**

---

## Open questions for Wyatt's revision

- _ASSUMPTION:_ Layer-1 brokerage classification of OPEN (Opendoor)
  and DOMA (Doma Holdings) — should these be split out as
  "iBuyer / digital-disruption" subsector rather than mixed into
  brokerage? The thesis exposure differs (iBuyers have inventory-
  carry risk; brokers don't).
- _ASSUMPTION:_ Layer-2 inclusion of EFC/NLY/AGNC (mortgage REITs).
  These are technically Layer 4 (asset holding) but the asset they
  hold is MBS, which is closer to Layer 2 financing. I've placed them
  here; revise if needed.
- _ASSUMPTION:_ Layer-7 mortgage insurance (PMI) names. Treated as
  high-beta sub-layer; could argue these belong in Layer 2.
- _ASSUMPTION:_ Senior housing (VTR, WELL) — kept in Layer 4 but
  flagged as demographic-wave-positive rather than unlock-positive.
  These are arguably their own "thesis-orthogonal" layer that
  shouldn't be part of the unlock-thesis ranking.

The default classification above is the input to Step 5; Wyatt's
revisions cascade through stock scoring.
