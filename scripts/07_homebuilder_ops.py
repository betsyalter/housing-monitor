"""Homebuilder operational KPIs from quarterly earnings press releases.

For each Tier 1 homebuilder, finds the last 8 earnings 8-Ks (Item 2.02),
downloads each EX-99.1 attachment, strips HTML, and uses Claude Haiku to
extract structured operational KPIs. Writes to data/homebuilder_ops.csv
in the long-format schema agreed with codex.

Incremental: skips (ticker, accession_no) combinations already on disk.
A clean re-run after backfill should be ~zero LLM calls.

Cost (initial backfill): 16 builders x 8 quarters x ~$0.008/call ≈ $1.
Cost (steady state, weekly cron): 16 builders x 1 new filing x $0.008 ≈ $0.13/quarter.
"""

import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY, DATA_DIR

import requests
import pandas as pd

try:
    from anthropic import Anthropic
except ImportError:
    raise SystemExit("anthropic package not installed. Run: pip install anthropic")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

QUERY_URL = "https://api.sec-api.io"
OUT_CSV = os.path.join(DATA_DIR, "homebuilder_ops.csv")
RAW_DIR = os.path.join(DATA_DIR, "homebuilder_press_releases")
MODEL = "claude-haiku-4-5-20251001"
QUARTERS_BACK = 8

TIER1_BUILDERS = [
    "DHI", "LEN", "NVR", "PHM", "TOL", "KBH", "MTH", "TMHC",
    "GRBK", "MHO", "SKY", "CCS", "LGIH", "CVCO", "DFH", "BZH", "HOV",
]

UA = {"User-Agent": "housing-monitor research betsy@fullertonlp.com"}

COLUMNS = [
    "ticker", "fiscal_period", "period_end_date", "accession_no",
    "segment", "metric_name", "metric_value", "metric_unit", "source_label",
]

METRIC_UNITS = {
    "net_orders_units": "units",
    "cancellation_rate_pct": "pct",
    "backlog_units": "units",
    "community_count": "count",
    "closings_units": "units",
    "asp_dollars": "usd",
    "gross_margin_pct": "pct",
}

EXTRACTION_PROMPT = """You are extracting standardized operational KPIs from a US homebuilder's quarterly earnings press release.

Extract these metrics for the **most recent reporting quarter only** (NOT year-to-date, NOT prior year comparable, NOT trailing twelve months):

- net_orders_units: net new home orders signed (units, integer)
- cancellation_rate_pct: cancelled orders as % of gross orders (numeric, e.g. 16.0)
- backlog_units: homes under contract but not yet closed at quarter end (units, integer)
- community_count: active selling communities (avg or end-of-period, integer)
- closings_units: homes closed/delivered in the quarter (units, integer)
- asp_dollars: average selling price of homes CLOSED. **MUST be in native USD, NOT thousands.** Many press releases show ASP in tabular columns labeled "in thousands" — in that case multiply by 1000 to get native USD (e.g., a table value of "459" with header "in thousands" means $459,000 → return 459000). Never return values <5000. If ASP for both closings and new orders is shown, prefer closings.
- gross_margin_pct: homebuilding gross margin (numeric, exclude financial services / mortgage subsidiary)

Rules:
- If a metric is NOT disclosed, return null. Do not guess.
- If both quarter and YTD are shown, take the QUARTER value.
- Compute ASP if revenue and units are given but ASP is not stated directly: revenue / units (return integer USD).
- For percentages, return numeric (16.0, not "16%").
- For unit counts, return integer (24992, not "24,992").
- fiscal_period: short label like "Q2 FY2026", "Q1 2026", or "2026-03-31".
- Return ONLY a JSON object. No prose, no markdown fences.

Schema:
{
  "fiscal_period": "string",
  "net_orders_units": int or null,
  "cancellation_rate_pct": float or null,
  "backlog_units": int or null,
  "community_count": int or null,
  "closings_units": int or null,
  "asp_dollars": int or null,
  "gross_margin_pct": float or null
}

Press release text:
---
{text}
---

Return only the JSON object."""


def find_earnings_8ks(ticker, n):
    body = {
        "query": f'ticker:{ticker} AND formType:"8-K" AND items:"Item 2.02"',
        "from": "0", "size": str(n),
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    r = requests.post(f"{QUERY_URL}?token={SEC_API_KEY}", json=body, timeout=30)
    r.raise_for_status()
    return r.json().get("filings", [])


def find_ex99_url(filing):
    for doc in filing.get("documentFormatFiles", []):
        if "EX-99" in (doc.get("type") or "").upper():
            return doc.get("documentUrl")
    return None


def html_to_text(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<br[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(p|tr|li|h\d)>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(td|th)>", "\t", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&#8217;", "'").replace("&#8220;", '"').replace("&#8221;", '"')
            .replace("&#8212;", "—").replace("&#160;", " ").replace("&#58;", ":")
            .replace("&#36;", "$").replace("&#37;", "%"))
    lines = []
    for line in html.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def extract_with_llm(client, press_text):
    prompt = EXTRACTION_PROMPT.replace("{text}", press_text[:50000])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, msg.usage.input_tokens, msg.usage.output_tokens
    return parsed, msg.usage.input_tokens, msg.usage.output_tokens


def existing_keys():
    if not os.path.exists(OUT_CSV):
        return set()
    try:
        df = pd.read_csv(OUT_CSV, usecols=["ticker", "accession_no"])
        return set(zip(df["ticker"].astype(str), df["accession_no"].astype(str)))
    except Exception:
        return set()


def _sanity_check_value(metric, value):
    """Catch unit-truncation bugs (e.g. ASP shown as 459 instead of $459,000).
    Returns (corrected_value, was_corrected_bool, reason_str)."""
    if value is None:
        return value, False, ""
    if metric == "asp_dollars":
        # Real homebuilder ASPs are $100,000-$2,000,000. Anything <5000 is
        # almost certainly truncated thousands. Scale up.
        if 50 <= value < 5000:
            return value * 1000, True, "asp_dollars scaled ×1000 (was implausibly small)"
        if value < 50 or value > 5_000_000:
            return value, False, f"asp_dollars={value} is out of range [50, 5_000_000]"
    elif metric in ("net_orders_units", "backlog_units", "closings_units"):
        if value < 0 or value > 200_000:
            return value, False, f"{metric}={value} out of range [0, 200000]"
    elif metric == "community_count":
        if value < 0 or value > 5_000:
            return value, False, f"community_count={value} out of range"
    elif metric.endswith("_pct"):
        if value < 0 or value > 100:
            return value, False, f"{metric}={value} not in [0, 100]"
    return value, False, ""


def melt_to_rows(ticker, filing, extracted, source_label):
    rows = []
    accession = filing.get("accessionNo", "")
    period_end = filing.get("periodOfReport", "")
    fiscal_period = extracted.get("fiscal_period") or period_end
    for metric, unit in METRIC_UNITS.items():
        v = extracted.get(metric)
        if v is None:
            continue
        v_corrected, was_fixed, reason = _sanity_check_value(metric, v)
        if was_fixed:
            print(f"  [{ticker}] {reason} (raw={v})")
        elif reason:
            print(f"  [{ticker}] WARN: {reason}")
        rows.append({
            "ticker": ticker,
            "fiscal_period": fiscal_period,
            "period_end_date": period_end,
            "accession_no": accession,
            "segment": "consolidated",
            "metric_name": metric,
            "metric_value": v_corrected,
            "metric_unit": unit,
            "source_label": source_label,
        })
    return rows


def main():
    if not SEC_API_KEY:
        raise SystemExit("SEC_API_KEY is empty. Check ~/.env")
    if not ANTHROPIC_API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY not set. Add to ~/.env.")

    os.makedirs(RAW_DIR, exist_ok=True)
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    seen = existing_keys()
    print(f"Already on disk: {len(seen)} (ticker, accession) pairs")

    all_new_rows = []
    total_in = 0
    total_out = 0
    summary = {"new": 0, "skipped": 0, "no_filing": 0, "no_ex99": 0, "llm_fail": 0, "error": 0}

    for ticker in TIER1_BUILDERS:
        print(f"\n=== {ticker} ===")
        try:
            filings = find_earnings_8ks(ticker, QUARTERS_BACK)
        except Exception as e:
            print(f"  query failed: {e}")
            summary["error"] += 1
            continue

        if not filings:
            print("  no earnings 8-Ks found")
            summary["no_filing"] += 1
            continue

        print(f"  {len(filings)} filings to consider")

        for filing in filings:
            accession = filing.get("accessionNo", "")
            if (ticker, accession) in seen:
                summary["skipped"] += 1
                continue

            ex99_url = find_ex99_url(filing)
            if not ex99_url:
                summary["no_ex99"] += 1
                continue

            try:
                r = requests.get(ex99_url, headers=UA, timeout=30)
                r.raise_for_status()
                text = html_to_text(r.text)

                raw_path = os.path.join(RAW_DIR, f"{ticker}_{accession.replace('-', '')}.txt")
                with open(raw_path, "w", encoding="utf-8") as f:
                    f.write(text)

                extracted, in_tok, out_tok = extract_with_llm(client, text)
                total_in += in_tok
                total_out += out_tok

                if extracted is None:
                    print(f"  [{accession[:18]}] LLM JSON parse failed")
                    summary["llm_fail"] += 1
                    continue

                rows = melt_to_rows(ticker, filing, extracted, source_label=ex99_url)
                all_new_rows.extend(rows)
                summary["new"] += 1
                period = extracted.get("fiscal_period", "?")
                metrics_filled = sum(1 for v in extracted.values() if v not in (None, "") and not isinstance(v, str))
                print(f"  [{period}] {metrics_filled}/7 metrics extracted, {len(rows)} rows")

            except Exception as e:
                print(f"  [{accession[:18]}] failed: {e}")
                summary["error"] += 1

            time.sleep(0.5)

    if all_new_rows:
        new_df = pd.DataFrame(all_new_rows, columns=COLUMNS)
        if os.path.exists(OUT_CSV):
            old_df = pd.read_csv(OUT_CSV)
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["ticker", "accession_no", "metric_name", "segment"],
                keep="last",
            )
        else:
            combined = new_df
        combined.to_csv(OUT_CSV, index=False)
        print(f"\nWrote {len(combined)} total rows ({len(new_df)} new) to {OUT_CSV}")
    else:
        print("\nNo new rows.")

    cost = total_in * 1.0 / 1_000_000 + total_out * 5.0 / 1_000_000
    print(f"\nLLM tokens: {total_in:,} in / {total_out:,} out — est. cost ${cost:.4f}")
    print(f"Run summary: {summary}")


if __name__ == "__main__":
    main()
