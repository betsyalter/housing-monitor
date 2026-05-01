"""Per-REIT geographic breakdown parser using Claude Haiku.

Reads raw 10-K Item 1+2+7 text already on disk (saved by Script 06)
for the 20 REITs and uses Haiku to extract state/MSA/market-level
breakdown rows. Appends to data/sec_reit_homes.csv with geo_type
∈ {state, msa, market, region}.

Schema agreed with codex (2026-04-30):
  ticker, filing_date, fiscal_year_end, accession_no,
  geo_type, geo_name, home_count, avg_monthly_rent, occupancy_pct

Each REIT structures Item 2/7 differently — INVH lists 16 MSAs, AMH
breaks down by 24 markets, EQR uses regions. Per-REIT regex would
be 20 brittle parsers. LLM extraction handles all 20 with one prompt.

Idempotent: skips REITs whose latest accession already has geo rows
in the CSV. Re-runs after a fresh 10-K filing pick up only the new one.

Usage:
  python scripts/06c_reit_geo_parser.py                  # all 20 REITs
  python scripts/06c_reit_geo_parser.py --ticker INVH    # one REIT for testing
  python scripts/06c_reit_geo_parser.py --dry-run        # extract but don't write CSV
"""

import sys, os, json, re, time, argparse
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import pandas as pd

try:
    from anthropic import Anthropic
except ImportError:
    raise SystemExit("anthropic package not installed. Run: pip install anthropic")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    raise SystemExit("ANTHROPIC_API_KEY not set in ~/.env.")

RAW_DIR = os.path.join(DATA_DIR, "sec_filings")
OUT_CSV = os.path.join(DATA_DIR, "sec_reit_homes.csv")
MODEL = "claude-haiku-4-5-20251001"

# REITs and their preferred reporting unit (helps the LLM frame the extraction)
REIT_UNITS = {
    "INVH": "single-family rental homes by MSA",
    "AMH":  "single-family rental homes by market",
    "MRP":  "homes / single-family land lots by region",
    "SUI":  "manufactured-home / RV sites by state",
    "ELS":  "manufactured-home / RV sites by state",
    "UMH":  "manufactured-home sites by state",
    "EQR":  "apartment homes by region / market",
    "AVB":  "apartment homes by region / metro",
    "MAA":  "apartment homes by metro",
    "CPT":  "apartment homes by metro",
    "UDR":  "apartment homes by region / metro",
    "ESS":  "apartment homes by region (West Coast focus)",
    "AIV":  "apartment homes by market",
    "IRT":  "apartment homes by metro",
    "NXRT": "apartment homes by metro",
    "BRT":  "apartment homes by market",
    "VRE":  "apartment homes by metro",
    "ELME": "apartment homes by region",
    "WELL": "senior-housing properties by region",
    "VTR":  "senior-housing properties by region",
}


EXTRACTION_PROMPT = """You are extracting geographic portfolio breakdowns from a US REIT's 10-K Item 2 / Item 7 text.

This REIT primarily holds: {unit_hint}.

Find every geographic breakdown table in the text. For each row of those tables, output one record:
  - geo_type: "state" (US state name), "msa" (metro statistical area), "market" (REIT-specific market like "Atlanta" or "Las Vegas"), "region" (REIT-defined region like "Sun Belt" or "Southeast"), or "total" if this is the portfolio-wide row.
  - geo_name: the label as written in the 10-K (e.g. "Atlanta-Sandy Springs-Alpharetta GA", or "Florida", or "Mid-Atlantic").
  - home_count: the property/unit/site count for that geography. Integer.
  - avg_monthly_rent: average monthly rent for that geography. USD integer. null if not disclosed at this granularity.
  - occupancy_pct: occupancy as a decimal percentage (e.g. 96.4 for 96.4%). null if not disclosed at this granularity.

Rules:
- If only home_count is disclosed for a region and rent / occupancy are portfolio-wide, leave rent / occupancy null for the region row.
- Do NOT invent values. If the table doesn't show a number, return null.
- Skip any table that's about non-property data (e.g., debt maturity by year, executive compensation).
- If multiple geographic breakdowns exist (e.g., breakdown by state AND by MSA), include both — distinguish by geo_type.
- Return ONLY a JSON array. No prose, no markdown fences. Empty array [] if no breakdown found.

Schema:
[
  {{"geo_type": "msa", "geo_name": "Atlanta-Sandy Springs-Alpharetta GA",
    "home_count": 12500, "avg_monthly_rent": 2150, "occupancy_pct": 96.4}},
  {{"geo_type": "state", "geo_name": "Florida",
    "home_count": 18000, "avg_monthly_rent": null, "occupancy_pct": null}}
]

10-K text:
---
{text}
---

Return only the JSON array."""


def load_existing():
    if not os.path.exists(OUT_CSV):
        return None
    return pd.read_csv(OUT_CSV)


def existing_geo_accessions(df):
    """Set of (ticker, accession_no) already with geo rows on disk."""
    if df is None or df.empty:
        return set()
    geo = df[df["geo_type"].isin(["state", "msa", "market", "region"])]
    return set(zip(geo["ticker"].astype(str), geo["accession_no"].astype(str)))


def load_item_text(ticker):
    """Concatenate Item 1, 2, 7 text saved by Script 06."""
    parts = []
    accession = None
    filing_date = None
    fiscal_period = None
    for item in ("1", "2", "7"):
        path = os.path.join(RAW_DIR, f"{ticker}_10K_item{item}.txt")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # First two lines are: "# TICKER 10-K Item N — filed YYYY-MM-DD — accession ..."
        lines = content.splitlines()
        if lines and lines[0].startswith("#"):
            m = re.search(r"filed (\d{4}-\d{2}-\d{2}).*accession (\S+)", lines[0])
            if m and not accession:
                filing_date = m.group(1)
                accession = m.group(2)
            content = "\n".join(lines[2:])  # strip the comment header lines
        parts.append(f"\n=== ITEM {item} ===\n{content}")
    if not parts:
        return None, None, None
    return "\n".join(parts), filing_date, accession


def extract_with_llm(client, ticker, text):
    unit_hint = REIT_UNITS.get(ticker, "real-estate properties")
    prompt = EXTRACTION_PROMPT.replace("{unit_hint}", unit_hint).replace("{text}", text[:60000])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return [], msg.usage.input_tokens, msg.usage.output_tokens
        return parsed, msg.usage.input_tokens, msg.usage.output_tokens
    except json.JSONDecodeError as e:
        print(f"  [{ticker}] JSON parse failed: {e}")
        print(f"    raw response head: {raw[:300]}")
        return None, msg.usage.input_tokens, msg.usage.output_tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="Run for a single REIT only (e.g. INVH)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Extract and print but do not write CSV")
    args = parser.parse_args()

    if not os.path.isdir(RAW_DIR):
        raise SystemExit(f"{RAW_DIR} missing — run scripts/06_sec_reit_properties.py first.")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    existing = load_existing()
    seen = existing_geo_accessions(existing)
    print(f"Existing geo rows for: {len(seen)} (ticker, accession) pairs")
    if args.dry_run:
        print("DRY RUN — will not write to CSV")

    all_new_rows = []
    summary = {"extracted": 0, "skipped": 0, "no_text": 0, "llm_fail": 0, "no_geo": 0}
    total_in = total_out = 0

    targets = [args.ticker] if args.ticker else list(REIT_UNITS.keys())
    if args.ticker and args.ticker not in REIT_UNITS:
        raise SystemExit(f"{args.ticker} not in REIT_UNITS list. Add it or pick from {sorted(REIT_UNITS.keys())}")

    for ticker in targets:
        text, filing_date, accession = load_item_text(ticker)
        if not text:
            print(f"  [{ticker}] no item text on disk")
            summary["no_text"] += 1
            continue

        if (ticker, accession) in seen:
            print(f"  [{ticker}] already extracted for {accession}")
            summary["skipped"] += 1
            continue

        print(f"  [{ticker}] extracting from {accession} (filed {filing_date})...")
        rows, in_tok, out_tok = extract_with_llm(client, ticker, text)
        total_in += in_tok
        total_out += out_tok

        if rows is None:
            summary["llm_fail"] += 1
            continue
        if not rows:
            print(f"    [no geo breakdown extracted]")
            summary["no_geo"] += 1
            continue

        # Get fiscal_year_end from existing total row if present
        fiscal_year_end = ""
        if existing is not None and not existing.empty:
            match = existing[(existing["ticker"] == ticker) &
                             (existing["accession_no"] == accession)]
            if not match.empty:
                fiscal_year_end = match.iloc[0].get("fiscal_year_end", "") or ""

        for row in rows:
            geo_type = row.get("geo_type", "")
            if geo_type not in ("state", "msa", "market", "region"):
                continue  # ignore "total" — already exists as a row
            all_new_rows.append({
                "ticker": ticker,
                "filing_date": filing_date,
                "fiscal_year_end": fiscal_year_end,
                "accession_no": accession,
                "geo_type": geo_type,
                "geo_name": row.get("geo_name", ""),
                "home_count": row.get("home_count"),
                "avg_monthly_rent": row.get("avg_monthly_rent"),
                "occupancy_pct": row.get("occupancy_pct"),
            })

        summary["extracted"] += 1
        print(f"    extracted {len(rows)} geo rows")
        time.sleep(0.5)

    if all_new_rows:
        if args.dry_run:
            print(f"\n=== DRY RUN: would write {len(all_new_rows)} new geo rows ===")
            new_df = pd.DataFrame(all_new_rows)
            print(new_df.to_string(index=False))
        else:
            new_df = pd.DataFrame(all_new_rows)
            if existing is not None:
                combined = pd.concat([existing, new_df], ignore_index=True)
                # Dedupe on (ticker, accession_no, geo_type, geo_name)
                combined = combined.drop_duplicates(
                    subset=["ticker", "accession_no", "geo_type", "geo_name"],
                    keep="last",
                )
            else:
                combined = new_df
            combined.to_csv(OUT_CSV, index=False)
            print(f"\nWrote {len(combined)} total rows ({len(all_new_rows)} new geo rows) -> {OUT_CSV}")

    cost = total_in * 1.0 / 1_000_000 + total_out * 5.0 / 1_000_000
    print(f"\nLLM tokens: {total_in:,} in / {total_out:,} out — est. cost ${cost:.4f}")
    print(f"Run summary: {summary}")


if __name__ == "__main__":
    main()
