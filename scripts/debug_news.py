"""Inspect news_stream_log.csv after a Script 14 run.

Use to calibrate scoring thresholds. If score distribution shows lots
of articles in the 1-2 range that should have been digest-worthy,
lower SCORE_DIGEST. If the highest-scoring articles look like garbage,
the keyword lists need pruning.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd

LOG_CSV = os.path.join(DATA_DIR, "news_stream_log.csv")

if not os.path.exists(LOG_CSV):
    print(f"Log not found: {LOG_CSV}")
    sys.exit(1)

df = pd.read_csv(LOG_CSV).fillna("")
print(f"Total rows: {len(df)}")
print(f"\n=== STREAM BREAKDOWN ===")
print(df["stream"].value_counts().to_string())

print(f"\n=== ALERT PRIORITY BREAKDOWN ===")
print(df["alert_priority"].value_counts().to_string())

print(f"\n=== SCORE DISTRIBUTION ===")
print(df["score"].value_counts().sort_index().to_string())

print(f"\n=== TOP 15 BY SCORE ===")
top = df.sort_values("score", ascending=False).head(15)
for _, r in top.iterrows():
    print(f"  [{r['score']:>2.0f}] [{r['stream']}] [{r['alert_priority']}] "
          f"{r.get('ticker','') or '(macro)':>5}  {(r['publisher'] or '?')[:25]:>25}")
    print(f"        {(r['title'] or '')[:130]}")
    high = str(r['keyword_hits_high'] or '').replace('|', ', ').replace('nan', '')
    medium = str(r['keyword_hits_medium'] or '').replace('|', ', ').replace('nan', '')
    print(f"        HIGH: {high or '—'}")
    print(f"        MED:  {medium or '—'}")

print(f"\n=== PUBLISHER COUNTS (top 15) ===")
print(df["publisher"].value_counts().head(15).to_string())

print(f"\n=== SITE COUNTS (top 15) ===")
print(df["site"].value_counts().head(15).to_string())

print(f"\n=== TOPIC-STREAM ARTICLES (all of them) ===")
topic = df[df["stream"] == "topic"].sort_values("score", ascending=False)
for _, r in topic.head(15).iterrows():
    print(f"  [{r['score']:>2.0f}] {(r['publisher'] or '?')[:20]:>20}  {(r['title'] or '')[:100]}")

print(f"\n=== ARTICLES WITH ANY HIGH-SIGNAL HIT ===")
hits = df[df["keyword_hits_high"].astype(str).str.len() > 0]
print(f"Count: {len(hits)}")
for _, r in hits.head(10).iterrows():
    print(f"  [{r['score']:>2.0f}] [{r['alert_priority']}] {(r['title'] or '')[:90]}")
    print(f"       hits: {r['keyword_hits_high']}")
