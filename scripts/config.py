"""Project config — loads ~/.env and exposes paths/keys to all scripts.

BASE_DIR is repo-relative (derived from __file__), not hardcoded to a
specific user's home directory — so the same code works from any clone
location (Mac mini, laptop, GitHub Actions runner).
"""
import os
from dotenv import load_dotenv

# Load .env from home directory (where API keys live, not in the repo)
load_dotenv(os.path.expanduser('~/.env'))

# API keys
FMP_API_KEY  = os.environ.get('FMP_API_KEY', '')
SEC_API_KEY  = os.environ.get('SEC_API_KEY', '')
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Email alerts
ALERT_EMAIL_FROM         = os.environ.get('ALERT_EMAIL_FROM', '')
ALERT_EMAIL_TO           = os.environ.get('ALERT_EMAIL_TO', '')
ALERT_GMAIL_APP_PASSWORD = os.environ.get('ALERT_GMAIL_APP_PASSWORD', '')

# Repo-relative paths (works on any machine, no hardcoding)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
