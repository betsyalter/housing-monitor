"""Congress.gov bill tracker — daily poll for housing-related federal legislation.

Catches bills BEFORE they get news coverage. Per Betsy's flag: she suspects
the admin will move legislatively to jumpstart housing despite high mortgage
rates and wants to detect it before it splashes on the tape.

Mirrors the producer/dispatcher pattern from 06b → 11 and 14 → 14b:
- This script (15) polls and logs to data/congress_bill_log.csv
- Script 15b reads the log, classifies, sends emails

Per codex audit (2026-05-01):
- Authenticated API only (free key from api.congress.gov)
- Current Congress only (119th, started Jan 2025)
- Two-stage fetch: list recent bills, then detail only for unseen / changed
- Each alertable event = new log row (not mutation)
- Re-alert on action signature change (date|action_text), not just date
- Hard-promote on Banking + Financial Services + Ways and Means + Finance
"""

import sys, os, json, time, hashlib, re
sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_DIR

import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

CONGRESS_API_KEY = os.environ.get("CONGRESS_API_KEY", "")

API_BASE = "https://api.congress.gov/v3"
CURRENT_CONGRESS = 119  # 2025-2027
BILL_TYPES = ["hr", "s"]  # House and Senate bills only — skip resolutions
LIST_PAGE_SIZE = 250  # Max per Congress.gov API
LIST_LIMIT_PER_TYPE = 250  # Most recent N per bill type per poll
DETAIL_THROTTLE_SEC = 0.2  # Be polite — 5k/hr limit, ~150/min budget

OUT_CSV = os.path.join(DATA_DIR, "congress_bill_log.csv")
STATE_PATH = os.path.join(DATA_DIR, "congress_bill_state.json")

SEEN_TTL_DAYS = 90

# ── keyword config ────────────────────────────────────────────────────────

# Substring match (case-insensitive) on bill title and policy_area / subjects
HIGH_KEYWORDS = [
    # housing-direct
    "housing", "homebuyer", "homeownership", "homebuilder", "first-time buyer",
    "down payment", "single-family rental", "manufactured housing",
    "low income housing", "lihtc", "section 8", "section 121",
    "assumable mortgage", "mortgage forbearance",
    # mortgage / GSE
    "mortgage", "fannie mae", "freddie mac", "ginnie mae", "gse", "fha",
    "veterans home loan", "qualified mortgage", "qm rule",
    "loan-level price adjustment", "llpa",
    # housing finance / regulators
    "fhfa", "hud", "federal housing", "conservatorship",
    # tax levers tied to housing
    "1031 exchange", "like-kind exchange", "capital gains exclusion",
    "first-time homebuyer credit", "real estate investment trust",
]

MEDIUM_KEYWORDS = [
    "rent", "rental", "evictions", "affordable housing",
    "zoning", "land use", "building code", "construction",
    "real estate", "property tax",
]

# Bill-number patterns — we already log structured bill_id, but use regex
# to catch legislative cross-references in bill TEXT
BILL_REF_RE = re.compile(r"\b(?:H\.?R\.?|S\.?)\s*\d+\b", re.IGNORECASE)

# Hard-promote committees (auto-immediate alert when bill is in any of these)
HARD_PROMOTE_COMMITTEES = {
    "House Financial Services Committee",
    "House Committee on Financial Services",
    "Financial Services Committee",
    "Senate Banking, Housing, and Urban Affairs Committee",
    "Senate Committee on Banking, Housing, and Urban Affairs",
    "Banking, Housing, and Urban Affairs Committee",
    "House Ways and Means Committee",
    "House Committee on Ways and Means",
    "Ways and Means Committee",
    "Senate Finance Committee",
    "Senate Committee on Finance",
}

# Sponsor watchlist — bills introduced by these members get +1 promotion
# (not auto-immediate, just a relevance bump). Update as Wyatt identifies
# the housing-vocal members of the 119th Congress.
SPONSOR_WATCHLIST = {
    # placeholder — populate from analyst/sponsor_watchlist.yaml later
}

CSV_COLUMNS = [
    "detected_at", "event_type", "bill_id", "congress", "bill_type", "bill_number",
    "title", "sponsor_name", "sponsor_party", "sponsor_state",
    "introduced_date", "latest_action_date", "latest_action_text",
    "latest_action_signature", "committees", "policy_area", "subjects",
    "url", "api_url", "matched_fields", "keyword_hits", "score",
    "alert_priority", "source_type", "email_status", "email_sent_at_utc",
    "dedupe_key",
]

SCORE_IMMEDIATE = 5
SCORE_DIGEST = 3


# ── helpers ────────────────────────────────────────────────────────────────

def api_get(path, params=None):
    if params is None:
        params = {}
    params["api_key"] = CONGRESS_API_KEY
    params["format"] = "json"
    r = requests.get(f"{API_BASE}/{path}", params=params, timeout=30)
    if r.status_code == 429:
        print("  [429] rate-limited; sleeping 60s")
        time.sleep(60)
        return api_get(path, {k: v for k, v in params.items() if k != "api_key"})
    r.raise_for_status()
    return r.json()


def load_state():
    if not os.path.exists(STATE_PATH):
        return {
            "last_run_utc": None,
            "seen_bill_ids": {},                       # bill_id -> first_seen_utc
            "tracked_bills": {},                       # bill_id -> last_seen_update_date
            "last_action_signature_per_bill": {},      # bill_id -> sig
        }
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {
            "last_run_utc": None, "seen_bill_ids": {}, "tracked_bills": {},
            "last_action_signature_per_bill": {}
        }


def save_state(s):
    with open(STATE_PATH, "w") as f:
        json.dump(s, f, indent=2)


def prune_seen(seen, now):
    cutoff = now - timedelta(days=SEEN_TTL_DAYS)
    return {k: v for k, v in seen.items()
            if pd.to_datetime(v, utc=True) >= cutoff}


def make_bill_id(congress, bill_type, bill_number):
    return f"{congress}-{bill_type.upper()}-{bill_number}"


def make_action_signature(latest_action):
    if not latest_action:
        return ""
    date = latest_action.get("actionDate", "") or ""
    text = (latest_action.get("text", "") or "")[:200]
    return f"{date}|{hashlib.md5(text.encode()).hexdigest()[:12]}"


def build_url(congress, bill_type, bill_number):
    return f"https://www.congress.gov/bill/{congress}th-congress/{'house' if bill_type.lower() == 'hr' else 'senate'}-bill/{bill_number}"


# ── scoring ────────────────────────────────────────────────────────────────

def find_keyword_hits(text, keywords):
    if not text:
        return []
    text_lower = text.lower()
    return [k for k in keywords if k in text_lower]


def score_bill(bill_detail):
    """Score a bill detail dict. Returns dict with score, hits, matched_fields,
    promote (bool), priority."""
    title = (bill_detail.get("title", "") or "")
    policy_area = (bill_detail.get("policyArea", {}) or {}).get("name", "")
    subjects_list = bill_detail.get("subjects", {}).get("legislativeSubjects", []) or []
    subjects = " ".join(s.get("name", "") for s in subjects_list if s)
    sponsor_name = ""
    sponsors = bill_detail.get("sponsors", []) or []
    if sponsors:
        sponsor_name = sponsors[0].get("fullName", "") or ""

    title_high = find_keyword_hits(title, HIGH_KEYWORDS)
    title_med = find_keyword_hits(title, MEDIUM_KEYWORDS)
    subj_high = find_keyword_hits(policy_area + " " + subjects, HIGH_KEYWORDS)
    subj_med = find_keyword_hits(policy_area + " " + subjects, MEDIUM_KEYWORDS)

    matched_fields = []
    if title_high or title_med:
        matched_fields.append("title")
    if subj_high or subj_med:
        matched_fields.append("subjects")

    all_hits = list(set(title_high + title_med + subj_high + subj_med))

    score = (3 * len(title_high) + 2 * len(subj_high)
             + 1 * len(title_med) + 1 * len(subj_med))

    # Sponsor watchlist promotion
    if sponsor_name in SPONSOR_WATCHLIST:
        score += 2
        matched_fields.append("sponsor")

    # Hard-promote: any matched committee in our promote-set
    committees = bill_detail.get("committees", {}) or {}
    committee_list = committees.get("committees", []) or []
    committee_names = [c.get("name", "") for c in committee_list]
    on_promote_committee = any(c in HARD_PROMOTE_COMMITTEES for c in committee_names)
    if on_promote_committee and (title_high or subj_high):
        matched_fields.append("committee")

    promote = on_promote_committee and (title_high or subj_high or title_med or subj_med)
    priority = "immediate" if (promote or score >= SCORE_IMMEDIATE) else (
        "digest" if score >= SCORE_DIGEST else "log")

    return {
        "score": score,
        "hits": all_hits,
        "matched_fields": matched_fields,
        "promote": promote,
        "priority": priority,
        "committee_names": committee_names,
        "sponsor_name": sponsor_name,
    }


# ── fetch ──────────────────────────────────────────────────────────────────

def list_recent_bills(bill_type):
    """Stage 1: list endpoint — get recent bills with title + update date."""
    out = []
    offset = 0
    while True:
        data = api_get(f"bill/{CURRENT_CONGRESS}/{bill_type}", {
            "limit": LIST_PAGE_SIZE, "offset": offset, "sort": "updateDate+desc",
        })
        bills = data.get("bills", []) or []
        if not bills:
            break
        out.extend(bills)
        if len(out) >= LIST_LIMIT_PER_TYPE or len(bills) < LIST_PAGE_SIZE:
            break
        offset += LIST_PAGE_SIZE
        time.sleep(DETAIL_THROTTLE_SEC)
    return out[:LIST_LIMIT_PER_TYPE]


def fetch_bill_detail(congress, bill_type, bill_number):
    """Stage 2: detail endpoint — get full bill object incl. committees, subjects."""
    data = api_get(f"bill/{congress}/{bill_type}/{bill_number}")
    return data.get("bill", {}) or {}


# ── main ───────────────────────────────────────────────────────────────────

def main():
    if not CONGRESS_API_KEY:
        raise SystemExit("CONGRESS_API_KEY missing — sign up free at api.congress.gov/sign-up "
                         "and add to ~/.env")

    state = load_state()
    now_utc = datetime.now(timezone.utc)
    state["seen_bill_ids"] = prune_seen(state.get("seen_bill_ids", {}), now_utc)

    print(f"=== Congress.gov bill poll @ {now_utc.isoformat()} ===")
    print(f"Polling {CURRENT_CONGRESS}th Congress, types: {BILL_TYPES}")

    new_rows = []
    summary = {"new_bills_logged": 0, "new_actions_logged": 0, "skipped_unchanged": 0,
               "no_match": 0, "detail_failed": 0, "list_failed": 0}

    # Combined keyword set for cheap stub-title pre-filter
    all_keywords = set(HIGH_KEYWORDS + MEDIUM_KEYWORDS)

    def stub_title_matches(stub_title):
        """Cheap pre-filter: does the stub title hit any housing keyword?
        Lets us skip ~95% of detail fetches on first-run (most bills aren't
        housing). False negatives possible if title is vague but subjects/
        committees would have hit — accept the trade for ~10x speedup."""
        if not stub_title:
            return False
        title_lower = stub_title.lower()
        return any(k in title_lower for k in all_keywords)

    for bill_type in BILL_TYPES:
        print(f"\n--- Listing recent {bill_type.upper()} bills ---")
        try:
            recent = list_recent_bills(bill_type)
        except Exception as e:
            print(f"  [list failed] {e}")
            summary["list_failed"] += 1
            continue
        print(f"  {len(recent)} bills returned")

        title_filtered = 0
        detail_fetched = 0
        for i, stub in enumerate(recent):
            bill_number = str(stub.get("number", ""))
            if not bill_number:
                continue
            bill_id = make_bill_id(CURRENT_CONGRESS, bill_type, bill_number)
            stub_update = stub.get("updateDate", "")
            stub_title = stub.get("title", "") or ""

            # Skip if seen and update-date hasn't changed
            prev_update = state["tracked_bills"].get(bill_id)
            if bill_id in state["seen_bill_ids"] and prev_update == stub_update:
                summary["skipped_unchanged"] += 1
                continue

            # Cheap stub-title pre-filter — skip detail fetch if title has
            # zero housing keywords. Tracked-bills with new actions are
            # exception (we still need to fetch their detail).
            already_tracked = bill_id in state["seen_bill_ids"]
            if not already_tracked and not stub_title_matches(stub_title):
                state["seen_bill_ids"][bill_id] = now_utc.isoformat()
                state["tracked_bills"][bill_id] = stub_update
                title_filtered += 1
                continue

            # Stage 2: fetch detail
            try:
                detail = fetch_bill_detail(CURRENT_CONGRESS, bill_type, bill_number)
                time.sleep(DETAIL_THROTTLE_SEC)
                detail_fetched += 1
            except Exception as e:
                print(f"  [{bill_id}] detail fetch failed: {e}")
                summary["detail_failed"] += 1
                continue

            # Progress every 25 detail fetches
            if detail_fetched % 25 == 0:
                print(f"  ({i+1}/{len(recent)} processed, {detail_fetched} detail fetches, "
                      f"{title_filtered} title-filtered)")

            # Score
            scored = score_bill(detail)
            if scored["priority"] == "log" and not scored["hits"]:
                # Not housing-relevant at all — mark seen so we don't re-evaluate
                state["seen_bill_ids"][bill_id] = now_utc.isoformat()
                state["tracked_bills"][bill_id] = stub_update
                summary["no_match"] += 1
                continue

            # Action-change detection (re-alert if signature changed)
            latest_action = detail.get("latestAction", {}) or {}
            new_signature = make_action_signature(latest_action)
            old_signature = state["last_action_signature_per_bill"].get(bill_id, "")

            is_new_bill = bill_id not in state["seen_bill_ids"]
            is_new_action = (not is_new_bill) and (new_signature != old_signature)

            if not is_new_bill and not is_new_action:
                summary["skipped_unchanged"] += 1
                continue

            event_type = "new_bill" if is_new_bill else "new_action"
            sponsor = (detail.get("sponsors", []) or [{}])[0]
            committees_names = "|".join(scored["committee_names"])
            subjects_list = detail.get("subjects", {}).get("legislativeSubjects", []) or []
            subjects_str = "|".join(s.get("name", "") for s in subjects_list[:10])
            policy_area = (detail.get("policyArea", {}) or {}).get("name", "")
            url = build_url(CURRENT_CONGRESS, bill_type, bill_number)
            api_url = f"{API_BASE}/bill/{CURRENT_CONGRESS}/{bill_type}/{bill_number}"
            dedupe_key = f"{bill_id}|{event_type}|{new_signature}"

            new_rows.append({
                "detected_at": now_utc.isoformat(),
                "event_type": event_type,
                "bill_id": bill_id,
                "congress": CURRENT_CONGRESS,
                "bill_type": bill_type.upper(),
                "bill_number": bill_number,
                "title": (detail.get("title", "") or "")[:300],
                "sponsor_name": sponsor.get("fullName", ""),
                "sponsor_party": sponsor.get("party", ""),
                "sponsor_state": sponsor.get("state", ""),
                "introduced_date": detail.get("introducedDate", ""),
                "latest_action_date": latest_action.get("actionDate", ""),
                "latest_action_text": (latest_action.get("text", "") or "")[:300],
                "latest_action_signature": new_signature,
                "committees": committees_names,
                "policy_area": policy_area,
                "subjects": subjects_str,
                "url": url,
                "api_url": api_url,
                "matched_fields": "|".join(scored["matched_fields"]),
                "keyword_hits": "|".join(scored["hits"]),
                "score": scored["score"],
                "alert_priority": scored["priority"],
                "source_type": "congress_direct",
                "email_status": "none",
                "email_sent_at_utc": "",
                "dedupe_key": dedupe_key,
            })

            # Update state
            state["seen_bill_ids"][bill_id] = state["seen_bill_ids"].get(bill_id, now_utc.isoformat())
            state["tracked_bills"][bill_id] = stub_update
            state["last_action_signature_per_bill"][bill_id] = new_signature

            if is_new_bill:
                summary["new_bills_logged"] += 1
            else:
                summary["new_actions_logged"] += 1

    # Append to CSV
    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=CSV_COLUMNS)
        if os.path.exists(OUT_CSV):
            new_df.to_csv(OUT_CSV, mode="a", header=False, index=False)
        else:
            new_df.to_csv(OUT_CSV, index=False)
        n_imm = sum(1 for r in new_rows if r["alert_priority"] == "immediate")
        n_dig = sum(1 for r in new_rows if r["alert_priority"] == "digest")
        n_log = sum(1 for r in new_rows if r["alert_priority"] == "log")
        print(f"\n  Logged {len(new_rows)} new rows: "
              f"immediate={n_imm}, digest={n_dig}, log={n_log}")

    state["last_run_utc"] = now_utc.isoformat()
    save_state(state)

    print(f"\nSummary: {summary}")
    print(f"State persisted to {STATE_PATH}")
    print(f"Tracking {len(state['tracked_bills'])} bills "
          f"({len(state['seen_bill_ids'])} seen, {SEEN_TTL_DAYS}-day TTL)")


if __name__ == "__main__":
    main()
