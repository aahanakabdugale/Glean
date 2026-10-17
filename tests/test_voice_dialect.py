import pytest
import sqlite3
import backend.db as glean_db
from backend import tools


@pytest.fixture
def db_conn(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)
    monkeypatch.setattr(glean_db, "get_connection", lambda: conn)
    return conn


def test_explain_for_grandparent(db_conn):
    res = tools.explain_for_generation("scss", "grandparent")
    assert "CROSS-GENERATIONAL VOICE DIALECT ENGINE" in res
    assert "Grandparent" in res
    assert "Warm & Reassuring (Zero Bureaucracy)" in res
    assert "piggy bank" in res or "piggy-bank" in res
    assert "0%" in res
    assert "Grade 4" in res


def test_explain_for_parent(db_conn):
    res = tools.explain_for_generation("scss", "parent")
    assert "Parent (Working Adult / Family Planner)" in res
    assert "Section 80C" in res
    assert "8.2%" in res
    assert "Financial Optimization" in res


def test_explain_for_young_adult(db_conn):
    res = tools.explain_for_generation("scss", "student")
    assert "Young Adult" in res
    assert "Tech-First" in res
    assert "8.2%" in res


def test_explain_ayushman_dialects(db_conn):
    res_grand = tools.explain_for_generation("ayushman_vay_vandana", "senior")
    assert "golden health shield" in res_grand or "Dadaji" in res_grand
    assert "5 lakh" in res_grand or "₹5,00,000" in res_grand

    res_youth = tools.explain_for_generation("ayushman_vay_vandana", "young_adult")
    assert "Ayushman app" in res_youth or "DigiLocker" in res_youth or "OTP" in res_youth


def test_explain_apy_dialects(db_conn):
    res_youth = tools.explain_for_generation("apy", "college student")
    assert "Young Adult" in res_youth
    assert "auto-debit" in res_youth


def test_unknown_scheme_error(db_conn):
    res = tools.explain_for_generation("super_secret_fake_scheme", "grandparent")
    assert "Unknown scheme" in res
    assert "Available schemes are:" in res


def test_empty_scheme_error(db_conn):
    res = tools.explain_for_generation("", "grandparent")
    assert "Please specify a scheme" in res


def test_security_sanitization(db_conn):
    res = tools.explain_for_generation("scss; DROP TABLE schemes;", "grandparent")
    assert "reserved words" in res.lower() or "not allowed" in res.lower() or "invalid" in res.lower()
