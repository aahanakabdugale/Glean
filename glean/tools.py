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