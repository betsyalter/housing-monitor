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


def extract_item(filing_url, item):
    r = requests.get(EXTRACTOR_URL, params={
        "url": filing_url, "item": item, "type": "text", "token": SEC_API_KEY,
    }, timeout=60)
    r.raise_for_status()
    return r.text


def extract_property_sections(filing_url):
    """Pull Item 1 (Business), Item 2 (Properties), Item 7 (MD&A).
    Many REITs cross-reference Item 2 → Item 7 for the actual portfolio detail."""
    sections = {}
    for item in ["1", "2", "7"]:
        try:
            sections[item] = extract_item(filing_url, item)
            time.sleep(0.3)
        except Exception:
            sections[item] = ""
    return sections


def parse_headline(text):
    """V1 best-effort: pull total home/unit count, avg rent, occupancy.
    Looks for portfolio totals — homes, units, sites, apartment homes, senior living units."""
    homes = None
    rent = None
    occ = None

    home_patterns = [
        r"portfolio\s+of\s+([\d,]{4,})\s+(?:wholly[- ]owned\s+)?(?:single-family\s+)?(?:rental\s+)?homes",
        r"owned\s+(?:and\s+operated\s+)?([\d,]{4,})\s+(?:single-family\s+)?(?:rental\s+)?homes",
        r"approximately\s+([\d,]{4,})\s+(?:single-family\s+)?(?:rental\s+)?homes",
        r"([\d,]{4,})\s+single-family\s+(?:rental\s+)?homes",
        r"([\d,]{4,})\s+homes\s+(?:in\s+(?:our|the)\s+|under\s+management|across)",
        r"portfolio\s+(?:of|consisted\s+of|comprised\s+of)\s+([\d,]{3,})\s+(?:apartment\s+homes|apartment\s+units|units|sites|properties)",
        r"owned\s+(?:or\s+had\s+an\s+(?:ownership\s+)?interest\s+in\s+)?([\d,]{3,})\s+(?:apartment\s+(?:homes|communities|units)|operating\s+communities|properties)",
        r"([\d,]{3,})\s+(?:apartment\s+homes|apartment\s+units|operating\s+apartment)",
        r"([\d,]{3,})\s+manufactured[- ]home\s+sites",
        r"approximately\s+([\d,]{3,})\s+(?:senior\s+housing\s+)?(?:communities|properties|units)",
        r"total\s+(?:homes|units|sites|properties)[:\s]+([\d,]{3,})",
    ]
    for pat in home_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            n = int(m.group(1).replace(",", ""))
            if 100 <= n <= 1_000_000:
                homes = n
                break

    rent_patterns = [
        r"average\s+monthly\s+rent(?:al)?(?:\s+(?:rate|per\s+(?:home|unit|site)))?[^$\d]*\$\s*([\d,]+(?:\.\d+)?)",
        r"monthly\s+(?:rent|rental\s+rate)\s+per\s+(?:home|unit|site)[^$\d]*\$\s*([\d,]+(?:\.\d+)?)",
        r"average\s+(?:effective\s+)?monthly\s+(?:rental\s+)?rate[^$\d]*\$\s*([\d,]+(?:\.\d+)?)",
        r"average\s+(?:monthly\s+)?rent\s+(?:was|of)[^$\d]*\$\s*([\d,]+(?:\.\d+)?)",
    ]
    for pat in rent_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            v = float(m.group(1).replace(",", ""))
            if 200 <= v <= 20000:
                rent = v
                break

    occ_patterns = [
        r"average\s+(?:weighted\s+)?(?:physical\s+)?occupancy(?:\s+rate)?[^\d]{0,30}([\d]{2,3}(?:\.\d+)?)\s*%",
        r"occupancy\s+(?:rate\s+)?(?:was|of)[^\d]{0,20}([\d]{2,3}(?:\.\d+)?)\s*%",
        r"([\d]{2,3}(?:\.\d+)?)\s*%\s+(?:average\s+)?(?:weighted\s+)?(?:physical\s+)?occupancy",
    ]
    for pat in occ_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            v = float(m.group(1))
            if 50 <= v <= 100:
                occ = v
                break

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

            sections = extract_property_sections(filing_url)
            for item, body in sections.items():
                if not body:
                    continue
                raw_path = os.path.join(RAW_DIR, f"{ticker}_10K_item{item}.txt")
                with open(raw_path, "w", encoding="utf-8") as f:
                    f.write(f"# {ticker} 10-K Item {item} — filed {filed_at} — accession {accession}\n")
                    f.write(f"# source: {filing_url}\n\n")
                    f.write(body)

            combined = "\n\n".join(sections.values())
            raw_path = os.path.join(RAW_DIR, f"{ticker}_10K_item2.txt")  # primary path for compatibility
            homes, rent, occ = parse_headline(combined)
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
