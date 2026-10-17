"""
Tests for orchestrate_life_event MCP tool.
Validates agentic multi-step planning, document audits, scheme cross-referencing,
phased task generation, and status progression.
"""

import datetime as _dt
import sqlite3
import pytest

import backend.db as glean_db
from backend.tools import (
    add_document,
    add_family_member,
    orchestrate_life_event,
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


def test_empty_member_name(db_conn):
    res = orchestrate_life_event("", "retirement")
    assert "Please provide a family member's name." in res


def test_empty_event_type(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    res = orchestrate_life_event("Chandler", "   ")
    assert "Please specify a life event" in res


def test_unknown_member(db_conn):
    res = orchestrate_life_event("UnknownPerson", "retirement")
    assert "I don't know anyone called UnknownPerson" in res


def test_unsupported_event(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    res = orchestrate_life_event("Chandler", "space_travel")
    assert "Supported life events are" in res


def test_retirement_orchestration(db_conn):
    add_family_member("Justin", "father", 1963, "employed")
    add_document("Aadhaar card", "Justin", "2030-01-01")

    res = orchestrate_life_event("Justin", "retirement")

    assert "Life-Event Roadmap Orchestrated: Retirement & Senior Transition" in res
    assert "employed ➔ Retired Senior" in res
    assert "In Vault: Aadhaar card" in res
    assert "Action Required (Missing):" in res
    assert "Senior Citizens Savings Scheme" in res or "SCSS" in res

    # Verify tasks created in DB
    tasks = db_conn.execute("SELECT * FROM tasks WHERE member_id = (SELECT id FROM family_members WHERE name='Justin')").fetchall()
    assert len(tasks) == 4
    titles = [t["title"] for t in tasks]
    assert any("pension papers" in t.lower() for t in titles)
    assert any("senior citizens savings scheme" in t.lower() for t in titles)

    # Verify member status updated in DB
    m = db_conn.execute("SELECT status FROM family_members WHERE name='Justin'").fetchone()
    assert m["status"] == "Retired Senior"


def test_adulthood_orchestration(db_conn):
    add_family_member("Jace", "son", 2008, "student")
    add_document("Aadhaar card", "Jace", "2032-05-15")

    res = orchestrate_life_event("Jace", "adulthood")

    assert "Adulthood & Independence" in res
    assert "student ➔ Young Adult" in res
    assert "Voter ID" in res
    assert "Atal Pension Yojana" in res

    # Verify tasks
    tasks = db_conn.execute("SELECT * FROM tasks WHERE member_id = (SELECT id FROM family_members WHERE name='Jace')").fetchall()
    assert len(tasks) == 3
    titles = [t["title"] for t in tasks]
    assert any("voter id" in t.lower() for t in titles)
    assert any("savings bank account" in t.lower() for t in titles)


def test_newborn_orchestration(db_conn):
    add_family_member("Ananya", "daughter", 2026, "newborn")

    res = orchestrate_life_event("Ananya", "birth")

    assert "Newborn & Early Childcare" in res
    assert "Municipal Birth Certificate" in res
    assert "Baal Aadhaar" in res

    tasks = db_conn.execute("SELECT * FROM tasks WHERE member_id = (SELECT id FROM family_members WHERE name='Ananya')").fetchall()
    assert len(tasks) == 3
    titles = [t["title"] for t in tasks]
    assert any("birth certificate" in t.lower() for t in titles)
    assert any("baal aadhaar" in t.lower() for t in titles)


def test_relocation_orchestration(db_conn):
    add_family_member("Maya", "mother", 1974, "employed")
    add_document("Aadhaar card", "Maya", "2029-12-31")

    res = orchestrate_life_event("Maya", "relocation")

    assert "Household Relocation & Address Transfer" in res
    assert "Aadhaar address update" in res

    tasks = db_conn.execute("SELECT * FROM tasks WHERE member_id = (SELECT id FROM family_members WHERE name='Maya')").fetchall()
    assert len(tasks) == 3


def test_security_sanitization_rejection(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    # Aadhaar number injected in notes
    res = orchestrate_life_event("Chandler", "retirement", notes="My Aadhaar is 1234 5678 9012")
    assert "Aadhaar number" in res or "forbidden pattern" in res
