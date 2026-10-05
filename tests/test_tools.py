"""
Tests for add_family_member, list_family_members, add_document,
and get_expiring_documents.

The db_conn fixture creates an in-memory SQLite database, runs init_db on it,
and monkeypatches glean.db.get_connection so every tool call uses it.
The production glean.db file is never touched.
"""

import datetime as _dt
import sqlite3

import pytest

import glean.db as glean_db
from glean.tools import (
    add_document,
    add_family_member,
    get_expiring_documents,
    list_family_members,
)


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
# Helpers
# ---------------------------------------------------------------------------


def _member_count(conn):
    return conn.execute("SELECT COUNT(*) FROM family_members").fetchone()[0]


def _document_count(conn):
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


def _get_member(conn, name):
    return conn.execute(
        "SELECT * FROM family_members WHERE name = ?", (name,)
    ).fetchone()


def _get_document(conn, owner_name, doc_type):
    return conn.execute(
        "SELECT d.* FROM documents d "
        "JOIN family_members m ON m.id = d.member_id "
        "WHERE m.name = ? AND d.doc_type = ?",
        (owner_name, doc_type),
    ).fetchone()


# ---------------------------------------------------------------------------
# add_family_member — happy path
# ---------------------------------------------------------------------------


def test_add_member_happy_path(db_conn):
    """Success returns the exact confirmation string and saves the row."""
    result = add_family_member("Maria", "daughter", 2005, "student")
    assert result == "Added Maria (daughter)."

    row = _get_member(db_conn, "Maria")
    assert row is not None
    assert row["relation"] == "daughter"
    assert row["birth_year"] == 2005
    assert row["status"] == "student"


# ---------------------------------------------------------------------------
# add_family_member — validation errors
# ---------------------------------------------------------------------------


def test_add_member_empty_name(db_conn):
    """Blank name returns the exact validation message; no row is saved."""
    result = add_family_member("   ", "daughter", 2005, "student")
    assert result == "Please provide a name."
    assert _member_count(db_conn) == 0


def test_add_member_empty_relation(db_conn):
    """Blank relation returns the exact validation message; no row is saved."""
    result = add_family_member("Maria", "  ", 2005, "student")
    assert result == "Please tell me how they are related to you."
    assert _member_count(db_conn) == 0


def test_add_member_bad_birth_year_too_old(db_conn):
    """A birth year before 1900 returns the exact validation message; no row is saved."""
    result = add_family_member("Maria", "daughter", 1800, "student")
    assert result == "That birth year doesn't look right."
    assert _member_count(db_conn) == 0


def test_add_member_bad_birth_year_future(db_conn):
    """A birth year far in the future returns the exact validation message; no row is saved."""
    result = add_family_member("Maria", "daughter", 9999, "student")
    assert result == "That birth year doesn't look right."
    assert _member_count(db_conn) == 0


# ---------------------------------------------------------------------------
# add_family_member — duplicate name (case-insensitive)
# ---------------------------------------------------------------------------


def test_add_member_duplicate_exact(db_conn):
    """Exact-match duplicate returns the collision message; only one row exists."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_family_member("Maria", "sister", 2007, "student")
    assert result == "I already have someone called Maria."
    assert _member_count(db_conn) == 1


def test_add_member_duplicate_case_insensitive(db_conn):
    """Case-variant duplicate returns the collision message; only one row exists."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_family_member("maria", "sister", 2007, "student")
    # The tool raises IntegrityError (UNIQUE constraint); message uses the passed name
    assert result == "I already have someone called maria."
    assert _member_count(db_conn) == 1


# ---------------------------------------------------------------------------
# list_family_members
# ---------------------------------------------------------------------------


def test_list_members_empty(db_conn):
    """Empty table returns the exact 'no members' message."""
    result = list_family_members()
    assert result == "No family members added yet."


def test_list_members_one(db_conn):
    """A single member is listed with the exact line format."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = list_family_members()
    assert result == "Maria (daughter) — born 2005, student"


def test_list_members_multiple(db_conn):
    """Multiple members appear, one per line, sorted by name."""
    add_family_member("Maria", "daughter", 2005, "student")
    add_family_member("John", "son", 2003, "engineer")
    result = list_family_members()
    lines = result.splitlines()
    assert lines[0] == "John (son) — born 2003, engineer"
    assert lines[1] == "Maria (daughter) — born 2005, student"


def test_list_members_format(db_conn):
    """Each line follows '<name> (<relation>) — born <year>, <status>' exactly."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = list_family_members()
    assert result == "Maria (daughter) — born 2005, student"


# ---------------------------------------------------------------------------
# add_document — happy path
# ---------------------------------------------------------------------------


def test_add_document_happy_path(db_conn):
    """Success returns the exact confirmation string and saves the row with correct values."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "2030-06-15")
    assert result == "Passport added for Maria, expires 2030-06-15."

    row = _get_document(db_conn, "Maria", "passport")
    assert row is not None
    assert row["expiry_date"] == "2030-06-15"


def test_add_document_uses_stored_capitalisation(db_conn):
    """Reply uses the stored member name, and doc_type is title-cased."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("driving licence", "Maria", "2028-03-10")
    assert result == "Driving Licence added for Maria, expires 2028-03-10."

    row = _get_document(db_conn, "Maria", "driving licence")
    assert row is not None
    assert row["expiry_date"] == "2028-03-10"


# ---------------------------------------------------------------------------
# add_document — validation errors
# ---------------------------------------------------------------------------


def test_add_document_empty_doc_type(db_conn):
    """Blank doc_type returns the exact validation message; no document row is saved."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("  ", "Maria", "2030-06-15")
    assert result == "Please tell me which document it is."
    assert _document_count(db_conn) == 0


def test_add_document_unknown_owner(db_conn):
    """Unknown owner returns the exact 'add them first' message; no document row is saved."""
    result = add_document("passport", "Nobody", "2030-06-15")
    assert result == "I don't know anyone called Nobody. Add them first."
    assert _document_count(db_conn) == 0


def test_add_document_bad_date_format(db_conn):
    """A date in the wrong format returns the exact format-error message; no row is saved."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "15-06-2030")
    assert result == "That date doesn't look right. Please use YYYY-MM-DD format."
    assert _document_count(db_conn) == 0


def test_add_document_bad_date_nonsense(db_conn):
    """A completely invalid date string returns the exact format-error message; no row is saved."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("passport", "Maria", "not-a-date")
    assert result == "That date doesn't look right. Please use YYYY-MM-DD format."
    assert _document_count(db_conn) == 0


# ---------------------------------------------------------------------------
# add_document — past expiry date is accepted
# ---------------------------------------------------------------------------


def test_add_document_past_expiry_date_accepted(db_conn):
    """A document that has already expired is still recorded; row is saved."""
    add_family_member("Maria", "daughter", 2005, "student")
    result = add_document("old id card", "Maria", "2000-01-01")
    assert result == "Old Id Card added for Maria, expires 2000-01-01."

    row = _get_document(db_conn, "Maria", "old id card")
    assert row is not None
    assert row["expiry_date"] == "2000-01-01"


# ---------------------------------------------------------------------------
# add_document — FK stored as member_id, not owner name
# ---------------------------------------------------------------------------


def test_documents_stores_member_id(db_conn):
    """documents.member_id is an integer matching the member's row id."""
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
    a personal identifier (id_number, passport_number, national, ssn, aadhar).
    """
    forbidden_substrings = ("id_number", "passport_number", "national", "ssn", "aadhar")
    cols = db_conn.execute("PRAGMA table_info(documents)").fetchall()
    col_names = [c["name"].lower() for c in cols]
    for col in col_names:
        for bad in forbidden_substrings:
            assert bad not in col, (
                f"Column '{col}' in documents table looks like a personal identifier"
            )


# ---------------------------------------------------------------------------
# get_expiring_documents — T-13
# ---------------------------------------------------------------------------


def test_expiring_none_in_window(db_conn):
    """No documents at all → returns the exact 'nothing expiring' message."""
    result = get_expiring_documents(7)
    assert result == "Nothing is expiring in the next 7 days."


def test_expiring_document_in_window(db_conn):
    """A document expiring in 5 days appears with the correct status text for days=7."""
    add_family_member("Maria", "daughter", 2005, "student")
    expiry = (_dt.date.today() + _dt.timedelta(days=5)).isoformat()
    add_document("passport", "Maria", expiry)
    result = get_expiring_documents(7)
    # 5 days left is > 7 threshold only if <=7 → URGENT; 5 <= 7 so status is URGENT
    assert result == f"Maria's passport - {expiry} (URGENT, 5 days left)"


def test_expiring_document_already_expired(db_conn):
    """A document expired 3 days ago shows the EXPIRED status with exact day count."""
    add_family_member("Maria", "daughter", 2005, "student")
    expiry = (_dt.date.today() - _dt.timedelta(days=3)).isoformat()
    add_document("driving licence", "Maria", expiry)
    result = get_expiring_documents(0)
    assert result == f"Maria's driving licence - {expiry} (EXPIRED 3 days ago)"


def test_expiring_document_more_than_7_days(db_conn):
    """A document expiring in 10 days shows the plain 'N days left' status (not URGENT)."""
    add_family_member("John", "son", 2000, "engineer")
    expiry = (_dt.date.today() + _dt.timedelta(days=10)).isoformat()
    add_document("passport", "John", expiry)
    result = get_expiring_documents(30)
    assert result == f"John's passport - {expiry} (10 days left)"


def test_expiring_sorted_soonest_first(db_conn):
    """Two documents expiring at different times appear soonest-first."""
    add_family_member("Maria", "daughter", 2005, "student")
    add_family_member("John", "son", 2000, "engineer")
    sooner = (_dt.date.today() + _dt.timedelta(days=3)).isoformat()
    later = (_dt.date.today() + _dt.timedelta(days=10)).isoformat()
    add_document("passport", "Maria", sooner)
    add_document("driving licence", "John", later)
    result = get_expiring_documents(30)
    lines = result.splitlines()
    assert lines[0] == f"Maria's passport - {sooner} (URGENT, 3 days left)"
    assert lines[1] == f"John's driving licence - {later} (10 days left)"


def test_expiring_invalid_days_negative(db_conn):
    """A negative days value returns the exact validation error; no DB query needed."""
    result = get_expiring_documents(-1)
    assert result == "Please give a number of days between 0 and 3650."


def test_expiring_invalid_days_over_limit(db_conn):
    """days=3651 returns the exact validation error."""
    result = get_expiring_documents(3651)
    assert result == "Please give a number of days between 0 and 3650."


# ---------------------------------------------------------------------------
# add_task and list_upcoming_tasks — T-15
#
# NOTE — spec/code mismatch:
#   T-14 spec says add_task(title, due_date, member_id=None) taking an integer.
#   The actual code has add_task(title, due_date, owner="") taking a member NAME.
#   Tests follow the code (owner = name string).
#
#   T-14 spec says list_upcoming_tasks validates days >= 1.
#   The actual code validates 0 <= days <= 3650 (same guard as get_expiring_documents).
#   Tests follow the code.
# ---------------------------------------------------------------------------

from glean.tools import add_task, list_upcoming_tasks


def _task_count(conn):
    return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]


def _get_task(conn, title):
    return conn.execute("SELECT * FROM tasks WHERE title = ?", (title,)).fetchone()


# ---------------------------------------------------------------------------
# add_task — success cases
# ---------------------------------------------------------------------------


def test_add_task_happy_path_no_owner(db_conn):
    """Success with no owner returns the exact confirmation; row has NULL member_id and done=0."""
    due = (_dt.date.today() + _dt.timedelta(days=7)).isoformat()
    result = add_task("Renew insurance", due)
    assert result == f"Task added: Renew insurance, due {due}."

    row = _get_task(db_conn, "Renew insurance")
    assert row is not None
    assert row["due_date"] == due
    assert row["member_id"] is None
    assert row["done"] == 0


def test_add_task_happy_path_with_owner(db_conn):
    """Success with a valid owner returns the exact confirmation; row has correct member_id and done=0."""
    add_family_member("Maria", "daughter", 2005, "student")
    due = (_dt.date.today() + _dt.timedelta(days=5)).isoformat()
    result = add_task("Buy textbooks", due, "Maria")
    assert result == f"Task added: Buy textbooks, due {due}."

    member = db_conn.execute(
        "SELECT id FROM family_members WHERE name = 'Maria'"
    ).fetchone()
    row = _get_task(db_conn, "Buy textbooks")
    assert row is not None
    assert row["due_date"] == due
    assert row["member_id"] == member["id"]
    assert row["done"] == 0


def test_add_task_past_date_accepted(db_conn):
    """A task with a past due date is accepted; row is saved."""
    due = (_dt.date.today() - _dt.timedelta(days=10)).isoformat()
    result = add_task("Old errand", due)
    assert result == f"Task added: Old errand, due {due}."

    row = _get_task(db_conn, "Old errand")
    assert row is not None
    assert row["due_date"] == due


# ---------------------------------------------------------------------------
# add_task — failure cases
# ---------------------------------------------------------------------------


def test_add_task_empty_title(db_conn):
    """Blank title returns the exact validation message; no row is saved."""
    due = (_dt.date.today() + _dt.timedelta(days=7)).isoformat()
    result = add_task("   ", due)
    assert result == "Please tell me what the task is."
    assert _task_count(db_conn) == 0


def test_add_task_bad_date_format(db_conn):
    """A date in wrong format returns the exact format-error message; no row is saved."""
    result = add_task("Fix leak", "25-12-2025")
    assert result == "That date doesn't look right. Please use YYYY-MM-DD format."
    assert _task_count(db_conn) == 0


def test_add_task_bad_date_nonsense(db_conn):
    """A completely invalid date string returns the exact format-error message; no row is saved."""
    result = add_task("Fix leak", "not-a-date")
    assert result == "That date doesn't look right. Please use YYYY-MM-DD format."
    assert _task_count(db_conn) == 0


def test_add_task_unknown_owner(db_conn):
    """Unknown owner name returns the exact 'add them first' message; no row is saved."""
    due = (_dt.date.today() + _dt.timedelta(days=7)).isoformat()
    result = add_task("Buy books", due, "Nobody")
    assert result == "I don't know anyone called Nobody. Add them first."
    assert _task_count(db_conn) == 0


# ---------------------------------------------------------------------------
# list_upcoming_tasks — success cases
# ---------------------------------------------------------------------------


def test_list_tasks_no_tasks(db_conn):
    """Empty tasks table returns the exact 'no tasks' message."""
    result = list_upcoming_tasks(7)
    assert result == "No tasks due in the next 7 days."


def test_list_tasks_one_in_window(db_conn):
    """A task due in 3 days appears with the exact output line (status = '3 days left')."""
    due = (_dt.date.today() + _dt.timedelta(days=3)).isoformat()
    add_task("Call dentist", due)
    result = list_upcoming_tasks(7)
    assert result == f"Call dentist - {due} (3 days left)"


def test_list_tasks_overdue(db_conn):
    """A task overdue by 2 days shows 'OVERDUE by 2 days' in the exact line."""
    due = (_dt.date.today() - _dt.timedelta(days=2)).isoformat()
    add_task("Pay bill", due)
    result = list_upcoming_tasks(0)
    assert result == f"Pay bill - {due} (OVERDUE by 2 days)"


def test_list_tasks_due_today(db_conn):
    """A task due today shows 'due today' in the exact line."""
    due = _dt.date.today().isoformat()
    add_task("Submit form", due)
    result = list_upcoming_tasks(0)
    assert result == f"Submit form - {due} (due today)"


def test_list_tasks_sorted_soonest_first(db_conn):
    """Two tasks with different due dates appear soonest-first."""
    sooner = (_dt.date.today() + _dt.timedelta(days=2)).isoformat()
    later = (_dt.date.today() + _dt.timedelta(days=8)).isoformat()
    add_task("Early task", sooner)
    add_task("Late task", later)
    result = list_upcoming_tasks(30)
    lines = result.splitlines()
    assert lines[0] == f"Early task - {sooner} (2 days left)"
    assert lines[1] == f"Late task - {later} (8 days left)"


def test_list_tasks_with_owner_name(db_conn):
    """A task linked to a member shows the member name in parentheses after the title."""
    add_family_member("Maria", "daughter", 2005, "student")
    due = (_dt.date.today() + _dt.timedelta(days=4)).isoformat()
    add_task("School fees", due, "Maria")
    result = list_upcoming_tasks(7)
    assert result == f"School fees (Maria) - {due} (4 days left)"


def test_list_tasks_without_owner(db_conn):
    """A task with no owner shows no parenthesised name."""
    due = (_dt.date.today() + _dt.timedelta(days=4)).isoformat()
    add_task("General errand", due)
    result = list_upcoming_tasks(7)
    assert result == f"General errand - {due} (4 days left)"


def test_list_tasks_done_excluded(db_conn):
    """A task with done=1 does not appear in the output."""
    due = (_dt.date.today() + _dt.timedelta(days=2)).isoformat()
    add_task("Done task", due)
    db_conn.execute("UPDATE tasks SET done = 1 WHERE title = 'Done task'")
    db_conn.commit()
    result = list_upcoming_tasks(7)
    assert result == "No tasks due in the next 7 days."


def test_list_tasks_beyond_window_excluded(db_conn):
    """A task due in 14 days does not appear when asking for a 7-day window."""
    far = (_dt.date.today() + _dt.timedelta(days=14)).isoformat()
    add_task("Far future task", far)
    result = list_upcoming_tasks(7)
    assert result == "No tasks due in the next 7 days."


# ---------------------------------------------------------------------------
# list_upcoming_tasks — invalid days
# ---------------------------------------------------------------------------


def test_list_tasks_invalid_days_negative(db_conn):
    """A negative days value returns the exact validation error."""
    result = list_upcoming_tasks(-1)
    assert result == "Please give a number of days between 0 and 3650."


def test_list_tasks_invalid_days_over_limit(db_conn):
    """days=3651 returns the exact validation error."""
    result = list_upcoming_tasks(3651)
    assert result == "Please give a number of days between 0 and 3650."
