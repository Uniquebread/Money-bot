"""
Optional secondary channel. Off by default - only sends if SMTP_USER,
SMTP_PASS and EMAIL_TO are all set as secrets. You said Telegram is your
main channel, so this is here purely as a fallback/backup you can enable
later without touching any other code.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config


def send(subject, html_body):
    if not (config.SMTP_USER and config.SMTP_PASS and config.EMAIL_TO):
        print("[emailer] SMTP secrets not fully set - skipping email (this is expected if you're Telegram-only).")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config.EMAIL_FROM_NAME} <{config.SMTP_USER}>"
    msg["To"] = config.EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_USER, [config.EMAIL_TO], msg.as_string())
        return True
    except Exception as e:
        print(f"[emailer] send failed: {e}")
        return False
