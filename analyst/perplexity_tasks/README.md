# Perplexity Computer Task Specs

Scheduled AI-research tasks that consume the housing-monitor pipeline and produce
analyst commentary. Each task is a fully-specified prompt that Perplexity
Computer (or any equivalent scheduled-agent system: Perplexity Comet,
ChatGPT Tasks, Claude Code scheduled jobs, etc.) runs on a cadence.

The pipeline ships data; these tasks ship **interpretation**.

## Tasks

| Task | Cadence | Spec | Output |
|---|---|---|---|
| **Weekly Housing Monitor** | Every Monday 7:00 AM ET | [`weekly_housing_monitor.md`](weekly_housing_monitor.md) | `output/perplexity/weekly/YYYY-MM-DD.md` + JSON sidecar |
| Monthly NAR Deep Dive | 22nd of each month, ~11:00 AM ET (NAR existing-home-sales release day) | _pending_ | `output/perplexity/monthly_nar/YYYY-MM.md` |
| Quarterly Structural Deep Dive | First Monday of Jan / Apr / Jul / Oct | _pending_ | `output/perplexity/quarterly/YYYY-QN.md` |

Spec format: each task is a single markdown file. The prompt sections (role,
inputs, workflow, output schema, quality requirements) are designed to be
copy-pasted into Perplexity Computer's task-creation UI. Do not edit the
prompt directly in the agent's UI — edit the markdown spec, commit, and
re-paste so version history stays in git.

## Naming convention for outputs

```
output/perplexity/
├── weekly/
│   └── 2026-05-04.md           # Monday-of-week date
│   └── 2026-05-04.json         # structured sidecar
├── monthly_nar/
│   └── 2026-04.md
└── quarterly/
    └── 2026-Q2.md
```

Each output file gets committed to the repo automatically (Perplexity Computer
writes a PR or pushes to a `perplexity/auto/...` branch). Wyatt reviews and
merges, or rejects. No auto-merge — the analyst's commentary always passes
human review before it surfaces in the dashboard.
