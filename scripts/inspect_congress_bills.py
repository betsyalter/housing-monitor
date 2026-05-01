"""Pretty-print congress_bill_log.csv: show bills by priority bucket."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd

CSV = os.path.join(DATA_DIR, "congress_bill_log.csv")
if not os.path.exists(CSV):
    print(f"No log at {CSV}")
    sys.exit(0)

df = pd.read_csv(CSV).fillna("")
print(f"Total rows: {len(df)}")
print(f"\nBreakdown by alert_priority:")
print(df["alert_priority"].value_counts().to_string())

for priority in ["immediate", "digest", "log"]:
    sub = df[df["alert_priority"] == priority]
    if sub.empty:
        continue
    print(f"\n{'='*70}\n=== {priority.upper()} ({len(sub)} bills) ===\n{'='*70}")
    for _, r in sub.iterrows():
        print(f"\n[{r['bill_id']}] score={r['score']}")
        print(f"  Title: {r['title'][:140]}")
        print(f"  Sponsor: {r['sponsor_name']} ({r['sponsor_party']}-{r['sponsor_state']})")
        print(f"  Introduced: {r['introduced_date']}")
        print(f"  Latest action ({r['latest_action_date']}): {r['latest_action_text'][:120]}")
        print(f"  Committees: {r['committees'][:120]}")
        print(f"  Policy area: {r['policy_area']}")
        print(f"  Keywords: {r['keyword_hits']}")
        print(f"  Matched: {r['matched_fields']}")
        print(f"  URL: {r['url']}")
