#!/bin/bash
# Hourly: scan SEC for new 8-Ks, then dispatch any matching alerts.
# Called by launchd plist com.housing-monitor.hourly.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/hourly.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 06b_sec_8k_scan ---"
  $PY scripts/06b_sec_8k_scan.py
  echo
  echo "--- 11_sec_alert_dispatcher ---"
  $PY scripts/11_sec_alert_dispatcher.py
  echo
} >> $LOG 2>&1
