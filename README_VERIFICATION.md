# ATEMS README Verification

What the README says ATEMS does vs. what the code actually implements.

---

## 1. Overview Claims

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Inventory control for tools rooms, warehouses, supply chain | **Partial** | Core: tools, users, check-in/out. No warehouse-specific features. |
| Modular: plug-in modules for industry | **Not implemented** | Single monolithic app, no module system. |
| Works in any environment / small business | **Partial** | Generic enough; no industry-specific modules. |

---

## 2. Automated

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Email reminders to bring items back on time | **Not implemented** | No email sending, no overdue reminders. |
| Emails to prevent jobs with tools overdue for calibration | **Not implemented** | Calibration overdue is detected and warned at checkout; no email. |

---

## 3. Barcode Tracking

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Active/passive RFID barcoding | **Not implemented** | No RFID integration. |
| Scan-gun or phone/tablet app | **Partial** | Check-in/out form + `/api/checkinout` accept tool IDs; no scanner-specific integration. |

---

## 4. ATEMS Tracks

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Where is the item stored | **Yes** | `Tools.tool_location` |
| Who checked in/out | **Yes** | `Tools.checked_out_by`, `CheckoutHistory` |
| What job it was used on | **Partial** | `CheckoutHistory.job_id` exists, not used in UI/flow |
| How long it has been checked out | **Partial** | `checkout_time` stored; duration not computed or displayed |
| Condition at check in/out | **Not implemented** | No condition field. |
| Does it require calibration | **Yes** | `tool_calibration_due`, `tool_calibration_date`, etc. |
| Does it have a shelf life | **Not implemented** | No shelf_life field. |

---

## 5. Equipment

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Records calibrated and non-calibrated equipment | **Yes** | Tools have calibration fields; N/A for non-calibrated |
| Historical serviceability data | **Partial** | `CheckoutHistory`; no explicit serviceability history |
| Info on calibration vendors | **Not implemented** | No vendor model. |
| NIST compliance / record keeping | **Not implemented** | No NIST-specific fields or workflows. |

---

## 6. Management

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Manages all types of inventory in one program | **Partial** | Manages tools only; no other inventory types. |

---

## 7. Reports

| README Claim | Status | Implementation |
|--------------|--------|----------------|
| Tool Usage History | **Partial** | `CheckoutHistory` + Admin view; no dedicated report UI |
| Calibration History | **Not implemented** | No calibration history model or report |
| User Activity History | **Partial** | `CheckoutHistory` by username; no dedicated report |
| Inventory Status Report | **Partial** | Dashboard stats (total, in stock, out, calibration overdue) |
| Generate custom report | **Not implemented** | No custom report builder |
| Print or email PDF | **Not implemented** | reportlab present; no report endpoints |

---

## 8. Summary

| Category | Implemented | Partial | Not Implemented |
|----------|-------------|---------|-----------------|
| Core tracking | 4 | 3 | 0 |
| Automation | 0 | 0 | 2 |
| Barcode/RFID | 0 | 1 | 1 |
| Equipment | 1 | 1 | 2 |
| Reports | 0 | 3 | 3 |
| **Total** | **5** | **8** | **8** |

---

## 9. Test Coverage

Run the full suite:
```bash
python tests/startup_test.py   # Quick startup validation
pytest tests/ -v               # All tests including README claims
./run_tests.sh                 # Both (if venv active)
```

**Test summary (19 tests):**
- `test_checkinout.py`: 7 tests — check-in/out flow, badge mismatch, unknown user/tool, industry format
- `test_readme_claims.py`: 12 tests — API health, tracks (where/who/calibration), check flow, inventory stats, documented gaps (email, job, condition, shelf_life)
