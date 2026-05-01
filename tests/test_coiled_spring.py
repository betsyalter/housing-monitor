"""Coiled spring math regression. Anchor values come from
data/coiled_spring_scenarios.csv (Betsy's first FHFA-derived run).
"""
from __future__ import annotations

import pytest

from lib.coiled_spring import (
    buckets_from_yaml,
    locked_at,
    unlock_scenarios,
    unlocked_vs_baseline,
)
from lib.yaml_config import load_coiled_spring_params


@pytest.fixture
def params():
    return load_coiled_spring_params()


@pytest.fixture
def buckets(params):
    return buckets_from_yaml(params["distribution"])


def test_distribution_pct_sums_to_one(params):
    pct = sum(b["pct_of_outstanding"] for b in params["distribution"])
    assert 0.999 < pct < 1.001


def test_lockin_at_baseline_matches_fhfa_csv(buckets):
    """At baseline 6.5% with threshold 1.5: locked = 41.5036M.
    Anchor: data/coiled_spring_scenarios.csv row 1.
    """
    locked = locked_at(market_rate=6.5, threshold=1.5, buckets=buckets)
    assert abs(locked - 41.5036) < 1e-6


def test_lockin_strict_inequality_at_625(buckets):
    """Strict > means a bucket exactly at midpoint+threshold is NOT locked.
    At market 6.25, threshold 1.5: the 4.5-5% bucket (mid 4.75) is exactly
    at boundary and should NOT be locked. Anchor: scenarios.csv row 2 → 36.068M.
    """
    locked = locked_at(market_rate=6.25, threshold=1.5, buckets=buckets)
    assert abs(locked - 36.068) < 1e-6


def test_unlock_at_5pct(buckets):
    """At 5%, dropping from 6.5% baseline unlocks 21.336M.
    Anchor: scenarios.csv row 7 (scenario_rate=5.0).
    """
    unlocked = unlocked_vs_baseline(5.0, 6.5, 1.5, buckets)
    assert abs(unlocked - 21.336) < 1e-6


def test_full_scenario_grid_matches_csv(buckets, params):
    """Reproduce all 9 rows of data/coiled_spring_scenarios.csv."""
    grid = [6.5, 6.25, 6.0, 5.75, 5.5, 5.25, 5.0, 4.75, 4.5]
    expected = [
        # (locked_millions, unlocked_millions, saar_uplift_k)
        (41.5036, 0.0, 0.0),
        (36.068, 5.4356, 1521.968),
        (36.068, 5.4356, 1521.968),
        (28.9052, 12.5984, 3527.552),
        (28.9052, 12.5984, 3527.552),
        (20.1676, 21.336, 5974.08),
        (20.1676, 21.336, 5974.08),
        (11.1252, 30.3784, 8505.952),
        (11.1252, 30.3784, 8505.952),
    ]
    scenarios = unlock_scenarios(
        baseline_rate=6.5,
        threshold=1.5,
        buckets=buckets,
        rate_grid=grid,
        saar_per_million=params["saar_per_million"],
    )
    for got, (exp_locked, exp_unlocked, exp_saar) in zip(scenarios, expected):
        assert abs(got.locked_millions - exp_locked) < 1e-3
        assert abs(got.unlocked_vs_today_millions - exp_unlocked) < 1e-3
        assert abs(got.saar_uplift_k - exp_saar) < 1e-2


def test_zero_rate_unlocks_everyone(buckets):
    locked = locked_at(market_rate=0.0, threshold=1.5, buckets=buckets)
    assert locked == 0.0


def test_high_rate_locks_almost_everyone(buckets):
    """At 99% market rate, every owner under (99 - threshold) is locked."""
    locked = locked_at(market_rate=99.0, threshold=1.5, buckets=buckets)
    total = sum(b.homes_millions for b in buckets)
    assert abs(locked - total) < 1e-6
