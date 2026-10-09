import datetime
import logging
import sqlite3

from glean import db, schemes
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


@mcp.tool()
def check_scheme_eligibility(name: str, tags: str = "") -> str:
    """Check government scheme eligibility for a family member by name.
    Optional tags can be provided as comma-separated labels (e.g. 'bpl', 'income_tax_payer')."""
    name = name.strip()
    if not name:
        return "Please provide a family member's name."

    try:
        conn = db.get_connection()
        member = conn.execute(
            "SELECT name, birth_year FROM family_members WHERE name = ?", (name,)
        ).fetchone()
        if member is None:
            return f"I don't know anyone called {name}. Add them first."

        parsed_tags = {t.strip().lower() for t in tags.split(",") if t.strip()}
        results = schemes.check_eligibility(member["birth_year"], parsed_tags)
    except Exception as exc:
        logger.error("check_scheme_eligibility failed: %s", exc)
        return "Something went wrong. Please try again."

    lines = [f"Eligibility check for {member['name']} (born {member['birth_year']}):"]

    eligible = [r for r in results if r["status"] == "may_be_eligible"]
    check_needed = [r for r in results if r["status"] == "check_needed"]
    not_eligible = [r for r in results if r["status"] == "not_eligible"]

    if eligible:
        lines.append("\nMay be eligible:")
        for r in eligible:
            reason = "; ".join(r["reasons"])
            lines.append(f"• {r['name']} — {reason}. Official link: {r['source_url']}")

    if check_needed:
        lines.append("\nRequires verification:")
        for r in check_needed:
            confirm = "; ".join(r["confirm"])
            lines.append(f"• {r['name']} — {confirm}. Official link: {r['source_url']}")

    if not_eligible:
        lines.append("\nNot eligible:")
        for r in not_eligible:
            reason = "; ".join(r["reasons"])
            lines.append(f"• {r['name']} — {reason}")

    lines.append("\nNote: Guidance only. Please verify details on official government portals.")
    return "\n".join(lines)


@mcp.tool()
def get_scheme_checklist(scheme: str) -> str:
    """Get the document checklist and application info for a government scheme.
    Pass either the scheme ID (e.g. 'ayushman_vay_vandana', 'apy', 'scss', 'ignoaps_mh') or scheme name."""
    scheme_query = scheme.strip().lower()
    if not scheme_query:
        return "Please provide a scheme name or ID."

    all_schemes = schemes.load_schemes()
    matched = None
    for s in all_schemes:
        if s["id"].lower() == scheme_query or scheme_query in s["name"].lower():
            matched = s
            break

    if not matched:
        available = ", ".join(f"{s['name']} (ID: {s['id']})" for s in all_schemes)
        return f"I couldn't find a scheme matching '{scheme}'. Available schemes: {available}."

    lines = [
        f"Document Checklist for {matched['name']}:",
        f"State: {matched.get('state', 'All India')}",
        f"Summary: {matched.get('summary', '')}",
        "\nRequired Documents:",
    ]
    for doc in matched.get("documents", []):
        lines.append(f"• {doc}")

    if matched.get("notes"):
        lines.append(f"\nNotes: {matched['notes']}")
    if matched.get("source_url"):
        lines.append(f"Official details: {matched['source_url']}")
    if matched.get("apply_url"):
        lines.append(f"Apply online: {matched['apply_url']}")

    return "\n".join(lines)


@mcp.tool()
def plan_scheme_application(name: str, scheme: str, days_to_prepare: int = 7) -> str:
    """Agentic multi-step workflow: checks eligibility, retrieves required documents,
    and automatically schedules preparation and submission deadlines as family tasks."""
    name = name.strip()
    scheme_query = scheme.strip().lower()
    if not name:
        return "Please provide a family member's name."
    if not scheme_query:
        return "Please provide a scheme name or ID."
    if not 1 <= days_to_prepare <= 365:
        return "Please give preparation days between 1 and 365."

    try:
        conn = db.get_connection()
        member = conn.execute(
            "SELECT id, name, birth_year FROM family_members WHERE name = ?", (name,)
        ).fetchone()
        if member is None:
            return f"I don't know anyone called {name}. Add them first."

        all_schemes = schemes.load_schemes()
        matched = None
        for s in all_schemes:
            if s["id"].lower() == scheme_query or scheme_query in s["name"].lower():
                matched = s
                break

        if not matched:
            available = ", ".join(s["name"] for s in all_schemes)
            return f"I couldn't find '{scheme}'. Available schemes: {available}."

        eligibility_list = schemes.check_eligibility(member["birth_year"])
        scheme_eval = next((r for r in eligibility_list if r["scheme_id"] == matched["id"]), None)

        today = datetime.date.today()
        gather_due = today + datetime.timedelta(days=days_to_prepare)
        apply_due = today + datetime.timedelta(days=days_to_prepare + 7)

        task1_title = f"Gather docs for {matched['name']}"
        task2_title = f"Submit application for {matched['name']}"

        conn.execute(
            "INSERT INTO tasks (title, due_date, member_id) VALUES (?, ?, ?)",
            (task1_title, gather_due.isoformat(), member["id"]),
        )
        conn.execute(
            "INSERT INTO tasks (title, due_date, member_id) VALUES (?, ?, ?)",
            (task2_title, apply_due.isoformat(), member["id"]),
        )
        conn.commit()
    except Exception as exc:
        logger.error("plan_scheme_application failed: %s", exc)
        return "Something went wrong. Please try again."

    status_str = scheme_eval["status"].replace("_", " ").title() if scheme_eval else "Evaluated"
    reasons = "; ".join(scheme_eval.get("reasons", [])) if scheme_eval else ""

    lines = [
        f"Application plan created for {member['name']} — {matched['name']}:",
        f"• Eligibility status: {status_str} ({reasons})",
        f"• Task 1 created: Gather documents by {gather_due.isoformat()}",
        f"• Task 2 created: Submit application by {apply_due.isoformat()}",
        f"• Official portal: {matched.get('apply_url') or matched.get('source_url')}",
        "\nDocuments needed:",
    ]
    for d in matched.get("documents", []):
        lines.append(f"  - {d}")

    return "\n".join(lines)


@mcp.tool()
def family_brief(member_name: str = "") -> str:
    """Provide a comprehensive spoken-style summary of paperwork, deadlines, and benefits.
    If member_name is specified (e.g. 'Aman', 'Grandma', 'Dad', 'Ramesh'),
    tailors the briefing personally for that individual including their documents,
    deadlines, and qualifying government schemes. If omitted or 'all', provides the whole-family briefing."""
    today = datetime.date.today()
    cutoff_docs = today + datetime.timedelta(days=30)
    cutoff_tasks = today + datetime.timedelta(days=14)

    target = member_name.strip()
    if target and target.lower() not in ("all", "everyone", "family"):
        # Personalised briefing
        try:
            conn = db.get_connection()
            # 1. Search member by name (case-insensitive)
            member = conn.execute(
                "SELECT id, name, relation, birth_year, status FROM family_members WHERE LOWER(name) = ?",
                (target.lower(),),
            ).fetchone()

            # 2. If not found by name, try matching by relation or common alias
            if not member:
                alias_map = {
                    "grandpa": "grandfather",
                    "granddad": "grandfather",
                    "dada": "grandfather",
                    "nana": "grandfather",
                    "grandma": "grandmother",
                    "granny": "grandmother",
                    "dadi": "grandmother",
                    "nani": "grandmother",
                    "dad": "father",
                    "papa": "father",
                    "mom": "mother",
                    "mummy": "mother",
                    "maa": "mother",
                    "admin": "admin",
                }
                normalized_target = alias_map.get(target.lower(), target.lower())
                member = conn.execute(
                    "SELECT id, name, relation, birth_year, status FROM family_members "
                    "WHERE LOWER(relation) LIKE ? OR LOWER(name) LIKE ?",
                    (f"%{normalized_target}%", f"%{target.lower()}%"),
                ).fetchone()

            if not member:
                return (
                    f"I don't have records for '{target}' yet. "
                    "Add them to your family list first, or ask for the whole-family briefing."
                )

            m_id = member["id"]
            m_name = member["name"]
            m_relation = member["relation"]
            m_birth = member["birth_year"]

            # Member's expiring documents
            exp_docs = conn.execute(
                "SELECT doc_type, expiry_date FROM documents "
                "WHERE member_id = ? AND expiry_date <= ? "
                "ORDER BY expiry_date",
                (m_id, cutoff_docs.isoformat()),
            ).fetchall()

            # Member's upcoming tasks (+ household tasks where member_id is NULL)
            tasks = conn.execute(
                "SELECT title, due_date, member_id FROM tasks "
                "WHERE (member_id = ? OR member_id IS NULL) AND done = 0 AND due_date <= ? "
                "ORDER BY due_date",
                (m_id, cutoff_tasks.isoformat()),
            ).fetchall()

            # Scheme eligibility evaluation
            eligibility = schemes.check_eligibility(m_birth)
            eligible_schemes = [s for s in eligibility if s["status"] == "may_be_eligible"]
            verify_schemes = [s for s in eligibility if s["status"] == "check_needed"]

        except Exception as exc:
            logger.error("family_brief personalized failed: %s", exc)
            return "Something went wrong. Please try again."

        lines = [f"Personal Briefing for {m_name} ({m_relation}, born {m_birth}):"]

        # Documents
        if exp_docs:
            lines.append(f"\nYour Expiring Documents (next 30 days): {len(exp_docs)}")
            for r in exp_docs:
                exp = datetime.date.fromisoformat(r["expiry_date"])
                left = (exp - today).days
                urgency = "EXPIRED" if left < 0 else (f"urgent ({left}d left)" if left <= 7 else f"{left}d left")
                lines.append(f"• {r['doc_type']}: {r['expiry_date']} ({urgency})")
        else:
            lines.append("\nDocuments: All your documents are up to date for the next 30 days.")

        # Tasks
        if tasks:
            lines.append(f"\nYour Upcoming Deadlines (next 14 days): {len(tasks)}")
            for r in tasks:
                due = datetime.date.fromisoformat(r["due_date"])
                left = (due - today).days
                status = "OVERDUE" if left < 0 else ("due today" if left == 0 else f"{left}d left")
                scope = " (household)" if r["member_id"] is None else ""
                lines.append(f"• {r['title']}{scope} — due {r['due_date']} ({status})")
        else:
            lines.append("\nTasks: No deadlines due for you in the next 14 days.")

        # Government schemes
        if eligible_schemes:
            lines.append("\nGovernment Benefits You May Qualify For:")
            for s in eligible_schemes:
                lines.append(f"• {s['name']} (Official link: {s['source_url']})")
            lines.append("Ask me 'Plan the application' or 'What documents are needed' anytime!")
        elif verify_schemes:
            lines.append("\nPotential Benefits (verification needed):")
            for s in verify_schemes:
                confirm = "; ".join(s["confirm"])
                lines.append(f"• {s['name']} — confirm: {confirm}")

        return "\n".join(lines)

    # Whole-family briefing
    try:
        conn = db.get_connection()
        members = conn.execute("SELECT COUNT(*) FROM family_members").fetchone()[0]
        exp_docs = conn.execute(
            "SELECT m.name, d.doc_type, d.expiry_date "
            "FROM documents d JOIN family_members m ON m.id = d.member_id "
            "WHERE d.expiry_date <= ? "
            "ORDER BY d.expiry_date",
            (cutoff_docs.isoformat(),),
        ).fetchall()

        tasks = conn.execute(
            "SELECT t.title, t.due_date, m.name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "WHERE t.done = 0 AND t.due_date <= ? "
            "ORDER BY t.due_date",
            (cutoff_tasks.isoformat(),),
        ).fetchall()
    except Exception as exc:
        logger.error("family_brief failed: %s", exc)
        return "Something went wrong. Please try again."

    if members == 0:
        return "No family members added yet. Start by adding a member."

    lines = [f"Family Briefing ({members} family member{'s' if members != 1 else ''} tracked):"]

    if not exp_docs and not tasks:
        lines.append("Everything looks great! No documents expiring in the next 30 days and no tasks due in the next 14 days.")
        return "\n".join(lines)

    if exp_docs:
        lines.append(f"\nExpiring Documents (next 30 days): {len(exp_docs)}")
        for r in exp_docs:
            exp = datetime.date.fromisoformat(r["expiry_date"])
            left = (exp - today).days
            urgency = "EXPIRED" if left < 0 else (f"urgent ({left}d left)" if left <= 7 else f"{left}d left")
            lines.append(f"• {r['name']}'s {r['doc_type']}: {r['expiry_date']} ({urgency})")
    else:
        lines.append("\nDocuments: All documents are up to date for the next 30 days.")

    if tasks:
        lines.append(f"\nUpcoming Tasks (next 14 days): {len(tasks)}")
        for r in tasks:
            due = datetime.date.fromisoformat(r["due_date"])
            left = (due - today).days
            status = "OVERDUE" if left < 0 else ("due today" if left == 0 else f"{left}d left")
            who = f" ({r['name']})" if r["name"] else ""
            lines.append(f"• {r['title']}{who} — due {r['due_date']} ({status})")
    else:
        lines.append("\nTasks: No tasks due in the next 14 days.")

    return "\n".join(lines)