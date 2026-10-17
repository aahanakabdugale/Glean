"""
Tests for audit_document_dependencies MCP tool.
Validates dependency graphs, blocker cascade detection, impending expiry risks,
and critical path resolution sequencing.
"""

import datetime as _dt
import sqlite3
import pytest

import backend.db as glean_db
from backend.tools import (
    add_document,
    add_family_member,
    audit_document_dependencies,
)


@pytest.fixture
def db_conn(monkeypatch):
    """In-memory SQLite DB fixture isolated for each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)

    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)
    yield conn


def test_empty_family_audit(db_conn):
    res = audit_document_dependencies()
    assert "No family members added yet" in res


def test_unknown_member_audit(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    res = audit_document_dependencies("NonexistentMember")
    assert "I don't know anyone called NonexistentMember" in res


def test_clean_dependency_path(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    today = _dt.date.today()
    # Add valid documents far in future
    future_date = (today + _dt.timedelta(days=400)).isoformat()
    add_document("Aadhaar card", "Chandler", future_date)
    add_document("PAN card", "Chandler", future_date)
    add_document("Passport", "Chandler", future_date)

    res = audit_document_dependencies("Chandler")
    assert "DOCUMENT DEPENDENCY & BOTTLENECK AUDIT" in res
    assert "0 Critical Blocker" in res
    assert "🟢 READY: All prerequisite docs valid" in res
    assert "CRITICAL PATH RESOLUTION SEQUENCE" in res
    assert "All family documents are in order" in res


def test_critical_blocker_detection(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    today = _dt.date.today()
    # Add expired Aadhaar
    past_date = (today - _dt.timedelta(days=10)).isoformat()
    add_document("Aadhaar card", "Chandler", past_date)

    res = audit_document_dependencies("Chandler")
    assert "1 Critical Blocker" in res
    assert "🛑 BLOCKER:" in res
    assert "blocks" in res
    assert "Step 1 [CRITICAL]: Renew Chandler's Aadhaar card immediately" in res
    assert "SPOKEN BRIEF" in res
    assert "Attention: Chandler's Aadhaar card is expired" in res


def test_impending_risk_detection(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    today = _dt.date.today()
    # Add document expiring in 15 days
    near_future = (today + _dt.timedelta(days=15)).isoformat()
    add_document("Aadhaar card", "Chandler", near_future)

    res = audit_document_dependencies("Chandler")
    assert "1 Impending Risk" in res
    assert "⚠️ RISK:" in res
    assert "expires in 15d" in res
    assert "jeopardizes" in res
    assert "[HIGH]: Schedule renewal for Chandler's Aadhaar card (15d left)" in res
    assert "SPOKEN BRIEF" in res
    assert "Heads up: Chandler's Aadhaar card expires in 15 days" in res


def test_whole_family_audit_synthesis(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    add_family_member("Justin", "father", 1968, "employed")
    today = _dt.date.today()

    add_document("Passport", "Chandler", (today - _dt.timedelta(days=5)).isoformat())
    add_document("Aadhaar card", "Justin", (today + _dt.timedelta(days=300)).isoformat())

    res = audit_document_dependencies("all")
    assert "Audited: 2 Member(s)" in res
    assert "Chandler" in res
    assert "Justin" in res
    assert "🛑 BLOCKER: Passport expired 5d ago" in res


def test_security_sanitization(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    res = audit_document_dependencies("Chandler; DROP TABLE family_members; --")
    assert "reserved words" in res or "not allowed" in res
