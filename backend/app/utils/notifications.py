"""
Lightweight notification service.

Sends transactional emails via SMTP when credentials are configured.
Falls back to logging when SMTP is not available so that the rest of the
application never crashes due to a missing mail server.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Thin wrapper around :mod:`smtplib` with graceful degradation."""

    def __init__(self) -> None:
        self._smtp_configured: bool = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _get_smtp_connection(self) -> smtplib.SMTP:
        """Create, authenticate and return an SMTP connection."""
        smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        smtp.ehlo()
        if settings.SMTP_TLS:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        return smtp

    # ── Public API ───────────────────────────────────────────────────────

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> bool:
        """Send a single email.

        Parameters
        ----------
        to_email:
            Recipient address.
        subject:
            Email subject line.
        body_html:
            HTML body content.
        body_text:
            Optional plain-text fallback.  If omitted, only the HTML
            part is sent.

        Returns
        -------
        bool
            ``True`` if the email was sent successfully, ``False`` otherwise.
        """
        if not self._smtp_configured:
            logger.warning(
                "SMTP not configured -- logging email instead. "
                "To=%s Subject=%s",
                to_email,
                subject,
            )
            logger.info("Email body (HTML): %s", body_html)
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        try:
            with self._get_smtp_connection() as smtp:
                smtp.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False


# Module-level singleton for convenience
_notification_service = NotificationService()


def send_autopilot_notification(
    user_email: str,
    actions_summary: list[dict[str, Any]],
) -> bool:
    """Notify a user about autopilot actions taken on their behalf.

    Parameters
    ----------
    user_email:
        Recipient email address.
    actions_summary:
        A list of dicts, each describing one automated action.  Expected
        keys include ``"device"``, ``"action"``, and ``"reason"``.

    Returns
    -------
    bool
        ``True`` if delivery succeeded, ``False`` otherwise (including
        when SMTP is not configured).
    """
    if not actions_summary:
        logger.debug("No autopilot actions to notify about; skipping.")
        return False

    rows = ""
    for action in actions_summary:
        device = action.get("device", "Unknown")
        act = action.get("action", "N/A")
        reason = action.get("reason", "")
        rows += (
            f"<tr>"
            f"<td style='padding:6px 12px;border:1px solid #ddd'>{device}</td>"
            f"<td style='padding:6px 12px;border:1px solid #ddd'>{act}</td>"
            f"<td style='padding:6px 12px;border:1px solid #ddd'>{reason}</td>"
            f"</tr>"
        )

    body_html = (
        "<h2>Autopilot Actions Summary</h2>"
        "<p>The following actions were automatically executed on your behalf:</p>"
        "<table style='border-collapse:collapse;width:100%'>"
        "<thead><tr>"
        "<th style='padding:6px 12px;border:1px solid #ddd;text-align:left'>Device</th>"
        "<th style='padding:6px 12px;border:1px solid #ddd;text-align:left'>Action</th>"
        "<th style='padding:6px 12px;border:1px solid #ddd;text-align:left'>Reason</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "<p style='margin-top:16px;color:#888;font-size:12px'>"
        "You can review or undo these actions from your dashboard.</p>"
    )

    body_text = "Autopilot Actions Summary\n\n" + "\n".join(
        f"- {a.get('device', 'Unknown')}: {a.get('action', 'N/A')} ({a.get('reason', '')})"
        for a in actions_summary
    )

    return _notification_service.send_email(
        to_email=user_email,
        subject=f"[{settings.APP_NAME}] Autopilot Actions Report",
        body_html=body_html,
        body_text=body_text,
    )
