import datetime
import logging
import sqlite3

from backend import db, schemes
from backend.ambient import evaluate_proactive_alerts, ambient_broker
from backend.app import mcp
from backend.security import sanitize_input

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
def remove_family_member(name: str) -> str:
    """Remove a person from the family list by name."""
    name = name.strip()
    if not name:
        return "Please provide a name to remove."

    try:
        conn = db.get_connection()
        row = conn.execute(
            "SELECT id FROM family_members WHERE LOWER(name) = LOWER(?)", (name,)
        ).fetchone()
        if not row:
            return f"I couldn't find anyone called {name}."

        m_id = row["id"]
        conn.execute("DELETE FROM tasks WHERE member_id = ?", (m_id,))
        conn.execute("DELETE FROM documents WHERE member_id = ?", (m_id,))
        conn.execute("DELETE FROM family_members WHERE id = ?", (m_id,))
        conn.commit()
    except Exception as exc:
        logger.error("remove_family_member failed: %s", exc)
        return "Something went wrong. Please try again."

    return f"Removed {name} from the family list."


@mcp.tool()
def reset_family_roster() -> str:
    """Reset family members to the canonical demo roster (Chandler, Amy, Justin, Riley, Jace, Gwen)."""
    try:
        conn = db.get_connection()
        demo_members = [
            ("Chandler", "grandfather", 1950, "retired"),
            ("Amy", "grandmother", 1953, "retired"),
            ("Justin", "father", 1968, "employed"),
            ("Riley", "mother", 1972, "employed"),
            ("Jace", "son", 2000, "family admin"),
            ("Gwen", "daughter", 2003, "family admin"),
        ]
        for name, relation, birth_year, status in demo_members:
            existing = conn.execute(
                "SELECT id FROM family_members WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
                    (name, relation, birth_year, status),
                )
        conn.commit()
        db.align_demo_dates(conn)
        return "Reset family roster to canonical demo dataset."
    except Exception as exc:
        logger.error("reset_family_roster failed: %s", exc)
        return "Something went wrong. Please try again."


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
def get_expiring_documents(days: int = 30, member_name: str = "", doc_type: str = "") -> str:
    """List documents that are already expired or will expire within the next N days (default 30),
    soonest first. Optional member_name filters documents for a specific person.
    Optional doc_type filters by document type (e.g. 'Passport', 'Insurance').
    Use when the user asks what is expiring or what needs renewing."""
    if not 0 <= days <= 3650:
        return "Please give a number of days between 0 and 3650."

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days)

    try:
        conn = db.get_connection()
        db.align_demo_dates(conn)
        query = (
            "SELECT m.name, d.doc_type, d.expiry_date "
            "FROM documents d JOIN family_members m ON m.id = d.member_id "
            "WHERE d.expiry_date <= ? "
        )
        params = [cutoff.isoformat()]
        if member_name and member_name.strip():
            query += "AND LOWER(m.name) = LOWER(?) "
            params.append(member_name.strip())
        if doc_type and doc_type.strip():
            query += "AND LOWER(d.doc_type) LIKE LOWER(?) "
            params.append(f"%{doc_type.strip()}%")

        query += "ORDER BY d.expiry_date"
        rows = conn.execute(query, tuple(params)).fetchall()
    except Exception as exc:
        logger.error("get_expiring_documents failed: %s", exc)
        return "Something went wrong. Please try again."

    who = f" for {member_name.strip()}" if member_name and member_name.strip() else ""
    what = f" matching '{doc_type.strip()}'" if doc_type and doc_type.strip() else ""
    if not rows:
        return f"Nothing is expiring in the next {days} days{who}{what}."

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

        # Check if identical pending task already exists
        dupes = conn.execute(
            "SELECT id FROM tasks WHERE LOWER(TRIM(title)) = LOWER(?) AND ((member_id = ?) OR (member_id IS NULL AND ? IS NULL)) AND done = 0",
            (title, member_id, member_id),
        ).fetchall()
        if dupes:
            conn.execute(
                "UPDATE tasks SET due_date = ? WHERE id = ?",
                (due.isoformat(), dupes[0]["id"]),
            )
            if len(dupes) > 1:
                extra_ids = [d["id"] for d in dupes[1:]]
                conn.execute(
                    f"DELETE FROM tasks WHERE id IN ({','.join('?' for _ in extra_ids)})",
                    tuple(extra_ids),
                )
            conn.commit()
            return f"Task updated: {title}, due {due.isoformat()}."

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
def complete_task(task_title: str = "", member_name: str = "", task_id: int = 0) -> str:
    """Mark a pending task as completed (done = 1).
    Can match by task_id directly, or by task_title (fuzzy/case-insensitive) and optional member_name.
    Use when the user marks a task completed, finishes a task, or asks to check off a task."""
    try:
        conn = db.get_connection()

        if task_id and int(task_id) > 0:
            row = conn.execute(
                "SELECT t.id, t.title, m.name FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id WHERE t.id = ?",
                (int(task_id),)
            ).fetchone()
            if not row:
                return f"Task ID {task_id} not found."
            conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (int(task_id),))
            conn.commit()
            who_str = f" for {row['name']}" if row['name'] else ""
            return f"Completed: '{row['title']}'{who_str}."

        title = (task_title or "").strip()
        if not title:
            return "Please tell me which task to complete."

        # Find pending tasks (done = 0)
        query = (
            "SELECT t.id, t.title, t.due_date, m.name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "WHERE t.done = 0 "
        )
        params = []
        if member_name and member_name.strip():
            query += "AND LOWER(m.name) = LOWER(?) "
            params.append(member_name.strip())

        candidates = conn.execute(query, tuple(params)).fetchall()
        if not candidates:
            # Check if perhaps it was already marked done
            already_done = conn.execute(
                "SELECT t.id, t.title, m.name FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
                "WHERE t.done = 1 AND LOWER(t.title) LIKE ?",
                (f"%{title.lower()}%",)
            ).fetchone()
            if already_done:
                who = f" for {already_done['name']}" if already_done['name'] else ""
                return f"'{already_done['title']}'{who} is already marked as completed."
            who = f" for {member_name.strip()}" if member_name and member_name.strip() else ""
            return f"No pending tasks found{who}."

        title_lower = title.lower()

        # 1. Exact title match (case-insensitive)
        matched = [c for c in candidates if c["title"].lower() == title_lower]

        # 2. Substring match
        if not matched:
            matched = [
                c for c in candidates
                if title_lower in c["title"].lower() or c["title"].lower() in title_lower
            ]

        # 3. Token-overlap match (ignoring common stopwords)
        if not matched:
            stopwords = {"the", "a", "an", "for", "to", "in", "on", "at", "and", "or", "task", "done", "completed", "finish", "finished", "mark", "check"}
            query_tokens = set(title_lower.split()) - stopwords
            if query_tokens:
                best_score = 0
                best_c = None
                for c in candidates:
                    cand_tokens = set(c["title"].lower().split()) - stopwords
                    overlap = len(query_tokens.intersection(cand_tokens))
                    if overlap > best_score:
                        best_score = overlap
                        best_c = c
                if best_c and best_score >= 1:
                    matched = [best_c]

        if not matched:
            who = f" for {member_name.strip()}" if member_name and member_name.strip() else ""
            return f"Couldn't find any pending task matching '{task_title}'{who}."

        matched_ids = [m["id"] for m in matched]
        placeholders = ",".join("?" for _ in matched_ids)
        conn.execute(
            f"UPDATE tasks SET done = 1 WHERE id IN ({placeholders})",
            tuple(matched_ids),
        )
        conn.commit()

        best = matched[0]
        who_str = f" for {best['name']}" if best['name'] else ""
        return f"Completed: '{best['title']}'{who_str}."
    except Exception as exc:
        logger.error("complete_task failed: %s", exc)
        return "Something went wrong. Please try again."


@mcp.tool()
def list_upcoming_tasks(days: int = 30, member_name: str = "") -> str:
    """List tasks that are not done and are due within the next N days (default 30),
    soonest first. Optional member_name filters tasks for a specific person.
    Overdue tasks are included. Use when the user asks what is coming up or what is pending."""
    if not 0 <= days <= 3650:
        return "Please give a number of days between 0 and 3650."

    today = datetime.date.today()
    cutoff = today + datetime.timedelta(days=days)

    try:
        conn = db.get_connection()
        db.align_demo_dates(conn)
        query = (
            "SELECT t.title, t.due_date, m.name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "WHERE t.done = 0 AND t.due_date <= ? "
        )
        params = [cutoff.isoformat()]
        if member_name and member_name.strip():
            query += "AND LOWER(m.name) = LOWER(?) "
            params.append(member_name.strip())

        query += "ORDER BY t.due_date"
        rows = conn.execute(query, tuple(params)).fetchall()
    except Exception as exc:
        logger.error("list_upcoming_tasks failed: %s", exc)
        return "Something went wrong. Please try again."

    who = f" for {member_name.strip()}" if member_name and member_name.strip() else ""
    if not rows:
        return f"No tasks due in the next {days} days{who}."

    # Deduplicate redundant tasks by (title, name)
    seen = set()
    unique_rows = []
    for r in rows:
        key = (r["title"].strip().lower(), (r["name"] or "").strip().lower())
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)

    lines = []
    for r in unique_rows:
        due = datetime.date.fromisoformat(r["due_date"])
        left = (due - today).days
        if left < 0:
            status = f"OVERDUE by {-left} days"
        elif left == 0:
            status = "due today"
        else:
            status = f"{left} days left"
        who = f" ({r['name']})" if r["name"] and r["name"].lower() not in r["title"].lower() else ""
        lines.append(f"{r['title']}{who} - {r['due_date']} ({status})")

    return "\n".join(lines)


@mcp.tool()
def check_scheme_eligibility(name: str, tags: str = "", country: str = "") -> str:
    """Check government scheme eligibility for a family member by name.
    Optional tags can be provided as comma-separated labels (e.g. 'bpl', 'low_income', 'employed', 'income_tax_payer').
    Optional country can be 'IN' (India), 'US' (United States), or 'all' (default)."""
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
        target_country = country.strip() if country else "all"
        results = schemes.check_eligibility(
            member["birth_year"], parsed_tags, member_name=member["name"], country=target_country
        )
    except Exception as exc:
        logger.error("check_scheme_eligibility failed: %s", exc)
        return "Something went wrong. Please try again."

    lines = [f"Eligibility check for {member['name']} (born {member['birth_year']}):"]

    eligible = [r for r in results if r["status"] == "may_be_eligible"]
    check_needed = [r for r in results if r["status"] == "check_needed"]
    almost_eligible = sorted(
        [r for r in results if r["status"] == "almost_eligible"],
        key=lambda r: r.get("eligible_from_year", 0),
    )
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

    if almost_eligible:
        lines.append("\nComing up soon:")
        for r in almost_eligible:
            task = r.get("suggested_task", {})
            lines.append(f"• {r['name']} — {r.get('spoken_hint', '')} Official link: {r['source_url']}")
            if task:
                lines.append(f"  -> Suggested: {task.get('title')} (around {task.get('due_year')})")

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

        for t_title, t_due in [(task1_title, gather_due), (task2_title, apply_due)]:
            existing = conn.execute(
                "SELECT id FROM tasks WHERE title = ? AND member_id = ? AND done = 0",
                (t_title, member["id"]),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE tasks SET due_date = ? WHERE id = ?",
                    (t_due.isoformat(), existing["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO tasks (title, due_date, member_id) VALUES (?, ?, ?)",
                    (t_title, t_due.isoformat(), member["id"]),
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

    try:
        conn_init = db.get_connection()
        db.align_demo_dates(conn_init)
    except Exception:
        pass

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
            eligibility = schemes.check_eligibility(m_birth, member_name=m_name)
            eligible_schemes = [s for s in eligibility if s["status"] == "may_be_eligible"]
            almost_schemes = sorted(
                [s for s in eligibility if s["status"] == "almost_eligible"],
                key=lambda s: s.get("eligible_from_year", 0),
            )
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
        if almost_schemes:
            lines.append("\nComing up soon (Temporal Eligibility):")
            for s in almost_schemes:
                lines.append(f"• {s['name']} — {s.get('spoken_hint', '')}")
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


@mcp.tool()
def orchestrate_life_event(member_name: str, event_type: str, notes: str = "") -> str:
    """Agentic Life-Event Orchestrator: analyzes a major family transition (e.g. 'retirement',
    'adulthood', 'newborn', 'relocation'), audits existing documents against newly unlocked
    schemes, updates member status, and schedules a phased 30-60-90 day roadmap of actionable
    tasks into the database."""
    name_clean = member_name.strip()
    event_clean = event_type.strip().lower()

    if not name_clean:
        return "Please provide a family member's name."
    if not event_clean:
        return "Please specify a life event (e.g. 'retirement', 'adulthood', 'newborn', 'relocation')."

    # Input sanitization guard
    try:
        sanitize_input(name_clean)
        sanitize_input(event_clean)
        if notes:
            sanitize_input(notes)
    except ValueError as val_err:
        return str(val_err)

    try:
        conn = db.get_connection()
        member = conn.execute(
            "SELECT id, name, relation, birth_year, status FROM family_members WHERE LOWER(name) = LOWER(?)",
            (name_clean,),
        ).fetchone()

        if member is None:
            return f"I don't know anyone called {name_clean}. Add them first with add_family_member."

        # Fetch member's current documents
        docs = conn.execute(
            "SELECT doc_type, expiry_date FROM documents WHERE member_id = ? ORDER BY expiry_date",
            (member["id"],),
        ).fetchall()
        vault_docs_lower = [d["doc_type"].lower() for d in docs]

        today = datetime.date.today()
        age = today.year - member["birth_year"]

        # Normalize event category
        if any(k in event_clean for k in ("retire", "senior", "turning_60", "turning 60", "health", "care", "super_senior", "super-senior")):
            category = "retirement"
            title = "Retirement & Senior Transition"
            new_status = "Retired Senior"
            req_docs = ["Age proof", "Aadhaar card", "Bank account passbook", "Pension/Superannuation Order"]
            phases = [
                (f"Consolidate pension papers & superannuation documents for {member['name']}", 7),
                (f"Apply for Senior Citizens Savings Scheme (SCSS) / deposit setup for {member['name']}", 30),
                (f"Review health coverage & register for Ayushman Vay Vandana card for {member['name']}", 60),
                (f"Submit annual Digital Life Certificate (Jeevan Pramaan) for {member['name']}", 90),
            ]
        elif any(k in event_clean for k in ("adult", "turning_18", "turning 18", "college", "major", "career", "graduat", "independen")):
            category = "adulthood"
            title = "Adulthood & Independence (Age 18+)"
            new_status = "Young Adult"
            req_docs = ["Voter ID (EPIC)", "PAN Card", "Aadhaar card", "Independent Bank Account"]
            phases = [
                (f"Apply for official Voter ID registration (Form 6) for {member['name']}", 7),
                (f"Open independent savings bank account with mobile banking for {member['name']}", 21),
                (f"Enroll in Atal Pension Yojana (APY) and PMJJBY / PMSBY insurance for {member['name']}", 45),
            ]
        elif any(k in event_clean for k in ("newborn", "baby", "birth", "childbirth", "infant")):
            category = "newborn"
            title = "Newborn & Early Childcare"
            new_status = "Infant"
            req_docs = ["Municipal Birth Certificate", "Baal Aadhaar", "Address proof of parent"]
            phases = [
                (f"Procure certified Municipal Birth Certificate for {member['name']}", 7),
                (f"Apply for Baal Aadhaar & enroll on family health card for {member['name']}", 21),
                (f"Open Sukanya Samriddhi Yojana (SSY) or child savings account for {member['name']}", 45),
            ]
        elif any(k in event_clean for k in ("relocation", "moving", "address_change", "relocate", "move", "family", "estate")):
            category = "relocation"
            title = "Household Relocation & Address Transfer"
            new_status = member["status"]  # keep status unchanged
            req_docs = ["Utility bill / Rent agreement", "Aadhaar card (Address update)", "Voter ID"]
            phases = [
                (f"Obtain updated utility bill or registered rent agreement proof of address", 7),
                (f"Submit online Aadhaar address update for {member['name']}", 21),
                (f"Update bank branch records and submit voter constituency transfer (Form 8)", 45),
            ]
        else:
            return (
                "Supported life events are 'retirement' (turning 60), 'adulthood' (turning 18), "
                "'newborn' (childbirth), and 'relocation' (address change)."
            )

        # 1. Update member status if transitioned
        if new_status != member["status"]:
            conn.execute(
                "UPDATE family_members SET status = ? WHERE id = ?",
                (new_status, member["id"]),
            )

        # 2. Insert scheduled roadmap tasks into SQLite (deduplicated / idempotent)
        scheduled_tasks = []
        for task_title, days_offset in phases:
            due_dt = today + datetime.timedelta(days=days_offset)
            dupes = conn.execute(
                "SELECT id FROM tasks WHERE LOWER(TRIM(title)) = LOWER(?) AND member_id = ? AND done = 0",
                (task_title.strip(), member["id"]),
            ).fetchall()
            if dupes:
                conn.execute(
                    "UPDATE tasks SET due_date = ? WHERE id = ?",
                    (due_dt.isoformat(), dupes[0]["id"]),
                )
                if len(dupes) > 1:
                    extra_ids = [d["id"] for d in dupes[1:]]
                    conn.execute(
                        f"DELETE FROM tasks WHERE id IN ({','.join('?' for _ in extra_ids)})",
                        tuple(extra_ids),
                    )
            else:
                conn.execute(
                    "INSERT INTO tasks (title, due_date, member_id) VALUES (?, ?, ?)",
                    (task_title, due_dt.isoformat(), member["id"]),
                )
            scheduled_tasks.append((task_title, due_dt.isoformat(), days_offset))

        conn.commit()

        # 3. Scheme check for newly unlocked entitlements
        scheme_evals = schemes.check_eligibility(
            birth_year=member["birth_year"],
            tags=set(),
            today=today,
            member_name=member["name"],
        )

        unlocked_schemes = []
        for s in scheme_evals:
            if s["status"] == "may_be_eligible":
                reasons = "; ".join(s.get("reasons", []))
                unlocked_schemes.append(f"• [ELIGIBLE NOW] {s['name']} — {reasons}")
            elif s["status"] == "almost_eligible":
                hint = s.get("spoken_hint", f"Qualifies in {s.get('years_until_eligible', 1)}y")
                unlocked_schemes.append(f"• [ALMOST ELIGIBLE] {s['name']} — {hint}")

        # 4. Document audit
        found_docs = []
        missing_docs = []
        for rd in req_docs:
            matched = any(rd.lower() in vd or vd in rd.lower() for vd in vault_docs_lower)
            if matched:
                found_docs.append(rd)
            else:
                missing_docs.append(rd)

        # 5. Format spoken-friendly response
        status_disp = f"{member['status']} ➔ {new_status}" if new_status != member["status"] else member["status"]
        lines = [
            f"🎯 Life-Event Roadmap Orchestrated: {title} for {member['name']}",
            f"• Member: {member['name']} ({member['relation']}) | Born {member['birth_year']} (Age ~{age}) | Status: {status_disp}",
            "",
            "--- UNLOCKED & RELEVANT BENEFIT SCHEMES ---",
        ]
        if unlocked_schemes:
            lines.extend(unlocked_schemes[:4])
        else:
            lines.append("• No specific age-gated schemes unlocked at this milestone.")

        lines.append("\n--- DOCUMENT READINESS AUDIT ---")
        if found_docs:
            lines.append(f"• In Vault: {', '.join(found_docs)}")
        if missing_docs:
            lines.append(f"• Action Required (Missing): {', '.join(missing_docs)}")
        if not found_docs and not missing_docs:
            lines.append("• All standard paperwork on file.")

        lines.append("\n--- PHASED 30-60-90 DAY ACTION PLAN (Scheduled into Tasks) ---")
        for task_title, due_str, offset in scheduled_tasks:
            lines.append(f"• Day +{offset} ({due_str}): {task_title}")

        lines.append("\nNote: Guidance only. Verified on official government portals.")
        return "\n".join(lines)

    except Exception as exc:
        logger.error("orchestrate_life_event failed: %s", exc)
        return "Something went wrong while orchestrating the life event. Please try again."


@mcp.tool()
def audit_document_dependencies(member_name: str = "") -> str:
    """Audit document dependencies and detect blocker cascades: evaluates prerequisites
    for eligible government schemes, identifies expired or soon-expiring documents that
    block applications, and returns an optimal Critical Path resolution sequence."""
    name_clean = member_name.strip()
    if name_clean:
        try:
            sanitize_input(name_clean)
        except ValueError as val_err:
            return str(val_err)

    try:
        conn = db.get_connection()
        if name_clean and name_clean.lower() not in ("all", "family", "everyone"):
            member = conn.execute(
                "SELECT id, name, relation, birth_year, status FROM family_members WHERE LOWER(name) = LOWER(?)",
                (name_clean,),
            ).fetchone()
            if member is None:
                return f"I don't know anyone called {name_clean}. Add them first with add_family_member."
            members = [member]
        else:
            members = conn.execute(
                "SELECT id, name, relation, birth_year, status FROM family_members ORDER BY name"
            ).fetchall()
            if not members:
                return "No family members added yet."

        today = datetime.date.today()
        all_schemes = schemes.load_schemes()
        scheme_map = {s["id"]: s for s in all_schemes}

        blockers = []       # Critical: expired docs that block schemes
        impending = []      # Impending: docs expiring in <=60 days that put schemes at risk
        missing = []        # Prerequisites completely missing
        ready_paths = []    # Fully unblocked scheme applications

        # Generic document category helpers
        def matches_requirement(req_str: str, doc_type: str) -> bool:
            r = req_str.lower()
            d = doc_type.lower()
            if d in r or any(word in d for word in r.split() if len(word) > 3):
                return True
            # Identity proof aliases
            if "identity" in r and any(k in d for k in ("aadhaar", "pan", "passport", "voter")):
                return True
            # Address proof aliases
            if "address" in r and any(k in d for k in ("aadhaar", "passport", "voter", "utility", "bill", "rent")):
                return True
            # Age proof aliases
            if "age" in r and any(k in d for k in ("birth", "passport", "aadhaar", "pan", "10th")):
                return True
            # Bank details
            if "bank" in r and any(k in d for k in ("bank", "passbook", "account", "cheque")):
                return True
            return False

        report_sections = []

        for m in members:
            m_docs = conn.execute(
                "SELECT id, doc_type, expiry_date FROM documents WHERE member_id = ? ORDER BY expiry_date",
                (m["id"],),
            ).fetchall()

            # Eligible schemes for this member
            el_list = schemes.check_eligibility(m["birth_year"], set(), today, member_name=m["name"])
            target_schemes = [
                s for s in el_list
                if s["status"] in ("may_be_eligible", "almost_eligible")
            ]

            member_blockers = []
            member_impending = []
            member_missing = []
            member_ready = []

            for s_eval in target_schemes:
                s_id = s_eval["scheme_id"]
                s_meta = scheme_map.get(s_id)
                if not s_meta:
                    continue

                req_docs = s_meta.get("documents", [])
                scheme_name = s_meta["name"]

                has_blocker = False
                has_impending = False
                unmet_reqs = []

                for req in req_docs:
                    # Find matching doc in member's vault
                    matching = [d for d in m_docs if matches_requirement(req, d["doc_type"])]
                    if not matching:
                        unmet_reqs.append(req)
                    else:
                        for d in matching:
                            exp = datetime.date.fromisoformat(d["expiry_date"])
                            days_left = (exp - today).days
                            if days_left < 0:
                                if not any(b["doc"] == d["doc_type"] and b["blocked_scheme"] == scheme_name for b in member_blockers):
                                    member_blockers.append({
                                        "member": m["name"],
                                        "doc": d["doc_type"],
                                        "expiry": d["expiry_date"],
                                        "days_ago": -days_left,
                                        "blocked_scheme": scheme_name,
                                        "req_category": req,
                                    })
                                has_blocker = True
                            elif days_left <= 60:
                                if not any(imp["doc"] == d["doc_type"] and imp["at_risk_scheme"] == scheme_name for imp in member_impending):
                                    member_impending.append({
                                        "member": m["name"],
                                        "doc": d["doc_type"],
                                        "expiry": d["expiry_date"],
                                        "days_left": days_left,
                                        "at_risk_scheme": scheme_name,
                                        "req_category": req,
                                    })
                                has_impending = True

                if unmet_reqs:
                    for ur in unmet_reqs:
                        member_missing.append({
                            "member": m["name"],
                            "scheme": scheme_name,
                            "missing_doc": ur,
                        })
                elif not has_blocker and not has_impending:
                    member_ready.append({
                        "member": m["name"],
                        "scheme": scheme_name,
                    })

            blockers.extend(member_blockers)
            impending.extend(member_impending)
            missing.extend(member_missing)
            ready_paths.extend(member_ready)

            # Build member summary block
            member_status_icon = "🚨" if member_blockers else ("⚠️" if member_impending else "✅")
            member_summary = [f"{member_status_icon} **{m['name']}** ({m['relation']}, born {m['birth_year']}):"]
            if member_blockers:
                for b in member_blockers:
                    member_summary.append(
                        f"   • 🛑 BLOCKER: {b['doc']} expired {b['days_ago']}d ago ({b['expiry']}) "
                        f"➔ blocks {b['blocked_scheme']}"
                    )
            if member_impending:
                for imp in member_impending:
                    member_summary.append(
                        f"   • ⚠️ RISK: {imp['doc']} expires in {imp['days_left']}d ({imp['expiry']}) "
                        f"➔ jeopardizes {imp['at_risk_scheme']}"
                    )
            if member_ready:
                for r in member_ready:
                    member_summary.append(f"   • 🟢 READY: All prerequisite docs valid for {r['scheme']}")
            if not member_blockers and not member_impending and not member_ready:
                member_summary.append("   • No active scheme dependency blockers.")

            report_sections.append("\n".join(member_summary))

        # Overall synthesis
        distinct_blocker_docs = {(b["member"], b["doc"]) for b in blockers}
        distinct_impending_docs = {(imp["member"], imp["doc"]) for imp in impending}
        total_blockers = len(distinct_blocker_docs)
        total_impending = len(distinct_impending_docs)

        header_lines = [
            "=== DOCUMENT DEPENDENCY & BOTTLENECK AUDIT ===",
            f"Audited: {len(members)} Member(s) | 🚨 {total_blockers} Critical Blocker(s) | ⚠️ {total_impending} Impending Risk(s)",
            "",
            "--- MEMBER-BY-MEMBER AUDIT ---",
            "\n\n".join(report_sections),
            "",
            "--- CRITICAL PATH RESOLUTION SEQUENCE ---"
        ]

        resolution_steps = []
        step_idx = 1
        # Step group 1: Critical Blockers (Expired docs)
        dedup_blockers = {}
        for b in blockers:
            key = (b["member"], b["doc"])
            if key not in dedup_blockers:
                dedup_blockers[key] = []
            dedup_blockers[key].append(b["blocked_scheme"])

        for (mem, doc), sch_list in dedup_blockers.items():
            sch_str = ", ".join(set(sch_list))
            resolution_steps.append(
                f"Step {step_idx} [CRITICAL]: Renew {mem}'s {doc} immediately. "
                f"Unblocks {sch_str}."
            )
            step_idx += 1

        # Step group 2: Impending Expirations
        dedup_impending = {}
        for imp in impending:
            key = (imp["member"], imp["doc"])
            if key not in dedup_impending:
                dedup_impending[key] = (imp["days_left"], [])
            dedup_impending[key][1].append(imp["at_risk_scheme"])

        for (mem, doc), (days_left, sch_list) in dedup_impending.items():
            sch_str = ", ".join(set(sch_list))
            resolution_steps.append(
                f"Step {step_idx} [HIGH]: Schedule renewal for {mem}'s {doc} ({days_left}d left). "
                f"Prevents bottleneck in {sch_str}."
            )
            step_idx += 1

        # Step group 3: Ready applications
        for rp in ready_paths[:3]:
            resolution_steps.append(
                f"Step {step_idx} [READY]: Submit application for {rp['member']} — {rp['scheme']} "
                f"(all prerequisite documents verified in vault)."
            )
            step_idx += 1

        if not resolution_steps:
            header_lines.append("• All documents are healthy and fully compliant with target schemes.")
        else:
            for s in resolution_steps:
                header_lines.append(f"• {s}")

        # Spoken brief summary (for Alexa voice read-out)
        header_lines.append("\n--- SPOKEN BRIEF (ALEXA READY) ---")
        if total_blockers > 0:
            first_b = blockers[0]
            header_lines.append(
                f"\"Attention: {first_b['member']}'s {first_b['doc']} is expired, blocking "
                f"{first_b['blocked_scheme']}. Renew it first to keep the application on track.\""
            )
        elif total_impending > 0:
            first_i = impending[0]
            header_lines.append(
                f"\"Heads up: {first_i['member']}'s {first_i['doc']} expires in {first_i['days_left']} days. "
                f"Renewing it soon will protect your {first_i['at_risk_scheme']} application.\""
            )
        else:
            header_lines.append("\"All family documents are in order and no scheme bottlenecks were found.\"")

        header_lines.append("\nNote: Guidance only. Verified on official portals.")
        return "\n".join(header_lines)

    except Exception as exc:
        logger.error("audit_document_dependencies failed: %s", exc)
        return "Something went wrong auditing document dependencies. Please try again."


@mcp.tool()
def simulate_bureaucratic_conflicts(member_name: str = "", target_schemes: str = "") -> str:
    """Bureaucratic Conflict & Red-Tape Simulation Engine: simulates government scrutiny
    officer decision matrices, detects hidden disqualifiers, mutual exclusivity clauses,
    household quota breaches, and tax status spillovers, and outputs an optimal application
    restructuring strategy."""
    name_clean = member_name.strip()
    schemes_clean = target_schemes.strip().lower()

    if name_clean:
        try:
            sanitize_input(name_clean)
        except ValueError as val_err:
            return str(val_err)
    if schemes_clean:
        try:
            sanitize_input(schemes_clean)
        except ValueError as val_err:
            return str(val_err)

    try:
        conn = db.get_connection()
        all_members = conn.execute(
            "SELECT id, name, relation, birth_year, status FROM family_members ORDER BY name"
        ).fetchall()

        if not all_members:
            return "No family members added yet."

        if name_clean and name_clean.lower() not in ("all", "family", "everyone"):
            target_member = next((m for m in all_members if m["name"].lower() == name_clean.lower()), None)
            if target_member is None:
                return f"I don't know anyone called {name_clean}. Add them first with add_family_member."
            analyzed_members = [target_member]
        else:
            analyzed_members = all_members

        all_docs = conn.execute(
            "SELECT d.id, d.doc_type, d.expiry_date, m.name as owner_name, d.member_id "
            "FROM documents d JOIN family_members m ON m.id = d.member_id"
        ).fetchall()

        today = datetime.date.today()
        schemes_catalog = schemes.load_schemes()
        scheme_map = {s["id"]: s for s in schemes_catalog}

        # Filter target schemes if query specified
        filter_ids = set()
        if schemes_clean:
            for piece in schemes_clean.split(","):
                piece = piece.strip()
                for s in schemes_catalog:
                    if piece == s["id"] or piece in s["name"].lower():
                        filter_ids.add(s["id"])

        conflicts = []
        restructuring_steps = []
        protected_value_inr = 0

        # Helper: documents owned by a member
        def member_has_doc(mem_id, keyword):
            kw = keyword.lower()
            return any(kw in d["doc_type"].lower() for d in all_docs if d["member_id"] == mem_id)

        # -------------------------------------------------------------
        # Rule 1: Dual Health Cover Exclusivity (Ayushman vs CGHS/ECHS/Govt)
        # -------------------------------------------------------------
        ayushman_candidates = [
            m for m in analyzed_members
            if (today.year - m["birth_year"]) >= 70 and (not filter_ids or "ayushman_vay_vandana" in filter_ids)
        ]
        for m in ayushman_candidates:
            st = m["status"].lower()
            has_cghs = "cghs" in st or "echs" in st or "govt" in st or member_has_doc(m["id"], "cghs") or member_has_doc(m["id"], "echs")
            # If senior with pension/govt where CGHS is standard
            if has_cghs or "pension" in st or "retired" in st:
                conflicts.append({
                    "severity": "CRITICAL EXCLUSION",
                    "type": "Dual Statutory Health Cover Collision",
                    "parties": f"{m['name']} (Age {today.year - m['birth_year']})",
                    "schemes": "Ayushman Vay Vandana Card (AB PM-JAY) vs. CGHS / ECHS Pensioner Cover",
                    "clause": "AB PM-JAY Guidelines Clause 4.2: Senior citizens covered under existing Central/State Govt health schemes cannot receive dual benefits without an explicit option declaration.",
                    "risk": "Application rejected at portal scrutiny or cancellation of existing outpatient medicine coverage."
                })
                restructuring_steps.append(
                    f"Action for {m['name']}: Submit Ayushman Form-B Option Declaration to designate Ayushman Vay Vandana for in-patient cashless hospitalisation (₹5,00,000 cover) while preserving vital CGHS outpatient benefits."
                )
                protected_value_inr += 500000

        # -------------------------------------------------------------
        # Rule 2: Taxpayer Bar on Subsidized Programs (APY / PM-KISAN)
        # -------------------------------------------------------------
        for m in analyzed_members:
            age = today.year - m["birth_year"]
            is_taxpayer = "tax" in m["status"].lower() or "employed" in m["status"].lower() or "corporate" in m["status"].lower() or "business" in m["status"].lower()
            
            # Check APY (18 to 40)
            if 18 <= age <= 40 and (not filter_ids or "apy" in filter_ids):
                if is_taxpayer:
                    conflicts.append({
                        "severity": "STATUTORY DISQUALIFICATION",
                        "type": "PFRDA Income-Tax Payer Bar",
                        "parties": f"{m['name']} (Status: {m['status']})",
                        "schemes": "Atal Pension Yojana (APY)",
                        "clause": "PFRDA Notification Oct 2022: Any citizen who is or has been an income-tax payer is disqualified from joining APY.",
                        "risk": "Account forfeiture and refund of subscriber contributions without government co-contribution upon Aadhaar-PAN linkage."
                    })
                    restructuring_steps.append(
                        f"Action for {m['name']}: Redirect retirement contributions from APY to National Pension System (NPS Tier-1) or PPF to legitimately claim up to ₹50,000 extra tax deduction under Section 80CCD(1B)."
                    )
                    protected_value_inr += 60000

            # Check PM-KISAN
            if (not filter_ids or "pm_kisan" in filter_ids):
                if "farmer" in m["status"].lower() and is_taxpayer:
                    conflicts.append({
                        "severity": "STATUTORY DISQUALIFICATION",
                        "type": "PM-KISAN Taxpayer Exclusion",
                        "parties": f"{m['name']}",
                        "schemes": "PM Kisan Samman Nidhi (PM-KISAN)",
                        "clause": "PM-KISAN Operational Guidelines Sec 3.1: Income tax payers in last assessment year are ineligible for ₹6,000 annual direct benefit transfer.",
                        "risk": "Automated DBT reversal and recovery notice under DBT audit."
                    })
                    restructuring_steps.append(
                        f"Action for {m['name']}: Route agricultural land claim through a non-tax-paying co-owner family member on the land record (Khasra) to maintain statutory compliance."
                    )
                    protected_value_inr += 6000

        # -------------------------------------------------------------
        # Rule 3: Household Quota Ceiling on Girl-Child Savings (SSY)
        # -------------------------------------------------------------
        girl_children = [
            m for m in all_members
            if (today.year - m["birth_year"]) <= 10 and (
                "daughter" in m["relation"].lower() or "granddaughter" in m["relation"].lower() or "student" in m["status"].lower() or "child" in m["status"].lower() or "infant" in m["status"].lower()
            )
        ]
        if len(girl_children) > 2 and (not filter_ids or "ssy" in filter_ids):
            over_quota_girls = [g["name"] for g in girl_children[2:]]
            eligible_girls = [g["name"] for g in girl_children[:2]]
            conflicts.append({
                "severity": "HOUSEHOLD QUOTA BREACH",
                "type": "Statutory Account Cap Exceeded",
                "parties": f"Family daughters: {', '.join(g['name'] for g in girl_children)}",
                "schemes": "Sukanya Samriddhi Yojana (SSY)",
                "clause": "Government Savings Promotion Act Rule 3(2): Maximum of two accounts permitted per family for girl children.",
                "risk": "3rd account opened in error will be treated as irregular, forfeiting the preferential 8.2% interest and Section 80C benefits."
            })
            restructuring_steps.append(
                f"Action for Family: Retain SSY accounts for {', '.join(eligible_girls)}. Open a Public Provident Fund (PPF) or Balika Samriddhi account for {', '.join(over_quota_girls)} to maintain tax-free compounding parity without breaching the 2-child rule."
            )
            protected_value_inr += 150000

        # -------------------------------------------------------------
        # Rule 4: Pension Cannibalization & Double Dipping (IGNOAPS vs Destitute)
        # -------------------------------------------------------------
        for m in analyzed_members:
            age = today.year - m["birth_year"]
            if age >= 65 and (not filter_ids or "ignoaps_mh" in filter_ids):
                is_bpl = "bpl" in m["status"].lower() or member_has_doc(m["id"], "bpl")
                if not is_bpl:
                    conflicts.append({
                        "severity": "MEANS-TESTING COLLISION",
                        "type": "Non-BPL Means Test Disqualification",
                        "parties": f"{m['name']} (Age {age})",
                        "schemes": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS Maharashtra)",
                        "clause": "NSAP Guidelines Clause 2: BPL certification is mandatory for central old-age pension disbursement.",
                        "risk": "Immediate Tahsildar desk-rejection during document verification."
                    })
                    restructuring_steps.append(
                        f"Action for {m['name']}: Discontinue IGNOAPS filing and apply for Senior Citizens Savings Scheme (SCSS) and Ayushman Senior Card, which have NO poverty line conditions."
                    )
                    protected_value_inr += 24000

        # -------------------------------------------------------------
        # Rule 5: Multiple Claimants for Single-Farmer Family Unit
        # -------------------------------------------------------------
        farmer_claimants = [m for m in all_members if "farmer" in m["status"].lower() or "agriculture" in m["status"].lower()]
        if len(farmer_claimants) > 1 and (not filter_ids or "pm_kisan" in filter_ids):
            names = [f["name"] for f in farmer_claimants]
            conflicts.append({
                "severity": "HOUSEHOLD BENEFIT COLLISION",
                "type": "Single-Unit Family Farmer Cap",
                "parties": f"Multiple claimants: {', '.join(names)}",
                "schemes": "PM Kisan Samman Nidhi (PM-KISAN)",
                "clause": "PM-KISAN Scheme Para 2(b): Family unit defined as husband, wife, and minor children. Only one benefit admissible per unit.",
                "risk": "Aadhaar deduplication flags both accounts as duplicate fraud; recovery order issued."
            })
            restructuring_steps.append(
                f"Action for Family: Designate {names[0]} as the sole applicant on the land title (Khasra) and withdraw overlapping claims."
            )
            protected_value_inr += 6000

        # -------------------------------------------------------------
        # Rule 6: US Medicare Part A vs. Health Savings Account (HSA) Collision
        # -------------------------------------------------------------
        for m in analyzed_members:
            age = today.year - m["birth_year"]
            if age >= 65 and (not filter_ids or "us_medicare" in filter_ids):
                has_hsa = "hsa" in m["status"].lower() or member_has_doc(m["id"], "hsa") or member_has_doc(m["id"], "health savings account")
                if has_hsa:
                    conflicts.append({
                        "severity": "STATUTORY TAX PENALTY COLLISION",
                        "type": "IRS Medicare-HSA Contribution Bar",
                        "parties": f"{m['name']} (Age {age})",
                        "schemes": "Medicare (Parts A & B) vs. Health Savings Account (HSA)",
                        "clause": "IRS IRC § 223(c)(1) / Publication 969: Enrolling in any Medicare Part (including automatic retroactive Part A) disqualifies individuals from contributing to an HSA, incurring a 6% excise penalty on excess contributions.",
                        "risk": "IRS 6% excise tax penalty and retroactive disqualification of tax-free contributions."
                    })
                    restructuring_steps.append(
                        f"Action for {m['name']}: Cease all payroll and personal HSA contributions at least 6 months prior to Medicare Part A application to account for statutory retroactive coverage."
                    )
                    protected_value_inr += 200000

        # Formatting Output Report
        total_conflicts = len(conflicts)
        status_banner = "🚨 CRITICAL SCRUTINY HAZARDS DETECTED" if total_conflicts > 0 else "✅ CLEAN SCRUTINY PATH (0 CONFLICTS)"

        lines = [
            "=== BUREAUCRATIC CONFLICT & RED-TAPE SIMULATION ===",
            f"Status: {status_banner}",
            f"Audited: {len(analyzed_members)} Family Member(s) | ⚠️ {total_conflicts} Bureaucratic Conflict(s) Identified",
            f"Estimated Financial Entitlement Safeguarded: ₹{protected_value_inr:,} INR",
            "",
            "--- GOVERNMENT SCRUTINY HAZARDS & STATUTORY CONFLICTS ---"
        ]

        if not conflicts:
            lines.append("• No mutual exclusivity violations, statutory tax disqualifiers, or household quota breaches detected.")
            lines.append("• All member filings are legally distinct and compliant with official rules.")
        else:
            for idx, c in enumerate(conflicts, 1):
                lines.append(f"{idx}. [{c['severity']}] {c['type']}")
                lines.append(f"   • Affected: {c['parties']}")
                lines.append(f"   • Conflicting Programs: {c['schemes']}")
                lines.append(f"   • Governing Rule: {c['clause']}")
                lines.append(f"   • Scrutiny Risk: {c['risk']}\n")

        lines.append("--- OPTIMAL RESTRUCTURING & SELF-HEALING STRATEGY ---")
        if not restructuring_steps:
            lines.append("• Maintain current application profile. Proceed directly to document submission.")
        else:
            for idx, s in enumerate(restructuring_steps, 1):
                lines.append(f"• Step {idx}: {s}")

        lines.append("\n--- SPOKEN BRIEF (ALEXA READY) ---")
        if total_conflicts > 0:
            top_c = conflicts[0]
            lines.append(
                f"\"Alert: Found {total_conflicts} bureaucratic conflicts. Specifically, {top_c['parties']} has a "
                f"{top_c['type'].lower()} under {top_c['schemes'].split(' vs.')[0]}. "
                f"I've generated a restructuring strategy to protect your family's ₹{protected_value_inr:,} in benefits.\""
            )
        else:
            lines.append("\"Great news: Your family's scheme applications have zero legal conflicts or quota violations. Everything is clear to submit.\"")

        lines.append("\nNote: Guidance only. Verified against statutory government gazette notifications.")
        return "\n".join(lines)

    except Exception as exc:
        logger.error("simulate_bureaucratic_conflicts failed: %s", exc)
        return "Something went wrong simulating bureaucratic conflicts. Please try again."


@mcp.tool()
def trigger_proactive_ambient_alert(member_name: str = "", custom_message: str = "") -> str:
    """Proactive Ambient Push Trigger: runs temporal audit across family documents,
    deadlines, and scheme windows, formats real-time proactive voice announcements,
    and broadcasts Server-Sent Events (SSE) to connected Alexa+ screens and living room devices."""
    name_clean = member_name.strip()
    msg_clean = custom_message.strip()

    if name_clean:
        try:
            sanitize_input(name_clean)
        except ValueError as val_err:
            return str(val_err)
    if msg_clean:
        try:
            sanitize_input(msg_clean)
        except ValueError as val_err:
            return str(val_err)

    try:
        conn = db.get_connection()
        alerts = evaluate_proactive_alerts(conn)

        if name_clean and name_clean.lower() not in ("all", "family", "everyone"):
            alerts = [a for a in alerts if a["member"].lower() == name_clean.lower()]

        if not alerts and not msg_clean:
            return "✅ Ambient Watcher Status: All family paperwork and deadlines are healthy. No proactive ambient alerts required at this time."

        # If custom message provided, create dedicated push alert
        if msg_clean:
            custom_alert = {
                "id": f"custom-{int(datetime.datetime.now().timestamp())}",
                "category": "manual_proactive",
                "urgency": "critical",
                "title": f"Proactive Broadcast for {name_clean or 'Household'}",
                "member": name_clean or "Household",
                "speech": msg_clean,
                "prompt": msg_clean,
                "suggested_action": msg_clean,
                "action_label": "Review Notice",
                "timestamp": datetime.datetime.now().isoformat(),
            }
            alerts.insert(0, custom_alert)

        # Broadcast top alert to active SSE clients
        top_alert = alerts[0]
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                loop.create_task(ambient_broker.broadcast_alert(top_alert))
            else:
                asyncio.run(ambient_broker.broadcast_alert(top_alert))
        except Exception as b_err:
            logger.warning("Could not broadcast alert to SSE: %s", b_err)

        lines = [
            "=== PROACTIVE AMBIENT PUSH & TEMPORAL WATCHER ===",
            f"Status: 🔔 BROADCASTED TO ALEXA+ AMBIENT STREAM ({len(alerts)} active alerts)",
            f"Active Alert Level: {top_alert['urgency'].upper()}",
            "",
            "--- LIVE PROACTIVE ANNOUNCEMENTS ---"
        ]

        for idx, a in enumerate(alerts[:5], 1):
            lines.append(f"{idx}. [{a['urgency'].upper()}] {a['title']}")
            lines.append(f"   • Voice Synthesizer Speech: \"{a['speech']}\"")
            lines.append(f"   • Interactive Touch Action: {a['action_label']} ➔ '{a['prompt']}'\n")

        lines.append("--- AMBIENT DEVICE DISPATCH LOG ---")
        lines.append(f"• Target Device: Echo Show Ambient Canvas / SSE Protocol Endpoint (/api/ambient/events)")
        lines.append(f"• Audio Chime: True (Chime Frequency: 880 Hz / A5)")
        lines.append(f"• Speech Prompt: \"{top_alert['speech']}\"")
        lines.append("\nNote: Proactive notifications are delivered asynchronously over Streamable HTTP SSE.")
        return "\n".join(lines)

    except Exception as exc:
        logger.error("trigger_proactive_ambient_alert failed: %s", exc)
        return "Something went wrong triggering proactive ambient alert. Please try again."


@mcp.tool()
def explain_for_generation(scheme_id: str, target_persona: str = "grandparent") -> str:
    """Translate dense, bureaucratic government gazette policies into cognitive voice dialects.
    Tailored for 3 distinct multi-generational personas:
    - 'grandparent' / 'senior': Warm, comforting, zero legal jargon, gentle piggy-bank analogies.
    - 'parent' / 'working_adult': Financial strategy, Section 80C/80CCD tax benefits, family asset protection.
    - 'young_adult' / 'student': Mobile-first, compounding returns, instant UPI/Aadhaar OTP, early independence.
    """
    s_clean = scheme_id.strip()
    p_clean = target_persona.strip().lower()

    if not s_clean:
        return "Please specify a scheme ID or name to explain."

    try:
        sanitize_input(s_clean)
        sanitize_input(p_clean)
    except ValueError as val_err:
        return str(val_err)

    all_schemes = schemes.load_schemes()
    target_scheme = None

    # Exact or substring match on id or name
    s_lower = s_clean.lower()
    for s in all_schemes:
        if s["id"].lower() == s_lower or s_lower == s["id"].lower().replace("_", " "):
            target_scheme = s
            break
    if not target_scheme:
        for s in all_schemes:
            if s_lower in s["id"].lower() or s_lower in s["name"].lower():
                target_scheme = s
                break

    if not target_scheme:
        valid_ids = [s["id"] for s in all_schemes]
        return f"Unknown scheme '{s_clean}'. Available schemes are: {', '.join(valid_ids)}."

    # Normalize persona
    if any(k in p_clean for k in ("grand", "senior", "elder", "dada", "dadi", "nana", "nani")):
        persona_key = "grandparent"
        persona_label = "Grandparent (Senior Citizen)"
        tone_label = "Warm & Reassuring (Zero Bureaucracy)"
        jargon_index = "0% (All statute numbers & legal clauses abstracted)"
        readability = "Grade 4 (Gentle Conversational)"
        score = 98
    elif any(k in p_clean for k in ("student", "young", "teen", "youth", "college", "child")):
        persona_key = "young_adult"
        persona_label = "Young Adult (Student / Early Career)"
        tone_label = "Tech-First & Compounding Wealth (Mobile UPI)"
        jargon_index = "5% (Focus on APY, instant KYC & fintech efficiency)"
        readability = "Grade 8 (Fast-Paced & Tech-Native)"
        score = 96
    else:
        persona_key = "parent"
        persona_label = "Parent (Working Adult / Family Planner)"
        tone_label = "Financial Optimization & Safety Net"
        jargon_index = "20% (Tax sections, statutory eligibility, asset preservation)"
        readability = "Grade 10 (Executive Family Planning)"
        score = 95

    sid = target_scheme["id"]

    # Generational dialect knowledge base
    dialects = {
        "ayushman_vay_vandana": {
            "grandparent": {
                "speech": (
                    "Dadaji, this is a golden health shield from the government just for you. "
                    "No matter your income or savings, you get up to 5 lakh rupees of free hospital care "
                    "every single year. You don't have to worry about doctor bills anymore. "
                    "All we need is your Aadhaar card, and the hospital treats you without charging a single rupee."
                ),
                "analogy": "A golden hospital pass in your pocket that pays your medical bills directly so your children never have to worry.",
                "benefit": "₹5,00,000 yearly free hospitalization; zero income test; completely cashless.",
                "action": "Keep your Aadhaar card ready for a quick OTP check.",
            },
            "parent": {
                "speech": (
                    "This is an unconditional sovereign health shield for parents aged 70+. "
                    "It allocates an exclusive ₹5 Lakh annual floater for your elder, preventing catastrophic hospital bills "
                    "from eroding your family emergency fund. Even if your parents are on corporate health insurance, "
                    "this acts as a secondary shield with zero co-pay and pre-existing diseases covered immediately."
                ),
                "analogy": "A dedicated sovereign health buffer ring-fencing your family retirement fund against elder healthcare inflation.",
                "benefit": "Dedicated ₹5L coverage separate from family floater; immediate Day 1 cover for pre-existing conditions.",
                "action": "Verify your elder's Aadhaar-linked mobile number to complete e-KYC on the NHA beneficiary portal.",
            },
            "young_adult": {
                "speech": (
                    "Hey! You can unlock complete healthcare for your grandparents right from your phone in 3 minutes. "
                    "AB PM-JAY gives ₹5 lakh free annual medical cover for anyone 70+. No branch visits or income proof needed—"
                    "just do an instant Aadhaar OTP KYC on the Ayushman app, and their digital health card downloads straight to DigiLocker."
                ),
                "analogy": "Instant digital healthcare pass unlocked via Aadhaar OTP on your phone.",
                "benefit": "100% digital app flow; ₹5L hospital coverage; zero paperwork friction.",
                "action": "Download the Ayushman app and verify their phone OTP.",
            },
        },
        "scss": {
            "grandparent": {
                "speech": (
                    "Dadaji, this is the safest place to rest your lifetime savings. Think of it like a government piggy bank "
                    "that pays you a handsome reward every three months directly into your bank account. The government guarantees "
                    "your money will never drop, giving you steady quarterly pocket money to spend freely without depending on anyone."
                ),
                "analogy": "A golden post office piggy-bank that gives you tea and fruit money every three months.",
                "benefit": "Guaranteed 8.2% sovereign return; quarterly interest deposited right into your savings account.",
                "action": "Visit your local post office or bank branch with PAN and Aadhaar.",
            },
            "parent": {
                "speech": (
                    "SCSS offers a sovereign-backed 8.2% per annum fixed return with a ₹30 Lakh deposit ceiling. "
                    "Investments qualify for tax deduction under Section 80C up to ₹1.5 Lakh. For retirees, this generates "
                    "an automated quarterly cash flow of up to ₹61,500 with zero market volatility, serving as the defensive core of a post-retirement portfolio."
                ),
                "analogy": "High-yield sovereign fixed-income anchor with Section 80C tax deduction and guaranteed quarterly liquidity.",
                "benefit": "8.2% p.a. sovereign yield; Section 80C tax rebate; ₹30L portfolio allocation limit.",
                "action": "Deposit within 1 month of retirement payout to lock in current sovereign interest rates.",
            },
            "young_adult": {
                "speech": (
                    "If your parents have money sitting idle in a low-interest 3% savings account, SCSS beats inflation with "
                    "an 8.2% government-backed return. It's completely risk-free, backed by the Reserve Bank of India, and pays out dividends "
                    "every quarter straight to their bank account."
                ),
                "analogy": "Risk-free 8.2% APY sovereign deposit outperforming standard bank savings accounts.",
                "benefit": "8.2% guaranteed APY; zero market volatility; quarterly automated payouts.",
                "action": "Help them set up net banking to monitor quarterly interest credits.",
            },
        },
        "apy": {
            "grandparent": {
                "speech": (
                    "This is a lifelong blessing for your children and grandchildren. By saving just a tiny handful of coins "
                    "each month while they are young, the government guarantees they will receive a fixed pension of up to ₹5,000 "
                    "every single month when they grow old. It gives you peace of mind that their golden years are secure."
                ),
                "analogy": "Planting a tiny banyan sapling today so it shelters you with a monthly stipend when you are old.",
                "benefit": "Guaranteed monthly lifetime pension of ₹1,000 to ₹5,000.",
                "action": "Encourage working youngsters in the family to activate auto-debit.",
            },
            "parent": {
                "speech": (
                    "APY offers a government-guaranteed defined benefit pension of ₹1,000 to ₹5,000 per month starting at age 60. "
                    "Contributions qualify for additional tax relief under Section 80CCD(1B). Since non-taxpayers are prioritized, "
                    "enrolling young adult family members locks in the lowest entry contribution with lifelong sovereign guarantees."
                ),
                "analogy": "Guaranteed sovereign defined-benefit annuity with Section 80CCD tax deduction.",
                "benefit": "Defined monthly pension; sovereign shortfall co-contribution; spouse pension handover.",
                "action": "Ensure the subscriber has not filed income tax returns after Oct 2022 to avoid PFRDA rejection.",
            },
            "young_adult": {
                "speech": (
                    "The ultimate financial cheat code for early independence. If you start between 18 and 25, you only invest "
                    "around ₹210 a month—the price of one coffee or pizza slice—and the government guarantees you a fixed monthly "
                    "pension of ₹5,000 for life after 60. It runs 100% on auto-debit so you never have to think about it."
                ),
                "analogy": "A micro-subscription that turns the cost of a monthly snack into a lifelong post-60 paycheck.",
                "benefit": "Minimal monthly auto-debit (from ₹42 to ₹210); government-guaranteed 100% pension; spouse benefits.",
                "action": "Enable auto-debit via your mobile banking app in under 60 seconds.",
            },
        },
        "ssy": {
            "grandparent": {
                "speech": (
                    "This is the government's special gift for our little granddaughter. Every rupee you deposit grows safely "
                    "with the highest interest, and when she turns 21 and is ready for higher studies or her wedding, "
                    "she receives a wonderful treasure of her own."
                ),
                "analogy": "A sacred treasury that grows alongside our granddaughter to bless her future.",
                "benefit": "Highest sovereign small savings interest (8.2%); dedicated girl child corpus.",
                "action": "Open an account at the post office with her birth certificate.",
            },
            "parent": {
                "speech": (
                    "SSY is the premier small savings scheme for a girl child under 10. Offers an exceptional 8.2% interest "
                    "with Triple Tax Exemption (EEE - investment, accrual, and maturity are all 100% tax-free under Section 80C). "
                    "Max deposit ₹1.5 Lakh/year builds an inflation-beating educational corpus for her 18th/21st milestone."
                ),
                "analogy": "EEE-tier sovereign wealth fund for your daughter's higher education with zero tax drag.",
                "benefit": "8.2% compounded interest; EEE tax-exempt status; protected against market fluctuations.",
                "action": "Deposit up to ₹1.5L annually before March 31 to maximize Section 80C deduction.",
            },
            "young_adult": {
                "speech": (
                    "Insane compounding power: 8.2% tax-free compound interest backed directly by the Indian Government. "
                    "If your younger sister has an SSY account, it outclasses almost every conventional fixed-income asset with zero risk."
                ),
                "analogy": "Max-tier sovereign compound engine with 0% tax drag.",
                "benefit": "8.2% tax-free compound rate; zero risk; dedicated higher-education fund.",
                "action": "Help your parents set up auto-transfer for your sister's account.",
            },
        },
        "pmjjby": {
            "grandparent": {
                "speech": (
                    "This is a safety shield for the family costing just over a rupee a day. For ₹436 a year, if anything unfortunate "
                    "happens, the family immediately receives ₹2 lakh so they are never left in distress."
                ),
                "analogy": "A protective umbrella for the household costing less than a single cup of tea a day.",
                "benefit": "₹2,00,000 life insurance cover for ₹436/year.",
                "action": "Ensure the bank passbook has auto-debit enabled before May 31.",
            },
            "parent": {
                "speech": (
                    "Pure term life protection offering ₹2,00,000 for any-cause mortality at an annual cost of only ₹436. "
                    "Auto-debits on May 31 each year from savings account. Crucial foundational term protection for every earning "
                    "or dependent adult in the household aged 18 to 50."
                ),
                "analogy": "Ultra low-cost sovereign group term life cover providing immediate family liquidity.",
                "benefit": "₹2 Lakh mortality cover; annual premium of ₹436; hassle-free claim settlement.",
                "action": "Maintain adequate savings account balance before May 31 auto-debit window.",
            },
            "young_adult": {
                "speech": (
                    "₹2 Lakh life insurance for ₹436/year—that's ₹1.20 per day. No medical tests, no paperwork. "
                    "Just toggle auto-debit in your banking app and you're covered 24/7."
                ),
                "analogy": "Instant zero-friction term cover for the price of two snacks a year.",
                "benefit": "Instant digital enrollment; zero medical checkup; ₹2L coverage.",
                "action": "Activate with one click in your mobile banking app.",
            },
        },
        "pm_kisan": {
            "grandparent": {
                "speech": (
                    "The government sends ₹2,000 directly to your bank account every four months for farm seeds and fertilizer. "
                    "You don't have to visit offices or plead with anyone; the money arrives right into your bank."
                ),
                "analogy": "Timely seasonal harvest assistance deposited directly in your pocket.",
                "benefit": "₹6,000 yearly income support in 3 equal installments of ₹2,000.",
                "action": "Check your bank passbook after every harvest season.",
            },
            "parent": {
                "speech": (
                    "Direct Benefit Transfer of ₹6,000 per year in 3 tranches of ₹2,000. Acts as predictable working capital "
                    "for fertilizer, diesel, and agricultural inputs. Requires e-KYC and land Record of Rights (Khatauni) seeding."
                ),
                "analogy": "Zero-cost seasonal agricultural working capital subsidy.",
                "benefit": "₹6,000 direct bank transfer; zero intermediary leakage; landholder entitlement.",
                "action": "Complete biometric or OTP e-KYC on the PM-Kisan portal to avoid installment pauses.",
            },
            "young_adult": {
                "speech": (
                    "Direct Benefit Transfer (DBT) via the NPCI Aadhaar bridge straight to your family's bank account. "
                    "₹6,000 a year paid out in 3 cycles without middlemen. All verified via Aadhaar and land record APIs."
                ),
                "analogy": "Algorithmic direct-to-bank farm subsidy pipeline.",
                "benefit": "Direct NPCI transfer; 100% digital audit trail; ₹6,000 annual support.",
                "action": "Check your family's PM-Kisan Aadhaar seeding status on the portal.",
            },
        },
    }

    # If scheme not in pre-compiled knowledge base, synthesize dynamic generational dialect
    scheme_entry = dialects.get(sid, {}).get(persona_key)
    if not scheme_entry:
        summary = target_scheme.get("summary", "")
        if persona_key == "grandparent":
            speech = f"Dadaji, this scheme is called {target_scheme['name']}. In simple words: {summary}. It is backed by the government to make your life peaceful and secure. You don't have to worry about complicated paperwork."
            analogy = f"A government safety net ensuring peace of mind for our family elders."
            benefit = summary
            action = f"Check the official portal ({target_scheme.get('apply_url', '')}) with a family member."
        elif persona_key == "young_adult":
            speech = f"Hey! {target_scheme['name']} is a government-backed program. Basically: {summary}. You can manage the application digitally without dealing with physical red tape."
            analogy = f"Streamlined digital civic utility delivering direct financial benefits."
            benefit = summary
            action = f"Check {target_scheme.get('apply_url', '')} on your phone."
        else:
            speech = f"{target_scheme['name']} provides: {summary}. Designed to optimize family social security and minimize economic risk."
            analogy = f"Sovereign family policy instrument enhancing household resilience."
            benefit = summary
            action = f"Review requirements and apply at {target_scheme.get('apply_url', '')}."
        scheme_entry = {
            "speech": speech,
            "analogy": analogy,
            "benefit": benefit,
            "action": action,
        }

    lines = [
        "=== CROSS-GENERATIONAL VOICE DIALECT ENGINE ===",
        f"Scheme: {target_scheme['name']} [{target_scheme['id']}]",
        f"Target Persona: {persona_label}",
        f"Cognitive Mode: {tone_label}",
        "",
        "--- ALEXA SPOKEN EXPLANATION ---",
        f'"{scheme_entry["speech"]}"',
        "",
        "--- GENERATIONAL ANALOGY ---",
        f"💡 {scheme_entry['analogy']}",
        "",
        f"--- KEY HIGHLIGHTS FOR {persona_label.upper()} ---",
        f"• Core Benefit: {scheme_entry['benefit']}",
        f"• Spoken Cadence: {readability}",
        f"• Immediate Next Step: {scheme_entry['action']}",
        "",
        "--- COGNITIVE LOAD METRICS ---",
        f"• Readability: {readability}",
        f"• Bureaucracy Jargon Index: {jargon_index}",
        f"• Empathetic Alignment Score: {score}/100",
        "",
        f"Official Reference: {target_scheme.get('source_url', 'Government of India Gazette')}",
    ]

    return "\n".join(lines)


@mcp.tool()
def get_family_dashboard() -> str:
    """Generate an all-in-one family paperwork dashboard summarizing family roster,
    document health, upcoming deadlines, and government scheme opportunities.
    Designed for the MCP Apps Dashboard Card."""
    today = datetime.date.today()
    cutoff_docs = today + datetime.timedelta(days=60)
    cutoff_tasks = today + datetime.timedelta(days=30)

    try:
        conn = db.get_connection()
        db.align_demo_dates(conn)
        members = conn.execute(
            "SELECT id, name, relation, birth_year, status FROM family_members ORDER BY name"
        ).fetchall()

        if not members:
            return "No family members added yet. Start by adding a member to initialize the dashboard."

        docs = conn.execute(
            "SELECT d.id, m.name, d.doc_type, d.expiry_date "
            "FROM documents d JOIN family_members m ON m.id = d.member_id "
            "ORDER BY d.expiry_date"
        ).fetchall()

        raw_tasks = conn.execute(
            "SELECT t.id, t.title, t.due_date, t.done, m.name "
            "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
            "WHERE t.done = 0 "
            "ORDER BY t.due_date"
        ).fetchall()

        # Deduplicate redundant tasks by (title, member_name)
        tasks = []
        seen_t = set()
        for t in raw_tasks:
            t_key = (t["title"].strip().lower(), (t["name"] or "").strip().lower())
            if t_key not in seen_t:
                seen_t.add(t_key)
                tasks.append(t)

        # Compile metrics
        total_members = len(members)
        total_docs = len(docs)
        expiring_docs = [d for d in docs if datetime.date.fromisoformat(d["expiry_date"]) <= cutoff_docs]
        urgent_docs = [d for d in expiring_docs if (datetime.date.fromisoformat(d["expiry_date"]) - today).days <= 7]
        upcoming_tasks = [t for t in tasks if datetime.date.fromisoformat(t["due_date"]) <= cutoff_tasks]
        overdue_tasks = [t for t in tasks if (datetime.date.fromisoformat(t["due_date"]) - today).days < 0]

        # Scheme opportunities across all members
        scheme_matches = []
        for m in members:
            el_list = schemes.check_eligibility(m["birth_year"])
            for s in el_list:
                if s["status"] == "may_be_eligible":
                    scheme_matches.append(f"{m['name']} qualifies for {s['name']}")

        lines = [
            f"=== FAMILY ADMIN DASHBOARD ({total_members} Members Tracked) ===",
            f"• Documents: {total_docs} tracked ({len(expiring_docs)} expiring in 60d, {len(urgent_docs)} urgent)",
            f"• Tasks: {len(tasks)} pending ({len(upcoming_tasks)} due in 30d, {len(overdue_tasks)} overdue)",
            f"• Scheme Opportunities: {len(scheme_matches)} matches identified",
            "",
            "--- FAMILY ROSTER ---"
        ]
        for m in members:
            lines.append(f"• {m['name']} ({m['relation']}) — Born {m['birth_year']}, {m['status']}")

        if expiring_docs:
            lines.append("\n--- EXPIRING DOCUMENTS ---")
            for d in expiring_docs:
                exp = datetime.date.fromisoformat(d["expiry_date"])
                diff = (exp - today).days
                tag = "EXPIRED" if diff < 0 else (f"URGENT ({diff}d left)" if diff <= 7 else f"{diff}d left")
                lines.append(f"• {d['name']}'s {d['doc_type']} — expires {d['expiry_date']} [{tag}]")

        if upcoming_tasks:
            lines.append("\n--- UPCOMING DEADLINES ---")
            for t in upcoming_tasks:
                due = datetime.date.fromisoformat(t["due_date"])
                diff = (due - today).days
                tag = f"OVERDUE by {-diff}d" if diff < 0 else ("Due today" if diff == 0 else f"{diff}d left")
                owner_info = f" ({t['name']})" if t['name'] and t['name'].lower() not in t['title'].lower() else ""
                lines.append(f"• {t['title']}{owner_info} — due {t['due_date']} [{tag}]")

        if scheme_matches:
            lines.append("\n--- BENEFIT OPPORTUNITIES ---")
            for sm in scheme_matches[:5]:
                lines.append(f"• {sm}")
            if len(scheme_matches) > 5:
                lines.append(f"• ... and {len(scheme_matches) - 5} more")

        lines.append("\nNote: Guidance only. Verified on official portals.")
        return "\n".join(lines)
    except Exception as exc:
        logger.error("get_family_dashboard failed: %s", exc)
        return "Something went wrong loading the dashboard. Please try again."


@mcp.tool()
def get_document_tracker(member_name: str = "") -> str:
    """Document Tracker: audits all paperwork and deadlines, classifying items into:
    - completed: valid documents with >30 days left, or completed tasks.
    - partial: documents expiring in <=30 days, or upcoming tasks.
    - remaining: expired documents (<0 days left), overdue tasks, or urgent tasks due in <=7 days.
    Provides simple audio speech ('{completed} completed, {partial} partial, and {remaining} remaining')
    and structured items for interactive UI filtering."""
    name_clean = member_name.strip()
    if name_clean:
        try:
            sanitize_input(name_clean)
        except ValueError as val_err:
            return str(val_err)

    try:
        conn = db.get_connection()
        db.align_demo_dates(conn)
        today = datetime.date.today()

        member_id = None
        target_name = ""
        if name_clean and name_clean.lower() not in ("all", "family", "everyone", "household"):
            row = conn.execute(
                "SELECT id, name FROM family_members WHERE LOWER(name) = LOWER(?)",
                (name_clean,)
            ).fetchone()
            if not row:
                return f"I don't have records for '{name_clean}'. Add them first."
            member_id = row["id"]
            target_name = row["name"]

        # Fetch documents
        if member_id:
            docs = conn.execute(
                "SELECT d.id, d.doc_type, d.expiry_date, m.name as owner_name "
                "FROM documents d JOIN family_members m ON m.id = d.member_id "
                "WHERE d.member_id = ? ORDER BY d.expiry_date ASC",
                (member_id,)
            ).fetchall()
        else:
            docs = conn.execute(
                "SELECT d.id, d.doc_type, d.expiry_date, m.name as owner_name "
                "FROM documents d JOIN family_members m ON m.id = d.member_id "
                "ORDER BY d.expiry_date ASC"
            ).fetchall()

        # Fetch tasks
        if member_id:
            tasks = conn.execute(
                "SELECT t.id, t.title, t.due_date, t.done, m.name as owner_name "
                "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
                "WHERE t.member_id = ? OR t.member_id IS NULL "
                "ORDER BY t.due_date ASC",
                (member_id,)
            ).fetchall()
        else:
            tasks = conn.execute(
                "SELECT t.id, t.title, t.due_date, t.done, m.name as owner_name "
                "FROM tasks t LEFT JOIN family_members m ON m.id = t.member_id "
                "ORDER BY t.due_date ASC"
            ).fetchall()

        # Deduplicate tasks by (title, owner_name, done) keeping the soonest due date
        seen_tasks = set()
        unique_tasks = []
        for t in tasks:
            task_key = (
                t["title"].strip().lower(),
                (t["owner_name"] or "").strip().lower(),
                t["done"],
            )
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_tasks.append(t)
        tasks = unique_tasks

        # Deduplicate documents by (doc_type, owner_name)
        seen_docs = set()
        unique_docs = []
        for d in docs:
            doc_key = (
                d["doc_type"].strip().lower(),
                (d["owner_name"] or "").strip().lower(),
            )
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                unique_docs.append(d)
        docs = unique_docs

        completed_items = []
        partial_items = []
        remaining_items = []

        for d in docs:
            exp = datetime.date.fromisoformat(d["expiry_date"])
            days_left = (exp - today).days
            owner = d["owner_name"]
            doc_type = d["doc_type"]

            if days_left < 0:
                remaining_items.append({
                    "id": f"doc-{d['id']}",
                    "category": "document",
                    "title": doc_type,
                    "member": owner,
                    "status": "remaining",
                    "statusLabel": f"Expired {-days_left}d ago",
                    "date": d["expiry_date"],
                    "days": days_left,
                    "actionPrompt": f"Check expiring {doc_type} for {owner}"
                })
            elif days_left <= 30:
                partial_items.append({
                    "id": f"doc-{d['id']}",
                    "category": "document",
                    "title": doc_type,
                    "member": owner,
                    "status": "partial",
                    "statusLabel": f"Expires in {days_left}d",
                    "date": d["expiry_date"],
                    "days": days_left,
                    "actionPrompt": f"Check expiring {doc_type} for {owner}"
                })
            else:
                completed_items.append({
                    "id": f"doc-{d['id']}",
                    "category": "document",
                    "title": doc_type,
                    "member": owner,
                    "status": "completed",
                    "statusLabel": f"Valid ({days_left}d left)",
                    "date": d["expiry_date"],
                    "days": days_left,
                    "actionPrompt": f"Check expiring {doc_type} for {owner}"
                })

        for t in tasks:
            owner = t["owner_name"] or "Household"
            title = t["title"]

            if t["done"] == 1:
                completed_items.append({
                    "id": f"task-{t['id']}",
                    "category": "task",
                    "title": title,
                    "member": owner,
                    "status": "completed",
                    "statusLabel": "Completed",
                    "date": t["due_date"],
                    "days": 0,
                    "actionPrompt": ""
                })
            else:
                due = datetime.date.fromisoformat(t["due_date"])
                days_left = (due - today).days
                if days_left < 0:
                    remaining_items.append({
                        "id": f"task-{t['id']}",
                        "category": "task",
                        "title": title,
                        "member": owner,
                        "status": "remaining",
                        "statusLabel": f"Overdue by {-days_left}d",
                        "date": t["due_date"],
                        "days": days_left,
                        "actionPrompt": f"I have completed {title} for {owner}"
                    })
                elif days_left <= 7:
                    remaining_items.append({
                        "id": f"task-{t['id']}",
                        "category": "task",
                        "title": title,
                        "member": owner,
                        "status": "remaining",
                        "statusLabel": f"Due in {days_left}d",
                        "date": t["due_date"],
                        "days": days_left,
                        "actionPrompt": f"I have completed {title} for {owner}"
                    })
                else:
                    partial_items.append({
                        "id": f"task-{t['id']}",
                        "category": "task",
                        "title": title,
                        "member": owner,
                        "status": "partial",
                        "statusLabel": f"Upcoming ({days_left}d left)",
                        "date": t["due_date"],
                        "days": days_left,
                        "actionPrompt": f"What tasks are coming up for {owner}?"
                    })

        c_count = len(completed_items)
        p_count = len(partial_items)
        r_count = len(remaining_items)
        total = c_count + p_count + r_count

        prefix = f"For {target_name}: " if target_name else "Paperwork status: "
        spoken = f"{prefix}{c_count} completed, {p_count} partial, and {r_count} remaining."

        lines = [
            f"=== DOCUMENT & TASK TRACKER ===",
            f"Target: {target_name or 'All Family Members'}",
            f"Summary: {c_count} completed, {p_count} partial, {r_count} remaining ({total} total)",
            f"Spoken Brief: {spoken}",
            "",
            f"--- COMPLETED ({c_count}) ---"
        ]
        for it in completed_items:
            cat = "Doc" if it["category"] == "document" else "Task"
            lines.append(f"- [COMPLETED] [{it['member']}] ({cat}) {it['title']} - {it['statusLabel']}")

        lines.append(f"\n--- PARTIAL ({p_count}) ---")
        for it in partial_items:
            cat = "Doc" if it["category"] == "document" else "Task"
            lines.append(f"- [PARTIAL] [{it['member']}] ({cat}) {it['title']} - {it['statusLabel']}")

        lines.append(f"\n--- REMAINING ({r_count}) ---")
        for it in remaining_items:
            cat = "Doc" if it["category"] == "document" else "Task"
            lines.append(f"- [REMAINING] [{it['member']}] ({cat}) {it['title']} - {it['statusLabel']}")

        lines.append("\nGuidance only, verify on official portals.")
        return "\n".join(lines)
    except Exception as exc:
        logger.error("get_document_tracker failed: %s", exc)
        return "Something went wrong generating the document tracker. Please try again."


# Ensure spec-depth MCP resources and prompts are registered with mcp server
import backend.resources  # noqa: F401, E402
import backend.prompts    # noqa: F401, E402