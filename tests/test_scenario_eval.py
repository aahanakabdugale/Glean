"""
Scenario Evaluation Suite for Glean
Evaluates 12 realistic multi-generational family scenarios across:
- Scheme routing & temporal eligibility
- Document expiration & deadline tracking
- Multi-step application task generation
- Security & PII guardrails
- Whole-family dashboard aggregation
"""

from datetime import date, timedelta
import sqlite3
import pytest

import glean.db as glean_db
from glean import schemes
from glean.security import sanitize_input
from glean.tools import (
    add_document,
    add_family_member,
    add_task,
    check_scheme_eligibility,
    family_brief,
    get_expiring_documents,
    get_family_dashboard,
    get_scheme_checklist,
    list_family_members,
    list_upcoming_tasks,
    plan_scheme_application,
)

TODAY = date(2026, 10, 6)


@pytest.fixture
def db_conn(monkeypatch):
    """Isolated in-memory database with foreign keys enabled."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)
    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)
    yield conn


# ---------------------------------------------------------------------------
# Scenario 1: Super Senior Health Coverage (Grandpa Chandler, Age 76)
# ---------------------------------------------------------------------------
def test_scenario_01_super_senior_health_coverage(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    result = check_scheme_eligibility("Chandler")

    # Must qualify for Ayushman 70+ and SCSS
    assert "May be eligible:" in result
    assert "Ayushman Vay Vandana Card" in result
    assert "Senior Citizens Savings Scheme" in result

    # Must be ineligible for APY (age 76 > 40)
    assert "Not eligible:" in result
    assert "Atal Pension Yojana" in result
    assert "Guidance only" in result


# ---------------------------------------------------------------------------
# Scenario 2: Low-Income Senior Pension Check (Grandma with BPL)
# ---------------------------------------------------------------------------
def test_scenario_02_low_income_senior_pension(db_conn):
    add_family_member("Amy", "grandmother", 1958, "retired")

    # Without BPL tag: must ask for verification
    unconfirmed = check_scheme_eligibility("Amy")
    assert "Requires verification:" in unconfirmed
    assert "needs: bpl" in unconfirmed

    # With BPL tag confirmed: must be eligible
    confirmed = check_scheme_eligibility("Amy", tags="bpl")
    assert "May be eligible:" in confirmed
    assert "Indira Gandhi National Old Age Pension Scheme" in confirmed


# ---------------------------------------------------------------------------
# Scenario 3: Temporal Eligibility / "Almost Eligible" (Father Justin, Age 58)
# ---------------------------------------------------------------------------
def test_scenario_03_temporal_eligibility_almost_eligible(db_conn):
    add_family_member("Justin", "father", 1968, "employed")
    result = check_scheme_eligibility("Justin")

    # SCSS min_age 60, current age 58 (2 years away, within 3-year window)
    assert "Coming up soon:" in result
    assert "Senior Citizens Savings Scheme" in result
    assert "may qualify around 2028" in result
    assert "Suggested: Check eligibility for Senior Citizens Savings Scheme (around 2028)" in result


# ---------------------------------------------------------------------------
# Scenario 4: Working Mother Insurance Audit (Mother Riley, Age 54)
# ---------------------------------------------------------------------------
def test_scenario_04_working_mother_insurance_audit(db_conn):
    add_family_member("Riley", "mother", 1972, "employed")
    result = check_scheme_eligibility("Riley", tags="bank_account")

    # PMSBY (18-70): eligible
    assert "May be eligible:" in result
    assert "Pradhan Mantri Suraksha Bima Yojana (PMSBY)" in result

    # PMJJBY (18-50): age 54 > 50 -> not eligible
    assert "Not eligible:" in result
    assert "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)" in result


# ---------------------------------------------------------------------------
# Scenario 5: Young Adult Pension & Life Cover (Son Jace, Age 26)
# ---------------------------------------------------------------------------
def test_scenario_05_young_adult_benefits(db_conn):
    add_family_member("Jace", "son", 2000, "employed")
    result = check_scheme_eligibility("Jace", tags="bank_account")

    # Matches APY, PMJJBY, and PMSBY
    assert "Atal Pension Yojana" in result
    assert "Pradhan Mantri Jeevan Jyoti Bima Yojana" in result
    assert "Pradhan Mantri Suraksha Bima Yojana" in result

    # Adding income_tax_payer tag immediately blocks APY
    tax_result = check_scheme_eligibility("Jace", tags="bank_account,income_tax_payer")
    lines = tax_result.split("\n")
    not_el_idx = next(i for i, l in enumerate(lines) if "Not eligible:" in l)
    not_el_text = "\n".join(lines[not_el_idx:])
    assert "Atal Pension Yojana" in not_el_text


# ---------------------------------------------------------------------------
# Scenario 6: Girl Child Education & Savings (Young Daughter, Age 6)
# ---------------------------------------------------------------------------
def test_scenario_06_girl_child_savings(db_conn):
    add_family_member("Tara", "daughter", 2020, "child")

    # With girl_child tag: eligible for Sukanya Samriddhi Yojana (SSY)
    result = check_scheme_eligibility("Tara", tags="girl_child")
    assert "May be eligible:" in result
    assert "Sukanya Samriddhi Yojana (SSY)" in result

    # Document checklist for SSY
    checklist = get_scheme_checklist("ssy")
    assert "Birth certificate of the girl child" in checklist
    assert "Identity proof of parent/guardian" in checklist


# ---------------------------------------------------------------------------
# Scenario 7: Rural / Agricultural Household Support (Farmer Uncle, Age 42)
# ---------------------------------------------------------------------------
def test_scenario_07_rural_farmer_support(db_conn):
    add_family_member("Mukesh", "uncle", 1984, "farmer")

    # Eligible with farmer tag
    result = check_scheme_eligibility("Mukesh", tags="farmer")
    assert "May be eligible:" in result
    assert "PM Kisan Samman Nidhi" in result

    # Excluded if tax payer
    excluded = check_scheme_eligibility("Mukesh", tags="farmer,income_tax_payer")
    lines = excluded.split("\n")
    not_el_idx = next(i for i, l in enumerate(lines) if "Not eligible:" in l)
    not_el_text = "\n".join(lines[not_el_idx:])
    assert "PM Kisan Samman Nidhi" in not_el_text


# ---------------------------------------------------------------------------
# Scenario 8: Urgent Passport Expiry & Renewal Alert (Emergency Paperwork)
# ---------------------------------------------------------------------------
def test_scenario_08_urgent_document_expiry_alert(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")

    # Add passport expiring in 5 days
    exp_date = (date.today() + timedelta(days=5)).isoformat()
    add_document("Passport", "Chandler", exp_date)

    # get_expiring_documents must flag urgency
    exp_output = get_expiring_documents(days=30)
    assert "Chandler's Passport" in exp_output
    assert "URGENT" in exp_output

    # family_brief must include urgent documents count
    brief = family_brief("Chandler")
    assert "Your Expiring Documents" in brief
    assert "Passport" in brief


# ---------------------------------------------------------------------------
# Scenario 9: Overdue Task Tracking & Deadline Escalation
# ---------------------------------------------------------------------------
def test_scenario_09_overdue_task_tracking(db_conn):
    add_family_member("Justin", "father", 1968, "employed")

    # Past task (overdue)
    past_due = (date.today() - timedelta(days=3)).isoformat()
    add_task("Renew car insurance", past_due, "Justin")

    # Today task
    add_task("Submit medical reimbursement", date.today().isoformat(), "Justin")

    # Future task
    future_due = (date.today() + timedelta(days=10)).isoformat()
    add_task("Dentist checkup", future_due, "Justin")

    tasks_output = list_upcoming_tasks(days=30)
    assert "OVERDUE by 3 days" in tasks_output
    assert "due today" in tasks_output
    assert "10 days left" in tasks_output


# ---------------------------------------------------------------------------
# Scenario 10: Multi-Step Scheme Application Planning
# ---------------------------------------------------------------------------
def test_scenario_10_scheme_application_planning(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")

    plan_output = plan_scheme_application("Chandler", "scss", days_to_prepare=5)
    assert "Application plan created for Chandler — Senior Citizens Savings Scheme" in plan_output
    assert "Task 1 created: Gather documents" in plan_output
    assert "Task 2 created: Submit application" in plan_output
    assert "Official portal:" in plan_output

    # Verify tasks actually written to database
    tasks = db_conn.execute("SELECT title, due_date FROM tasks ORDER BY due_date").fetchall()
    assert len(tasks) == 2
    assert "Gather docs" in tasks[0]["title"]
    assert "Submit application" in tasks[1]["title"]


# ---------------------------------------------------------------------------
# Scenario 11: Security & Privacy Guardrails (Aadhaar & Injection Rejection)
# ---------------------------------------------------------------------------
def test_scenario_11_security_and_privacy_guardrails():
    # 1. 12-digit Aadhaar pattern must be rejected with ValueError
    with pytest.raises(ValueError, match="Aadhaar"):
        sanitize_input("My Aadhaar number is 1234 5678 9012")

    # 2. SQL injection pattern must be rejected with ValueError
    with pytest.raises(ValueError, match="reserved words"):
        sanitize_input("DROP TABLE family_members; SELECT * FROM tasks")

    # 3. Legitimate numbers and text must NOT be falsely rejected
    safe_text = sanitize_input("Born in 1968, document selection completed")
    assert safe_text == "Born in 1968, document selection completed"


# ---------------------------------------------------------------------------
# Scenario 12: Whole-Family Admin Dashboard & Roster Synthesis
# ---------------------------------------------------------------------------
def test_scenario_12_whole_family_dashboard_synthesis(db_conn):
    add_family_member("Chandler", "grandfather", 1950, "retired")
    add_family_member("Amy", "grandmother", 1953, "retired")
    add_family_member("Justin", "father", 1968, "employed")

    # Add doc and task
    exp = (date.today() + timedelta(days=20)).isoformat()
    add_document("Health Card", "Chandler", exp)
    add_task("Review health policy", exp, "Chandler")

    dashboard = get_family_dashboard()
    assert "FAMILY ADMIN DASHBOARD (3 Members Tracked)" in dashboard
    assert "Documents: 1 tracked" in dashboard
    assert "Tasks: 1 pending" in dashboard
    assert "FAMILY ROSTER" in dashboard
    assert "Chandler (grandfather)" in dashboard
    assert "BENEFIT OPPORTUNITIES" in dashboard
    assert "Guidance only" in dashboard
