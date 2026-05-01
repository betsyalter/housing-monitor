#!/bin/bash
# End-to-end health check for the housing-monitor cron pipeline.
# Reports launchd job status, log freshness, upstream data freshness,
# and the dashboard's last-generated timestamp.
#
# Usage: bash scripts/health_check.sh   (run on the Mac mini)

set -u
cd "$(dirname "$0")/.."

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
divider() { printf -- "── %s ──\n" "$1"; }

bold "=== loaded launchd jobs (PID, last exit, label) ==="
launchctl list | grep housing-monitor || echo "  (no housing-monitor jobs loaded)"
echo

bold "=== latest log lines per job ==="
for log in daily market_close hourly news news_digest legislative; do
  f="logs/${log}.log"
  if [ -f "$f" ]; then
    mtime=$(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$f")
    divider "$f (last modified $mtime)"
    tail -3 "$f"
    echo
  else
    divider "$f (does not exist yet)"
    echo
  fi
done

bold "=== upstream data freshness ==="
for f in data/news_stream_log.csv data/sec_stream_log.csv \
         data/correlation_matrix.csv data/correlation_rankings.csv \
         housing_context.json housing_context.md; do
  if [ -f "$f" ]; then
    stat -f '%Sm  %8z bytes  %N' -t '%Y-%m-%d %H:%M' "$f"
  else
    echo "  (missing) $f"
  fi
done
echo

bold "=== newest 5 price CSVs ==="
ls -lt data/fmp_prices/*.csv 2>/dev/null | head -5 || echo "  (no price files)"
echo

bold "=== last 5 commits (daily cron pushes show up here) ==="
git log --oneline -5
echo

bold "=== generated_at inside housing_context.json ==="
if [ -f housing_context.json ]; then
  python3 -c "import json; print(json.load(open('housing_context.json'))['generated_at'])"
else
  echo "  (housing_context.json missing)"
fi
echo

bold "=== status interpretation ==="
echo "✓ healthy  : every job's exit code is 0 or '-', logs touched within"
echo "             expected schedule, generated_at within the last 24h."
echo "✗ broken   : non-zero exit code, log unchanged since yesterday on a"
echo "             schedule that should have fired, or generated_at > 36h."
