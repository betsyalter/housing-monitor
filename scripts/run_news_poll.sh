#!/bin/bash
# News pipeline (5 min cadence in market hours, throttled internally off-hours).
# Polls FMP news, scores, dispatches immediate-priority alerts.
# Called by launchd plist com.housing-monitor.news.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/news_poll.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 14_news_poll ---"
  $PY scripts/14_news_poll.py
  echo
  echo "--- 14b_news_alert_dispatcher (immediates) ---"
  $PY scripts/14b_news_alert_dispatcher.py
  echo
} >> $LOG 2>&1
