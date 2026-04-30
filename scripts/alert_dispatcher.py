import smtplib, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_GMAIL_APP_PASSWORD
from email.mime.text import MIMEText

def send_alert_sync(message: str, priority: str = 'normal'):
    subject = "🏠 HOUSING ALERT" if priority == 'high' else "📰 Housing Monitor"
    to_list = ALERT_EMAIL_TO.split(',')
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From']    = ALERT_EMAIL_FROM
    msg['To']      = ', '.join(to_list)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(ALERT_EMAIL_FROM, ALERT_GMAIL_APP_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, to_list, msg.as_string())
    print(f"Alert sent to: {to_list}")

async def send_alert(message: str, priority: str = 'normal'):
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_alert_sync, message, priority)

if __name__ == '__main__':
    send_alert_sync("✅ Housing monitor test — email working!", priority='high')
