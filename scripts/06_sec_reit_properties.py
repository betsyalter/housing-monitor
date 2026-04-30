import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY, DATA_DIR

import requests
import pandas as pd
import time
import re

QUERY_URL = "https://api.sec-api.io"
EXTRACTOR_URL = "https://api.sec-api.io/extractor"
RAW_DIR = os.path.join(DATA_DIR, "sec_filings")
OUT_CSV = os.path.join(DATA_DIR, "sec_reit_homes.csv")

REIT_LIST = [
    "INVH", "AMH", "MRP",
    "SUI", "ELS", "UMH",
    "EQR", "AVB", "MAA", "CPT", "UDR", "ESS",
    "AIV", "IRT", "NXRT", "BRT", "VRE", "ELME",
    "WELL", "VTR",
]

NUM_RE = re.compile(r"([\d,]+(?:\.\d+)?)")


def latest_10k(ticker):
    body = {
        "query": f'ticker:{ticker} AND formType:"10-K"',
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}],
    }
    r = requests.post(f"{QUERY_URL}?token={SEC_API_KEY}", json=body, timeout=30)
    r.raise_for_status()
    filings = r.json().get("filings", [])
    return filings[0] if filings else None


def extract_item2(filing_url):
    r = requests.get(EXTRACTOR_URL, params={
        "url": filing_url, "item": "2", "type": "text", "token": SEC_API_KEY,
    }, timeout=60)
    r.raise_for_status()
    return r.text


def parse_headline(text):
    """V1 best-effort: pull total home/unit count, avg rent, occupancy from Item 2 text."""
    homes = None
    rent = None
    occ = None

    for pat in [
        r"approximately\s+([\d,]+)\s+(?:single-family\s+)?homes",
        r"owned\s+([\d,]+)\s+(?:single-family\s+)?(?:homes|units)",
        r"portfolio\s+(?:of|consisted of)\s+([\d,]+)\s+(?:homes|units|sites)",
        r"([\d,]+)\s+(?:homes|units|sites)\s+in\s+(?:our|the)\s+portfolio",
        r"total\s+(?:homes|units|sites)[:\s]+([\d,]+)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            homes = int(m.group(1).replace(",", ""))
            break

    m = re.search(r"average\s+monthly\s+(?:rent|rental\s+rate)[^$\d]*\$?([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        rent = float(m.group(1).replace(",", ""))

    m = re.search(r"(?:average\s+)?occupancy(?:\s+rate)?[^\d]*([\d.]+)\s*%", text, re.IGNORECASE)
    if m:
        occ = float(m.group(1))

    return homes, rent, occ


def main():
    if not SEC_API_KEY:
        raise SystemExit("SEC_API_KEY is empty. Check ~/.env")

    os.makedirs(RAW_DIR, exist_ok=True)

    rows = []
    for i, ticker in enumerate(REIT_LIST):
        print(f"  [{i+1}/{len(REIT_LIST)}] {ticker}...", end=" ", flush=True)
        try:
            filing = latest_10k(ticker)
            if not filing:
                print("no 10-K found")
                continue

            filing_url = filing.get("linkToFilingDetails") or filing.get("linkToHtml")
            accession = filing.get("accessionNo", "")
            filed_at = filing.get("filedAt", "")[:10]
            period = filing.get("periodOfReport", "")

            text = extract_item2(filing_url)
            raw_path = os.path.join(RAW_DIR, f"{ticker}_10K_item2.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(f"# {ticker} 10-K Item 2 — filed {filed_at} — accession {accession}\n")
                f.write(f"# source: {filing_url}\n\n")
                f.write(text)

            homes, rent, occ = parse_headline(text)
            rows.append({
                "ticker": ticker,
                "filing_date": filed_at,
                "fiscal_year_end": period,
                "accession_no": accession,
                "geo_type": "total",
                "geo_name": "portfolio",
                "home_count": homes,
                "avg_monthly_rent": rent,
                "occupancy_pct": occ,
            })
            print(f"homes={homes}, rent={rent}, occ={occ}")

        except Exception as e:
            print(f"FAILED: {e}")

        time.sleep(0.5)

    if not rows:
        raise SystemExit("No filings parsed. Aborting before overwriting CSV.")

    df = pd.DataFrame(rows, columns=[
        "ticker", "filing_date", "fiscal_year_end", "accession_no",
        "geo_type", "geo_name", "home_count", "avg_monthly_rent", "occupancy_pct",
    ])
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(df)} rows to {OUT_CSV}")
    print(f"Raw Item 2 text saved per filing in {RAW_DIR}/")
    print("\nNote: geographic (state/MSA) breakdown rows not yet parsed — that's Script 06c.")


if __name__ == '__main__':
    main()
