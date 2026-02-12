# AFI 21-101 Compliance — ATEMS Readiness

**Purpose:** Align ATEMS with Air Force Instruction 21-101 (Aircraft and Equipment Maintenance Management) and CTK (Consolidated Tool Kit) requirements so it can support Air Force tool accountability contracts.

---

## 1. AFI 21-101 / CTK requirements (summary)

| Requirement | AFI 21-101 / CTK | ATEMS capability |
|-------------|------------------|------------------|
| **Positive control** | All tools and equipment under positive control to prevent FOD | Check-in/check-out with user + badge; every tool has status and custody |
| **Master Inventory List (MIL)** | Unit establishes MIL as standard for all CTKs | **Inventory report** (Reports → Inventory) = full tool list by status/category; export as CSV/PDF/Excel = MIL export |
| **Custodian designation** | Primary and alternate tool control custodians designated in writing | **CTK Custodian** role in ATEMS; designate users as CTK Custodian in Admin → Users |
| **Accountability** | Inventory control, lost-tool procedures, documented control systems | Checkout history (audit trail), calibration due/overdue, reports (Usage, Calibration, Inventory, Overdue Returns) |
| **Calibration** | Calibrated tools tracked; next due dates | `tool_calibration_due`, `tool_calibration_date`, calibration report, calibration overdue alerts |
| **Scope** | TOs, checklists, job guides, aircraft files, laptops when taken to job sites | Tools + optional categories; extend with custom fields if needed for TO/device tracking |

---

## 2. ATEMS features mapped to CTK

- **Check-in / Check-out** — Supports AFI 21-101 positive control and custody. Use badge + username for accountability.
- **Inventory report** — Use as your **Master Inventory List (MIL)**. Export CSV/Excel for official records.
- **Calibration report** — Tools due/overdue; supports calibration schedule compliance.
- **Usage report** — Checkout history for utilization and accountability.
- **Overdue returns** — Return-by date and overdue-returns report support lost-tool and FOD procedures.
- **Roles** — **Admin** = CTK program manager; **CTK Custodian** = primary/alternate tool control custodian; **User** = CTK employee.

---

## 3. Designating CTK custodians

1. In ATEMS, go to **Admin** → **Users**.
2. For each primary or alternate tool control custodian, set **Role** to **CTK Custodian**.
3. Keep at least one **Admin** (e.g. Flight Chief / Section NCOIC) for program management.

Designation in ATEMS satisfies “designated in writing” when combined with your unit memo or SOP naming those usernames as custodians.

---

## 4. Master Inventory List (MIL)

- **Reports** → **Inventory** shows all tools by status and category.
- **Export** → choose **Inventory**, format CSV or Excel, to produce a MIL-compliant list for records or audits.

---

## 5. Compliance checklist (for proposals)

- [x] Positive tool control (check-in/check-out, custody)
- [x] Master Inventory List (inventory report + export)
- [x] Primary/alternate custodian designation (CTK Custodian role)
- [x] Calibration tracking and due/overdue reporting
- [x] Audit trail (checkout history)
- [x] Lost-tool / overdue-return procedures (overdue-returns report, return-by date)
- [x] Applicable from small shops to large tool sets (scalable)

---

## 6. References

- **AFI 21-101** — Aircraft and Equipment Maintenance Management (CTK program).
- **Wing supplements** — e.g. 452 AMWI 21-102, 920 RQWI 21-117 (unit-specific CTK procedures).
- **ATEMS research** — `docs/USAF_TOOL_ACCOUNTABILITY_RESEARCH.md` for Air Force context and contract angles.

---

*Last updated Feb 2026.*
