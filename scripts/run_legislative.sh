#!/bin/bash
# Legislative monitor — daily 6:15 PM ET (= 3:15 PM Mac mini PT during DST).
# Same-day detection of new housing-related bill introductions and
# committee actions. Called by launchd plist com.housing-monitor.legislative.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/legislative.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 15_congress_bill_poll ---"
  $PY scripts/15_congress_bill_poll.py
  echo
  echo "--- 15b_congress_alert_dispatcher (immediates) ---"
  $PY scripts/15b_congress_alert_dispatcher.py
  echo
} >> $LOG 2>&1
