"""sec-api.io client wrapper. Used by scripts/06_sec_reit.py (pending).

Thin shim — sec-api supports a Query API that returns JSON. We don't need
auth helpers beyond the token header.
"""
from __future__ import annotations

import os
from typing import Any

import requests

BASE = "https://api.sec-api.io"


def _api_key() -> str:
    key = os.environ.get("SEC_API_KEY", "")
    if not key:
        raise RuntimeError("SEC_API_KEY not set")
    return key


def query(payload: dict, *, timeout: int = 30) -> Any:
    headers = {"Authorization": _api_key()}
    r = requests.post(BASE, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()
