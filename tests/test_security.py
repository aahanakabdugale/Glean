"""
tests/test_security.py — unit tests for glean/security.py

Covers:
  - validate_token: dev mode (no env var), valid token, invalid token,
    missing token, Bearer header, query-param fallback.
  - validate_origin: absent origin, allowed localhost origins, blocked
    external origins, custom pattern list.
  - sanitize_input: clean text, length limit, Aadhaar, passport, PAN,
    voter ID detection, SQL injection keywords, whitespace stripping.
"""

import os

import pytest

from glean.security import (
    DEFAULT_ALLOWED_ORIGINS,
    sanitize_input,
    validate_origin,
    validate_token,
)


# ===========================================================================
# validate_token
# ===========================================================================


class TestValidateTokenDevMode:
    """When GLEAN_ACCESS_TOKEN is not set the guard is a no-op."""

    def test_no_env_var_no_headers_is_ok(self, monkeypatch):
        monkeypatch.delenv("GLEAN_ACCESS_TOKEN", raising=False)
        ok, err = validate_token({})
        assert ok is True
        assert err is None

    def test_no_env_var_any_headers_is_ok(self, monkeypatch):
        monkeypatch.delenv("GLEAN_ACCESS_TOKEN", raising=False)
        ok, err = validate_token({"Authorization": "Bearer anything"})
        assert ok is True

    def test_empty_env_var_is_dev_mode(self, monkeypatch):
        monkeypatch.setenv("GLEAN_ACCESS_TOKEN", "")
        ok, err = validate_token({})
        assert ok is True


class TestValidateTokenProdMode:
    """When GLEAN_ACCESS_TOKEN is set the token must match."""

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("GLEAN_ACCESS_TOKEN", "secret-token-123")

    def test_correct_bearer_token_accepted(self):
        ok, err = validate_token({"Authorization": "Bearer secret-token-123"})
        assert ok is True
        assert err is None

    def test_wrong_bearer_token_rejected(self):
        ok, err = validate_token({"Authorization": "Bearer wrong-token"})
        assert ok is False
        assert "Invalid" in err

    def test_missing_auth_header_rejected(self):
        ok, err = validate_token({})
        assert ok is False
        assert "Missing" in err

    def test_bearer_prefix_case_insensitive(self):
        # Header key casing varies by framework; our loop handles it.
        ok, err = validate_token({"authorization": "Bearer secret-token-123"})
        assert ok is True

    def test_query_param_fallback_accepted(self):
        ok, err = validate_token({}, query_params={"token": "secret-token-123"})
        assert ok is True

    def test_query_param_wrong_value_rejected(self):
        ok, err = validate_token({}, query_params={"token": "bad"})
        assert ok is False

    def test_bearer_takes_priority_over_query_param(self):
        # Header is correct, query param is wrong — header should win.
        ok, err = validate_token(
            {"Authorization": "Bearer secret-token-123"},
            query_params={"token": "wrong"},
        )
        assert ok is True

    def test_empty_bearer_value_rejected(self):
        ok, err = validate_token({"Authorization": "Bearer "})
        assert ok is False

    def test_non_bearer_scheme_is_treated_as_missing(self):
        ok, err = validate_token({"Authorization": "Basic abc123"})
        assert ok is False
        assert "Missing" in err


# ===========================================================================
# validate_origin
# ===========================================================================


class TestValidateOriginAbsent:
    def test_none_origin_allowed(self):
        ok, err = validate_origin(None)
        assert ok is True

    def test_empty_string_origin_allowed(self):
        ok, err = validate_origin("")
        assert ok is True


class TestValidateOriginDefaultPatterns:
    def test_localhost_http_allowed(self):
        ok, _ = validate_origin("http://localhost:3000")
        assert ok is True

    def test_localhost_https_allowed(self):
        ok, _ = validate_origin("https://localhost:443")
        assert ok is True

    def test_loopback_http_allowed(self):
        ok, _ = validate_origin("http://127.0.0.1:8080")
        assert ok is True

    def test_loopback_https_allowed(self):
        ok, _ = validate_origin("https://127.0.0.1:8000")
        assert ok is True

    def test_external_domain_blocked(self):
        ok, err = validate_origin("https://evil.example.com")
        assert ok is False
        assert "not allowed" in err

    def test_external_http_blocked(self):
        ok, err = validate_origin("http://192.168.1.50:3000")
        assert ok is False

    def test_empty_pattern_list_blocks_all_origins(self):
        ok, err = validate_origin("http://localhost:3000", allowed_origins=[])
        assert ok is False

    def test_wildcard_custom_pattern(self):
        ok, _ = validate_origin(
            "https://myapp.example.com",
            allowed_origins=["https://myapp.example.com"],
        )
        assert ok is True

    def test_subdomain_not_matched_by_localhost_pattern(self):
        # "http://localhost.evil.com:80" must NOT match "http://localhost:*"
        ok, _ = validate_origin("http://localhost.evil.com:80")
        assert ok is False

    def test_error_message_includes_origin(self):
        _, err = validate_origin("https://bad.example.com")
        assert "bad.example.com" in err


# ===========================================================================
# sanitize_input
# ===========================================================================


class TestSanitizeInputHappyPath:
    def test_clean_text_returned(self):
        assert sanitize_input("Renew passport") == "Renew passport"

    def test_whitespace_stripped(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_normal_name_accepted(self):
        assert sanitize_input("Priya Sharma") == "Priya Sharma"

    def test_unicode_accepted(self):
        assert sanitize_input("प्रिया") == "प्रिया"

    def test_empty_string_accepted(self):
        assert sanitize_input("") == ""


class TestSanitizeInputLengthLimit:
    def test_exactly_at_limit_accepted(self):
        text = "a" * 500
        assert sanitize_input(text) == text

    def test_one_over_limit_rejected(self):
        with pytest.raises(ValueError, match="too long"):
            sanitize_input("a" * 501)

    def test_custom_max_len_respected(self):
        with pytest.raises(ValueError):
            sanitize_input("hello world", max_len=5)

    def test_custom_max_len_at_boundary_accepted(self):
        assert sanitize_input("hello", max_len=5) == "hello"


class TestSanitizeInputPIIRejection:
    def test_aadhaar_plain_digits_rejected(self):
        with pytest.raises(ValueError, match="Aadhaar"):
            sanitize_input("My Aadhaar is 1234 5678 9012")

    def test_aadhaar_hyphen_separated_rejected(self):
        with pytest.raises(ValueError, match="Aadhaar"):
            sanitize_input("1234-5678-9012")

    def test_aadhaar_no_spaces_rejected(self):
        with pytest.raises(ValueError, match="Aadhaar"):
            sanitize_input("123456789012")

    def test_passport_number_rejected(self):
        with pytest.raises(ValueError, match="passport"):
            sanitize_input("Passport A1234567 expires next year")

    def test_pan_number_rejected(self):
        with pytest.raises(ValueError, match="PAN"):
            sanitize_input("My PAN is ABCDE1234F")

    def test_voter_id_rejected(self):
        with pytest.raises(ValueError, match="voter"):
            sanitize_input("Voter ID: ABC1234567")

    def test_normal_text_with_numbers_accepted(self):
        # "Flat 12, Block 34" should not trigger Aadhaar (not 12 digits)
        assert sanitize_input("Flat 12, Block 34, Mumbai") == "Flat 12, Block 34, Mumbai"

    def test_short_digit_sequence_accepted(self):
        assert sanitize_input("born in 1985") == "born in 1985"


class TestSanitizeInputSQLInjection:
    def test_drop_table_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("'; DROP TABLE family_members; --")

    def test_select_keyword_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("SELECT * FROM users")

    def test_union_keyword_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("1 UNION SELECT password FROM accounts")

    def test_double_dash_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("admin'--")

    def test_semicolon_alone_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("title; second statement")

    def test_exec_keyword_rejected(self):
        with pytest.raises(ValueError, match="reserved"):
            sanitize_input("EXEC xp_cmdshell('dir')")

    def test_normal_text_with_select_substring_safe(self):
        # "selection" contains "select" as substring — should still be rejected
        # because our regex uses \b word boundary before SELECT.
        # "selection" does NOT match \bSELECT\b so it must be accepted.
        result = sanitize_input("My document selection is ready")
        assert result == "My document selection is ready"

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="text"):
            sanitize_input(123)  # type: ignore[arg-type]
