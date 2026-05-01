"""SMTP transport for housing-monitor alerts.

Exposes send_email(subject, body) as the canonical helper. Other scripts
(notably 11_alert_dispatcher.py) use it for per-event/digest emails with
custom subjects.
"""
import smtplib, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_GMAIL_APP_PASSWORD
from email.mime.text import MIMEText


def send_email(subject: str, body: str) -> None:
    """Send a plain-text email via Gmail SMTP. Raises on failure."""
    if not (ALERT_EMAIL_FROM and ALERT_EMAIL_TO and ALERT_GMAIL_APP_PASSWORD):
        raise RuntimeError("Email env vars missing — check ~/.env for "
                           "ALERT_EMAIL_FROM, ALERT_EMAIL_TO, ALERT_GMAIL_APP_PASSWORD")
    to_list = [a.strip() for a in ALERT_EMAIL_TO.split(',') if a.strip()]
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = ALERT_EMAIL_FROM
    msg['To']      = ', '.join(to_list)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(ALERT_EMAIL_FROM, ALERT_GMAIL_APP_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, to_list, msg.as_string())


def send_alert_sync(message: str, priority: str = 'normal') -> None:
    """Legacy entry point — keeps backward compat with anything still calling
    this. Prefer send_email() for new code."""
    subject = "HOUSING ALERT" if priority == 'high' else "Housing Monitor"
    send_email(subject, message)
    to_list = [a.strip() for a in ALERT_EMAIL_TO.split(',') if a.strip()]
    print(f"Alert sent to: {to_list}")


async def send_alert(message: str, priority: str = 'normal'):
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_alert_sync, message, priority)


if __name__ == '__main__':
    send_email("Housing monitor — SMTP test", "Email transport working.")
    print("Test email sent.")
