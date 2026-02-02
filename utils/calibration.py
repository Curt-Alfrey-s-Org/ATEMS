# calibration.py - Parse calibration dates, detect overdue

from datetime import datetime, timedelta
from typing import Optional


def parse_calibration_due(value: Optional[str]) -> Optional[datetime]:
    """Parse tool_calibration_due string to date. Returns None if N/A or unparseable."""
    if not value or (value or "").strip().upper() in ("", "N/A", "NA", "NONE"):
        return None
    s = (value or "").strip()
    s_date = s[:10] if len(s) >= 10 else s
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s_date, fmt)
        except ValueError:
            continue
    return None


def is_calibration_overdue(cal_due_str: Optional[str]) -> bool:
    """True if calibration_due is a valid date and is in the past."""
    dt = parse_calibration_due(cal_due_str)
    return dt is not None and dt.date() < datetime.now().date()


def calibration_due_soon(cal_due_str: Optional[str], days: int = 30) -> bool:
    """True if calibration is due within the next N days."""
    dt = parse_calibration_due(cal_due_str)
    if dt is None:
        return False
    today = datetime.now().date()
    due = dt.date()
    return today <= due <= (today + timedelta(days=days))
