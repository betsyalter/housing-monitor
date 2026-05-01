#!/bin/bash
# Weekday market-close: refresh daily prices for the 262 universe, then
# rerun the correlation engine against the new prints.
# Called by launchd plist com.housing-monitor.market-close.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/market_close.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 04_fmp_prices ---"
  $PY scripts/04_fmp_prices.py
  echo
  echo "--- 09_correlation_engine ---"
  $PY scripts/09_correlation_engine.py
  echo
} >> $LOG 2>&1
