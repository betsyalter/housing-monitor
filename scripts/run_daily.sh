#!/bin/bash
# Daily 6 AM ET: regenerate the dashboard, commit + push if changed.
# Called by launchd plist com.housing-monitor.daily.

set -e
cd "$(dirname "$0")/.."

PY=/opt/homebrew/Caskroom/miniforge/base/envs/housing/bin/python3
LOG=logs/daily.log

mkdir -p logs

{
  echo "===== $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  echo "--- 10_context_generator ---"
  $PY scripts/10_context_generator.py
  echo

  # Commit + push only if the report content actually changed
  git add housing_context.md housing_context.json
  if git diff --cached --quiet; then
    echo "No content change in housing_context.md — skipping commit."
  else
    git commit -m "Daily context refresh: $(date -u +%Y-%m-%d)"
    git push
    echo "Pushed daily context update."
  fi
  echo

  echo "--- watchdog ---"
  $PY scripts/watchdog.py
  echo
} >> $LOG 2>&1
