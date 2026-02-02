# ATEMS — Plan (Most Important First)

Complete in this order. Item 0 done; then the five features by impact.

---

## 0. Move ATEMS to its own repo (outside rankings-bot) — DONE

- **Goal:** ATEMS lives in its own directory/repo.
- **Tasks:** [x] Clone to ~/ATEMS; [x] tests pass; [x] desktop paths updated; [ ] optional: remove from rankings-bot.

---

## 1. "Return by" date + overdue-returns list/reminders — DONE

- **Goal:** Set return-by date at checkout; list overdue returns; optional reminders.
- **Tasks:** [x] return_by field; [x] dashboard + report "Overdue Returns"; [ ] optional email reminders.
- **Reference:** COMPETITOR_RESEARCH.md — "Due dates & reminders".

---

## 2. Email reminders for calibration due/overdue — DONE

- **Goal:** Configurable email reminders when calibration is due soon or overdue.
- **Tasks:** [x] Env CALIBRATION_REMIND_DAYS, MAIL_*; [x] send_calibration_reminders(); [x] Settings → Send now; [x] cron example.
- **Reference:** COMPETITOR_RESEARCH.md — "Email (or SMS) alerts".

---

## 3. Barcode/QR scan at checkout — DONE

- **Goal:** Scan tool ID and badge at checkout (camera or scanner).
- **Tasks:** [x] Scan input (keyboard wedge); [x] /api/user-by-badge; [x] camera scan (html5-qrcode); [x] scan-tool-then-badge flow.
- **Reference:** COMPETITOR_RESEARCH.md — "Barcode / QR".

---

## 4. Export reports (PDF and/or Excel) — DONE

- **Goal:** Export report data as PDF and/or Excel, not only CSV.
- **Tasks:** [x] PDF export (reportlab); [x] Excel export (openpyxl); [x] Export PDF/Excel buttons on Reports.
- **Reference:** COMPETITOR_RESEARCH.md — "Export – PDF, Excel, CSV".

---

## 5. CSV/Excel import for tools (and optionally users) — DONE

- **Goal:** Bulk import tools from CSV or Excel; optionally users.
- **Tasks:** [x] Required: tool_id_number, tool_name; [x] /import page + preview + import APIs; [ ] optional: user import.
- **Reference:** COMPETITOR_RESEARCH.md — bulk import.

---

## Quick checklist

| # | Feature | Status |
|---|---------|--------|
| 0 | Move ATEMS to its own repo | ☑ |
| 1 | Return-by date + overdue-returns list/reminders | ☑ |
| 2 | Email reminders (calibration due/overdue) | ☑ |
| 3 | Barcode/QR scan at checkout | ☑ |
| 4 | Export reports (PDF and/or Excel) | ☑ |
| 5 | CSV/Excel import for tools (and optionally users) | ☑ |
