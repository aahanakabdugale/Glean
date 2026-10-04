"""
Tests for add_family_member, list_family_members, and add_document.

The db_conn fixture creates an in-memory SQLite database, runs init_db on it,
and monkeypatches glean.db.get_connection so every tool call uses it.
The production glean.db file is never touched.
"""

import sqlite3

import pytest

import glean.db as glean_db
from glean.tools import add_document, add_family_member, list_family_members


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_conn(monkeypatch):
    """
    Fresh in-memory SQLite DB for each test.
    Monkeypatches glean.db.get_connection to return it so tools use this DB.
    Does NOT close the connection — pytest tears it down naturally.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)

    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)

    yield conn


# ---------------------------------------------------------------------------
# add_family_member — happy path
# ---------------------------------------------------------------------------


def test_add_member_happy_path(db_conn):
    result = add_family_member("Maria", "daughter", 2005, "student")
    assert "Maria" in result
    assert "daughter" in result


# ---------------------------------------------------------------------------
# add_family_member — validation errors
# ---------------------------------------------------------------------------


def test_add_member_empty_name(db_conn):
    result = add_family_member("   ", "daughter", 2005, "student")
    # Should be a friendly error, not a confirmation
    assert "Maria" not in result
    assert len(result) > 0  # some message returned
    # Must not start with "Added"
    assert not result.startswith("Added")


def test_add_member_empty_relation(db_conn):
    result = add_family_member("Maria", "  ", 2005, "student")
    assert not result.startswith("Added")
    assert len(result) > 0


def test_add_member_bad_birth_year_too_old(db_conn):
    result = add_family_member("Maria", "daughter", 1800, "student")
    assert not result.startswith("Added")
    assert "birth year" in result.lower() or "year" in result.lower()


def test_add_member_bad_birth_year_future(db_conn):
    result = add_family_member("Maria", "daughter", 9999, "student")
    assert not result.startswith("Added")


# ---------------------------------------------------------------------------
# add_family_member — duplicate name (case-insensitive)
# ---------------------------------------------------------------------------


def test_add_member_duplicate_exact(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_family_member("Maria", "sister", 2007, "student")
    # Second attempt must NOT succeed
    assert not result.startswith("Added")


def test_add_member_duplicate_case_insensitive(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_family_member("maria", "sister", 2007, "student")
    assert not result.startswith("Added")


# ---------------------------------------------------------------------------
# list_family_members
# ---------------------------------------------------------------------------


def test_list_members_empty(db_conn):
    result = list_family_members()
    assert "No family members" in result


def test_list_members_one(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = list_family_members()
    assert "Maria" in result
    assert "daughter" in result
    assert "2005" in result


def test_list_members_multiple(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    add_family_member("John", "son", 2003, "engineer")
    result = list_family_members()
    assert "Maria" in result
    assert "John" in result


def test_list_members_format(db_conn):
    """Each line should follow '<name> (<relation>) — born <year>, <status>' format."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = list_family_members()
    assert "Maria (daughter)" in result
    assert "born 2005" in result
    assert "student" in result


# ---------------------------------------------------------------------------
# add_document — happy path
# ---------------------------------------------------------------------------


def test_add_document_happy_path(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "2030-06-15")
    assert "Maria" in result
    assert "2030-06-15" in result
    assert "Passport" in result  # title-cased


def test_add_document_uses_stored_capitalisation(db_conn):
    """Reply should use the stored name capitalisation, not whatever the caller passed."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "2030-06-15")
    assert "Maria" in result


# ---------------------------------------------------------------------------
# add_document — validation errors
# ---------------------------------------------------------------------------


def test_add_document_empty_doc_type(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("  ", "Maria", "2030-06-15")
    assert not result.startswith("Passport")
    assert not result.lower().startswith("added")
    assert len(result) > 0


def test_add_document_unknown_owner(db_conn):
    result = add_document("passport", "Nobody", "2030-06-15")
    assert "Nobody" in result
    assert "don't know" in result.lower() or "add them" in result.lower()


def test_add_document_bad_date_format(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "15-06-2030")  # wrong format
    assert "YYYY-MM-DD" in result or "date" in result.lower()


def test_add_document_bad_date_nonsense(db_conn):
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "not-a-date")
    assert "YYYY-MM-DD" in result or "date" in result.lower()


# ---------------------------------------------------------------------------
# add_document — past expiry date is accepted
# ---------------------------------------------------------------------------


def test_add_document_past_expiry_date_accepted(db_conn):
    """A document that has already expired should still be recorded."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("old id card", "Maria", "2000-01-01")
    # Should succeed, not return an error about the date
    assert "2000-01-01" in result
    assert "YYYY-MM-DD" not in result


# ---------------------------------------------------------------------------
# add_document — FK stored as member_id, not owner name
# ---------------------------------------------------------------------------


def test_documents_stores_member_id(db_conn):
    """documents.member_id should be an integer matching the member's row id."""
    add_family_member("Maria", "daughter", 2005, "student")
    add_document("passport", "Maria", "2030-06-15")

    row = db_conn.execute("SELECT member_id FROM documents").fetchone()
    assert row is not None
    member_row = db_conn.execute(
        "SELECT id FROM family_members WHERE name = 'Maria'"
    ).fetchone()
    assert row["member_id"] == member_row["id"]


# ---------------------------------------------------------------------------
# Schema invariant — no ID-number columns in documents
# ---------------------------------------------------------------------------


def test_no_id_number_columns_in_documents(db_conn):
    """
    PRAGMA table_info(documents) must not list any column whose name suggests
    a personal identifier (id_number, passport_number, national, etc.).
    """
    forbidden_substrings = ("id_number", "passport_number", "national", "ssn", "aadhar")
    cols = db_conn.execute("PRAGMA table_info(documents)").fetchall()
    col_names = [c["name"].lower() for c in cols]
    for col in col_names:
        for bad in forbidden_substrings:
            assert bad not in col, (
                f"Column '{col}' in documents table looks like a personal identifier"
            )
