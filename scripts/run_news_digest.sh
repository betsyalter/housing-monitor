#!/bin/bash
# Send the day's queued digest articles. Triggered at 4:15 PM ET via launchd.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/news_digest.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 14b_news_alert_dispatcher --digest ---"
  $PY scripts/14b_news_alert_dispatcher.py --digest
  echo
} >> $LOG 2>&1
