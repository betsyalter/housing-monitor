import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from config import SEC_API_KEY

import requests

body = {
    "query": 'formType:"8-K" AND ticker:DHI',
    "from": "0",
    "size": "1",
    "sort": [{"filedAt": {"order": "desc"}}],
}
r = requests.post(f"https://api.sec-api.io?token={SEC_API_KEY}", json=body, timeout=30)
r.raise_for_status()
filings = r.json().get("filings", [])
if not filings:
    print("NO FILINGS RETURNED")
else:
    print(json.dumps(filings[0], indent=2)[:4000])
