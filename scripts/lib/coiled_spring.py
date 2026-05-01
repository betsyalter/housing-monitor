"""Coiled spring math: pent-up housing transaction volume unlocked as rates fall.

Thesis: ~70% of US mortgages are below 4%; rates above ~6% trap sellers because
moving means trading their below-market mortgage for a market-rate one. As
market rates fall, owners progressively unlock — those at lower locked-in
rates only move when market rates fall to (their_rate + threshold).

Inputs (from analyst/coiled_spring_params.yaml):
  - distribution: rate buckets with pct_of_outstanding + est_homes_millions
  - baseline_market_rate, lockin_threshold, saar_per_million

Outputs:
  - locked_at(rate): millions of homes whose owners are locked at `rate`
  - unlock_scenarios(grid): table of locked/unlocked/SAAR-uplift across rates
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RateBucket:
    midpoint: float
    pct: float
    homes_millions: float


@dataclass(frozen=True)
class UnlockScenario:
    scenario_rate: float
    locked_millions: float
    unlocked_vs_today_millions: float
    saar_uplift_k: float


def buckets_from_yaml(distribution: list[dict]) -> list[RateBucket]:
    return [
        RateBucket(
            midpoint=float(b["approx_midpoint_rate"]),
            pct=float(b["pct_of_outstanding"]),
            homes_millions=float(b["est_homes_millions"]),
        )
        for b in distribution
    ]


def locked_at(market_rate: float, threshold: float, buckets: Iterable[RateBucket]) -> float:
    """Total millions of homes whose owners are locked in at `market_rate`.

    A bucket is locked when market_rate > midpoint + threshold (strict >).
    """
    return sum(b.homes_millions for b in buckets if market_rate > b.midpoint + threshold)


def unlocked_vs_baseline(
    scenario_rate: float,
    baseline_rate: float,
    threshold: float,
    buckets: Iterable[RateBucket],
) -> float:
    bs = list(buckets)
    return locked_at(baseline_rate, threshold, bs) - locked_at(scenario_rate, threshold, bs)


def unlock_scenarios(
    baseline_rate: float,
    threshold: float,
    buckets: Iterable[RateBucket],
    rate_grid: Iterable[float],
    saar_per_million: float = 280.0,
) -> list[UnlockScenario]:
    bs = list(buckets)
    out: list[UnlockScenario] = []
    for r in rate_grid:
        unlocked = unlocked_vs_baseline(r, baseline_rate, threshold, bs)
        out.append(
            UnlockScenario(
                scenario_rate=r,
                locked_millions=locked_at(r, threshold, bs),
                unlocked_vs_today_millions=unlocked,
                saar_uplift_k=unlocked * saar_per_million,
            )
        )
    return out
