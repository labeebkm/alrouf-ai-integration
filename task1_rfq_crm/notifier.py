"""
Internal Alert Notifier
Sends a new-RFQ alert to Slack (webhook) and/or email (SMTP).
Falls back gracefully when credentials are absent.
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
import urllib.request
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertResult:
    slack_sent: bool
    email_sent: bool
    slack_error: Optional[str] = None
    email_error: Optional[str] = None


def send_internal_alert(
    rfq,
    deal_id: str,
    crm_url: Optional[str] = None,
    mock_mode: bool = True,
) -> AlertResult:
    """
    Fire a new-RFQ alert to Slack and/or email.
    In mock_mode, just logs the alert without hitting any external service.
    """
    items_text = "\n".join(
        f"  • {li.product_description} × {li.quantity or '?'}"
        for li in rfq.line_items[:5]
    ) or "  • (no items parsed)"

    message = (
        f"🔔 *New RFQ Received* — Deal {deal_id}\n"
        f"*From:* {rfq.sender_name or 'Unknown'} <{rfq.sender_email or '?'}>\n"
        f"*Company:* {rfq.sender_company or '—'}\n"
        f"*Subject:* {rfq.subject or '—'}\n"
        f"*Items:*\n{items_text}\n"
        f"*Delivery:* {rfq.delivery_date or '—'}\n"
        f"*Destination:* {rfq.destination_port or '—'}\n"
        + (f"*CRM Link:* {crm_url}\n" if crm_url else "")
    )

    if mock_mode:
        logger.info("[MOCK ALERT]\n%s", message)
        return AlertResult(slack_sent=False, email_sent=False)

    slack_ok, slack_err = _send_slack(message)
    email_ok, email_err = _send_email(rfq, deal_id, message)

    return AlertResult(
        slack_sent=slack_ok,
        email_sent=email_ok,
        slack_error=slack_err,
        email_error=email_err,
    )


def _send_slack(message: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook:
        logger.info("SLACK_WEBHOOK_URL not configured — skipping Slack alert")
        return False, "not_configured"
    try:
        body = json.dumps({"text": message}).encode()
        req = urllib.request.Request(
            webhook,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            _ = resp.read()
        logger.info("Slack alert sent")
        return True, None
    except Exception as exc:
        logger.error("Slack alert failed: %s", exc)
        return False, str(exc)


def _send_email(rfq, deal_id: str, message_text: str):
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_addr = os.getenv("ALERT_EMAIL_FROM", smtp_user)
    to_addr   = os.getenv("ALERT_EMAIL_TO", "")

    if not all([smtp_host, smtp_user, to_addr]):
        logger.info("SMTP not configured — skipping email alert")
        return False, "not_configured"
    try:
        subject = f"[NEW RFQ] {rfq.sender_company or rfq.sender_email} — {deal_id}"
        msg = MIMEText(message_text.replace("*", "").replace("🔔 ", ""), "plain")
        msg["Subject"] = subject
        msg["From"]    = from_addr
        msg["To"]      = to_addr

        with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        logger.info("Email alert sent to %s", to_addr)
        return True, None
    except Exception as exc:
        logger.error("Email alert failed: %s", exc)
        return False, str(exc)
