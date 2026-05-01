# Weekly Housing Monitor — v3 Patch (legislative scuttlebutt monitoring)

> Apply on top of v2. Adds explicit legislative + policy scouring per
> coordination note `docs/coordination/2026-05-01-legislative-monitoring.md`.

## Change 1 — Add §8a: Legislative scuttlebutt monitoring (load-bearing)

Insert as a new mandatory step in the workflow (after Step 8 External
Event Scan). The principal's thesis includes administration moves to
jumpstart housing — those signals must be detected before they hit
Bloomberg/Reuters/WSJ. The pipeline's news-stream catches policy items
*after* mainstream coverage. Your job is to catch them *before*.

**Sources to scour every run** (trailing 7 days):

| Source | Why |
|---|---|
| `congress.gov` | Bills introduced or marked-up; House Financial Services + Senate Banking committee activity |
| White House pressroom (`whitehouse.gov/briefing-room/`) | Executive orders, fact sheets, signed legislation |
| Treasury (`home.treasury.gov/news/press-releases`) | Conservatorship signals, GSE policy, MBS rule-makings |
| HUD (`hud.gov/press`) | FHA rule changes, down-payment assistance, secretary statements |
| FHFA (`fhfa.gov/news`) | Conforming loan limits, conservatorship, credit-scoring, assumable-mortgage policy |
| Politico Pro / Punchbowl / The Hill | DC trade press housing coverage |
| Twitter/X — `@POTUS`, `@SecretaryHUD`, `@SecBessent`, `@FHFA`, `@MBAMortgage`, `@NAHBhome`, `@NAR_Govt` | Real-time policy tells |
| Sell-side DC analysts — Cowen Washington Research Group, Capital Alpha Partners, Compass Point Research | Buy-side-grade DC interpretation |
| HousingWire, Inman, RealtorMag | Real estate trade press |

**Specific levers to track each week** (any movement = report it):

- **Section 121** — capital gains exclusion expansion (currently $250K
  / $500K, unchanged since 1997). Highest-leverage Factor 1 lever:
  reduces tax friction on selling primary residences, directly attacks
  lock-in.
- **Assumable mortgage reform** — FHFA could expand assumability
  beyond VA/FHA. Mechanically increases the value of moving for locked
  owners (the buyer assumes the seller's sub-4% rate). Direct Factor 1
  catalyst.
- **GSE conservatorship exit** — if Treasury moves on Fannie/Freddie,
  mortgage-rate behavior shifts materially. Factor 1 (rates) + Factor
  4 (credit availability).
- **Down-payment assistance / first-time-buyer credits** — Factor 4
  affordability ceiling lever.
- **1031 exchange reform** — capital tied up in deferred-gains
  property unlocks if 1031 narrows; second-home and investor turnover.
- **Tax credit housing expansion (LIHTC)** — supply-side response.
- **Executive orders on housing** — any.
- **Treasury or FHFA rule-makings on housing** — any.
- **Tariffs affecting building materials** — lumber, steel, cement;
  cost-side input to Factor 1 (Fed constraint via inflation pass-through).

## Change 2 — Output destination

Legislative-monitoring content sits inside the standard weekly report
under a new required section: **"Legislative & Policy Watch"** —
between "Material policy / legislative events" (existing) and "Key
risk."

A separate file `analyst/perplexity_outputs/policy_watch_YYYY-WNN.md`
is written in parallel containing only the legislative content (more
exhaustive than the report version). The dashboard's policy-watch
section reads from that file. The weekly report's "Legislative &
Policy Watch" section is a curated subset (top 3-5 items only).

## Change 3 — Format for the new section

For each item:
- **Source** (URL — required, including for X/Twitter posts)
- **Date** (when posted/announced/marked-up)
- **What it is** (1-2 sentences)
- **Lever it touches** (which of the 7 levers above, or "other — describe")
- **Direction for thesis** (+ / 0 / − with one-sentence reasoning)
- **Watchlist trigger** — what would need to happen next to escalate this from "track" to "act on"

## Change 4 — Calibration discipline

Two failure modes to actively avoid:

1. **Headline-noise inflation.** A senator tweeting about housing is
   not a policy event. A senator introducing a bill, signing onto a
   bipartisan letter, or being named to a relevant committee chair is
   a policy event. The discipline: a "policy event" requires a
   procedural action with a paper trail, not a sentiment expression.

2. **Conservative bias toward inaction.** Most policy proposals die in
   committee. Default direction for a "newly introduced bill" without
   bipartisan markup is `0` (no thesis update yet). Move to `+/−` only
   when (a) a bill clears committee, (b) a markup schedule is set, or
   (c) a White House signing-statement signal is on record.

## Why these changes

Per `docs/coordination/2026-05-01-legislative-monitoring.md`:
> "Betsy's thesis hardened — *she suspects the administration will move
> legislatively to jumpstart housing despite high mortgage rates, and
> we should be detecting it before it hits the tape.*"

Engineering's parallel build (Script 15 — Congressional bill tracker,
expanded news keywords, DC trade press in `news_sources.yaml`) catches
the structured signal. This patch puts the *interpretive layer* on top.

— Wyatt's Claude
