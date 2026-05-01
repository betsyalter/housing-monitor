"""Quick check that Script 10's outputs include the new correlations section."""
import os, json
import sys
sys.path.insert(0, os.path.dirname(__file__))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH = os.path.join(REPO_ROOT, "housing_context.md")
JSON_PATH = os.path.join(REPO_ROOT, "housing_context.json")

print("=== MARKDOWN: new correlations section ===")
if not os.path.exists(MD_PATH):
    print(f"  [missing] {MD_PATH} — run Script 10 first")
else:
    with open(MD_PATH) as f:
        text = f.read()
    if "Rate Sensitivity Rankings" not in text:
        print("  [warn] 'Rate Sensitivity Rankings' header not found in markdown")
    else:
        # Print just the rate-sensitivity section
        start = text.index("## Rate Sensitivity Rankings")
        next_section = text.find("\n## ", start + 1)
        end = next_section if next_section > 0 else len(text)
        print(text[start:end].rstrip())

print("\n\n=== JSON: rankings embedded ===")
if not os.path.exists(JSON_PATH):
    print(f"  [missing] {JSON_PATH} — run Script 10 first")
else:
    with open(JSON_PATH) as f:
        d = json.load(f)
    sec = d.get("sections", {}).get("correlations", {})
    status = sec.get("status", "<no status>")
    indicators = sec.get("indicators_with_rankings", [])
    rankings = sec.get("rankings_by_indicator", {})
    print(f"  Section status: {status}")
    print(f"  Indicators with rankings: {len(indicators)}")
    for ind in indicators:
        n_records = len(rankings.get(ind, []))
        print(f"    - {ind}: {n_records} ranked records")

print("\n\n=== MARKDOWN: dollar formatting fix ===")
if os.path.exists(MD_PATH):
    with open(MD_PATH) as f:
        text = f.read()
    # Look for median home price line
    for line in text.split("\n"):
        if "Median Home Price" in line:
            print(f"  {line}")
            break
    for line in text.split("\n"):
        if "Existing Home Sales (SAAR)" in line:
            print(f"  {line}")
            break

print("\n=== Section status summary (full report) ===")
if os.path.exists(JSON_PATH):
    with open(JSON_PATH) as f:
        d = json.load(f)
    for name, s in d.get("section_status", {}).items():
        print(f"  {name:20s} {s}")
