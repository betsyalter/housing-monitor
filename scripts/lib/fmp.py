"""FMP client. Shared retry + rate-limit handling.

Lifted from scripts/expand_and_validate_tickers.py:13-23 and
scripts/validate_tickers.py:28-44. The original scripts still work; new
code should import from here.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import requests

BASE = "https://financialmodelingprep.com/stable"


def _api_key() -> str:
    key = os.environ.get("FMP_API_KEY", "")
    if not key:
        raise RuntimeError("FMP_API_KEY not set; export it or write it to .env")
    return key


def fmp_get(endpoint: str, params: Optional[dict] = None, *, timeout: int = 30) -> Any:
    params = dict(params or {})
    params["apikey"] = _api_key()
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
    if r.status_code == 429:
        time.sleep(60)
        retry_params = {k: v for k, v in params.items() if k != "apikey"}
        return fmp_get(endpoint, retry_params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def validate_ticker(symbol: str) -> tuple[bool, Optional[str]]:
    """Returns (is_active, reason_if_not)."""
    try:
        data = fmp_get("profile", {"symbol": symbol}, timeout=10)
    except Exception as e:
        return False, f"error: {e}"
    if not data or not isinstance(data, list) or len(data) == 0:
        return False, "not_found"
    if not data[0].get("isActivelyTrading", True):
        return False, "inactive"
    return True, None
