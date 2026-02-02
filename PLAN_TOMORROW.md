# ATEMS — Plan for Tomorrow (Higher Impact, Moderate Effort)

Complete these items in order. Start with moving ATEMS to its own repo; then the five feature items.

---

## 0. Move ATEMS to its own repo (outside rankings-bot)

- **Goal:** ATEMS should live in its own directory/repo, not inside the rankings-bot folder.
- **Tasks:**
  - [x] Clone or copy the ATEMS repo to a separate location (e.g. `~/ATEMS` or `~/projects/ATEMS`).
  - [x] Confirm it runs and tests pass from the new location.
  - [x] Update desktop shortcuts / start scripts if they point at the old path.
  - [ ] Optionally remove or archive ATEMS from inside `rankings-bot` so there’s a single canonical copy.

---

## 1. Barcode/QR scan at checkout

- **Goal:** Scan tool ID and badge at checkout (e.g. handheld scanner or camera).
- **Tasks:**
  - [ ] Add barcode/QR input on checkout form (camera or scanner input).
  - [ ] Parse scanned value into tool ID and/or user badge.
  - [ ] Optional: support “scan tool then scan badge” flow.
- **Reference:** COMPETITOR_RESEARCH.md — “Barcode / QR” in Check-in/out and Mobile & scanning.

---

## 2. Email reminders for calibration due/overdue

- **Goal:** Configurable email reminders when calibration is due soon or overdue.
- **Tasks:**
  - [ ] Add settings for “remind X days before due” and “remind when overdue” (e.g. in Settings or env).
  - [ ] Background job or scheduled task that finds tools due/overdue and sends emails.
  - [ ] Email content: tool ID, description, due date, link to tool/calibration report.
- **Reference:** COMPETITOR_RESEARCH.md — “Email (or SMS) alerts” in Calibration & maintenance.

---

## 3. “Return by” date on checkout and overdue-returns list/reminders

- **Goal:** Set return-by date at checkout; list overdue returns and optionally remind.
- **Tasks:**
  - [ ] Add “return by” date field to checkout (model + form + UI).
  - [ ] Dashboard or report: “Overdue returns” list (checked out past return-by).
  - [ ] Optional: email reminders for overdue returns (reuse pattern from calibration reminders).
- **Reference:** COMPETITOR_RESEARCH.md — “Due dates & reminders” in Check-in/out.

---

## 4. Export reports (PDF and/or Excel)

- **Goal:** Export report data as PDF and/or Excel, not only CSV.
- **Tasks:**
  - [ ] Add PDF export for at least one report (e.g. Tool Usage or Calibration).
  - [ ] Add Excel (.xlsx) export for same reports (e.g. openpyxl or xlsxwriter).
  - [ ] Expose “Export PDF” / “Export Excel” on Reports page next to existing CSV.
- **Reference:** COMPETITOR_RESEARCH.md — “Export – PDF, Excel, CSV” in Reporting & analytics.

---

## 5. CSV/Excel import for tools (and optionally users)

- **Goal:** Bulk import tools from CSV or Excel; optionally users.
- **Tasks:**
  - [ ] Define required columns for tools (e.g. tool_id, description, category, calibration_due).
  - [ ] Admin or dedicated page: “Import tools” with file upload (CSV and/or .xlsx).
  - [ ] Validate rows, show preview/errors, then insert or update tools.
  - [ ] Optional: same flow for users (username, role, email, etc.).
- **Reference:** COMPETITOR_RESEARCH.md — bulk data and reporting/import patterns.

---

## Quick checklist (tomorrow)

| # | Feature | Status |
|---|---------|--------|
| 0 | Move ATEMS to its own repo (outside rankings-bot) | ☑ |
| 1 | Barcode/QR scan at checkout | ☐ |
| 2 | Email reminders (calibration due/overdue) | ☐ |
| 3 | Return-by date + overdue-returns list/reminders | ☐ |
| 4 | Export reports (PDF and/or Excel) | ☐ |
| 5 | CSV/Excel import for tools (and optionally users) | ☐ |
