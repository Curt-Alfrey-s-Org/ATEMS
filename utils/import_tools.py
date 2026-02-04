# import_tools.py - Parse and validate CSV/Excel for tool import

import csv
import io
import re
from typing import List, Tuple, Dict, Any, Optional

# Expected columns (case-insensitive). Required: tool_id_number, tool_name.
# Optional: tool_location, tool_status, tool_calibration_due, tool_calibration_date,
#           tool_calibration_cert, tool_calibration_schedule, category.
TOOL_REQUIRED = {"tool_id_number", "tool_name"}
TOOL_OPTIONAL = {
    "tool_location", "tool_status", "tool_calibration_due", "tool_calibration_date",
    "tool_calibration_cert", "tool_calibration_schedule", "category",
}
DEFAULT_NA = "N/A"


def _normalize_header(h: str) -> str:
    return (h or "").strip().lower().replace(" ", "_").replace("-", "_")


# Aliases: normalized header -> canonical field name (for column lookup)
HEADER_ALIASES = {
    "tool_id": "tool_id_number",
    "id_number": "tool_id_number",
    "tool_number": "tool_id_number",
    "name": "tool_name",
    "tool_name": "tool_name",
    "location": "tool_location",
    "status": "tool_status",
    "calibration_due": "tool_calibration_due",
    "cal_due": "tool_calibration_due",
    "calibration_date": "tool_calibration_date",
    "calibration_cert": "tool_calibration_cert",
    "calibration_schedule": "tool_calibration_schedule",
    "category": "category",
}


def _normalize_header_map(headers: List[str]) -> Dict[str, int]:
    out = {}
    for i, h in enumerate(headers):
        norm = _normalize_header(h)
        out[norm] = i
        canonical = HEADER_ALIASES.get(norm)
        if canonical:
            out[canonical] = i
    # Ensure canonical names from aliases
    for alias, canonical in HEADER_ALIASES.items():
        if canonical not in out and alias in out:
            out[canonical] = out[alias]
    return {k: v for k, v in out.items() if v >= 0}


def parse_csv(content: bytes) -> Tuple[List[str], List[List[str]]]:
    """Parse CSV bytes. Returns (headers, rows)."""
    text = content.decode("utf-8-skip", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    headers = [c.strip() for c in rows[0]]
    data_rows = [row for row in rows[1:] if any(c.strip() for c in row)]
    return headers, data_rows


def parse_xlsx(content: bytes) -> Tuple[List[str], List[List[str]]]:
    """Parse first sheet of xlsx. Returns (headers, rows)."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    headers = [str(c).strip() if c is not None else "" for c in rows[0]]
    data_rows = []
    for row in rows[1:]:
        vals = [str(c).strip() if c is not None else "" for c in row]
        if any(vals):
            data_rows.append(vals)
    return headers, data_rows


def parse_file(content: bytes, filename: str) -> Tuple[List[str], List[List[str]]]:
    """Parse CSV or xlsx by filename. Returns (headers, rows)."""
    fn = (filename or "").lower()
    if fn.endswith(".xlsx") or fn.endswith(".xls"):
        return parse_xlsx(content)
    return parse_csv(content)


def validate_tool_row(row: List[str], col_index: Dict[str, int], row_num: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate one row and return (dict for Tools, None) or (None, error_message).
    row_num is 1-based for display.
    """
    def get(key: str) -> str:
        idx = col_index.get(_normalize_header(key))
        if idx is None:
            return ""
        if idx >= len(row):
            return ""
        return (row[idx] or "").strip()

    tool_id = get("tool_id_number")
    tool_name = get("tool_name")

    if not tool_id:
        return None, f"Row {row_num}: tool_id_number is required"
    if len(tool_id) > 64:
        return None, f"Row {row_num}: tool_id_number too long"
    if not re.match(r"^[A-Za-z0-9\-]+$", tool_id):
        return None, f"Row {row_num}: tool_id_number must be alphanumeric and hyphens only"

    if not tool_name:
        return None, f"Row {row_num}: tool_name is required"
    if len(tool_name) > 64:
        return None, f"Row {row_num}: tool_name too long"

    return {
        "tool_id_number": tool_id,
        "tool_name": tool_name[:64],
        "tool_location": get("tool_location") or DEFAULT_NA,
        "tool_status": get("tool_status") or "In Stock",
        "tool_calibration_due": get("tool_calibration_due") or DEFAULT_NA,
        "tool_calibration_date": get("tool_calibration_date") or DEFAULT_NA,
        "tool_calibration_cert": get("tool_calibration_cert") or DEFAULT_NA,
        "tool_calibration_schedule": get("tool_calibration_schedule") or DEFAULT_NA,
        "category": get("category") or None,
    }, None


def parse_and_validate_tools(content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse file and validate each row. Returns (valid_rows, errors).
    errors: list of { "row": 1-based index, "message": "..." }
    """
    headers, rows = parse_file(content, filename)
    col_index = _normalize_header_map(headers)

    missing = TOOL_REQUIRED - set(col_index.keys())
    if missing:
        return [], [{"row": 1, "message": f"Missing required column(s): {', '.join(sorted(missing))}. Use: tool_id_number (or Tool ID), tool_name (or Name)."}]

    valid = []
    errors = []
    for i, row in enumerate(rows):
        row_num = i + 2  # 1-based + header row
        data, err = validate_tool_row(row, col_index, row_num)
        if err:
            errors.append({"row": row_num, "message": err})
        else:
            valid.append(data)
    return valid, errors


def import_tools_rows(rows: List[Dict[str, Any]]):  # noqa: no cover - uses db
    """
    Insert or update tools. Uses Tools model and db from Flask app context.
    Returns (created_count, updated_count, errors_list).
    """
    from models.tools import Tools
    from extensions import db

    created = 0
    updated = 0
    errors = []
    for i, r in enumerate(rows):
        try:
            existing = Tools.query.filter_by(tool_id_number=r["tool_id_number"]).first()
            if existing:
                existing.tool_name = r["tool_name"][:64]
                existing.tool_location = (r["tool_location"] or DEFAULT_NA)[:64]
                existing.tool_status = (r["tool_status"] or "In Stock")[:64]
                existing.tool_calibration_due = (r["tool_calibration_due"] or DEFAULT_NA)[:64]
                existing.tool_calibration_date = (r["tool_calibration_date"] or DEFAULT_NA)[:64]
                existing.tool_calibration_cert = (r["tool_calibration_cert"] or DEFAULT_NA)[:64]
                existing.tool_calibration_schedule = (r["tool_calibration_schedule"] or DEFAULT_NA)[:64]
                if r.get("category") is not None:
                    existing.category = (r["category"] or "")[:64]
                updated += 1
            else:
                t = Tools(
                    tool_id_number=r["tool_id_number"],
                    tool_name=r["tool_name"][:64],
                    tool_location=(r["tool_location"] or DEFAULT_NA)[:64],
                    tool_status=(r["tool_status"] or "In Stock")[:64],
                    tool_calibration_due=(r["tool_calibration_due"] or DEFAULT_NA)[:64],
                    tool_calibration_date=(r["tool_calibration_date"] or DEFAULT_NA)[:64],
                    tool_calibration_cert=(r["tool_calibration_cert"] or DEFAULT_NA)[:64],
                    tool_calibration_schedule=(r["tool_calibration_schedule"] or DEFAULT_NA)[:64],
                    category=(r.get("category") or "")[:64] or None,
                )
                db.session.add(t)
                created += 1
        except Exception as e:
            errors.append({"row": i + 1, "message": str(e)})
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append({"row": 0, "message": f"Commit failed: {e}"})
    return created, updated, errors
