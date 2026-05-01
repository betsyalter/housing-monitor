# Reference reports

Third-party research drops Betsy uploaded for the deep-dive report. **Read these before drafting the Five-Factor Framework prose / Apartment-REIT short basket / Stock scoring sections** — they're the analytical context the buy-side report sits on top of.

## Macro / structural

- **`FILE_4211.pdf` — Apollo "US Housing Outlook" (Torsten Slok et al, January 2026, 126 slides)**
  Buy-side macro deck. The empirical anchors for the structural-vs-cyclical framework. Key data points to cite (slide references):
  - Slide 38: 95% of US mortgages are 30-year fixed-rate — the structural lock-in mechanism.
  - Slide 72: >50% of mortgages outstanding have rate <4% (matches our coiled-spring math).
  - Slide 68: 2.4M home deficit (supply-side anchor).
  - Slide 31, 32: Median age of homebuyers 59 (was 31 in 1981); first-time buyer 40 (was 30 in 2008).
  - Slide 13: First-time-buyer share declining structurally, not cyclically.
  - Slide 90: Median sales price $403K.
  - Slide 50, 67-68: Inventory low across all price tiers.
  - Slides 110-113: Side-by-side comparison to Volcker-era slowdown.
  - Slide 114: "Fastest Fed-driven housing slowdown on record."

## Industry / cohort

- **`U.S. Homebuilding and Building Products_ Earnings Catch-Up_ HLMN, JELD, TOL.pdf`** — Multi-name industry note covering recent earnings prints from Hillman (HLMN), Jeld-Wen (JELD), and Toll Brothers (TOL). Useful for cohort-positioning context spanning building products and homebuilders.

## DHI (D.R. Horton — Tier 1, volume leader)

- **`2026-04-22-DHI.N-BTIG-2Q26 EPS Beats, Upbeat Commentary on Demand. Reiterate Buy.pdf`** — BTIG note on Q2 print (April 22). Their take on DHI specifically + cohort read.
- **`D.R. Horton Inc._ Steady Hand in a Choppy Demand Environment.pdf`** — Equity research note framing DHI relative to peers.
- **`DHI FY2Q26 earnings debrief takeaways.pdf`** — Compact post-earnings analytical recap.
- **`Morningstar Equity Analyst Report DHI.pdf`** — Morningstar's view (different methodology — moat / fair-value framing).
- **`Wells Fargo DHI Note 4-23-26.pdf`** — Wells Fargo sell-side post-print.

## NVR (Tier 1, build-to-order — highest-margin model)

Different operating model than DHI or TOL — NVR doesn't speculate on land, only builds when there's a signed contract. Lowest inventory risk, highest gross margin, but slowest to flex up when demand returns. Q1 2026 print was weak; sell-side flagging margin pressure and pricing adjustments.

- **`2026-04-23-NVR.N-Truist Securities-NVR - 1Q26 Earnings - Stock Down On Margin Performance And D.pdf`** — Truist note on Q1 print, stock-down explanation focused on margin compression.
- **`NVR, Inc._ Post-Call Notes_ We Believe 1Q Demand Slowed in March, Prompting Further Pricing Adjustments_ Slightly Raising Our Ests, PT_ Neutral.pdf`** — Post-call sell-side analysis. Notes March demand slowdown drove pricing adjustments.
- **`NVR Final_ Weak 1Q Results, Estimates Moving Lower.pdf`** — Sell-side estimate cuts.

## TOL (Toll Brothers — Tier 1, luxury/move-up)

Key counterweight to DHI's entry-level/volume thesis — TOL is positioned for higher-income, less rate-sensitive buyers. The TOL coverage cluster lets Wyatt write the **"market segmentation by income cohort"** angle of the deep dive.

- **`2026-02-19-TOL.N-Citizens-F1Q26 Recap Early Spring Signals Appear Positive, FY26 Guid.pdf`** — Citizens Bank on TOL F1Q26 print, early-spring read.
- **`Toll Brothers_ Post-Call Notes_ FY26 Guide Reiterated Across All Key Metrics, Slightly Raising Our FY26-27E and PT, Maintain Relative OW Rating.pdf`** — Sell-side post-call notes, raised estimates, OW maintained.
- **`Wells Fargo TOL Note 2-20-26.pdf`** — Wells Fargo post-Q1 note (companion to their DHI April note).
- **`FQ1 Down the Fairway, TOL Remains Best-Positioned.pdf`** — Sell-side framing TOL as best-positioned vs. peers in current environment.
- **`TOL Final_ One of the Best Houses in the Neighborhood.pdf`** — Bullish thematic note on TOL's relative strength.

## PHM (PulteGroup — Tier 1, mix-shift to entry/active-adult)

PHM bridges DHI's entry-level volume play and TOL's move-up positioning — they run a deliberate three-segment mix (entry / move-up / active-adult). Q1 2026 print: 2026 guidance reiterated but gross margins now likely at the lower end of the range, prompting estimate-trims and "sidelined-on-valuation" calls. Useful for the "mid-cycle margin compression" cohort read where rate-sensitivity is real but not catastrophic.

- **`2026-04-24-PHM.N-Oppenheimer  Co., I-Model Update_ 2026 Guide Reiterated, Execution Remains Stron...-121617753 (1).pdf`** — Oppenheimer model update post-print.
- **`PHM 1Q26 earnings debrief takeaways.pdf`** — Compact post-earnings analytical recap (matches the DHI debrief format).
- **`PHM_ 1Q26 Conference Call Takeaways.pdf`** — Conference call read-through.
- **`PulteGroup Inc._ More 2H Weighting Pending Better Mix_ Sidelined on Valuation.pdf`** — Cautious sell-side framing — guide intact but mix-shift back-half-loaded, valuation no longer compelling.
- **`PulteGroup Inc._ Post-Call Notes_ 2026 Guidance Reiterated Although GMs Now Likely at Lower End of Range_ Slightly Lowering Our Ests, PT_ Overweight. Fri Apr 24 2026.pdf`** — Sell-side post-call notes, estimates trimmed, OW maintained.
- **`Wells Fargo PHM Note 5-1-26.pdf`** — Wells Fargo PHM note (5/1/26) — completes the Wells Fargo Tier-1 set (DHI 4-23, TOL 2-20, PHM 5-1).

## How to use these in the deep dive

DHI = volume leader. TOL = move-up/luxury. NVR = high-margin build-to-order. PHM = mix-shift across entry/move-up/active-adult. **Four distinct operating models** in Tier 1, each with different rate-sensitivity. Use all four clusters as **calibration points** for what the Street is saying — confirms / disconfirms / extends Wyatt's Five-Factor Framework reads. Specifically:

- The DHI / NVR / TOL / PHM notes have order/backlog/cancel commentary that maps directly to our `homebuilder_ops.csv` Q1 2026 data. Cross-checking these against our Haiku-extracted ops gives us a sell-side ground-truth for cohort patterns.
- **The NVR weakness vs TOL strength is itself signal** — NVR's build-to-order model means they need confirmed contracts; weak Q1 demand hits them first. TOL's luxury cohort is more rate-insensitive and is reiterating guidance. Map this to Wyatt's Step 2 (Demand Cohorts) as the bifurcating affordability story.
- **PHM is the mid-cycle tell** — guide reiterated but margins at the lower end, mix shift back-half-loaded, valuation calls turning cautious. If PHM (which is the most "average" Tier-1 by mix) starts under-delivering on margins while TOL's luxury holds, that's confirmation the affordability bifurcation is real — not just a TOL-luxury halo.
- TOL ASP ~$977K vs DHI ASP ~$361K vs NVR ASP ~$457K vs PHM ASP ~$570K spans the affordability spectrum — direct support for the median-buyer-age findings in Apollo deck slides 31–32.
- The HLMN/JELD/TOL multi-name note is useful for Step 3 (Value Chain) — building products vs homebuilders read.
- The Morningstar fair-value framework is the right lens for the Stock-Scoring section (Step 5 of Part 12).
- The Apollo deck is the **macro spine** for the Structural Map (Step 1) and Wave Position (Step 4) sections — its thesis-direction frames where we are in the cycle.

These materials are NOT a substitute for the framework — Wyatt's read is the value-add. They're the empirical and cohort-positioning context.

## Coverage gaps

We now have heavy DHI + TOL + NVR + PHM coverage spanning four Tier-1 operating-model archetypes. Other Tier-1 builders (LEN, KBH, MTH, MHO) and the apartment REIT short basket (EQR, AVB, MAA, CPT, UDR, ESS) lack equivalent sell-side context. Wyatt: drop sell-side notes for those — especially the apartment REIT thesis — in this folder as `<source>_<ticker>_<date>.pdf` and re-run the README.
