"""News poller — fetches ticker-specific + macro news, scores, logs.

Mirrors the 06b → 11 architecture: this script fetches and writes to
data/news_stream_log.csv with email_status='none'. Script 14b reads
the log and dispatches alerts.

Streams:
- ticker:  /stable/news/stock?symbols=...   (262 tickers, batched 20)
- topic:   /stable/news/general-latest      (filtered post-fetch by keywords)

Scoring (per codex audit):
- score = 2 * (high-signal keyword hits) + 1 * (medium hits)
       + 2 * (trusted source) - 2 * (penalty source)
- Hard-promote rule: macro-policy term + housing-transmission term → priority='immediate'
  even if score < 5
- Cadence-aware: skip fetch if too soon since last_poll for current ET window
"""

import sys, os, json, csv, re, time, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import yaml
import pandas as pd
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

BASE = "https://financialmodelingprep.com/stable"
OUT_CSV = os.path.join(DATA_DIR, "news_stream_log.csv")
STATE_PATH = os.path.join(DATA_DIR, "news_state.json")
SOURCES_YAML = os.path.join(os.path.dirname(__file__), "..", "analyst", "news_sources.yaml")
TICKERS_CSV = os.path.join(DATA_DIR, "fmp_tickers.csv")

ET = ZoneInfo("America/New_York")

TICKER_BATCH_SIZE = 20
TICKER_NEWS_LIMIT_PER_BATCH = 50
TOPIC_NEWS_LIMIT = 100
SEEN_TTL_DAYS = 14
FIRST_RUN_LOOKBACK_HOURS = 6   # only alert on articles within this window on first run

# Keyword lists — codex's recommended structure
HIGH_SIGNAL = [
    "federal reserve", "fomc", "rate cut", "rate hike", "fed cuts", "fed hikes",
    "housing legislation", "fannie mae", "freddie mac", "fhfa", "hud",
    "assumable mortgage", "capital gains exclusion", "section 8",
    "ginnie mae", "gse reform", "housing finance reform",
]
MEDIUM_SIGNAL = [
    "nar", "national association of realtors", "existing home sales",
    "housing starts", "building permits", "mortgage rate", "30-year mortgage",
    "homebuilder", "home price", "case-shiller", "case shiller",
    "homeownership", "household formation", "rent control", "single-family rental",
]

# Hard-promote: if BOTH a macro-policy term AND a housing-transmission term hit,
# article is immediate regardless of raw score
MACRO_POLICY_TERMS = ["federal reserve", "fomc", "fhfa", "fannie", "freddie",
                      "hud", "housing legislation", "assumable mortgage",
                      "capital gains exclusion"]
HOUSING_TRANSMISSION_TERMS = ["mortgage", "housing", "home sales", "homebuilder",
                              "permits", "starts", "home price", "homeowner"]

# Tighter rule for ambiguous terms: require co-occurrence in same article
AMBIGUOUS_REQUIRES_HOUSING = ["federal reserve", "fomc", "rate cut", "rate hike",
                              "fed cuts", "fed hikes", "30-year"]

# Topic-stream denylist — drop article entirely if title matches any
TOPIC_DENY_PATTERNS = [
    r"\bpayment(?:s)?\s+system\b",
    r"\bbank supervis",
    r"\breserve bank\b",     # FRBs operating, not policy
    r"\b(?:cyber|software|staff(?:ing)?)\b",
    r"\bzelle\b",
    r"\bbasel\b",
    r"\bsupervisory letter\b",
]

# Threshold scores
SCORE_IMMEDIATE = 5
SCORE_DIGEST = 3

CSV_COLUMNS = [
    "detected_at", "published_at", "stream", "ticker", "fmp_symbol",
    "publisher", "site", "title", "text", "url", "dedupe_key",
    "score", "keyword_hits_high", "keyword_hits_medium", "matched_in",
    "matched_tickers", "alert_priority", "email_status", "email_sent_at_utc",
]


# ── helpers ────────────────────────────────────────────────────────

def load_sources():
    if not os.path.exists(SOURCES_YAML):
        return {"trusted": set(), "normal": set(), "penalty": set(), "exclude": set()}
    with open(SOURCES_YAML) as f:
        data = yaml.safe_load(f) or {}
    return {k: set(v or []) for k, v in data.items()}


def source_tier(site, publisher, sources):
    """Classify article source into trusted / normal / penalty / exclude."""
    site_lower = (site or "").lower()
    pub_lower = (publisher or "").lower()
    for tier in ("exclude", "trusted", "penalty", "normal"):
        for entry in sources.get(tier, []):
            if entry.lower() in site_lower or entry.lower() in pub_lower:
                return tier
    return "normal"  # default


def normalize_url(url):
    """Strip query params and fragments for stable dedupe."""
    if not url:
        return ""
    try:
        p = urlsplit(url.strip().lower())
        return urlunsplit((p.scheme, p.netloc, p.path.rstrip("/"), "", ""))
    except Exception:
        return url.strip().lower()


def build_dedupe_key(stream, url, publisher, published_at, title):
    norm = normalize_url(url)
    if norm:
        return f"{stream}|{norm}"
    # Fallback: publisher + date + title hash
    h = hashlib.md5(f"{publisher}|{published_at}|{title}".encode()).hexdigest()[:16]
    return f"{stream}|{h}"


def fmp_get(endpoint, params=None, timeout=30):
    if params is None:
        params = {}
    params["apikey"] = FMP_API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
    if r.status_code == 429:
        time.sleep(60)
        return fmp_get(endpoint, params, timeout)
    r.raise_for_status()
    return r.json()


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"last_run_utc": None, "last_poll_utc": None, "seen_keys": {}}
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {"last_run_utc": None, "last_poll_utc": None, "seen_keys": {}}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def prune_seen(seen, now_utc):
    cutoff = now_utc - timedelta(days=SEEN_TTL_DAYS)
    return {k: v for k, v in seen.items()
            if pd.to_datetime(v, utc=True) >= cutoff}


def should_poll_now(now_utc, last_poll_utc):
    """Cadence: 5 min market hours, 15 min 4-8 PM ET, 30 min off-hours."""
    if last_poll_utc is None:
        return True, "first poll"
    last_poll = pd.to_datetime(last_poll_utc, utc=True)
    elapsed = (now_utc - last_poll).total_seconds()
    now_et = now_utc.astimezone(ET)
    weekday = now_et.weekday() < 5
    hour = now_et.hour
    minute = now_et.minute

    in_market = weekday and ((hour == 9 and minute >= 30) or (10 <= hour < 16))
    in_extended = weekday and (16 <= hour < 20)

    if in_market:
        return elapsed >= 285, f"market hours, {int(elapsed)}s since last poll"
    if in_extended:
        return elapsed >= 880, f"extended hours, {int(elapsed)}s since last poll"
    return elapsed >= 1780, f"off-hours, {int(elapsed)}s since last poll"


# ── scoring ────────────────────────────────────────────────────────

def find_hits(text, keywords):
    text_lower = text.lower()
    return [k for k in keywords if k in text_lower]


def score_article(title, body, site, publisher, sources):
    title_lower = (title or "").lower()
    body_lower = (body or "").lower()
    combined = title_lower + " " + body_lower

    high_hits = find_hits(combined, HIGH_SIGNAL)
    medium_hits = find_hits(combined, MEDIUM_SIGNAL)

    # Apply ambiguity rule: if hit is in AMBIGUOUS_REQUIRES_HOUSING but no
    # housing-transmission term in the article, drop it from the count
    if any(amb in high_hits or amb in medium_hits for amb in AMBIGUOUS_REQUIRES_HOUSING):
        if not any(t in combined for t in HOUSING_TRANSMISSION_TERMS):
            high_hits = [h for h in high_hits if h not in AMBIGUOUS_REQUIRES_HOUSING]
            medium_hits = [m for m in medium_hits if m not in AMBIGUOUS_REQUIRES_HOUSING]

    # Title-first: hits in title get +1 bonus each
    title_high = find_hits(title_lower, HIGH_SIGNAL)
    title_medium = find_hits(title_lower, MEDIUM_SIGNAL)

    score = 2 * len(high_hits) + len(medium_hits) + len(title_high) + len(title_medium) // 2

    # Source tier adjustment
    tier = source_tier(site, publisher, sources)
    if tier == "trusted":
        score += 2
    elif tier == "penalty":
        score -= 2
    # exclude is filtered before scoring

    matched_in = []
    if title_high or title_medium:
        matched_in.append("title")
    if (set(high_hits) - set(title_high)) or (set(medium_hits) - set(title_medium)):
        matched_in.append("text")

    # Hard-promote: macro + housing combo
    has_macro = any(t in combined for t in MACRO_POLICY_TERMS)
    has_housing = any(t in combined for t in HOUSING_TRANSMISSION_TERMS)
    promote = has_macro and has_housing

    return {
        "score": score,
        "high_hits": high_hits,
        "medium_hits": medium_hits,
        "matched_in": "|".join(matched_in) if matched_in else "",
        "tier": tier,
        "promote": promote,
    }


def alert_priority(score, promote):
    if promote or score >= SCORE_IMMEDIATE:
        return "immediate"
    if score >= SCORE_DIGEST:
        return "digest"
    return "log"


def topic_passes_denylist(title):
    title_lower = (title or "").lower()
    return not any(re.search(p, title_lower) for p in TOPIC_DENY_PATTERNS)


# ── fetch ──────────────────────────────────────────────────────────

def fetch_ticker_news(tickers):
    """Returns list of (article_dict, ticker_or_None) tuples."""
    out = []
    for i in range(0, len(tickers), TICKER_BATCH_SIZE):
        batch = tickers[i:i + TICKER_BATCH_SIZE]
        symbols = ",".join(batch)
        try:
            data = fmp_get("news/stock", {
                "symbols": symbols,
                "limit": TICKER_NEWS_LIMIT_PER_BATCH,
            })
            for art in (data or []):
                out.append((art, art.get("symbol")))
        except Exception as e:
            print(f"  ticker batch {i//TICKER_BATCH_SIZE+1} failed: {e}")
        time.sleep(0.2)
    return out


def fetch_topic_news():
    try:
        data = fmp_get("news/general-latest", {"limit": TOPIC_NEWS_LIMIT})
        return [(a, None) for a in (data or [])]
    except Exception as e:
        print(f"  topic stream failed: {e}")
        return []


def extract_universe_tickers_from_topic(title, body, universe_set):
    """Find $TICKER mentions in article body for topic-stream articles."""
    text = (title or "") + " " + (body or "")
    matches = re.findall(r"\$([A-Z]{1,5})\b", text)
    matches += re.findall(r"\b([A-Z]{2,5})\b", text)
    return sorted(set(m for m in matches if m in universe_set))


# ── main ───────────────────────────────────────────────────────────

def main():
    if not FMP_API_KEY:
        raise SystemExit("FMP_API_KEY is empty. Check ~/.env")

    state = load_state()
    now_utc = datetime.now(timezone.utc)
    state["seen_keys"] = prune_seen(state.get("seen_keys", {}), now_utc)

    ok, reason = should_poll_now(now_utc, state.get("last_poll_utc"))
    if not ok:
        print(f"Skipping poll — {reason}")
        return
    print(f"Polling — {reason}")

    sources = load_sources()
    universe_df = pd.read_csv(TICKERS_CSV)
    tickers = universe_df["ticker"].dropna().unique().tolist()
    universe_set = set(tickers)
    seen = state.get("seen_keys", {})
    first_run = state.get("last_run_utc") is None

    # Fetch
    ticker_articles = fetch_ticker_news(tickers)
    topic_articles_raw = fetch_topic_news()
    topic_articles = [(a, None) for a, _ in topic_articles_raw
                      if topic_passes_denylist(a.get("title", ""))]
    print(f"  Ticker articles: {len(ticker_articles)} fetched")
    print(f"  Topic articles: {len(topic_articles)} after denylist "
          f"(of {len(topic_articles_raw)} raw)")

    new_rows = []
    suppressed_first_run = 0
    skipped_dedupe = 0
    skipped_excluded = 0

    for article, fmp_symbol in ticker_articles + topic_articles:
        title = article.get("title", "") or ""
        body = (article.get("text", "") or "")[:5000]
        url = article.get("url", "") or article.get("link", "") or ""
        publisher = article.get("publisher", "") or article.get("source", "") or ""
        site = article.get("site", "") or ""
        published_at = article.get("publishedDate", "") or ""

        stream = "ticker" if fmp_symbol else "topic"
        key = build_dedupe_key(stream, url, publisher, published_at, title)
        if key in seen:
            skipped_dedupe += 1
            continue

        # Pre-score: drop excluded sources entirely
        tier = source_tier(site, publisher, sources)
        if tier == "exclude":
            seen[key] = now_utc.isoformat()  # mark seen so we don't re-evaluate
            skipped_excluded += 1
            continue

        # Score
        s = score_article(title, body, site, publisher, sources)
        priority = alert_priority(s["score"], s["promote"])

        # Determine ticker for the row
        ticker = fmp_symbol if fmp_symbol in universe_set else ""
        matched_tickers = []
        if stream == "topic":
            matched_tickers = extract_universe_tickers_from_topic(title, body, universe_set)
            if matched_tickers and not ticker:
                ticker = matched_tickers[0]

        # First-run: suppress alerts on articles older than FIRST_RUN_LOOKBACK_HOURS
        if first_run and priority != "log":
            try:
                pub = pd.to_datetime(published_at, utc=True, errors="coerce")
                if pd.notna(pub) and (now_utc - pub).total_seconds() > FIRST_RUN_LOOKBACK_HOURS * 3600:
                    priority = "log"  # demote to log-only
                    suppressed_first_run += 1
            except Exception:
                pass

        new_rows.append({
            "detected_at": now_utc.isoformat(),
            "published_at": published_at,
            "stream": stream,
            "ticker": ticker,
            "fmp_symbol": fmp_symbol or "",
            "publisher": publisher,
            "site": site,
            "title": title[:300],
            "text": body[:600],
            "url": url,
            "dedupe_key": key,
            "score": s["score"],
            "keyword_hits_high": "|".join(s["high_hits"]),
            "keyword_hits_medium": "|".join(s["medium_hits"]),
            "matched_in": s["matched_in"],
            "matched_tickers": "|".join(matched_tickers),
            "alert_priority": priority,
            "email_status": "none",
            "email_sent_at_utc": "",
        })
        seen[key] = now_utc.isoformat()

    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=CSV_COLUMNS)
        if os.path.exists(OUT_CSV):
            new_df.to_csv(OUT_CSV, mode="a", header=False, index=False)
        else:
            new_df.to_csv(OUT_CSV, index=False)
        n_imm = sum(1 for r in new_rows if r["alert_priority"] == "immediate")
        n_dig = sum(1 for r in new_rows if r["alert_priority"] == "digest")
        n_log = sum(1 for r in new_rows if r["alert_priority"] == "log")
        print(f"  Logged {len(new_rows)} new rows: "
              f"immediate={n_imm}, digest={n_dig}, log={n_log}")
    else:
        print("  No new articles after dedupe.")

    print(f"  Skipped: {skipped_dedupe} (already seen), {skipped_excluded} (excluded source)")
    if first_run:
        print(f"  First-run: suppressed {suppressed_first_run} alerts on articles older than {FIRST_RUN_LOOKBACK_HOURS}h")

    state["last_poll_utc"] = now_utc.isoformat()
    state["last_run_utc"] = now_utc.isoformat()
    state["seen_keys"] = seen
    save_state(state)


if __name__ == "__main__":
    main()
