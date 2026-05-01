"""POC: Parse DHI's most recent earnings press release (8-K Item 2.02 EX-99.1).

If this works for DHI, we scale to per-builder modules in 07_homebuilder_ops.py.
Goal: extract the 6 priority metrics (net_orders_units, cancellation_rate_pct,
backlog_units, community_count, closings_units, asp_dollars) for the most recent
quarter and print them to stdout for visual inspection."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY

import requests
import re

QUERY_URL = "https://api.sec-api.io"
TICKER = "DHI"

UA = {"User-Agent": "housing-monitor research betsy@fullertonlp.com"}


def find_latest_earnings_8k():
    body = {
        "query": f'ticker:{TICKER} AND formType:"8-K" AND items:"Item 2.02"',
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    r = requests.post(f"{QUERY_URL}?token={SEC_API_KEY}", json=body, timeout=30)
    r.raise_for_status()
    filings = r.json().get("filings", [])
    if not filings:
        raise SystemExit(f"No earnings 8-K found for {TICKER}")
    return filings[0]


def find_ex99_url(filing):
    for doc in filing.get("documentFormatFiles", []):
        if "EX-99" in (doc.get("type") or "").upper():
            return doc.get("documentUrl")
    return None


def html_to_text(html):
    # Strip script/style
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace <br>, </p>, </tr>, </td> with newlines/tabs to preserve table structure
    html = re.sub(r"<br[^>]*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(p|tr|li|h\d)>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(td|th)>", "\t", html, flags=re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode common entities
    html = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'").replace("&#8220;", '"').replace("&#8221;", '"').replace("&#8212;", "—")
    # Collapse whitespace within lines
    lines = []
    for line in html.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def parse_dhi(text):
    """DHI press release patterns. Each metric anchored by its label."""
    metrics = {}

    patterns = {
        "closings_units":         r"(?:Homes\s+closed|Homes\s+sold\s+and\s+closed)[^\n]*?\b([\d,]{3,})\b",
        "net_orders_units":       r"(?:Net\s+sales\s+orders|Net\s+new\s+(?:home\s+)?orders)[^\n]*?\b([\d,]{3,})\b",
        "cancellation_rate_pct":  r"Cancellation\s+rate[^\n]*?(\d{1,2}(?:\.\d+)?)\s*%",
        "backlog_units":          r"(?:Sales\s+order\s+backlog|Backlog\s+of\s+homes?(?:\s+under\s+contract)?)[^\n]*?\b([\d,]{3,})\b",
        "community_count":        r"(?:Active\s+selling\s+communities|Number\s+of\s+(?:active\s+)?selling\s+communities|Average\s+(?:active\s+)?selling\s+communities)[^\n]*?\b([\d,]{2,})\b",
        "asp_dollars":            r"(?:Average\s+(?:selling|sales)\s+price)[^\n]*?\$\s*([\d,]+)",
    }

    for metric, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw) if "." in raw else int(raw)
                metrics[metric] = val
            except ValueError:
                metrics[metric] = None
        else:
            metrics[metric] = None

    return metrics


def main():
    if not SEC_API_KEY:
        raise SystemExit("SEC_API_KEY is empty. Check ~/.env")

    print(f"Finding latest earnings 8-K for {TICKER}...")
    filing = find_latest_earnings_8k()
    print(f"  Filed: {filing.get('filedAt')}")
    print(f"  Accession: {filing.get('accessionNo')}")
    print(f"  Period: {filing.get('periodOfReport')}")

    ex99_url = find_ex99_url(filing)
    if not ex99_url:
        raise SystemExit("No EX-99 attachment found")
    print(f"  EX-99 URL: {ex99_url}")

    print(f"\nDownloading press release...")
    r = requests.get(ex99_url, headers=UA, timeout=30)
    r.raise_for_status()
    print(f"  {len(r.text):,} chars HTML")

    text = html_to_text(r.text)
    print(f"  {len(text):,} chars after HTML strip")

    # Save the cleaned text for inspection
    out_path = "/tmp/dhi_press_release.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  Cleaned text saved to {out_path}")

    print(f"\nParsing priority metrics...")
    metrics = parse_dhi(text)
    print()
    for k, v in metrics.items():
        marker = "OK" if v is not None else "??"
        print(f"  [{marker}] {k:30s} = {v}")

    parsed_count = sum(1 for v in metrics.values() if v is not None)
    print(f"\n{parsed_count}/{len(metrics)} metrics parsed")
    if parsed_count < len(metrics):
        print(f"\nIf any are missing, grep the saved text:\n  grep -A2 -i 'cancellation\\|backlog\\|orders\\|closed\\|community' {out_path}")


if __name__ == "__main__":
    main()
