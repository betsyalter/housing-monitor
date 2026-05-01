import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY, DATA_DIR

import requests
import pandas as pd
import time
import re
from datetime import datetime, timezone, timedelta

QUERY_URL = "https://api.sec-api.io"
RAW_DIR = os.path.join(DATA_DIR, "sec_raw")
OUT_CSV = os.path.join(DATA_DIR, "sec_stream_log.csv")
LOOKBACK_HOURS = 24
PAGE_SIZE = 50
MAX_PAGES = 20

RELEVANT_ITEMS = {"1.01", "1.02", "1.03", "2.01", "2.02", "2.03", "2.04",
                  "2.05", "2.06", "4.02", "5.02", "7.01", "8.01"}
# Intentionally excluded as noise:
#   5.07 (security holder votes — annual meeting routine)
#   5.03 (bylaw/charter amendments — usually procedural)
#   9.01 alone (exhibits-only filings — material is in the paired item)

COLUMNS = [
    "detected_at", "filed_at", "ticker", "cik", "company_name", "form_type",
    "item_codes", "accession_no", "filing_url", "primary_doc_url", "title",
    "is_amendment", "has_ex99", "excerpt", "raw_text_path",
]


def query_8ks(since_iso, until_iso):
    out = []
    for page in range(MAX_PAGES):
        body = {
            "query": f'formType:"8-K" AND filedAt:[{since_iso} TO {until_iso}]',
            "from": str(page * PAGE_SIZE),
            "size": str(PAGE_SIZE),
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        r = requests.post(f"{QUERY_URL}?token={SEC_API_KEY}", json=body, timeout=30)
        r.raise_for_status()
        filings = r.json().get("filings", [])
        out.extend(filings)
        if len(filings) < PAGE_SIZE:
            break
        time.sleep(0.3)
    return out


def existing_accessions():
    if not os.path.exists(OUT_CSV):
        return set()
    try:
        df = pd.read_csv(OUT_CSV, usecols=["accession_no"])
        return set(df["accession_no"].dropna().astype(str))
    except Exception:
        return set()


def fetch_excerpt(url):
    try:
        r = requests.get(url, headers={
            "User-Agent": "housing-monitor research betsy@fullertonlp.com",
        }, timeout=30)
        if r.status_code != 200:
            return "", None
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text).strip()
        excerpt = text[:400]
        return excerpt, text
    except Exception:
        return "", None


def main():
    if not SEC_API_KEY:
        raise SystemExit("SEC_API_KEY is empty. Check ~/.env")

    os.makedirs(RAW_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=LOOKBACK_HOURS)
    since_iso = since.strftime("%Y-%m-%d")
    until_iso = now.strftime("%Y-%m-%d")
    detected_at = now.isoformat()

    print(f"Scanning 8-Ks filed {since_iso} to {until_iso}...")
    filings = query_8ks(since_iso, until_iso)
    print(f"  {len(filings)} total 8-Ks returned by sec-api")

    universe = set(pd.read_csv(f"{DATA_DIR}/fmp_tickers.csv")["ticker"].dropna().astype(str))
    seen = existing_accessions()

    item_code_re = re.compile(r"Item\s+(\d+\.\d+[A-Z]?)", re.IGNORECASE)

    new_rows = []
    matched_count = 0
    drop_no_ticker = 0
    drop_not_in_universe = 0
    drop_no_relevant_items = 0
    sample_other_tickers = []

    for f in filings:
        accession = f.get("accessionNo", "")
        if not accession or accession in seen:
            continue

        ticker = (f.get("ticker") or "").upper()
        if not ticker:
            drop_no_ticker += 1
            continue
        if ticker not in universe:
            drop_not_in_universe += 1
            if len(sample_other_tickers) < 10:
                sample_other_tickers.append(ticker)
            continue

        items_raw = f.get("items") or []
        item_codes = sorted({m.group(1) for s in items_raw if s for m in [item_code_re.search(s)] if m})
        if not (set(item_codes) & RELEVANT_ITEMS):
            drop_no_relevant_items += 1
            print(f"  [skipped {ticker}] items={item_codes}")
            continue
        matched_count += 1

        primary_doc_url = f.get("linkToFilingDetails") or ""
        for doc in f.get("documentFormatFiles", []):
            if doc.get("type", "").startswith("8-K"):
                primary_doc_url = doc.get("documentUrl") or primary_doc_url
                break

        excerpt, full_text = fetch_excerpt(primary_doc_url)

        raw_path = ""
        if full_text:
            raw_path = os.path.join(RAW_DIR, f"{accession.replace('-', '')}.txt")
            with open(raw_path, "w", encoding="utf-8") as f_out:
                f_out.write(full_text)

        has_ex99 = any("EX-99" in (d.get("type") or "").upper()
                       for d in f.get("documentFormatFiles", []))

        new_rows.append({
            "detected_at": detected_at,
            "filed_at": f.get("filedAt", ""),
            "ticker": ticker,
            "cik": f.get("cik", ""),
            "company_name": f.get("companyName", ""),
            "form_type": f.get("formType", ""),
            "item_codes": "|".join(item_codes),
            "accession_no": accession,
            "filing_url": f.get("linkToFilingDetails", ""),
            "primary_doc_url": primary_doc_url,
            "title": f.get("description", "")[:200],
            "is_amendment": "8-K/A" in f.get("formType", ""),
            "has_ex99": has_ex99,
            "excerpt": excerpt,
            "raw_text_path": raw_path,
        })

        time.sleep(0.2)

    print(f"  Drop breakdown: no_ticker={drop_no_ticker}, not_in_universe={drop_not_in_universe}, no_relevant_items={drop_no_relevant_items}")
    if sample_other_tickers:
        print(f"  Sample non-universe tickers: {sample_other_tickers}")
    print(f"  In-universe + relevant-item matches: {matched_count}")

    if not new_rows:
        print("No new in-universe 8-Ks with relevant items. Nothing to append.")
        return

    new_df = pd.DataFrame(new_rows, columns=COLUMNS)
    if os.path.exists(OUT_CSV):
        old_df = pd.read_csv(OUT_CSV)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["accession_no"], keep="first")
    else:
        combined = new_df
    combined.to_csv(OUT_CSV, index=False)
    print(f"Appended {len(new_df)} new rows. Total log: {len(combined)} rows -> {OUT_CSV}")


if __name__ == '__main__':
    main()
