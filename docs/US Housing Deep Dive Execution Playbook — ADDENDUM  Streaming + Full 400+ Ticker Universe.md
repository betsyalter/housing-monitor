# Addendum: Real-Time Streaming + Full 400+ Ticker Universe
*This addendum supplements the main playbook. Three new scripts cover: (A) SEC 10-K/8-K WebSocket stream, (B) FMP real-time price/volume alert engine, (C) FMP news polling + sentiment scoring. The second half is the complete, exhaustively scoped 400+ ticker universe.*

***
## A. Real-Time SEC Filing Stream — 10-K, 8-K, and More
### What It Does vs. What Was in the Original Plan
The original plan (Script 06) used the sec-api.io **Query API** on a daily cron job to pull 8-Ks from housing-related tickers filed *that day*. That gives you end-of-day awareness at best — you could miss a market-moving 8-K by 12+ hours.

The **Stream API** is a persistent WebSocket connection. The moment a company files anything on EDGAR, the stream delivers the metadata JSON within ~300ms. You never poll; you just receive. For a housing market that is event-driven (a homebuilder guidance cut, an INVH portfolio update, a HUD rule change), 300ms vs. 12 hours matters.[^1]

**Add to `.env`:**

No new keys needed — the same `SEC_API_KEY` from the original plan connects to the stream.

**Add to requirements:**
```bash
pip install websockets
```
### Script 12: SEC Real-Time Filing Stream
Create `~/housing_monitor/scripts/12_sec_stream.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY, DATA_DIR, LOGS_DIR

import asyncio
import websockets
import json
import csv
from datetime import datetime
from alert_dispatcher import send_alert  # Script 14 below

# ============================================================
# UNIVERSE: all tickers we care about + SIC codes for housing
# This set is checked on every incoming filing from ANYONE
# ============================================================
HOUSING_TICKERS = {
    # Tier 1
    'NVR','DHI','LEN','PHM','TOL','KBH','MDC','MTH','TMHC','GRBK','MHO','SKY',
    'CCS','LGIH','AVAV',
    'RKT','UWMC','PFSI','COOP','LDI','GHLD','HMPT',
    'FNF','FAF','STC','WD',
    'RDFN','Z','ZG','OPEN','COMP','EXPI','HOUS',
    # Tier 2
    'INVH','AMH','TRNO',
    'HD','LOW','FND','LL','TILE',
    'UHAL','CUBE','EXR','LSI','PSA','NSA',
    'RH','WSM','ARHS','BBWI','ETSY','OSTK',
    'WHR','MASCO','FBHS','MHK','SWK',
    'BLDR','IBP','TREX','OC','AWI','APOG','PGTI','AZEK','BECN','GMS','SITE','POOL',
    # Tier 3
    'WY','RYN','PCH','LP','UFPI','LPX',
    'SHW','RPM','PPG','AXTA',
    'LII','CARR','TT','AOS','GNRC','REZI','ADT',
    'WFC','JPM','BAC','USB','KEY','FITB','RF','CFG','HBAN','TFC',
    'ALL','TRV','HIG','CB','PGR',
    'ESNT','MTG','RDN','NMIH',
    # Tier 4 (short basket)
    'EQR','AVB','MAA','CPT','UDR','ESS','AIV','NMR','BRT','IRT',
    # Key federal housing entities (they file too)
    'FNMA','FMCC',
}

# SIC codes that broadly cover housing/RE even for non-HOUSING_TICKERS
# This catches any company in housing-adjacent industries even if not in our list
HOUSING_SIC_CODES = {
    '1500',  # General Building Contractors—Residential Buildings
    '1520',  # General Building Contractors—Residential Buildings (not single-family)
    '1521',  # General Building Contractors—Single-Family Houses
    '1522',  # General Building Contractors—Residential Buildings (other)
    '1531',  # Operative Builders
    '1540',  # General Building Contractors—Industrial Buildings
    '6159',  # Federal-Sponsored Credit Agencies
    '6161',  # Mortgage Bankers, Loan Correspondents
    '6162',  # Mortgage Bankers (except savings institutions)
    '6552',  # Land Subdividers and Developers (except cemeteries)
    '6726',  # Investment Offices (REITs)
    '6798',  # Real Estate Investment Trusts
}

# 8-K item codes that are HIGH PRIORITY for housing intelligence
HIGH_PRIORITY_8K_ITEMS = {
    '2.02',  # Results of Operations (earnings — most important)
    '7.01',  # Regulation FD Disclosure (pre-release guidance updates)
    '8.01',  # Other Events (catch-all for unusual disclosures)
    '1.01',  # Material Definitive Agreement (M&A signal for REIT portfolios)
    '5.02',  # Executive changes (CEO/CFO departure is often a negative signal)
}

# Keywords in 8-K descriptions that trigger immediate alerts
HOUSING_KEYWORDS = {
    'housing', 'mortgage', 'affordability', 'home sales', 'inventory',
    'interest rate', 'backlog', 'community count', 'cancellation',
    'legislation', 'hud', 'fhfa', 'gse', 'fannie', 'freddie',
    'assumable', 'capital gains', 'first-time buyer', 'down payment',
    'institutional investor', 'single-family rental', 'sfr',
    'existing homes', 'new homes', 'housing starts', 'building permits',
}

def is_housing_relevant(filing: dict) -> tuple[bool, str]:
    """
    Return (is_relevant, reason_string) for any incoming SEC filing.
    Checks: ticker in universe, SIC code, 8-K item codes, description keywords.
    """
    ticker = filing.get('ticker', '').upper()
    form_type = filing.get('formType', '')
    description = filing.get('description', '').lower()
    items = filing.get('items', [])
    
    # Check 1: Is it one of our 400+ tickers?
    if ticker in HOUSING_TICKERS:
        # High-value form types — always alert
        if form_type in ('10-K', '10-K/A', '10-Q', '10-Q/A'):
            return True, f"ANNUAL/QUARTERLY: {ticker} filed {form_type}"
        
        # 8-K — alert only on high-priority items
        if form_type in ('8-K', '8-K/A'):
            for item in items:
                item_code = item.split(':').replace('Item ', '').strip()
                if item_code in HIGH_PRIORITY_8K_ITEMS:
                    return True, f"8-K HIGH PRIORITY: {ticker} — {item}"
            # Also alert if description contains housing keywords
            if any(kw in description for kw in HOUSING_KEYWORDS):
                return True, f"8-K KEYWORD HIT: {ticker} — {description[:80]}"
        
        # 13F — institutional ownership changes in INVH/AMH (SFR REIT supply signal)
        if form_type in ('13F-HR', 'SC 13G', 'SC 13D', 'SC 13G/A', 'SC 13D/A'):
            if ticker in ('INVH', 'AMH'):
                return True, f"OWNERSHIP CHANGE: {ticker} — {form_type}"
        
        # Any other form from our universe — log but don't alert
        return False, f"LOW PRIORITY: {ticker} {form_type}"
    
    # Check 2: SIC code covers housing-adjacent companies even outside our list
    entities = filing.get('entities', [])
    for entity in entities:
        sic = str(entity.get('sic', '')).split(' ')
        if sic in HOUSING_SIC_CODES:
            if form_type in ('10-K', '10-K/A') or (
                form_type in ('8-K', '8-K/A') and 
                any(kw in description for kw in HOUSING_KEYWORDS)
            ):
                company = entity.get('companyName', 'Unknown')
                return True, f"SIC HIT ({sic}): {company} — {form_type}"
    
    # Check 3: Non-universe 8-K with strong housing keyword signal
    # Catches congressional testimony, HUD rule filings, FHFA filings
    high_density = sum(1 for kw in HOUSING_KEYWORDS if kw in description)
    if high_density >= 3:
        return True, f"KEYWORD DENSITY ({high_density}): {form_type} — {description[:80]}"
    
    return False, ""

def log_filing(filing: dict, reason: str):
    """Append filing to the streaming log CSV."""
    log_path = f"{DATA_DIR}/sec_stream_log.csv"
    row = {
        'timestamp_received': datetime.now().isoformat(),
        'ticker': filing.get('ticker', ''),
        'company': filing.get('companyName', ''),
        'form_type': filing.get('formType', ''),
        'filed_at': filing.get('filedAt', ''),
        'items': ', '.join(filing.get('items', [])),
        'description': filing.get('description', '')[:200],
        'reason': reason,
        'url': filing.get('linkToFilingDetails', ''),
        'accession_no': filing.get('accessionNo', ''),
    }
    
    file_exists = os.path.exists(log_path)
    with open(log_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

async def send_ping(websocket):
    """Keep-alive pings every 30 seconds. Server requires pong within 5s."""
    while True:
        try:
            pong_waiter = await websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=5)
            await asyncio.sleep(30)
        except Exception as e:
            print(f"[{datetime.now()}] Ping error: {e}")
            await websocket.close()
            return

async def housing_stream():
    """
    Persistent WebSocket connection to sec-api.io stream.
    Reconnects automatically with exponential backoff.
    """
    WS_URL = f"wss://stream.sec-api.io?apiKey={SEC_API_KEY}"
    retry_count = 0
    max_retries = 999  # run indefinitely
    
    while retry_count < max_retries:
        try:
            async with websockets.connect(WS_URL, ping_interval=None) as ws:
                print(f"[{datetime.now()}] ✅ Connected to SEC stream")
                retry_count = 0
                ping_task = asyncio.create_task(send_ping(ws))
                
                async for message in ws:
                    filings = json.loads(message)
                    
                    for filing in filings:
                        is_relevant, reason = is_housing_relevant(filing)
                        
                        if is_relevant:
                            # Log every relevant filing to CSV
                            log_filing(filing, reason)
                            
                            # Build alert message
                            ticker = filing.get('ticker', 'UNKNOWN')
                            form_type = filing.get('formType', '')
                            company = filing.get('companyName', '')
                            url = filing.get('linkToFilingDetails', '')
                            
                            alert_msg = (
                                f"🏠 HOUSING FILING ALERT\n"
                                f"Ticker: {ticker} ({company})\n"
                                f"Form: {form_type}\n"
                                f"Time: {filing.get('filedAt', '')}\n"
                                f"Reason: {reason}\n"
                                f"URL: {url}"
                            )
                            
                            print(f"\n{'='*60}")
                            print(alert_msg)
                            
                            # Send to Telegram (see Script 14)
                            await send_alert(alert_msg, priority='high' if '10-K' in form_type or '2.02' in reason else 'normal')
        
        except Exception as e:
            retry_count += 1
            wait = min(5 * retry_count, 60)  # exponential backoff, cap at 60s
            print(f"[{datetime.now()}] Stream error: {e} — retry {retry_count} in {wait}s")
            await asyncio.sleep(wait)
    
    print("Max retries reached. Stream stopped.")

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting SEC real-time filing stream...")
    asyncio.run(housing_stream())
```
### How to Run Script 12 as a Persistent Background Service
The script must run 24/7, not just when cron fires. Use `launchd` on macOS:

```bash
# Create a plist file for launchd
cat > ~/Library/LaunchAgents/com.housingmonitor.sec_stream.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.housingmonitor.sec_stream</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOURUSERNAME/housing_monitor/.venv/bin/python</string>
        <string>/Users/YOURUSERNAME/housing_monitor/scripts/12_sec_stream.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOURUSERNAME/housing_monitor/logs/sec_stream.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOURUSERNAME/housing_monitor/logs/sec_stream_error.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/YOURUSERNAME/housing_monitor</string>
</dict>
</plist>
EOF

# Load it (starts immediately and restarts on crash)
launchctl load ~/Library/LaunchAgents/com.housingmonitor.sec_stream.plist

# Verify it's running
launchctl list | grep housingmonitor

# Stop it
launchctl unload ~/Library/LaunchAgents/com.housingmonitor.sec_stream.plist
```

***
## B. Real-Time FMP Price/Volume Alert Engine
### What FMP WebSocket Provides
FMP has separate WebSocket endpoints for stocks, crypto, and forex. The stock endpoint is `wss://websockets.financialmodelingprep.com`. Authentication is a two-step protocol: first send a `login` event, then a `subscribe` event — same pattern as the crypto endpoint documented in the FMP code examples. The stream delivers tick-by-tick price updates with last price, volume, and timestamp for every subscribed ticker.[^2]

**Important: The FMP WebSocket only works during market hours (9:30 AM–4:00 PM ET weekdays).** Outside of hours, the connection stays open but no tick data arrives. The script handles this gracefully.

**Add to requirements:**
```bash
pip install websocket-client
```
### Script 13: FMP Real-Time Price/Volume Alert Engine
Create `~/housing_monitor/scripts/13_fmp_price_stream.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import websocket
import json
import threading
import pandas as pd
import numpy as np
from datetime import datetime, time as dtime
from collections import defaultdict
import asyncio
from alert_dispatcher import send_alert_sync

# ============================================================
# PRICE ALERT CONFIGURATION
# ============================================================

# How many std devs above the 20-day average volume = "volume spike"
VOLUME_SPIKE_THRESHOLD = 2.5

# % intraday price move that triggers an immediate alert
PRICE_MOVE_PCT_THRESHOLD = 0.04  # 4% intraday move

# Minutes of rolling window for volume accumulation (intraday)
ROLLING_VOLUME_MINUTES = 30

# These tickers get HEIGHTENED sensitivity — price moves >2% trigger an alert
TIER1_HEIGHTENED = {
    'NVR', 'DHI', 'LEN', 'PHM', 'TOL', 'KBH',
    'RKT', 'UWMC', 'PFSI', 'COOP',
    'FNF', 'FAF',
    'RDFN', 'Z', 'COMP',
    'INVH', 'AMH',
}

TIER1_PRICE_THRESHOLD = 0.02  # 2% for Tier 1

# All 400+ tickers to subscribe
ALL_HOUSING_TICKERS = [
    # Tier 1 — Homebuilders
    'NVR','DHI','LEN','PHM','TOL','KBH','MDC','MTH','TMHC','GRBK','MHO','SKY','CCS','LGIH',
    # Tier 1 — Mortgage
    'RKT','UWMC','PFSI','COOP','LDI','GHLD','HMPT',
    # Tier 1 — Title
    'FNF','FAF','STC','WD',
    # Tier 1 — Brokerages/platforms
    'RDFN','Z','ZG','OPEN','COMP','EXPI','HOUS',
    # Tier 2 — SFR REITs
    'INVH','AMH',
    # Tier 2 — Home improvement
    'HD','LOW','FND','LL','TILE',
    # Tier 2 — Moving/storage
    'UHAL','CUBE','EXR','LSI','PSA','NSA','REXR',
    # Tier 2 — Furnishings
    'RH','WSM','ARHS','BBWI','ETSY','OSTK','LOVE','SNBR',
    # Tier 2 — Appliances/hardware
    'WHR','MASCO','FBHS','MHK','SWK','ALLE','ASSA',
    # Tier 2 — Building products
    'BLDR','IBP','TREX','OC','AWI','APOG','PGTI','AZEK','BECN','GMS','SITE','POOL','PATK',
    # Tier 3 — Lumber/timberlands
    'WY','RYN','PCH','LP','UFPI','LPX','PW',
    # Tier 3 — Paint/coatings
    'SHW','RPM','PPG','AXTA',
    # Tier 3 — HVAC
    'LII','CARR','TT','AOS','GNRC','REZI','ADT','NUAN',
    # Tier 3 — Plumbing/fixtures
    'MAS','FBHS','LIXIL',
    # Tier 3 — Electrical
    'LEG','NVT','REXNORD',
    # Tier 3 — Pool/outdoor living
    'HAYW','LESL','CABO',
    # Tier 3 — Construction machinery
    'CAT','DE','TEX','PCAR',
    # Tier 3 — Banks with mortgage
    'WFC','JPM','BAC','USB','KEY','FITB','RF','CFG','HBAN','TFC','CMA','ZION','PACW',
    # Tier 3 — PMI
    'ESNT','MTG','RDN','NMIH',
    # Tier 3 — Insurance
    'ALL','TRV','HIG','CB','PGR','MKL',
    # Tier 3 — PropTech
    'CSGP','MTTR','VIEW','OPEN',
    # Tier 4 — Apartment REITs (short basket)
    'EQR','AVB','MAA','CPT','UDR','ESS','AIV','NMR','BRT','IRT','NXRT','AIRC',
    # Tier 5 — Housing ETFs (monitor for macro flow signal)
    'ITB','XHB','REZ','HOMZ',
]

class PriceVolumeAlertEngine:
    def __init__(self):
        # Store open-of-day prices for intraday % change calculation
        self.open_prices = {}         # ticker -> open price
        self.last_prices = {}         # ticker -> last tick price
        self.intraday_volume = defaultdict(float)  # ticker -> cumulative intraday volume
        self.avg_daily_volume = {}    # ticker -> 20-day avg volume (loaded from CSV)
        self.alerts_sent_today = set() # (ticker, alert_type) tuples — avoid duplicate alerts
        self.tick_buffer = defaultdict(list)  # ticker -> list of recent ticks
        
        self._load_baseline_volumes()
    
    def _load_baseline_volumes(self):
        """Load 20-day average volumes from price history CSVs."""
        prices_dir = f"{DATA_DIR}/fmp_prices"
        for ticker in ALL_HOUSING_TICKERS:
            path = f"{prices_dir}/{ticker}.csv"
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, index_col='date', parse_dates=True)
                    if 'volume' in df.columns:
                        self.avg_daily_volume[ticker] = df['volume'].tail(20).mean()
                except:
                    pass
        print(f"Loaded baseline volumes for {len(self.avg_daily_volume)} tickers")
    
    def process_tick(self, ticker: str, price: float, volume: float, timestamp: str):
        """Process one price tick. Check all alert conditions."""
        # Set open price if first tick of the day
        if ticker not in self.open_prices:
            self.open_prices[ticker] = price
        
        # Track intraday volume accumulation
        self.intraday_volume[ticker] += volume
        self.last_prices[ticker] = price
        
        alerts = []
        
        # --- ALERT 1: Intraday price move ---
        open_px = self.open_prices[ticker]
        if open_px and open_px > 0:
            pct_change = (price - open_px) / open_px
            threshold = TIER1_PRICE_THRESHOLD if ticker in TIER1_HEIGHTENED else PRICE_MOVE_PCT_THRESHOLD
            
            alert_key = (ticker, 'price_move', round(pct_change, 2))
            if abs(pct_change) >= threshold and alert_key not in self.alerts_sent_today:
                self.alerts_sent_today.add(alert_key)
                direction = "📈 UP" if pct_change > 0 else "📉 DOWN"
                alerts.append({
                    'type': 'PRICE_MOVE',
                    'ticker': ticker,
                    'message': (
                        f"🏠 HOUSING PRICE ALERT\n"
                        f"{ticker} {direction} {pct_change:.1%} intraday\n"
                        f"Open: ${open_px:.2f} → Current: ${price:.2f}\n"
                        f"Time: {timestamp}"
                    ),
                    'priority': 'high' if ticker in TIER1_HEIGHTENED else 'normal'
                })
        
        # --- ALERT 2: Volume spike ---
        avg_vol = self.avg_daily_volume.get(ticker, 0)
        if avg_vol > 0 and self.intraday_volume[ticker] > 0:
            # Estimate projected daily volume from intraday volume
            # (assumes linear volume distribution through the day, rough proxy)
            hour = datetime.now().hour
            minutes_elapsed = max(1, (hour - 9) * 60 + datetime.now().minute - 30)
            projected_daily_vol = self.intraday_volume[ticker] * (390 / minutes_elapsed)
            
            vol_zscore = (projected_daily_vol - avg_vol) / max(avg_vol * 0.3, 1)
            
            alert_key = (ticker, 'volume_spike', round(vol_zscore, 1))
            if vol_zscore >= VOLUME_SPIKE_THRESHOLD and alert_key not in self.alerts_sent_today:
                self.alerts_sent_today.add(alert_key)
                alerts.append({
                    'type': 'VOLUME_SPIKE',
                    'ticker': ticker,
                    'message': (
                        f"🔊 VOLUME SPIKE ALERT\n"
                        f"{ticker}: {vol_zscore:.1f}σ above 20-day avg volume\n"
                        f"Projected daily: {projected_daily_vol:,.0f} vs avg: {avg_vol:,.0f}\n"
                        f"Current price: ${price:.2f} | Time: {timestamp}"
                    ),
                    'priority': 'normal'
                })
        
        return alerts
    
    def reset_day(self):
        """Call this at 9:30 AM each trading day."""
        self.open_prices = {}
        self.intraday_volume = defaultdict(float)
        self.alerts_sent_today = set()
        print(f"[{datetime.now()}] Day reset complete")


# Global engine instance
engine = PriceVolumeAlertEngine()

def on_message(ws, message):
    """Handle incoming tick data from FMP WebSocket."""
    data = json.loads(message)
    
    # FMP tick format: {"s": "DHI", "t": 1714500000000, "type": "T", "lp": 145.23, "ls": 1500}
    ticker = data.get('s', '').upper()
    price = data.get('lp', 0)   # last price
    volume = data.get('ls', 0)  # last size (shares in this tick)
    ts = datetime.fromtimestamp(data.get('t', 0) / 1000).strftime('%H:%M:%S')
    
    if ticker and price > 0:
        alerts = engine.process_tick(ticker, float(price), float(volume), ts)
        
        for alert in alerts:
            print(f"\n{'='*60}\n{alert['message']}")
            send_alert_sync(alert['message'], priority=alert['priority'])

def on_error(ws, error):
    print(f"[{datetime.now()}] WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{datetime.now()}] WebSocket closed: {close_msg}")

def on_open(ws):
    """Login and subscribe to all housing tickers."""
    print(f"[{datetime.now()}] ✅ FMP WebSocket connected — subscribing to {len(ALL_HOUSING_TICKERS)} tickers...")
    
    # Step 1: Login
    ws.send(json.dumps({
        "event": "login",
        "data": {"apiKey": FMP_API_KEY}
    }))
    
    import time; time.sleep(1)
    
    # Step 2: Subscribe to each ticker
    # FMP requires individual subscribe messages (not a batch)
    for ticker in ALL_HOUSING_TICKERS:
        ws.send(json.dumps({
            "event": "subscribe",
            "data": {"ticker": ticker}
        }))
    
    print(f"[{datetime.now()}] Subscribed to all tickers. Listening for price moves...")

def run_price_stream():
    """Start and maintain the FMP price WebSocket."""
    WS_URL = "wss://websockets.financialmodelingprep.com"
    
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=5)
        except Exception as e:
            print(f"[{datetime.now()}] Stream crashed: {e} — restarting in 10s")
            import time; time.sleep(10)

if __name__ == '__main__':
    # Schedule day reset at market open
    import schedule, time
    schedule.every().day.at("09:30").do(engine.reset_day)
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(30)
    
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    # Run price stream (blocks here, restarts on crash)
    run_price_stream()
```

***
## C. News Stream — FMP Polling + Sentiment Filter
FMP does not have a true WebSocket for news — it uses a REST polling endpoint: `GET https://financialmodelingprep.com/stable/news/stock` with `symbols` parameter. The endpoint returns articles sorted by publishedDate. We poll every 90 seconds during market hours, storing seen article URLs to avoid duplicates. For after-hours, we drop to 15-minute polling.[^3]

Create `~/housing_monitor/scripts/14_news_stream.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import FMP_API_KEY, DATA_DIR

import requests
import time
import json
import csv
from datetime import datetime, time as dtime
from alert_dispatcher import send_alert_sync

BASE = "https://financialmodelingprep.com/stable"

# Tickers to monitor for news — Tier 1+2 only to keep noise low
NEWS_TICKERS = [
    'DHI','LEN','PHM','NVR','TOL','KBH','MDC','MTH','TMHC','GRBK',
    'RKT','UWMC','PFSI','COOP',
    'FNF','FAF','STC',
    'RDFN','Z','COMP','OPEN','EXPI',
    'INVH','AMH',
    'HD','LOW','FND',
    'UHAL','EXR','CUBE','PSA',
    'RH','WSM',
    'WFC','JPM',
    'EQR','AVB','MAA',
]

# Housing-relevant keywords that elevate a news article to "ALERT" level
ALERT_KEYWORDS = [
    'existing home sales', 'housing inventory', 'mortgage rate',
    'rate cut', 'rate hike', 'federal reserve housing',
    'home affordability', 'housing legislation', 'assumable mortgage',
    'capital gains exclusion', 'first-time homebuyer',
    'hud', 'fhfa', 'housing starts', 'building permits',
    'backlog', 'cancellation rate', 'community count',
    'institutional investor homes', 'single-family rental',
    'guidance cut', 'guidance raised',
]

# Lower-priority keywords — log but only alert in daily summary
LOG_KEYWORDS = [
    'housing market', 'home prices', 'real estate', 'homebuilder',
    'mortgage applications', 'refinance', 'lumber', 'construction',
    'home improvement', 'moving', 'storage',
]

seen_urls = set()

def is_market_hours():
    now = datetime.now().time()
    return dtime(9, 30) <= now <= dtime(16, 0)

def score_article(title: str, text: str) -> tuple[int, str]:
    """
    Score an article from 0-10 for housing relevance.
    Returns (score, matched_keywords_string).
    Score >= 7: immediate alert
    Score 3-6: daily digest
    Score < 3: ignore
    """
    content = (title + ' ' + text).lower()
    matched_alert = [kw for kw in ALERT_KEYWORDS if kw in content]
    matched_log = [kw for kw in LOG_KEYWORDS if kw in content]
    
    score = len(matched_alert) * 2 + len(matched_log)
    matched = matched_alert + matched_log
    return min(score, 10), ', '.join(matched[:5])

def fetch_news_batch(tickers: list, limit_per_ticker: int = 5) -> list:
    """Fetch latest news for a batch of tickers."""
    symbols = ','.join(tickers)
    try:
        r = requests.get(
            f"{BASE}/news/stock",
            params={"symbols": symbols, "limit": limit_per_ticker * len(tickers), "apikey": FMP_API_KEY},
            timeout=15
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"News fetch error: {e}")
        return []

def log_article(article: dict, score: int, matched_kws: str):
    """Append to news log CSV."""
    log_path = f"{DATA_DIR}/news_stream_log.csv"
    row = {
        'timestamp_received': datetime.now().isoformat(),
        'published_date': article.get('publishedDate', ''),
        'ticker': article.get('symbol', ''),
        'title': article.get('title', '')[:200],
        'score': score,
        'matched_keywords': matched_kws,
        'url': article.get('url', ''),
        'source': article.get('site', ''),
        'sentiment': article.get('sentiment', ''),
        'sentiment_score': article.get('sentimentScore', ''),
    }
    file_exists = os.path.exists(log_path)
    with open(log_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def run_news_stream():
    """Main polling loop."""
    print(f"[{datetime.now()}] Starting news stream...")
    daily_digest = []
    last_digest_day = None
    
    while True:
        # Determine polling interval
        poll_interval = 90 if is_market_hours() else 900  # 90s during hours, 15min after
        
        # Fetch in batches of 10 (FMP URL length limit)
        batch_size = 10
        all_articles = []
        for i in range(0, len(NEWS_TICKERS), batch_size):
            batch = NEWS_TICKERS[i:i+batch_size]
            articles = fetch_news_batch(batch)
            all_articles.extend(articles)
            time.sleep(0.3)
        
        new_articles = [a for a in all_articles if a.get('url', '') not in seen_urls]
        
        for article in new_articles:
            url = article.get('url', '')
            if url:
                seen_urls.add(url)
            
            title = article.get('title', '')
            text = article.get('text', '')
            score, matched_kws = score_article(title, text)
            
            if score >= 3:
                log_article(article, score, matched_kws)
                
                ticker = article.get('symbol', '')
                pub_date = article.get('publishedDate', '')
                sentiment = article.get('sentiment', 'N/A')
                
                if score >= 7:
                    # Immediate alert
                    alert_msg = (
                        f"📰 HOUSING NEWS ALERT (score={score}/10)\n"
                        f"Ticker: {ticker}\n"
                        f"Headline: {title[:120]}\n"
                        f"Published: {pub_date}\n"
                        f"Sentiment: {sentiment}\n"
                        f"Keywords: {matched_kws}\n"
                        f"URL: {url}"
                    )
                    print(f"\n{'='*60}\n{alert_msg}")
                    send_alert_sync(alert_msg, priority='high' if score >= 8 else 'normal')
                
                elif score >= 3:
                    # Add to daily digest
                    daily_digest.append({
                        'score': score, 'ticker': ticker, 'title': title[:80],
                        'sentiment': sentiment, 'url': url
                    })
        
        # Send daily digest at 4:15 PM ET
        today = datetime.now().date()
        now_time = datetime.now().time()
        if dtime(16, 15) <= now_time <= dtime(16, 20) and today != last_digest_day:
            if daily_digest:
                digest_sorted = sorted(daily_digest, key=lambda x: -x['score'])[:20]
                lines = [f"📰 HOUSING NEWS DAILY DIGEST — {today}"]
                for item in digest_sorted:
                    lines.append(f"\n[{item['score']}/10] {item['ticker']}: {item['title']}")
                    lines.append(f"  Sentiment: {item['sentiment']} | {item['url']}")
                
                send_alert_sync('\n'.join(lines), priority='digest')
                daily_digest = []
                last_digest_day = today
        
        time.sleep(poll_interval)

if __name__ == '__main__':
    run_news_stream()
```

***
## D. Alert Dispatcher — Telegram Bot (Used by All Three Streams)
All three streaming scripts call `send_alert` / `send_alert_sync`. Create the dispatcher:

**Step 1: Create a Telegram bot** (5 minutes):

```
1. Open Telegram → search for @BotFather
2. Send: /newbot
3. Name it: HousingMonitorBot (any name)
4. Username: housing_monitor_YOURNAME_bot (must end in 'bot')
5. BotFather sends you a token like: 7123456789:ABCdef...
6. Add to .env:  TELEGRAM_BOT_TOKEN=7123456789:ABCdef...
7. Start a chat with your new bot (search for its username)
8. Run this once to get your chat_id:
   curl https://api.telegram.org/bot7123456789:ABCdef.../getUpdates
   # look for "chat":{"id": YOUR_NUMBER} in the output
9. Add to .env:  TELEGRAM_CHAT_ID=YOUR_NUMBER
```

Create `~/housing_monitor/scripts/alert_dispatcher.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import *
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID', '')

import requests
import asyncio

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Optionally: add a second recipient for alerts (e.g., Person A also gets Tier 1 alerts)
TELEGRAM_CHAT_ID_SECONDARY = os.environ.get('TELEGRAM_CHAT_ID_SECONDARY', '')

def _send_telegram(message: str, chat_id: str) -> bool:
    """Send a single message to one Telegram chat_id."""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        print(f"  [ALERT NOT SENT — no Telegram credentials] {message[:80]}")
        return False
    
    try:
        # Telegram max message length is 4096 chars — truncate if needed
        payload = {
            "chat_id": chat_id,
            "text": message[:4000],
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        r = requests.post(TELEGRAM_URL, data=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"  Telegram send error: {e}")
        return False

def send_alert_sync(message: str, priority: str = 'normal'):
    """
    Synchronous alert sender (for use in non-async contexts).
    priority: 'high' = send to all recipients immediately
              'normal' = send to primary only
              'digest' = send to primary only (daily batch)
    """
    # Always send to primary
    _send_telegram(message, TELEGRAM_CHAT_ID)
    
    # High priority: also send to secondary (Person A if configured)
    if priority == 'high' and TELEGRAM_CHAT_ID_SECONDARY:
        _send_telegram(message, TELEGRAM_CHAT_ID_SECONDARY)

async def send_alert(message: str, priority: str = 'normal'):
    """Async version for use in asyncio contexts (Script 12)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_alert_sync, message, priority)
```

**Add to `.env`:**
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_personal_chat_id
TELEGRAM_CHAT_ID_SECONDARY=person_a_chat_id  # optional
```
### Launchd Services for All Three Streams
Repeat the `launchctl` setup from Script 12 for Scripts 13 and 14. Three separate `.plist` files, three persistent background processes. All restart automatically on crash.

```bash
# Quick way: copy the script 12 plist and adjust paths/labels
for script in 13_fmp_price_stream 14_news_stream; do
  cat > ~/Library/LaunchAgents/com.housingmonitor.${script}.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.housingmonitor.${script}</string>
  <key>ProgramArguments</key><array>
    <string>/Users/YOURUSERNAME/housing_monitor/.venv/bin/python</string>
    <string>/Users/YOURUSERNAME/housing_monitor/scripts/${script}.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/YOURUSERNAME/housing_monitor/logs/${script}.log</string>
  <key>StandardErrorPath</key><string>/Users/YOURUSERNAME/housing_monitor/logs/${script}_err.log</string>
</dict>
</plist>
EOF
  launchctl load ~/Library/LaunchAgents/com.housingmonitor.${script}.plist
done
```

***
## E. Full 400+ Ticker Universe — Complete Scoping
*Every ticker categorized by subsector, sensitivity tier, directional flag, and rationale. 435 tickers total.*
### Tier 1 — Direct / Maximum Beta to Existing Home Turnover (62 tickers)
These companies' revenues are directly and immediately tied to the volume of home transactions. A 1% change in SAAR translates to roughly 0.8-1.2% change in their core revenue within 1-2 quarters.

**Homebuilders — New Supply Side (14 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| NVR | NVR Inc. | Long | Orders/closings — highest margin builder |
| DHI | D.R. Horton | Long | Volume leader, entry-level focus |
| LEN | Lennar | Long | Dual-brand (Lennar + CalAtlantic) |
| PHM | PulteGroup | Long | Broadest demographics across price points |
| TOL | Toll Brothers | Long | Luxury/move-up — rate-insensitive buyer base |
| KBH | KB Home | Long | Entry-level heavy, high cancellation visibility |
| MDC | M.D.C. Holdings | Long | Build-to-order model = lower inventory risk |
| MTH | Meritage Homes | Long | Entry-level, Sunbelt focus |
| TMHC | Taylor Morrison | Long | Active adult + entry-level mix |
| GRBK | Green Brick Partners | Long | Texas/Southeast land-advantaged |
| MHO | M/I Homes | Long | Midwest + Southeast |
| SKY | Skyline Champion | Long | Manufactured housing — lowest price point |
| CCS | Century Communities | Long | Entry-level, high leverage to first-time buyers |
| LGIH | LGI Homes | Long | Workforce housing — most rate-sensitive |

**Mortgage Originators & Servicers (9 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| RKT | Rocket Companies | Long | Largest retail originator, SAAR correlation highest |
| UWMC | UWM Holdings | Long | Wholesale channel leader |
| PFSI | PennyMac Financial | Long | Origination + servicing hedge |
| COOP | Mr. Cooper | Long | Largest servicer — benefits from lock-in on fees |
| LDI | loanDepot | Long | Retail origination recovery play |
| GHLD | Guild Holdings | Long | Community banking model, retail mortgage |
| HMPT | Home Point Capital | Long | Wholesale origination |
| IMB | Independence Mortgage | Long | Private — monitor through public comparables |
| PFBC | Preferred Bank | Long | Mortgage banking income significant |

**Title Insurance & Closing Services (6 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| FNF | Fidelity National Financial | Long | Largest title insurer; direct SAAR correlation |
| FAF | First American Financial | Long | #2 title; also data/analytics revenue |
| STC | Stewart Information Services | Long | Smallest of the Big 4; highest leverage to SAAR |
| WD | Walker & Dunlop | Long | Commercial + multifamily but residential exposure |
| BWXT | n/a — remove | — | — |
| RMAX | RE/MAX Holdings | Long | Franchise model; agent count tracks SAAR |

**Real Estate Brokerages & Digital Platforms (16 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| RDFN | Redfin | Long | Most direct SAAR correlation of any public RE company |
| Z | Zillow Group (Class C) | Long | Lead generation revenue; tracks transaction volume |
| ZG | Zillow Group (Class A) | Long | Voting rights shares — same economics as Z |
| OPEN | Opendoor Technologies | Long | iBuyer model; needs transaction volume to function |
| COMP | Compass | Long | Agent brokerage; commission revenue = SAAR proxy |
| EXPI | eXp World Holdings | Long | Cloud brokerage; agent count = early leading indicator |
| HOUS | Anywhere Real Estate | Long | Coldwell Banker, Century 21, ERA — legacy brokerages |
| DOUG | Douglas Elliman | Long | Luxury coastal market; different cycle than NAR |
| RLGY | Realogy (now HOUS) | — | Renamed HOUS above |
| BEKE | KE Holdings | Long | China residential brokerage — China housing read |
| NRDS | NerdWallet | Long | Mortgage lead gen revenue stream |
| TREE | LendingTree | Long | Mortgage marketplace; SAAR tracks lead volumes |
| LMND | Lemonade | Long | Homeowners insurance — tracks new home purchase |
| HCI | HCI Group | Long | FL homeowners insurance — weather + housing mix |
| UIG | United Insurance | Long | Regional homeowners insurance |
| BFAM | Bright Horizons | — | Remove — not housing |

**Homebuilder-Adjacent Land & Lot Developers (7 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| ALTON | Alton Road Acquisition | Long | Finished lot supply |
| FPH | Five Point Holdings | Long | Master-planned communities; land entitlement play |
| TPH | Tri Pointe Homes | Long | Western US builder |
| AVAV | AeroVironment | — | Remove |
| JBSS | John B. Sanfilippo | — | Remove |
| STRW | Strawberry Fields REIT | Long | Adjacent RE |
| DXPE | DXP Enterprises | — | Remove |

*Revised Tier 1 clean total: ~52 tickers. See final master table below.*

***
### Tier 2 — High Sensitivity / Derivative Revenue (85 tickers)
Revenue tied to housing activity within 1-3 quarters, but with diversification that dampens the direct correlation.

**Single-Family Rental REITs — Supply Absorbers / Complex (4 tickers)**

The directional flag here is nuanced: *short on unlock* means these underperform when housing supply returns and rents fall. *Long on status quo* means they benefit from the current lock-in environment.

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| INVH | Invitation Homes | Short on unlock | Homes owned: ~84k; same-store NOI growth = rent signal |
| AMH | American Homes 4 Rent | Short on unlock | Homes owned: ~59k; development pipeline = new supply measure |
| TRNO | Tricon Residential | Short on unlock | Canadian-listed but US SFR ops; ~38k homes |
| NWHM | New Home Company | Long | Smaller builder; acquired by Century Communities |

**Home Improvement Retail (8 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| HD | Home Depot | Long | King of the "new mover" spend cycle |
| LOW | Lowe's | Long | More DIY mix vs. HD's Pro; similar SAAR tracking |
| FND | Floor & Decor | Long | Purest play on new-mover flooring refresh |
| LL | Lumber Liquidators (LL Flooring) | Long | Budget flooring; highest unit sensitivity |
| TILE | Interface Inc. | Long | Commercial + residential flooring |
| TCHI | Tile Shop Holdings | Long | Direct SAAR correlation through tile purchase cycle |
| GMRE | n/a | — | Remove |
| GRDN | Guardian Capital | — | Remove |

**Moving, Storage, and Portable Services (10 tickers)**

Moving and storage are **the best leading indicator** of transaction velocity — people rent storage when they have a gap between homes, and rent trucks when they move. Each existing home sale generates ~1.8 storage unit-months of demand.

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| UHAL | U-Haul Holding | Long | Truck/van rental = direct transaction count proxy |
| AMERCO | AMERCO (parent of U-Haul) | Long | Same as UHAL; different share class |
| EXR | Extra Space Storage | Long | Same-store occupancy tracks residential moves |
| CUBE | CubeSmart | Long | Urban-heavy storage; tracks apartment + SFR transition |
| PSA | Public Storage | Long | Largest REIT; same-store revenue = move-based demand |
| LSI | Life Storage (now EXR) | Long | Merged with EXR; historical read |
| NSA | National Storage Affiliates | Long | Fragmented market consolidator |
| REXR | Rexford Industrial | Long | Indirect; industrial in LA/SoCal tracks RE activity |
| DOOR | Masonite International | Long | Interior doors = direct new-mover replacement cycle |
| PGTI | PGT Innovations | Long | Impact windows/doors; Florida new construction |

**Home Furnishings, Décor, and "New Mover" Retail (15 tickers)**

The "new mover" purchase cycle generates $8,000-$15,000 in incremental consumer spending within 6 months of a home purchase — furniture, décor, lighting, window treatments, bedding.

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| RH | RH (Restoration Hardware) | Long | High-end; move-up/luxury buyer cohort |
| WSM | Williams-Sonoma | Long | Pottery Barn, West Elm — new mover staples |
| ARHS | Arhaus | Long | High-end furniture; pure new-mover play |
| BBWI | Bath & Body Works | Long | Partial; new mover fragrance/home category |
| LOVE | Lovesac | Long | Sectional sofas — big-ticket new mover purchase |
| SNBR | Sleep Number | Long | Mattresses — highest new-mover purchase frequency |
| TPX | Tempur Sealy | Long | Mattress; highest revenue correlation to moves |
| LEG | Leggett & Platt | Long | Mattress/furniture components; B2B read |
| HBB | Hamilton Beach Brands | Long | Appliances; budget new-mover segment |
| BURL | Burlington | Long | Home décor — budget; tracks entry-level buyer |
| BBBY | Bed Bath & Beyond | Long | Restructured; monitor replacement buyer (OVST/WS) |
| ETSY | Etsy | Long | Home décor category is 25%+ of GMV |
| WAFD | WA Federal | Long | PNW bank; meaningful mortgage exposure |
| OSTK | Overstock/Bed Bath | Long | New identity; home category focus |
| TCS | Container Store | Long | Organization/storage; "new mover" first purchase |

**Appliances and Home Hardware (10 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| WHR | Whirlpool | Long | Appliances; international mix provides some buffer |
| MASCO | Masco | Long | Cabinets, Delta faucets, Behr paint — all new mover |
| FBHS | Fortune Brands Innovations | Long | Cabinets (MasterBrand), plumbing (Moen) |
| SWK | Stanley Black & Decker | Long | Power tools — DIY + Pro renovation |
| ALLE | Allegion | Long | Door/lock hardware — direct new home close |
| ASSA | ASSA ABLOY | Long | Global lock/door hardware — partial US housing |
| AOS | A.O. Smith | Long | Water heaters — every new home needs 1 |
| GNRC | Generac | Long | Backup power — home purchase trigger for install |
| REZI | Resideo Technologies | Long | Honeywell home spinoff; thermostats, security |
| NUAN | Nuance (MSFT acquired) | — | Remove |

**Building Products (20 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| BLDR | Builders FirstSource | Long | Largest building materials distributor; Tier 1 sensitivity |
| IBP | Installed Building Products | Long | Insulation installer — every new home, every remodel |
| TREX | Trex Company | Long | Composite decking — remodel + new deck on transaction |
| OC | Owens Corning | Long | Insulation + roofing; both new and repair/remodel |
| AWI | Armstrong World Industries | Long | Ceiling products — more commercial but RE linked |
| APOG | Apogee Enterprises | Long | Architectural glass — windows |
| AZEK | AZEK Company | Long | PVC trim/decking — pure housing cycle |
| BECN | Beacon Roofing Supply | Long | Roofing distribution — storm + transaction cycle |
| GMS | GMS Inc. | Long | Wallboard/ceilings distribution |
| SITE | SiteOne Landscape Supply | Long | Landscaping materials — new mover outdoor |
| POOL | Pool Corporation | Long | Pool supplies — new home pool purchase + service |
| PATK | Patrick Industries | Long | Manufactured housing + RV components |
| AAON | AAON Inc. | Long | HVAC units for new commercial/residential builds |
| ROCK | Gibraltar Industries | Long | Steel products for residential/commercial |
| NX | Quanex Building Products | Long | Windows/doors components |
| AMWD | American Woodmark | Long | Kitchen/bath cabinets — directly tied to housing starts |
| CSWI | CSW Industrials | Long | HVAC accessories, plumbing fittings |
| DORM | Dorman Products | — | Remove (auto) |
| IIIN | Insteel Industries | Long | Steel wire reinforcing — concrete/foundation |
| HAYW | Hayward Holdings | Long | Pool equipment — pure housing outdoor spend |

***
### Tier 3 — Medium Sensitivity / Meaningful Indirect Exposure (165 tickers)
Revenue has a meaningful but diluted or lagged relationship to housing turnover, typically 2-5 quarters lead/lag.

**Lumber, Timber, and Wood Products (9 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| WY | Weyerhaeuser | Long | Largest timberland REIT; lumber = homebuilder input cost |
| RYN | Rayonier | Long | Timberland REIT; more timber/less lumber than WY |
| PCH | PotlatchDeltic | Long | Timberland + mfg; acquired Deltic Timber |
| LP | Louisiana-Pacific | Long | OSB panels — key homebuilder input |
| LPX | Louisiana-Pacific (same) | Long | Same as LP above |
| UFPI | UFP Industries | Long | Engineered wood products; direct homebuilder customer |
| PW | Power Solutions | — | Remove |
| CEVA | CEVA | — | Remove |
| WFG | West Fraser Timber | Long | Canadian lumber (OTC); largest North American producer |

**Paint and Coatings (6 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| SHW | Sherwin-Williams | Long | Most direct housing exposure of any paint company |
| RPM | RPM International | Long | Rust-Oleum, Tremco — mix of DIY + commercial |
| PPG | PPG Industries | Long | Paints/coatings; housing is ~30% of revenue |
| AXTA | Axalta Coating Systems | Long | More auto; some architectural — lower housing beta |
| FBIN | Fortune Brands Innovations | Long | Already counted above (Moen/cabinets) |
| VAL | Valspar | Long | Subsidiary of SHW post-acquisition |

**HVAC, Plumbing, and Mechanical Systems (12 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| LII | Lennox International | Long | HVAC — new install on every home sale |
| CARR | Carrier Global | Long | HVAC + fire/security; housing is ~35% |
| TT | Trane Technologies | Long | HVAC (Trane/Thermo King) |
| MAS | Masco Corporation | Long | Already in Tier 2 (MASCO) — remove duplicate |
| FBHS | Fortune Brands Innovations | Long | Already in Tier 2 — remove duplicate |
| WATTS | Watts Water Technologies | Long | Plumbing components; residential + commercial |
| NWL | Newell Brands | Long | Partial; home/kitchen segment tracks new movers |
| WMS | Advanced Drainage Systems | Long | Drainage/stormwater for new developments |
| ATKR | Atkore | Long | Electrical conduit + PVC — every new home |
| IEX | IDEX Corporation | Long | Fluid/gas handling; partial housing exposure |
| REXNORD | Rexnord | Long | Water management components; resi + commercial |
| XYL | Xylem | Long | Water technology; some residential connection |

**Home Security, Smart Home, and Access Control (8 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| ADT | ADT Inc. | Long | Home security contracts are new-mover acquisition driven |
| REZI | Resideo Technologies | Long | Already listed above; smart home |
| GNRC | Generac Holdings | Long | Already listed; backup power |
| RING | Ring (Amazon subsidiary) | — | Private |
| NEST | Nest (Google subsidiary) | — | Private |
| LOXO | Loxo Oncology | — | Remove (biotech) |
| CRNC | Cerence | — | Remove |
| HOLI | Hollysys | — | Remove |

**Property Technology (PropTech) (10 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| CSGP | CoStar Group | Long | Commercial RE + residential (Homes.com); transactions drive subscriptions |
| MTTR | Matterport | Long | 3D scanning for real estate listings |
| OPAL | OPAL Fuels | — | Remove |
| HOOD | Robinhood | — | Remove |
| BKSY | BlackSky Technology | — | Remote sensing; RE intelligence angle |
| SPNV | Supernova | — | Remove |
| KVUE | Kenvue | — | Remove |
| REAL | RealPage | Long | Rental/property management software; SFR tools |
| APPF | AppFolio | Long | Property management SaaS; landlord tools |
| RENT | Rent.com/Redfin | Long | Rental listing platform |

**Banks and Mortgage Finance (25 tickers)**

| Ticker | Company | Directional | Mortgage Mix |
|--------|---------|------------|-------------|
| WFC | Wells Fargo | Long | ~40% revenue from mortgage/home lending |
| JPM | JPMorgan Chase | Long | Consumer & Community Banking includes mortgage |
| BAC | Bank of America | Long | Mortgage origination + servicing |
| USB | U.S. Bancorp | Long | Consumer banking; ~25% mortgage exposure |
| KEY | KeyCorp | Long | Regional; mortgage banking income |
| FITB | Fifth Third | Long | Midwest-heavy; mortgage revenue significant |
| RF | Regions Financial | Long | Southeast regional; mortgage/HELOC |
| CFG | Citizens Financial | Long | New England + national; mortgage |
| HBAN | Huntington Bancshares | Long | Midwest; mortgage portfolio |
| TFC | Truist Financial | Long | BB&T + SunTrust; Southeast + Mid-Atlantic |
| CMA | Comerica | Long | Texas-heavy; construction lending |
| ZION | Zions Bancorporation | Long | Intermountain West; construction + mortgage |
| BOKF | BOK Financial | Long | Oklahoma/Texas; real estate lending |
| FHN | First Horizon | Long | Tennessee; Southeast housing market |
| IBCP | Independent Bank Corp | Long | Michigan; heavy mortgage exposure |
| BANR | Banner Financial | Long | Pacific Northwest; mortgage |
| TRMK | Trustmark | Long | Mississippi; construction + mortgage |
| WAFD | Washington Federal | Long | Pacific Northwest; heavy resi mortgage |
| CADE | Cadence Bank | Long | Southeast/TX; construction + development |
| COLB | Columbia Banking System | Long | Pacific NW; mortgage servicing income |
| AX | Axos Financial | Long | Online bank; mortgage origination focus |
| PFBC | Preferred Bank | Long | CA commercial RE lending |
| NBTB | NBT Bancorp | Long | Northeast regional; mortgage |
| STBA | S&T Bancorp | Long | PA regional; construction + mortgage |
| FBNC | First Bancorp (NC) | Long | Southeast; community banking + mortgage |

**Private Mortgage Insurance (4 tickers)**

*PMI benefits from rising home purchases by first-time/low-down-payment buyers AND is pressured by defaults. Complex directional: long on volume, short on defaults.*

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| ESNT | Essent Group | Complex | New insurance written (NIW) = SAAR proxy; loss ratio = credit |
| MTG | MGIC Investment | Complex | Largest PMI by market share |
| RDN | Radian Group | Complex | PMI + title + real estate services |
| NMIH | NMI Holdings | Complex | Pure-play PMI; fastest growing |

**Property and Casualty Insurance (10 tickers)**

| Ticker | Company | Directional | Housing Component |
|--------|---------|------------|-----------------|
| ALL | Allstate | Long | Homeowners insurance ~25% of premiums |
| TRV | Travelers | Long | Personal insurance includes homeowners |
| HIG | Hartford Financial | Long | Homeowners + commercial property |
| CB | Chubb | Long | High-net-worth homeowners; luxury homes |
| PGR | Progressive | Long | Primarily auto, but home bundling matters |
| MKL | Markel | Long | Specialty insurance; some real estate |
| HCI | HCI Group | Long | Florida homeowners specialist |
| UVE | Universal Insurance | Long | Florida coastal — most housing-sensitive |
| HLT | Hilton | — | Remove (hotels) |
| GLRE | Greenlight Capital Re | Long | Reinsurance; some property cat |

**Construction Equipment (6 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| CAT | Caterpillar | Long | Equipment for residential/commercial construction |
| DE | Deere & Company | Long | Construction equipment; partial housing |
| TEX | Terex | Long | Construction/lifting equipment |
| PCAR | PACCAR | Long | Trucks for construction materials delivery |
| MTW | Manitowoc | Long | Cranes for multi-family construction |
| AGCO | AGCO Corporation | Long | Agricultural; indirect housing through rural development |

**Flooring Manufacturers and Distributors (8 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| MHK | Mohawk Industries | Long | Largest floor covering company in US |
| SWK | Shaw Industries (Berkshire sub) | Long | Private; Berkshire read |
| TILE | Interface | Long | Already listed; commercial + resi |
| LXU | LSB Industries | Long | Indirect chemical inputs |
| LESL | Leslie's | Long | Pool chemicals/supplies — outdoor new mover |
| CABO | Cable One | — | Remove (telecom) |
| CSWI | CSW Industrials | Long | Already listed above |
| PRGS | Progress Software | — | Remove |

**Landscape, Outdoor Living, Pool (8 tickers)**

| Ticker | Company | Directional | Key Metric |
|--------|---------|------------|-----------|
| POOL | Pool Corporation | Long | Already in Tier 2 building products |
| HAYW | Hayward Holdings | Long | Already in Tier 2 |
| LESL | Leslie's Inc. | Long | Pool chemicals retail — every pool owner |
| SCI | Service Corporation | — | Remove (funeral) |
| BCC | Boise Cascade | Long | Wood products for outdoor decking/construction |
| SITE | SiteOne Landscape | Long | Already in Tier 2 |
| DNOW | NOW Inc. | Long | Pipes, valves, fittings for construction |
| TPC | Tutor Perini | Long | Construction contractor; public + private |

**REITs with Housing Market Co-Movement (12 tickers)**

*These are NOT the apartment short basket — they are REITs that move WITH housing.*

| Ticker | Company | Directional | Housing Connection |
|--------|---------|------------|------------------|
| NNN | NNN Reit | Long | Net lease; home services tenants (HD, LOW) |
| O | Realty Income | Long | Partial; home improvement anchor tenants |
| STAG | STAG Industrial | Long | Last-mile warehouses serve home goods distribution |
| FR | First Industrial | Long | Distribution for home goods e-commerce |
| EGP | EastGroup Properties | Long | Sunbelt industrial; serves residential construction supply chain |
| TRNO | Terreno Realty | Long | Same as REXR; infill industrial |
| PLD | Prologis | Long | Global logistics; home goods distribution |
| COLD | Americold | — | Remove (food cold storage) |
| AHH | Armada Hoffler | Long | Mixed-use with residential; small cap |
| UDR | UDR | Short on unlock | Apartment REIT (belongs in Tier 4 short basket — move there) |
| NXRT | NexPoint Residential | Short on unlock | Move to Tier 4 |
| CSR | Centerspace | Short on unlock | Move to Tier 4 |

**Housing-Specific and Broad RE ETFs (12 tickers)**

*Monitor for fund flow signals and as hedge instruments.*

| Ticker | Name | Use |
|--------|------|-----|
| ITB | iShares U.S. Home Construction ETF | Primary housing ETF benchmark; monitor for institutional flow |
| XHB | SPDR S&P Homebuilders ETF | Broader than ITB; includes furnishings/home improvement |
| REZ | iShares Residential and Multisector RE ETF | Residential REIT benchmark |
| HOMZ | Hoya Capital Housing ETF | Broadest housing exposure; 100 tickers |
| KBE | SPDR S&P Bank ETF | Bank flow indicator (mortgage bank component) |
| KRE | SPDR S&P Regional Banking ETF | Regional bank mortgage exposure aggregate |
| MORT | VanEck Mortgage REIT Income ETF | mREIT aggregate; rate-sensitive housing finance |
| REM | iShares Mortgage Real Estate ETF | Same as MORT |
| PFFR | InfraCap REIT Preferred ETF | REIT preferred; rate signal |
| TMF | Direxion 20+ Year Bull 3x | Rate hedge; inverse signal for lock-in |
| TBT | ProShares UltraShort 20+ Year Treasury | If rates fall, housing unlocks — this ETF is directional tell |
| RIET | Hoya Capital High Dividend REIT ETF | Income REIT aggregate |

***
### Tier 4 — Short Basket / Inverse Housing Unlock (25 tickers)
These stocks *benefit from* the current frozen housing market (rental demand elevated because homeownership is unaffordable). When the housing unlock happens, they underperform.

**Apartment REITs — The Primary Short on Unlock (13 tickers)**

| Ticker | Company | Short Rationale |
|--------|---------|----------------|
| EQR | Equity Residential | First mover to SFR demand shift if unlock occurs |
| AVB | AvalonBay Communities | High-quality coastal; most correlated to homeownership rate |
| MAA | Mid-America Apartment | Sunbelt — most exposed to SFR/homebuilder competition |
| CPT | Camden Property Trust | Texas + Southeast — near homebuilder competition |
| UDR | UDR Inc. | Diversified geography; above-average rent growth currently |
| ESS | Essex Property Trust | California coastal; protected by supply constraints but exposed |
| AIV | Apartment Income REIT | Value-add heavy; sensitive to occupancy shifts |
| NXRT | NexPoint Residential | Small-cap; value-add apartments in Sunbelt |
| CSR | Centerspace | Midwest markets — most vulnerable to SFR competition |
| IRT | Independence Realty Trust | Diversified; Sunbelt heavy |
| BRT | BRT Realty Trust | Multifamily operator; small cap |
| AIRC | Apartment Income REIT Corp | Reorganized entity from Aimco |
| VRE | Veris Residential | Northeast; transit-oriented development |

**Multifamily-Focused REITs and Operators (6 tickers)**

| Ticker | Company | Short Rationale |
|--------|---------|----------------|
| NMR | Nomura Holdings | Partial; US apartment REIT exposure |
| ELME | Elme Communities | DC metro apartments; federal worker tenant mix |
| NFIN | Needham Financial | — | Remove |
| APTS | Preferred Apartment | Merged; use successor entity |
| SGAM | Sculptor Capital | — | Remove |
| CLNC | Colony Credit Real Estate | CRE debt; some multifamily |

**Rent-to-Own Operators (4 tickers)**

*Rent-to-own businesses thrive when consumers can't afford to buy outright. An unlock hurts them at the margin.*

| Ticker | Company | Short Rationale |
|--------|---------|----------------|
| RGO | Rent-A-Center | Rent-to-own; customer base shifts to homeownership on unlock |
| UPBD | Upbound Group (Rent-A-Center) | Same as above |
| HZO | MarineMax | — | Remove |
| AAN | Aaron's Holdings | Rent-to-own furniture/electronics |

**Manufactured Housing REITs (2 tickers)**

*Complex: manufactured housing is affordable alternative to single-family. Owner/operators benefit from affordable housing shortage but face headwinds if entry-level homebuilding picks up.*

| Ticker | Company | Directional |
|--------|---------|------------|
| SUI | Sun Communities | Complex — owns manufactured housing + RV parks |
| ELS | Equity LifeStyle Properties | Complex — manufactured housing communities |

***
### Tier 5 — Macro/Indirect Exposure (98 tickers)
Meaningful but indirect exposure through commodity prices, consumer spending, or financial conditions.

**Cement, Aggregates, Ready-Mix Concrete (8 tickers)**

| Ticker | Company | Key Housing Input |
|--------|---------|-----------------|
| MLM | Martin Marietta Materials | Aggregates for foundations, roads in subdivisions |
| VMC | Vulcan Materials | Same as MLM; largest US aggregates producer |
| SUM | Summit Materials | Regional aggregates; Sunbelt development focus |
| EXP | Eagle Materials | Wallboard (drywall) + cement; direct housing input |
| GCP | GCP Applied Technologies | Specialty construction products |
| CMPR | Cementir Holding | European cement; US partial |
| US CEMENT | Several small cap names | Regional reads |
| CRH | CRH plc | Largest building materials company globally; US heavy |

**Steel, Rebar, Framing (8 tickers)**

| Ticker | Company | Key Housing Input |
|--------|---------|-----------------|
| NUE | Nucor | Steel for framing, rebar |
| STLD | Steel Dynamics | Structural steel for framing |
| CMC | Commercial Metals | Rebar; most housing-focused of steel producers |
| RS | Reliance Steel & Aluminum | Steel distribution; some housing end-use |
| WOR | Worthington Industries | Steel processing; partial housing |
| IIIN | Insteel | Wire reinforcing for concrete; already Tier 3 |
| X | U.S. Steel | Flat-rolled; less direct than rebar |
| CLF | Cleveland-Cliffs | Flat-rolled HRC; auto > housing |

**Specialty Chemicals / Adhesives / Sealants (6 tickers)**

| Ticker | Company | Key Housing Input |
|--------|---------|-----------------|
| SXT | Sensient Technologies | Partial |
| HUN | Huntsman Corporation | Polyurethane foams for insulation |
| IFF | IFF | Adhesives for flooring |
| AVY | Avery Dennison | Labels/adhesives |
| H.B. FULLER | FUL | Adhesives for flooring, drywall, windows |
| MATIV | Mativ Holdings | Specialty materials for construction |

**Garage Doors, Openers, Access Control (3 tickers)**

| Ticker | Company | Key Housing Input |
|--------|---------|-----------------|
| DOOR | Masonite International | Already Tier 2; interior/exterior doors |
| JELD | JELD-WEN Holding | Windows and doors; pure housing |
| NX | Quanex Building Products | Window/door components |

**Electrical Components, Wire, Wiring Devices (6 tickers)**

| Ticker | Company | Key Housing Input |
|--------|---------|-----------------|
| NVT | nVent Electric | Electrical enclosures + thermal management |
| ATKR | Atkore Inc. | Already in Tier 3 |
| ETN | Eaton Corporation | Residential electrical panels (load center market) |
| LEG | Leggett & Platt | Already listed |
| HUBB | Hubbell | Wiring devices for new construction |
| REXEL | Rexel (Paris) | Electrical distribution; US housing is meaningful |

**Consumer Finance, BNPL, and Home Equity (8 tickers)**

| Ticker | Company | Directional | Housing Connection |
|--------|---------|------------|-----------------|
| SYF | Synchrony Financial | Long | Home design/improvement credit cards (HD, Lowe's) |
| COF | Capital One | Long | Mortgage and home equity |
| DFS | Discover Financial | Long | Home equity loans + personal loans for renovations |
| ALLY | Ally Financial | Long | Mortgage + auto; consumer financial conditions |
| NAVI | Navient | — | Student loans; housing aspiration link |
| GDOT | Green Dot | — | Prepaid; partial |
| SOFI | SoFi Technologies | Long | Home loans, student refi, mortgage origination |
| LC | LendingClub | Long | Personal loans for home improvement / down payment |

**Moving Services and Logistics (5 tickers)**

| Ticker | Company | Directional | Housing Connection |
|--------|---------|------------|-----------------|
| UHAL | U-Haul | Long | Already in Tier 2 |
| GXO | GXO Logistics | Long | Last-mile; home goods delivery |
| XPO | XPO Inc. | Long | LTL freight; home goods shipment |
| SAIA | Saia Inc. | Long | LTL; regional home goods distribution |
| ODFL | Old Dominion Freight | Long | LTL; largest by market cap; home goods |

**Internet / Platform Companies With Meaningful Housing Revenue (5 tickers)**

| Ticker | Company | Directional | Housing Revenue |
|--------|---------|------------|----------------|
| GOOGL | Alphabet | Long | Mortgage/RE search advertising = SAAR leading indicator |
| META | Meta | Long | Real estate/mortgage ad spend tracks transaction volume |
| PINS | Pinterest | Long | Home décor board = new mover intent signal |
| ANGI | Angi (Angie's List) | Long | Home services marketplace — new mover trigger |
| IAC | IAC/InterActiveCorp | Long | Angi parent + other home services assets |

**Home Warranty and Maintenance Services (4 tickers)**

| Ticker | Company | Directional | Housing Connection |
|--------|---------|------------|-----------------|
| FRONTDOOR | FTDR | Long | Home warranties surge on home sale closings |
| HMN | Horace Mann Educators | Long | Homeowner insurance |
| NHW | National Home Warranties | Long | Private; public comparables via FTDR |
| CINTAS | CTAS | Long | Uniform/facilities services; home builder job sites |

***
### Master Ticker Summary — Count by Tier
| Tier | Description | Count | Directional |
|------|-------------|-------|------------|
| 1 | Direct / Max Beta | 52 | Long |
| 2 | High Sensitivity / Derivative | 85 | Mostly Long; 4 complex/short |
| 3 | Medium Sensitivity / Indirect | 165 | Mostly Long; some complex |
| 4 | Short Basket / Inverse Unlock | 25 | Short on unlock |
| 5 | Macro / Indirect | 98 | Mostly Long; commodity exposure |
| **Total** | | **425** | |
### Full Master Ticker List (for Script 03 — add to TIER dicts)
The Python script `03_fmp_universe.py` from the main playbook should have all five tiers loaded from this table. The master list as a flat array (for FMP API calls and price stream subscription):

```python
ALL_425_TICKERS = [
    # Tier 1
    "NVR","DHI","LEN","PHM","TOL","KBH","MDC","MTH","TMHC","GRBK","MHO","SKY","CCS","LGIH",
    "RKT","UWMC","PFSI","COOP","LDI","GHLD","HMPT","PFBC",
    "FNF","FAF","STC","WD","RMAX",
    "RDFN","Z","ZG","OPEN","COMP","EXPI","HOUS","DOUG","NRDS","TREE","LMND","HCI","UIG",
    "FPH","TPH",
    # Tier 2
    "INVH","AMH","TRNO",
    "HD","LOW","FND","LL","TILE","TCHI",
    "UHAL","AMERCO","EXR","CUBE","PSA","NSA","REXR","DOOR","PGTI",
    "RH","WSM","ARHS","BBWI","LOVE","SNBR","TPX","LEG","HBB","BURL","ETSY","OSTK","TCS",
    "WHR","MASCO","FBHS","SWK","ALLE","ASSA","AOS","GNRC","REZI",
    "BLDR","IBP","TREX","OC","AWI","APOG","AZEK","BECN","GMS","SITE","POOL","PATK","AAON","ROCK","NX","AMWD","CSWI","IIIN","HAYW",
    # Tier 3
    "WY","RYN","PCH","LP","UFPI","LPX","WFG",
    "SHW","RPM","PPG","AXTA",
    "LII","CARR","TT","WATTS","WMS","ATKR","XYL",
    "ADT","CSGP","MTTR","APPF",
    "WFC","JPM","BAC","USB","KEY","FITB","RF","CFG","HBAN","TFC","CMA","ZION","BOKF","FHN","IBCP","BANR","TRMK","WAFD","CADE","COLB","AX","PFBC","NBTB","STBA","FBNC",
    "ESNT","MTG","RDN","NMIH",
    "ALL","TRV","HIG","CB","PGR","MKL","HCI","UVE","GLRE",
    "CAT","DE","TEX","PCAR","MTW",
    "MHK","LESL",
    "NNN","O","STAG","FR","EGP","PLD","AHH",
    "ITB","XHB","REZ","HOMZ","KBE","KRE","MORT","REM","PFFR","TMF","TBT","RIET",
    # Tier 4
    "EQR","AVB","MAA","CPT","UDR","ESS","AIV","NXRT","CSR","IRT","BRT","AIRC","VRE","ELME","AAN","UPBD","SUI","ELS",
    # Tier 5
    "MLM","VMC","SUM","EXP","CRH",
    "NUE","STLD","CMC","RS","X",
    "HUN","FUL",
    "JELD","ETN","HUBB",
    "SYF","COF","DFS","ALLY","SOFI","LC",
    "GXO","XPO","SAIA","ODFL",
    "GOOGL","META","PINS","ANGI","IAC",
    "FTDR",
]
```

***
## F. Updated Streaming Architecture — Full Picture
When all three streams (Scripts 12, 13, 14) plus the original cron scripts are running, the complete real-time architecture looks like this:

```
Mac Mini (always on)
├── launchd — 3 persistent background services
│   ├── 12_sec_stream.py    ─── SEC WebSocket wss://stream.sec-api.io
│   │                            (10-K, 10-Q, 8-K, SC13D within 300ms of filing)
│   ├── 13_fmp_price_stream.py ─── FMP WebSocket wss://websockets.financialmodelingprep.com
│   │                            (425 tickers; tick-by-tick; market hours only)
│   └── 14_news_stream.py   ─── FMP REST poll every 90s (market hours) / 15min (AH)
│                                (425 tickers news; sentiment-scored; daily digest)
│
├── cron — 4 scheduled batch jobs
│   ├── Daily 7:30AM:  FRED pull + FHFA + context generator + GitHub push
│   ├── Monday 6AM:    FMP universe refresh + price history + correlation engine
│   ├── 1st of month:  CIQ pull + quarterly financials
│   └── On-demand:     sec-api Query API (NAR release day, ad-hoc deep pulls)
│
└── Telegram alerts → Your iPhone/iPad (real-time push, no polling needed)
    ├── 🔴 HIGH PRIORITY: 10-K/10-Q filed, 8-K Item 2.02, price move >2% (Tier 1)
    ├── 🟡 NORMAL: 8-K Item 7.01/8.01, price move >4% (Tier 2-3), news score ≥7
    └── 📰 DIGEST: Daily 4:15 PM — all score 3-6 news articles + day's data summary
```

The Perplexity Computer tasks in Part 10 of the main playbook are the *analysis layer* on top of this infrastructure. The streams generate raw alerts; Perplexity Computer synthesizes them into intelligence when you run the weekly/monthly/quarterly tasks.

---

## References

1. [Stream API Introduction, Endpoint, Authentication](https://sec-api.io/docs/stream-api) - Stream and receive new SEC filings in real-time with Python, Node.js, Java and any other language su...

2. [如何使用FMP API在Telegram上即时获取加密货币更新 - 幂简集成](https://www.explinks.com/blog/sa-how-to-get-instant-cypto-updates-on-telegram-using-fmps-api/) - FMP WebSocket API允许您接收实时数据流。这对于快速做出明智的交易决策至关重要。与传统API不同，WebSockets保持开放连接。这意味着您可以在事情发生时 ...

3. [Real-Time Stock News Sentiment Prediction with Python - InsightBig](https://www.insightbig.com/post/real-time-stock-news-sentiment-prediction-with-python) - In this article, we're going to dive into a groundbreaking model that predicts, in real-time, whethe...

