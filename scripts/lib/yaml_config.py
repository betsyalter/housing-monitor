"""Load+validate analyst/*.yaml configs.

Pipeline reads these to keep analyst values out of source. Updates land via PR.
Validation is intentionally loud — a malformed YAML should fail bootstrap, not
silently produce wrong numbers downstream.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ANALYST_DIR = Path(__file__).resolve().parent.parent.parent / "analyst"


def _load(name: str) -> dict[str, Any]:
    path = ANALYST_DIR / f"{name}.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{name}.yaml must be a mapping at the top level")
    return data


def load_factor_weights() -> dict[str, Any]:
    data = _load("factor_weights")
    weights = data.get("weights") or {}
    if not weights:
        raise ValueError("factor_weights.yaml: 'weights' missing or empty")
    total = sum(weights.values())
    if not (0.99 < total < 1.01):
        raise ValueError(f"factor_weights.yaml: weights must sum to 1.0, got {total}")
    return data


def load_coiled_spring_params() -> dict[str, Any]:
    data = _load("coiled_spring_params")
    dist = data.get("distribution") or []
    if not dist:
        raise ValueError("coiled_spring_params.yaml: 'distribution' missing or empty")
    pct_total = sum(b["pct_of_outstanding"] for b in dist)
    if not (0.99 < pct_total < 1.01):
        raise ValueError(
            f"coiled_spring_params.yaml: pct_of_outstanding must sum to 1.0, got {pct_total}"
        )
    for k in ("baseline_market_rate", "lockin_threshold", "saar_per_million"):
        if k not in data:
            raise ValueError(f"coiled_spring_params.yaml: missing required key '{k}'")
    return data


def load_ticker_overrides() -> dict[str, Any]:
    data = _load("ticker_overrides")
    if "overrides" not in data:
        raise ValueError("ticker_overrides.yaml: 'overrides' key missing (use {} for none)")
    return data
