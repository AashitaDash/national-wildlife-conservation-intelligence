import asyncio
import logging
import ssl
import smtplib
from email.message import EmailMessage

from backend.app.config import settings

logger = logging.getLogger("wildlife_platform.email")

class EmailService:
    """Simple async email sender.
    If SMTP configuration is missing, the call becomes a no‑op that logs the
    intended email – this matches the project's "optional, safe mock delivery"
    comment in `Settings`.
    """

    @staticmethod
    async def send_email(to: str, subject: str, body: str) -> None:
        """Send an email via the configured SMTP server.
        Raises any `smtplib` exception so callers can handle delivery failures.
        """
        if not settings.SMTP_HOST:
            logger.info(f"[Mock email] To: {to} | Subject: {subject}\n{body}")
            return

        msg = EmailMessage()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        def _send():
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls(context=context)
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
                server.send_message(msg)

        await asyncio.to_thread(_send)
