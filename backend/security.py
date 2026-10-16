"""
glean/security.py — reusable security helpers for the Glean MCP server.

Three public functions:
  validate_token(headers)               → (ok: bool, error: str | None)
  validate_origin(origin, allowed)      → (ok: bool, error: str | None)
  sanitize_input(text, max_len)         → str  (raises ValueError on rejection)

Environment variables:
  GLEAN_ACCESS_TOKEN   If set, every request must carry a matching Bearer token
                       or ?token= query parameter.  When unset the guard is a
                       no-op (dev mode).
"""

from __future__ import annotations

import fnmatch
import os
import re

# ---------------------------------------------------------------------------
# PII patterns that must never appear in free-text inputs
# ---------------------------------------------------------------------------

# 12-digit Aadhaar (spaces or hyphens every 4 digits are also caught)
_AADHAAR_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# Indian passport: one letter + 7 digits  (e.g. A1234567)
_PASSPORT_RE = re.compile(r"\b[A-Z]\d{7}\b", re.IGNORECASE)

# PAN card: 5 letters + 4 digits + 1 letter  (e.g. ABCDE1234F)
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)

# Voter ID (EPIC): 3 letters + 7 digits  (e.g. ABC1234567)
_VOTER_ID_RE = re.compile(r"\b[A-Z]{3}\d{7}\b", re.IGNORECASE)

_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Aadhaar number", _AADHAAR_RE),
    ("passport number", _PASSPORT_RE),
    ("PAN number", _PAN_RE),
    ("voter ID", _VOTER_ID_RE),
]

# Default maximum length for any single input field
_DEFAULT_MAX_LEN = 500

# Characters that could form a SQL injection attempt; we reject rather than escape
# because every DB call already uses parameterised queries — this is a belt-and-
# braces check for inputs that become part of constructed strings (e.g. log lines).
_SQL_INJECTION_RE = re.compile(
    r"(--|;|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b|\bUNION\b|\bEXEC\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

def validate_token(
    headers: dict[str, str],
    query_params: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Check a Bearer token or ?token= query parameter against GLEAN_ACCESS_TOKEN.

    Returns (True, None) when:
      - GLEAN_ACCESS_TOKEN is not set (dev / open mode).
      - The token in the request matches GLEAN_ACCESS_TOKEN.

    Returns (False, reason) otherwise.

    Args:
        headers:      HTTP headers dict (case-insensitive lookup attempted for
                      'Authorization').
        query_params: Optional dict of parsed query string parameters.
    """
    expected = os.environ.get("GLEAN_ACCESS_TOKEN", "").strip()
    if not expected:
        # Guard is disabled in dev mode.
        return True, None

    # Accept header keys with any casing.
    auth_header = ""
    for key, value in (headers or {}).items():
        if key.lower() == "authorization":
            auth_header = value.strip()
            break

    provided = ""
    if auth_header.lower().startswith("bearer "):
        provided = auth_header[7:].strip()
    elif query_params:
        provided = (query_params.get("token") or "").strip()

    if not provided:
        return False, "Missing access token."

    # Use a constant-time comparison to avoid timing attacks.
    import hmac
    if hmac.compare_digest(provided, expected):
        return True, None

    return False, "Invalid access token."


# ---------------------------------------------------------------------------
# Origin validation
# ---------------------------------------------------------------------------

#: Default set of allowed origin patterns (glob-style).
DEFAULT_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:*",
    "http://127.0.0.1:*",
    "https://localhost:*",
    "https://127.0.0.1:*",
]


def validate_origin(
    origin: str | None,
    allowed_origins: list[str] | None = None,
) -> tuple[bool, str | None]:
    """Check that an HTTP Origin header is in the allowed list.

    Patterns are matched with ``fnmatch`` so ``http://localhost:*`` accepts
    any port.  An absent or empty Origin header is allowed (non-browser
    clients such as the MCP inspector and CLI tools do not send one).

    Returns (True, None) if allowed, (False, reason) if blocked.

    Args:
        origin:          Value of the HTTP Origin header, or None / "".
        allowed_origins: List of glob patterns.  Defaults to
                         DEFAULT_ALLOWED_ORIGINS when omitted.
    """
    if not origin:
        # No Origin header → not a cross-origin browser request → allow.
        return True, None

    patterns = allowed_origins if allowed_origins is not None else DEFAULT_ALLOWED_ORIGINS

    for pattern in patterns:
        if fnmatch.fnmatch(origin, pattern):
            return True, None

    return False, f"Origin '{origin}' is not allowed."


# ---------------------------------------------------------------------------
# Input sanitisation
# ---------------------------------------------------------------------------

def sanitize_input(text: str, max_len: int = _DEFAULT_MAX_LEN) -> str:
    """Clean and validate a free-text input field.

    Steps (in order):
      1. Strip leading/trailing whitespace.
      2. Reject if longer than *max_len* characters.
      3. Reject if it contains a recognisable PII pattern
         (Aadhaar, passport, PAN, voter ID).
      4. Reject if it contains SQL injection keywords / syntax.
      5. Return the stripped text.

    Raises:
        ValueError: with a user-friendly message on any rejection.

    Args:
        text:    The raw input string to check.
        max_len: Maximum allowed character count (default 500).
    """
    if not isinstance(text, str):
        raise ValueError("Input must be text.")

    text = text.strip()

    if len(text) > max_len:
        raise ValueError(
            f"Input is too long ({len(text)} characters). "
            f"Please keep it under {max_len} characters."
        )

    for label, pattern in _PII_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                f"Please do not include a {label} in this field. "
                "Glean never stores identity document numbers."
            )

    if _SQL_INJECTION_RE.search(text):
        raise ValueError("Input contains reserved words that are not allowed.")

    return text
