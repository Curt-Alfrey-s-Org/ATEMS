"""Authentication hardening helpers (security review 2026-09-25).

- No built-in default credentials: every login comes from env vars or the DB.
- Passwords that were ever shipped as defaults in this repo (or that are
  trivially guessable) are refused, so leftover rows created with them can
  no longer be used to sign in.
- In production, bootstrapping the first admin fails fast unless
  ADMIN_PASSWORD is set.

"Production" is the default. Set ENVIRONMENT=development (or test) for local
dev and CI so an empty database can start without an admin being created.
"""
import os

# Passwords that were once hardcoded defaults in ATEMS (or are trivially
# guessable). They are a blocklist, not credentials: login and admin bootstrap
# both refuse them.
KNOWN_DEFAULT_PASSWORDS = frozenset({
    "admin",
    "admin123",
    "user",
    "user123",
    "password",
    "changeme",
    "changeme123",
    "demo123",
})

NON_PRODUCTION_ENVIRONMENTS = frozenset({"development", "dev", "local", "test", "testing", "ci"})


def is_production() -> bool:
    """True unless ENVIRONMENT names a non-production environment."""
    env = (os.getenv("ENVIRONMENT") or "production").strip().lower()
    return env not in NON_PRODUCTION_ENVIRONMENTS


def is_known_default_password(password) -> bool:
    """True if the password is a known default/placeholder that must not be accepted."""
    if password is None:
        return True
    return password.strip().lower() in KNOWN_DEFAULT_PASSWORDS


def get_bootstrap_admin_credentials():
    """Return (username, password, email) for the first admin, or None.

    Only called when the users table is empty.
    - Production + ADMIN_PASSWORD missing -> RuntimeError (fail fast).
    - Non-production + ADMIN_PASSWORD missing -> None (caller skips bootstrap).
    - ADMIN_PASSWORD set to a known default -> RuntimeError in any environment.
    """
    username = (os.getenv("ADMIN_USERNAME") or "").strip() or "admin"
    password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    email = (os.getenv("ADMIN_EMAIL") or "").strip() or "admin@example.com"

    if not password:
        if is_production():
            raise RuntimeError(
                "ADMIN_PASSWORD is not set. The users table is empty, so ATEMS must "
                "create the first admin account. Set ADMIN_PASSWORD (and optionally "
                "ADMIN_USERNAME / ADMIN_EMAIL) in the environment and restart. "
                "For local development set ENVIRONMENT=development to skip this."
            )
        return None

    if is_known_default_password(password):
        raise RuntimeError(
            "ADMIN_PASSWORD is set to a known default/placeholder value, which is not "
            "accepted. Choose a strong, unique password."
        )

    return username, password, email
