# ATEMS Improvements

Improvements applied from patterns used in workspace docs and other APIs (e.g. market-pie5-bot).

---

## CI/CD (GitHub Actions)

- **`.github/workflows/tests.yml`** — Runs on push/PR to main/master. Sets up Python 3.10–3.12, installs dependencies, runs startup tests and pytest. Uses SQLite for CI DB.
- **`.github/workflows/lint.yml`** — Runs flake8 (critical errors only) and black --check (non-blocking). Keeps code quality consistent.

---

## Documentation

- **`docs/USER_GUIDE.md`** — Quick start, login, main features, reports/export, API summary, deployment, testing, and links to workspace docs.
- **README** — Added pointer to `docs/USER_GUIDE.md`.
- **Workspace** — README already linked to `docs/BOTS_OVERVIEW.md` and `docs/QUICK_REFERENCE.md`.

---

## Already in place (unchanged)

- **Startup self-tests** — `selftest/startup.py` (syntax, imports, app structure).
- **Pytest** — `conftest.py`, fixtures for app, client, db_session, seed_user, seed_tool.
- **Tests** — startup_test, test_http_and_api, test_checkinout, test_error_patterns, test_readme_claims.
- **Deployment** — RUN_ON_SERVER.md, TRAEFIK_ATEMS.md, PORT_INFO.md, atems.service, traefik-atems.yml.

---

## Summary

| Area   | Change                                      |
|--------|---------------------------------------------|
| CI/CD  | Added `.github/workflows/tests.yml`, `lint.yml` |
| Docs   | Added `docs/USER_GUIDE.md`; README link     |
| Workspace | Already linked in README                 |
