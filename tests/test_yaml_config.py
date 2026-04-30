from __future__ import annotations

import pytest
import yaml

from lib.yaml_config import (
    ANALYST_DIR,
    load_coiled_spring_params,
    load_factor_weights,
    load_ticker_overrides,
)


def test_factor_weights_sum_to_one():
    data = load_factor_weights()
    total = sum(data["weights"].values())
    assert 0.999 < total < 1.001


def test_factor_weights_has_required_factors():
    data = load_factor_weights()
    factors = set(data["weights"].keys())
    assert {"rate_lockin", "affordability", "inventory", "demographics", "policy"} <= factors


def test_coiled_spring_params_has_all_required_keys():
    data = load_coiled_spring_params()
    for k in ("distribution", "baseline_market_rate", "lockin_threshold", "saar_per_million"):
        assert k in data
    assert len(data["distribution"]) >= 5


def test_ticker_overrides_loads():
    data = load_ticker_overrides()
    assert "overrides" in data


def test_factor_weights_invalid_sum_raises(tmp_path, monkeypatch):
    bad = tmp_path / "factor_weights.yaml"
    bad.write_text(yaml.safe_dump({"weights": {"a": 0.5, "b": 0.3}}))
    monkeypatch.setattr("lib.yaml_config.ANALYST_DIR", tmp_path)
    with pytest.raises(ValueError, match="must sum to 1.0"):
        load_factor_weights()
