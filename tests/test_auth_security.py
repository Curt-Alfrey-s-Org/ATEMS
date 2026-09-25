"""
Unit tests for utils/auth_security.py (security review 2026-09-25, findings #2 and #14).
No app or database needed.
"""
import pytest

from utils import auth_security
from utils.auth_security import (
    get_bootstrap_admin_credentials,
    is_known_default_password,
    is_production,
)


@pytest.fixture
def clean_env(monkeypatch):
    for var in ("ENVIRONMENT", "ADMIN_USERNAME", "ADMIN_PASSWORD", "ADMIN_EMAIL"):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


class TestKnownDefaultPasswords:
    @pytest.mark.parametrize("pw", ["admin123", "user123", "changeme123", "demo123", " Admin123 ", "password", None])
    def test_known_defaults_are_refused(self, pw):
        assert is_known_default_password(pw)

    @pytest.mark.parametrize("pw", ["testpass", "S0me-Unique-Passphrase!", ""])
    def test_other_passwords_allowed(self, pw):
        assert not is_known_default_password(pw)


class TestIsProduction:
    def test_default_is_production(self, clean_env):
        assert is_production()

    @pytest.mark.parametrize("env", ["development", "dev", "test", "TESTING", "local", "ci"])
    def test_non_production_values(self, clean_env, env):
        clean_env.setenv("ENVIRONMENT", env)
        assert not is_production()

    def test_production_value(self, clean_env):
        clean_env.setenv("ENVIRONMENT", "production")
        assert is_production()


class TestBootstrapAdminCredentials:
    def test_production_without_admin_password_fails_fast(self, clean_env):
        with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
            get_bootstrap_admin_credentials()

    def test_non_production_without_admin_password_skips(self, clean_env):
        clean_env.setenv("ENVIRONMENT", "test")
        assert get_bootstrap_admin_credentials() is None

    @pytest.mark.parametrize("env", ["production", "test"])
    def test_known_default_admin_password_rejected(self, clean_env, env):
        clean_env.setenv("ENVIRONMENT", env)
        clean_env.setenv("ADMIN_PASSWORD", "admin123")
        with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
            get_bootstrap_admin_credentials()

    def test_uses_env_values(self, clean_env):
        clean_env.setenv("ADMIN_USERNAME", "opsadmin")
        clean_env.setenv("ADMIN_PASSWORD", "Str0ng-Test-Passphrase")
        clean_env.setenv("ADMIN_EMAIL", "ops@example.com")
        assert get_bootstrap_admin_credentials() == ("opsadmin", "Str0ng-Test-Passphrase", "ops@example.com")

    def test_username_and_email_fall_back(self, clean_env):
        clean_env.setenv("ADMIN_PASSWORD", "Str0ng-Test-Passphrase")
        username, _, email = get_bootstrap_admin_credentials()
        assert username == "admin"
        assert email == "admin@example.com"


def test_blocklist_is_not_empty():
    assert "admin123" in auth_security.KNOWN_DEFAULT_PASSWORDS
