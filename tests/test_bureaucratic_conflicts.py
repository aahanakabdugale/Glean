"""
Tests for simulate_bureaucratic_conflicts MCP tool.
Validates statutory conflict detection, dual-benefit exclusivity, taxpayer bars,
household quota ceiling audits, and self-healing restructuring plans.
"""

import datetime as _dt
import sqlite3
import pytest

import backend.db as glean_db
from backend.tools import (
    add_document,
    add_family_member,
    simulate_bureaucratic_conflicts,
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


def test_empty_db_conflict_simulation(db_conn):
    res = simulate_bureaucratic_conflicts()
    assert "No family members added yet" in res


def test_unknown_member_conflict_simulation(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    res = simulate_bureaucratic_conflicts("UnknownGuy")
    assert "I don't know anyone called UnknownGuy" in res


def test_dual_health_cover_conflict(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "Retired Pensioner")
    res = simulate_bureaucratic_conflicts("Chandler")

    assert "BUREAUCRATIC CONFLICT & RED-TAPE SIMULATION" in res
    assert "CRITICAL EXCLUSION" in res
    assert "Dual Statutory Health Cover Collision" in res
    assert "Ayushman Vay Vandana" in res
    assert "CGHS" in res
    assert "Form-B Option Declaration" in res
    assert "524,000" in res or "5,00,000" in res


def test_taxpayer_disqualification_conflict(db_conn):
    add_family_member("Jace", "son", 1998, "Corporate Taxpayer")
    res = simulate_bureaucratic_conflicts("Jace", target_schemes="apy")

    assert "STATUTORY DISQUALIFICATION" in res
    assert "PFRDA Income-Tax Payer Bar" in res
    assert "Atal Pension Yojana" in res
    assert "National Pension System" in res or "PPF" in res


def test_girl_child_quota_breach(db_conn):
    add_family_member("Priya", "daughter", 2018, "student")
    add_family_member("Rhea", "daughter", 2020, "child")
    add_family_member("Ananya", "daughter", 2023, "infant")

    res = simulate_bureaucratic_conflicts("all", target_schemes="ssy")

    assert "HOUSEHOLD QUOTA BREACH" in res
    assert "Sukanya Samriddhi Yojana" in res
    assert "Maximum of two accounts permitted" in res
    assert "Public Provident Fund" in res or "PPF" in res


def test_means_testing_ignoaps_conflict(db_conn):
    add_family_member("Amy", "grandmother", 1955, "retired")  # Age 71, not marked BPL
    res = simulate_bureaucratic_conflicts("Amy", target_schemes="ignoaps_mh")

    assert "MEANS-TESTING COLLISION" in res
    assert "IGNOAPS" in res or "Indira Gandhi" in res
    assert "BPL certification is mandatory" in res


def test_clean_family_simulation(db_conn):
    add_family_member("Sunita", "mother", 1985, "homemaker")  # Non-taxpayer, age 41
    res = simulate_bureaucratic_conflicts("Sunita", target_schemes="scss")

    assert "CLEAN SCRUTINY PATH (0 CONFLICTS)" in res
    assert "No mutual exclusivity violations" in res


def test_security_sanitization(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    res = simulate_bureaucratic_conflicts("Justin; DROP TABLE tasks; --")
    assert "reserved words" in res or "not allowed" in res


def test_us_medicare_hsa_conflict(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "employed with HSA")
    res = simulate_bureaucratic_conflicts("Chandler", target_schemes="us_medicare")
    assert "STATUTORY TAX PENALTY COLLISION" in res
    assert "IRS Medicare-HSA Contribution Bar" in res
    assert "Medicare (Parts A & B) vs. Health Savings Account (HSA)" in res
    assert "6% excise penalty" in res

