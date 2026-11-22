'''Build, preview and send the report email.'''

import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from getpass import getpass
from pathlib import Path

REPORT_FILENAME  = 'report.txt'
SMTP_TIMEOUT_SECONDS = 30

def build_message(sender: str, recipients: list[str], report: str) -> EmailMessage:
    '''Return and email to ``recipients`` with ``report`` attached as a text file.'''
    msg = EmailMessage()
    msg['Subject'] = f'Report {date.today():%d %B %Y}'
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.set_content('Hellow,\n\nThe latest report is attached.\n')
    msg.add_attachment(
        report.encode('utf-8'),
        maintype='text',
        subtype='plain',
        filename=REPORT_FILENAME
    )
    return msg


def save_preview(msg: EmailMessage, path: str | Path) -> None:
    """Write ``msg`` to ``path`` as an .eml file without sending it."""
    with open(path, "wb") as f:
        f.write(bytes(msg))


def get_credentials() -> tuple[str, str]:
    """Return (address, password) from the environment, asking for any that is missing.

    Reads EMAIL_USER and EMAIL_PASSWORD.
    """
    user = os.environ.get("EMAIL_USER") or input("Email address: ")
    password = os.environ.get("EMAIL_PASSWORD") or getpass("Password: ")
    return user, password


def send_message(
    msg: EmailMessage, host: str, port: int, user: str, password: str
) -> None:
    """Send ``msg`` through the SMTP server at ``host``:``port`` using STARTTLS.

    Raises ``smtplib.SMTPException`` or ``OSError`` if the connection, login or
    delivery fails.
    """
    with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(user, password)
        server.send_message(msg)