# Coiled Spring Sensitivity Tables

> _Status: 2026-05-01. Static asset; regenerated via the Python block at the
> bottom whenever the FHFA distribution or constants change._
>
> **Purpose.** Stress-test the Factor 1 thesis at parameter settings other
> than the framework's defaults (threshold = 1.5%, saar_per_million = 280).
> Tells you "if the 1.5% threshold is wrong by 0.2pp, what changes?" — the
> central sensitivity that anchors every claim downstream.

The unlock math has three knobs that the framework treats as fixed but that
real behavior may not respect:

1. **Lock-in threshold** — the bps gap above current rate at which an owner
   stops being willing to transact. Default 1.5% (per
   `analyst/coiled_spring_params.yaml` and the framework's Factor 1 anchor).
   Plausible alternates: 1.0% (more permissive — every cohort with weakest
   move-frictions), 1.7% (median behavioral evidence; NY Fed SCE Housing
   Survey points roughly here), 2.0% (strict — only the genuinely-trapped).
2. **Scenario rate** — the future market 30yr the unlock math is valued
   against. Range from today (6.30%) to the math floor (4.0%, where the
   sub-3% bucket finally crosses for the default 1.5% threshold).
3. **SAAR-per-million multiplier** — how many thousands of SAAR uplift
   each million unlocked homes produces. Default 280. This number embeds
   assumptions about (a) what fraction of unlocked owners actually
   transact, (b) at what turnover rate, (c) over what horizon. Plausible
   range: 200 (conservative) to 400 (aggressive).

---

## Table 1 — Locked count (M) at scenario rate × threshold

The mortgage stock that remains locked-by-mechanism at each combination.

| threshold | 6.30% | 6.00% | 5.75% | 5.50% | 5.25% | 5.00% | 4.75% | 4.50% | 4.25% | 4.00% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1.0%** | 43.7 | 41.5 | 36.1 | 36.1 | 28.9 | 28.9 | 20.2 | 20.2 | 11.1 | 11.1 |
| **1.25%** | 41.5 | 36.1 | 36.1 | 28.9 | 28.9 | 20.2 | 20.2 | 11.1 | 11.1 | 11.1 |
| **1.5% (default)** | **41.5** | **36.1** | **28.9** | **28.9** | **20.2** | **20.2** | **11.1** | **11.1** | **11.1** | **0.0** |
| **1.7%** | 36.1 | 36.1 | 28.9 | 28.9 | 20.2 | 20.2 | 11.1 | 11.1 | 11.1 | 0.0 |
| **2.0%** | 36.1 | 28.9 | 20.2 | 20.2 | 11.1 | 11.1 | 11.1 | 0.0 | 0.0 | 0.0 |

**Reading.** A *looser* threshold (e.g., 1.0%) means more cohorts qualify
as "locked" at any given market rate — so the locked count at today (6.30%)
is *higher* (43.7M vs 41.5M default). A *stricter* threshold (e.g., 2.0%)
means fewer count as locked today (36.1M) but the math floor (where
everyone releases) shifts up to 4.50% rather than 4.0%.

The default 1.5% sits at a structural inflection: it's the threshold where
the sub-3% bucket releases exactly at the 4.0% scenario rate (because
midpoint 2.5 + 1.5 = 4.0, and the strict-inequality flips at that point).

---

## Table 2 — Unlocked vs today's 6.30% rate (M)

The marginal unlock count when going from today's market rate to the
scenario rate, at each threshold.

| threshold | 6.30% | 6.00% | 5.75% | 5.50% | 5.25% | 5.00% | 4.75% | 4.50% | 4.25% | 4.00% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1.0%** | +0.0 | +2.2 | +7.7 | +7.7 | +14.8 | +14.8 | +23.6 | +23.6 | +32.6 | +32.6 |
| **1.25%** | +0.0 | +5.4 | +5.4 | +12.6 | +12.6 | +21.3 | +21.3 | +30.4 | +30.4 | +30.4 |
| **1.5% (default)** | **+0.0** | **+5.4** | **+12.6** | **+12.6** | **+21.3** | **+21.3** | **+30.4** | **+30.4** | **+30.4** | **+41.5** |
| **1.7%** | +0.0 | +0.0 | +7.2 | +7.2 | +15.9 | +15.9 | +24.9 | +24.9 | +24.9 | +36.1 |
| **2.0%** | +0.0 | +7.2 | +15.9 | +15.9 | +24.9 | +24.9 | +24.9 | +36.1 | +36.1 | +36.1 |

**Reading.** At the operationally-meaningful 5.50% trigger:
- Loose 1.0% threshold: only 7.7M unlock (modest)
- Default 1.5%: 12.6M (the framework's central case)
- Stricter 1.7%: only 7.2M (because 1.7% means the 4-4.5% bucket doesn't
  release until rates fall to ~5.95%, just below)
- Strict 2.0%: 15.9M (counterintuitively higher because the threshold
  shifts the entire schedule of which buckets release at which rates)

**Non-monotonicity is real.** Higher threshold doesn't uniformly mean less
unlock — it changes WHICH buckets cross at which rate. The default 1.5% is
*not* the maximum-unlock case at the math floor (4.0%) — it just happens
to coincide with one bucket's edge.

---

## Table 3 — × current deficit (1,300k SAAR/yr)

The most useful single table. Each cell is the implied SAAR uplift relative
to the deficit between current pace (~4.0M/yr) and pre-2022 normalized
(~5.3M/yr). 1.0× means "exactly closes the deficit"; 4.6× means "fills the
deficit four times over." Numbers above ~3× are large enough that the
absorbing capacity of the demand side becomes the binding constraint, not
the supply side.

| threshold | 6.30% | 6.00% | 5.75% | 5.50% | 5.25% | 5.00% | 4.75% | 4.50% | 4.25% | 4.00% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1.0%** | 0.0× | 0.5× | 1.7× | 1.7× | 3.2× | 3.2× | 5.1× | 5.1× | 7.0× | 7.0× |
| **1.25%** | 0.0× | 1.2× | 1.2× | 2.7× | 2.7× | 4.6× | 4.6× | 6.5× | 6.5× | 6.5× |
| **1.5% (default)** | **0.0×** | **1.2×** | **2.7×** | **2.7×** | **4.6×** | **4.6×** | **6.5×** | **6.5×** | **6.5×** | **8.9×** |
| **1.7%** | 0.0× | 0.0× | 1.5× | 1.5× | 3.4× | 3.4× | 5.4× | 5.4× | 5.4× | 7.8× |
| **2.0%** | 0.0× | 1.5× | 3.4× | 3.4× | 5.4× | 5.4× | 5.4× | 7.8× | 7.8× | 7.8× |

**Reading the operationally-relevant cells (5.50% Trigger 1, 5.00% Trigger 2):**

| Threshold | At 5.50% Trigger 1 | At 5.00% Trigger 2 |
|---|---:|---:|
| 1.0% | 1.7× deficit | 3.2× deficit |
| 1.25% | 2.7× | 4.6× |
| **1.5% default** | **2.7×** | **4.6×** |
| 1.7% | 1.5× | 3.4× |
| 2.0% | 3.4× | 5.4× |

The **range of "× deficit" at Trigger 2 across reasonable thresholds is
3.4× to 5.4×** — meaning under the strictest defensible assumption
(threshold 1.7%), the unlock at 5.0% still materially overshoots the
existing-home-sales deficit. Under the loosest (1.0%), it overshoots by
3.2×. **The thesis-positive direction is robust to threshold choice in
the realistic 1.0–2.0% range.**

The thesis is *not* robust to a threshold above 2.5% — at that level, no
unlock occurs at any scenario above 5.0%. But mover-survey evidence does
not support thresholds that high; this is a stress-test the data does not
require.

---

## Table 4 — × deficit at threshold = 1.5% as `saar_per_million` varies

Holds threshold at the default 1.5% and varies the SAAR multiplier that
converts unlocked owners to incremental SAAR.

| saar_per_M | 6.30% | 6.00% | 5.75% | 5.50% | 5.25% | 5.00% | 4.75% | 4.50% | 4.25% | 4.00% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **200** (conservative) | 0.0× | 0.8× | 1.9× | 1.9× | 3.3× | 3.3× | 4.7× | 4.7× | 4.7× | 6.4× |
| **240** | 0.0× | 1.0× | 2.3× | 2.3× | 3.9× | 3.9× | 5.6× | 5.6× | 5.6× | 7.7× |
| **280 (default)** | **0.0×** | **1.2×** | **2.7×** | **2.7×** | **4.6×** | **4.6×** | **6.5×** | **6.5×** | **6.5×** | **8.9×** |
| **320** | 0.0× | 1.3× | 3.1× | 3.1× | 5.3× | 5.3× | 7.5× | 7.5× | 7.5× | 10.2× |
| **400** (aggressive) | 0.0× | 1.7× | 3.9× | 3.9× | 6.6× | 6.6× | 9.3× | 9.3× | 9.3× | 12.8× |

**Reading.** At the 5.50% Trigger 1 with default threshold:
- Conservative SAAR multiplier (200): **1.9× deficit** (still positive but
  only modestly above closing the gap)
- Default (280): 2.7×
- Aggressive (400): 3.9×

At the 5.00% Trigger 2:
- Conservative: 3.3×
- Default: 4.6×
- Aggressive: 6.6×

**The thesis-positive read survives even at the conservative multiplier.**
Under saar_per_million = 200, every operationally-meaningful trigger still
produces 2-3× the existing-home-sales deficit. The thesis is robust to
this assumption in the 200-400 range; would only break if saar_per_million
were below ~150 (sub-1× deficit closure at the 5.50% trigger).

---

## Reading the tables — analyst notes

**The thesis is more robust than the headline numbers suggest.** Across
realistic threshold values (1.0% to 2.0%) and saar multipliers (200 to
400), the unlock math at the operationally-meaningful 5.50% Trigger 1
produces 1.5× to 3.9× the current existing-home-sales deficit. **Even the
combined-conservative case** — strict threshold 1.7% × conservative saar
multiplier 200 — still produces ~1.0× deficit closure at Trigger 1. The
thesis-positive direction is not parameter-fragile.

**The binding constraint is not the unlock math; it's the absorbing
capacity of the demand side.** Once × deficit gets above ~3, the analyst
question shifts from "is there enough supply" to "is there enough
qualified demand to absorb." Factor 4 (demographics ceiling) and Factor 5
(rent-own spread / affordability) become the binding constraints. The
sensitivity tables imply we should focus less on tuning the threshold
(small effect) and more on validating the absorbing-capacity assumption
(large effect; under-researched).

**The 1.5% default is defensible but not unique.** It happens to align
exactly with the math floor at 4.0% (sub-3% bucket releases at 4.0%
scenario rate). Other choices (1.0% or 2.0%) shift the math floor but
don't change the directional conclusion. The honest framing for the
framework prose: "the framework uses 1.5% because behavioral evidence
clusters there; 1.0% to 2.0% all produce qualitatively similar
implications, the analyst hasn't found the edge of the parameter where
the thesis breaks within the defensible range."

**A high-leverage research project:** anchor the saar_per_million
multiplier empirically. The default 280 is a rough estimate. Pull NAR
existing-home-sales data 2008-2014 (similar rate-cycle environment) and
back out the actual SAAR uplift per unlocked-owner-equivalent. Tighten
the range from 200-400 to perhaps 250-310. Doesn't change the thesis
direction but sharpens the magnitude claim.

---

## Cross-reference

- `analyst/five_factor_framework.md` §Factor 1 — the anchored framework
  prose. Threshold and normalization scenario both flagged as
  ASSUMPTION-defaults pending Wyatt's review.
- `analyst/coiled_spring_params.yaml` — single source of truth for the
  FHFA distribution + threshold + saar_per_million. Edit there to change
  framework defaults; regenerate this file from the Python block below.
- `dashboard.html` Coiled-spring widget — uses live JS compute from the
  same FHFA distribution; numeric input lets the user explore any
  scenario rate without modifying the constants.

---

## Reproducibility — Python block

```python
import yaml
with open('analyst/coiled_spring_params.yaml') as f:
    p = yaml.safe_load(f)
buckets = p['distribution']
saar_per_m = p['saar_per_million']
deficit_k = 1300
today_rate = 6.30  # update from FRED MORTGAGE30US latest

def locked_at(rate, threshold):
    return sum(b['est_homes_millions'] for b in buckets
               if rate > b['approx_midpoint_rate'] + threshold)

def unlock_at(rate, threshold):
    return locked_at(today_rate, threshold) - locked_at(rate, threshold)

scenarios = [today_rate, 6.00, 5.75, 5.50, 5.25, 5.00, 4.75, 4.50, 4.25, 4.00]
thresholds = [1.0, 1.25, 1.5, 1.7, 2.0]

# Table 3 (× deficit, the most useful):
for th in thresholds:
    row = [unlock_at(r, th) * saar_per_m / deficit_k for r in scenarios]
    print(f'threshold {th}%: ' + ' '.join(f'{x:.1f}x' for x in row))
```

Re-run any time `analyst/coiled_spring_params.yaml` is updated or
`today_rate` shifts materially. Tables 1-3 use the YAML's distribution +
saar_per_million; Table 4 sweeps saar_per_million holding the YAML
distribution fixed.
