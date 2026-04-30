import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser('~/.env'))

FMP_API_KEY  = os.environ.get('FMP_API_KEY', '')
SEC_API_KEY  = os.environ.get('SEC_API_KEY', '')
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
ALERT_EMAIL_FROM         = os.environ.get('ALERT_EMAIL_FROM', '')
ALERT_EMAIL_TO           = os.environ.get('ALERT_EMAIL_TO', '')
ALERT_GMAIL_APP_PASSWORD = os.environ.get('ALERT_GMAIL_APP_PASSWORD', '')

BASE_DIR = os.path.expanduser('~/housing_monitor')
DATA_DIR = f'{BASE_DIR}/data'
LOGS_DIR = f'{BASE_DIR}/logs'
