# calibration_reminders.py - Email reminders for calibration due/overdue

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from utils.calibration import is_calibration_overdue, calibration_due_soon, parse_calibration_due

logger = logging.getLogger(__name__)


def get_reminder_days() -> int:
    """Days before due date to consider 'due soon'. From env CALIBRATION_REMIND_DAYS."""
    try:
        return max(1, min(365, int(os.getenv("CALIBRATION_REMIND_DAYS", "30"))))
    except ValueError:
        return 30


def get_remind_overdue() -> bool:
    """Whether to include overdue tools in reminder. From env REMIND_OVERDUE."""
    return os.getenv("REMIND_OVERDUE", "true").lower() in ("1", "true", "yes")


def get_recipients() -> List[str]:
    """Comma-separated emails from CALIBRATION_REMIND_TO. Empty if not set."""
    to = (os.getenv("CALIBRATION_REMIND_TO") or "").strip()
    if not to:
        return []
    return [e.strip() for e in to.split(",") if e.strip()]


def is_mail_configured() -> bool:
    """True if MAIL_SERVER and at least one recipient are set."""
    return bool(os.getenv("MAIL_SERVER") and get_recipients())


def get_due_and_overdue_tools(tools_query):
    """
    Split tools with calibration_due into (overdue_list, due_soon_list).
    Each item: dict with tool_id_number, tool_name, tool_location, category, tool_calibration_due.
    """
    overdue = []
    due_soon = []
    days = get_reminder_days()
    include_overdue = get_remind_overdue()

    for t in tools_query:
        if not t.tool_calibration_due or (t.tool_calibration_due or "").strip().upper() in ("", "N/A", "NA"):
            continue
        row = {
            "tool_id_number": t.tool_id_number or "",
            "tool_name": t.tool_name or "",
            "tool_location": t.tool_location or "",
            "category": t.category or "",
            "tool_calibration_due": t.tool_calibration_due,
        }
        if is_calibration_overdue(t.tool_calibration_due):
            if include_overdue:
                overdue.append(row)
        elif calibration_due_soon(t.tool_calibration_due, days=days):
            due_soon.append(row)

    return overdue, due_soon


def build_email_body(overdue: list, due_soon: list, base_url: str = "") -> Tuple[str, str]:
    """Plain text and HTML body for calibration reminder email."""
    lines = ["ATEMS Calibration Reminder", ""]
    if overdue:
        lines.append("Overdue:")
        for r in overdue:
            lines.append(f"  - {r['tool_id_number']} | {r['tool_name']} | Due: {r['tool_calibration_due']}")
        lines.append("")
    if due_soon:
        lines.append("Due soon:")
        for r in due_soon:
            lines.append(f"  - {r['tool_id_number']} | {r['tool_name']} | Due: {r['tool_calibration_due']}")
        lines.append("")
    if base_url:
        lines.append(f"View full report: {base_url.rstrip('/')}/reports")
    plain = "\n".join(lines)

    # Simple HTML
    html_parts = ["<h2>ATEMS Calibration Reminder</h2>"]
    if overdue:
        html_parts.append("<h3>Overdue</h3><ul>")
        for r in overdue:
            html_parts.append(f"<li><strong>{r['tool_id_number']}</strong> {r['tool_name']} — Due: {r['tool_calibration_due']}</li>")
        html_parts.append("</ul>")
    if due_soon:
        html_parts.append("<h3>Due soon</h3><ul>")
        for r in due_soon:
            html_parts.append(f"<li><strong>{r['tool_id_number']}</strong> {r['tool_name']} — Due: {r['tool_calibration_due']}</li>")
        html_parts.append("</ul>")
    if base_url:
        html_parts.append(f'<p><a href="{base_url.rstrip("/")}/reports">View calibration report</a></p>')
    html = "\n".join(html_parts)

    return plain, html


def send_calibration_reminders(app=None) -> dict:
    """
    Find tools due/overdue, build email, send to CALIBRATION_REMIND_TO.
    Returns dict: sent (bool), message (str), overdue_count, due_soon_count, error (optional).
    """
    from models.tools import Tools

    if app is None:
        from atems import create_app
        app = create_app()

    with app.app_context():
        tools = Tools.query.filter(
            Tools.tool_calibration_due.isnot(None),
            Tools.tool_calibration_due != "",
            Tools.tool_calibration_due != "N/A",
        ).order_by(Tools.tool_calibration_due).all()

        overdue, due_soon = get_due_and_overdue_tools(tools)
        total = len(overdue) + len(due_soon)

        if not is_mail_configured():
            return {
                "sent": False,
                "message": "Email not configured. Set MAIL_SERVER and CALIBRATION_REMIND_TO in .env.",
                "overdue_count": len(overdue),
                "due_soon_count": len(due_soon),
                "total": total,
            }

        if total == 0:
            return {
                "sent": True,
                "message": "No tools due or overdue for calibration.",
                "overdue_count": 0,
                "due_soon_count": 0,
                "total": 0,
            }

        recipients = get_recipients()
        base_url = os.getenv("ATEMS_BASE_URL", "http://127.0.0.1:5000")
        plain, html = build_email_body(overdue, due_soon, base_url)

        subject = f"ATEMS Calibration Reminder: {len(overdue)} overdue, {len(due_soon)} due soon"
        sender = os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("MAIL_USERNAME") or "atems@local"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            use_tls = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
            port = int(os.getenv("MAIL_PORT", "587") if use_tls else os.getenv("MAIL_PORT", "25"))
            server = smtplib.SMTP(os.getenv("MAIL_SERVER"), port)
            if use_tls:
                server.starttls()
            username = os.getenv("MAIL_USERNAME")
            password = os.getenv("MAIL_PASSWORD")
            if username and password:
                server.login(username, password)
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            logger.info("Calibration reminder email sent to %s (%s overdue, %s due soon)", recipients, len(overdue), len(due_soon))
            return {
                "sent": True,
                "message": f"Calibration reminder sent to {len(recipients)} recipient(s).",
                "overdue_count": len(overdue),
                "due_soon_count": len(due_soon),
                "total": total,
            }
        except Exception as e:
            logger.exception("Failed to send calibration reminder email")
            return {
                "sent": False,
                "message": "Failed to send email.",
                "overdue_count": len(overdue),
                "due_soon_count": len(due_soon),
                "total": total,
                "error": str(e),
            }
