"""POC: LLM-based homebuilder press release parser using Claude Haiku.

Tests on DHI, LEN, NVR — three builders with deliberately different press
release templates. If the LLM nails all three, we scale to 07_homebuilder_ops.py
covering all 16 Tier 1 homebuilders. If it whiffs on one, we iterate the prompt.

Cost: ~3 builders x ~$0.001/call = trivial. Each press release is 5-30k tokens
of cleaned text in, ~200 tokens of JSON out.
"""

import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY

import requests

try:
    from anthropic import Anthropic
except ImportError:
    raise SystemExit("anthropic package not installed. Run: pip install anthropic")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    raise SystemExit("ANTHROPIC_API_KEY not set in ~/.env. Get one at console.anthropic.com.")

QUERY_URL = "https://api.sec-api.io"
TICKERS = ["DHI", "LEN", "NVR"]
MODEL = "claude-haiku-4-5-20251001"
UA = {"User-Agent": "housing-monitor research betsy@fullertonlp.com"}

EXTRACTION_PROMPT = """You are extracting standardized operational KPIs from a US homebuilder's quarterly earnings press release.

Extract the following metrics for the **most recent reporting quarter only** (NOT year-to-date, NOT prior year comparable, NOT trailing twelve months):

- net_orders_units: net new home orders signed in the quarter (units)
- cancellation_rate_pct: cancelled orders as % of gross orders
- backlog_units: homes under contract but not yet closed (as of quarter end)
- community_count: active selling communities (avg or end-of-period)
- closings_units: homes closed/delivered in the quarter (units)
- asp_dollars: average selling price per home (USD, not in thousands)
- gross_margin_pct: homebuilding gross margin (exclude financial services)

Rules:
- If a metric is not disclosed in the document, return null.
- If both quarter and YTD figures are shown, extract the QUARTER value only.
- For ASP, if the press release shows "homes closed: 19,486 units, $7,045.5 million revenue", compute ASP = 7045500000 / 19486 = 361562 (return as integer USD).
- For percentages, return numeric value (16.0, not "16%").
- For unit counts, return integer (24992, not "24,992").
- Return ONLY the JSON object. No prose, no markdown fences, no commentary.

Schema:
{
  "fiscal_period": "string (e.g. 'Q2 FY2026' or '2026-03-31')",
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


def find_latest_earnings_8k(ticker):
    body = {
        "query": f'ticker:{ticker} AND formType:"8-K" AND items:"Item 2.02"',
        "from": "0", "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    r = requests.post(f"{QUERY_URL}?token={SEC_API_KEY}", json=body, timeout=30)
    r.raise_for_status()
    return (r.json().get("filings") or [None])[0]


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


def extract_with_llm(client, ticker, press_text):
    prompt = EXTRACTION_PROMPT.replace("{text}", press_text[:50000])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # Strip code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw), msg.usage.input_tokens, msg.usage.output_tokens
    except json.JSONDecodeError as e:
        print(f"  [{ticker}] JSON parse failed: {e}")
        print(f"  Raw response: {raw[:500]}")
        return None, msg.usage.input_tokens, msg.usage.output_tokens


def main():
    if not SEC_API_KEY:
        raise SystemExit("SEC_API_KEY is empty. Check ~/.env")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    results = {}
    total_in = 0
    total_out = 0

    for ticker in TICKERS:
        print(f"\n=== {ticker} ===")
        filing = find_latest_earnings_8k(ticker)
        if not filing:
            print(f"  No earnings 8-K found")
            continue
        print(f"  Filed: {filing.get('filedAt')}")
        print(f"  Period: {filing.get('periodOfReport')}")

        ex99_url = find_ex99_url(filing)
        if not ex99_url:
            print(f"  No EX-99 attachment")
            continue

        r = requests.get(ex99_url, headers=UA, timeout=30)
        r.raise_for_status()
        text = html_to_text(r.text)
        print(f"  Cleaned text: {len(text):,} chars")

        out, in_tokens, out_tokens = extract_with_llm(client, ticker, text)
        total_in += in_tokens
        total_out += out_tokens
        if out:
            results[ticker] = out
            print(f"  Tokens: {in_tokens} in / {out_tokens} out")
            for k, v in out.items():
                print(f"    {k:25s} = {v}")
        else:
            print(f"  Extraction failed")

    print(f"\n=== Cost summary ===")
    cost = total_in * 1.0 / 1_000_000 + total_out * 5.0 / 1_000_000  # Haiku 4.5 pricing
    print(f"Total tokens: {total_in:,} in / {total_out:,} out")
    print(f"Estimated cost: ${cost:.4f}")

    print(f"\n=== Comparison table ===")
    if results:
        metrics = ["net_orders_units", "cancellation_rate_pct", "backlog_units",
                   "community_count", "closings_units", "asp_dollars", "gross_margin_pct"]
        print(f"{'metric':25s} | " + " | ".join(f"{t:>12s}" for t in results.keys()))
        print("-" * (28 + 15 * len(results)))
        for m in metrics:
            row = f"{m:25s} | " + " | ".join(f"{str(results[t].get(m)):>12s}" for t in results.keys())
            print(row)


if __name__ == "__main__":
    main()
