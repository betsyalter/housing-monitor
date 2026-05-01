# Weekly Housing Monitor — Patch Notes (apply before next run)

> Apply these four changes to your task definition. They override the
> corresponding rules in the original spec
> (`analyst/perplexity_tasks/weekly_housing_monitor.md`). Source of
> truth on `main` always wins; this file documents what changed
> between the first run (2026-05-04) and the next.

## Change 1 — Drop the length cap

**Old:** "Length cap. Markdown report must be ≤ 1,500 words."

**New:** Length is quality-driven, no upper bound. Write what the
substance warrants. A week with a major signal cluster (FOMC + earnings
cohort pattern + policy event) deserves a long report; a quiet week
deserves a short one. Cut any sentence that doesn't pull weight; merge
sections that say substantially the same thing.

## Change 2 — Named-person attributions need a URL

**New rule:** any quote, paraphrase, or position attributed to a
specific person (Powell, Yun, Director Pulte, a CEO, a sell-side
analyst) must include a reachable primary-source URL. If the citation
isn't available, mark it `[unsourced]` inline rather than implying a
citation you can't produce.

## Change 3 — §7 schema is a minimum, not a maximum

**Old:** "§7.1 Markdown report — strict format" implied no extensions
to the template.

**New:** §7's required sections must appear in every report (silence
on a section is a signal). You **may add** sections, tables, or
analytical asides when they improve clarity. Examples that were
valuable in the first run: subsector basket dispersion table, builder
cohort QoQ matrix, correlation rankings cross-check.

## Change 4 — Framework SHA must be retrieved, not invented

**Old:** Output schema field was `framework_sha: <git SHA of
five_factor_framework.md at run time>` with no retrieval instruction.

**New:** retrieve the actual SHA via the gh CLI:

```
git log -1 --format=%H -- analyst/five_factor_framework.md
```

If retrieval fails, write `framework_version: unknown (could not
retrieve)`. Never invent a SHA. Same rule for
`factor_weights_last_updated` — read the YAML's `last_updated` field
directly; do not infer from filename or memory.

## Why these four

The first-run audit found:
- Length cap was actively counterproductive — agent correctly ignored
  it because the substance warranted ~6,000 words.
- One named-person attribution (Director Pulte on LLPAs) had no URL.
- Three valuable analytical extensions (subsector dispersion, builder
  cohort table, correlation cross-check) were not in the strict §7
  template but should be welcomed.
- Framework SHA `3bc1b7f` was cited but does not exist in the repo —
  hallucinated.

Everything else worked. Persona, current thesis state, workflow steps,
factor lens scoring, JSON sidecar schema, citation density, skeptical
posture, data integrity flags, "what would change my mind" discipline
— all held. No other changes needed yet.
