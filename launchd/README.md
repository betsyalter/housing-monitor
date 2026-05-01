# launchd automation

Two scheduled jobs make this a real-time monitor instead of a manually-run tool.

## What runs when

| Plist | Schedule | What it runs |
|-------|----------|--------------|
| `com.housing-monitor.hourly`   | Every hour, 24/7 | `06b_sec_8k_scan.py` → `11_sec_alert_dispatcher.py`. Pulls new 8-Ks from sec-api, classifies them, emails alerts on hits. |
| `com.housing-monitor.daily`    | 6:00 AM Mac mini local time | `10_context_generator.py` then `git commit + push` if `housing_context.md` changed. Refreshes the GitHub Pages dashboard. |

Schedules are intentionally simple — every hour and once a day. 8-Ks land any time (not just market hours), and the alert dispatcher is a no-op when nothing's new, so over-running it costs nothing.

## Install on the Mac mini

```bash
# Make wrapper scripts executable
chmod +x ~/housing_monitor/scripts/run_hourly.sh
chmod +x ~/housing_monitor/scripts/run_daily.sh

# Symlink (or copy) plists into LaunchAgents
mkdir -p ~/Library/LaunchAgents
ln -sf ~/housing_monitor/launchd/com.housing-monitor.hourly.plist ~/Library/LaunchAgents/
ln -sf ~/housing_monitor/launchd/com.housing-monitor.daily.plist ~/Library/LaunchAgents/

# Load them
launchctl load ~/Library/LaunchAgents/com.housing-monitor.hourly.plist
launchctl load ~/Library/LaunchAgents/com.housing-monitor.daily.plist

# Verify they're loaded
launchctl list | grep housing-monitor
```

You should see both labels with PID `-` (not yet run) and exit code `0`.

## Test before waiting

You can fire either job immediately without waiting for the schedule:

```bash
launchctl start com.housing-monitor.hourly
# tail the log to see output
tail -f ~/housing_monitor/logs/hourly.log
```

## Disable temporarily

```bash
launchctl unload ~/Library/LaunchAgents/com.housing-monitor.hourly.plist
launchctl unload ~/Library/LaunchAgents/com.housing-monitor.daily.plist
```

## Logs

- `~/housing_monitor/logs/hourly.log` — accumulates hourly run output (each run timestamped)
- `~/housing_monitor/logs/daily.log` — accumulates daily run output
- `~/housing_monitor/logs/hourly.stderr.log` and `daily.stderr.log` — launchd captures any stderr that escapes the wrapper script

The `logs/` directory is gitignored.

## When to re-load

After editing a plist (schedule, paths, env vars) you must `unload` then `load` again — launchd caches the old version until you do.
