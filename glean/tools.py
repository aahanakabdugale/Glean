import datetime
import logging
import sqlite3

from glean import db
from glean.app import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
def add_family_member(name: str, relation: str, birth_year: int, status: str) -> str:
    """Add a person to the family list. Use when the user mentions a new family member.
    relation is a free label like 'daughter' or 'grandfather'; status is free text like 'student' or 'retired'."""
    name = name.strip()
    relation = relation.strip()
    status = status.strip()

    if not name:
        return "Please provide a name."
    if not relation:
        return "Please tell me how they are related to you."
    if not 1900 <= birth_year <= datetime.date.today().year:
        return "That birth year doesn't look right."

    try:
        conn = db.get_connection()
        conn.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            (name, relation, birth_year, status),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return f"I already have someone called {name}."
    except Exception as exc:
        logger.error("add_family_member failed: %s", exc)
        return "Something went wrong. Please try again."

    return f"Added {name} ({relation})."


@mcp.tool()
def list_family_members() -> str:
    """List everyone in the family with their relation, birth year and status."""
    try:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT name, relation, birth_year, status FROM family_members ORDER BY name"
        ).fetchall()
    except Exception as exc:
        logger.error("list_family_members failed: %s", exc)
        return "Something went wrong. Please try again."

    if not rows:
        return "No family members added yet."

    return "\n".join(
        f"{r['name']} ({r['relation']}) — born {r['birth_year']}, {r['status']}"
        for r in rows
    )


@mcp.tool()
def add_document(doc_type: str, owner: str, expiry_date: str) -> str:
    """Save a document's type and expiry date for a family member, e.g. passport, Aadhaar card, driving licence.
    expiry_date must be YYYY-MM-DD. Never ask for or store the document number."""
    doc_type = doc_type.strip()
    owner = owner.strip()

    if not doc_type:
        return "Please tell me which document it is."

    try:
        expiry = datetime.datetime.strptime(expiry_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "That date doesn't look right. Please use YYYY-MM-DD format."

    try:
        conn = db.get_connection()
        member = conn.execute(
            "SELECT id, name FROM family_members WHERE name = ?", (owner,)
        ).fetchone()
        if member is None:
            return f"I don't know anyone called {owner}. Add them first."

        conn.execute(
            "INSERT INTO documents (member_id, doc_type, expiry_date) VALUES (?, ?, ?)",
            (member["id"], doc_type, expiry.isoformat()),
        )
        conn.commit()
    except Exception as exc:
        logger.error("add_document failed: %s", exc)
        return "Something went wrong. Please try again."

    return f"{doc_type.title()} added for {member['name']}, expires {expiry.isoformat()}."


@mcp.tool()
def get_expiring_documents(days: int = 30) -> str:
    """List documents that are already expired or will expire within the next N days (default 30),
    soonest first. Use when the user asks what is expiring or what needs renewing."""
    if not 0 <= days <= 3650:
        return "Please give a number of days between 0 and 3650."

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days)

    try:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT m.name, d.doc_type, d.expiry_date "
            "FROM documents d JOIN family_members m ON m.id = d.member_id "
            "WHERE d.expiry_date <= ? "
            "ORDER BY d.expiry_date",
            (cutoff.isoformat(),),
        ).fetchall()
    except Exception as exc:
        logger.error("get_expiring_documents failed: %s", exc)
        return "Something went wrong. Please try again."

    if not rows:
        return f"Nothing is expiring in the next {days} days."

    lines = []
    for r in rows:
        expiry = datetime.date.fromisoformat(r["expiry_date"])
        left = (expiry - today).days
        if left < 0:
            status = f"EXPIRED {-left} days ago"
        elif left <= 7:
            status = f"URGENT, {left} days left"
        else:
            status = f"{left} days left"
        lines.append(f"{r['name']}'s {r['doc_type']} - {r['expiry_date']} ({status})")

    return "\n".join(lines)

@mcp.tool()
def add_task(title: str, due_date: str, owner: str = "") -> str:
    """Add a task or deadline, e.g. 'Renew passport'. due_date must be YYYY-MM-DD.
    owner is optional: the name of the family member the task is for. Leave it empty for a general task."""
    title = title.strip()
    owner = owner.strip()

    if not title:
        return "Please tell me what the task is."

    try:
        due = datetime.datetime.strptime(due_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "That date doesn't look right. Please use YYYY-MM-DD format."

    try:
        conn = db.get_connection()
        member_id = None
        if owner:
            member = conn.execute(
                "SELECT id FROM family_members WHERE name = ?", (owner,)
            ).fetchone()
            if member is None:
                return f"I don't know anyone called {owner}. Add them first."
            member_id = member["id"]

        conn.execute(
            "INSERT INTO tasks (title, due_date, member_id) VALUES (?, ?, ?)",
            (title, due.isoformat(), member_id),
        )
        conn.commit()
    except Exception as exc:
        logger.error("add_task failed: %s", exc)
        return "Something went wrong. Please try again."

    return f"Task added: {title}, due {due.isoformat()}."


@mcp.tool()
def list_upcoming_tasks(days: int = 30) -> str:
    """List tasks that are not done and are due within the next N days (default 30),
    soonest first. Overdue tasks are included. Use when the user asks what is coming up or what is pending."""
    if not 0 <= days <= 3650:
        return "Please give a number of days between 0 and 3650."

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days)

    try:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT t.title, t.due_date, m.name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "WHERE t.done = 0 AND t.due_date <= ? "
            "ORDER BY t.due_date",
            (cutoff.isoformat(),),
        ).fetchall()
    except Exception as exc:
        logger.error("list_upcoming_tasks failed: %s", exc)
        return "Something went wrong. Please try again."

    if not rows:
        return f"No tasks due in the next {days} days."

    lines = []
    for r in rows:
        due = datetime.date.fromisoformat(r["due_date"])
        left = (due - today).days
        if left < 0:
            status = f"OVERDUE by {-left} days"
        elif left == 0:
            status = "due today"
        else:
            status = f"{left} days left"
        who = f" ({r['name']})" if r["name"] else ""
        lines.append(f"{r['title']}{who} - {r['due_date']} ({status})")

    return "\n".join(lines)