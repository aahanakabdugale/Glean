"""
Glean MCP Resources — Model Context Protocol spec-depth resources.

Exposes structured data as first-class MCP resources that AI clients, Claude Desktop,
and the MCP Inspector can read, subscribe to, or attach directly to context:
  - glean://schemes               → Complete government schemes catalog
  - glean://schemes/{scheme_id}   → Specific scheme details, checklists, and portal links
  - glean://family/roster         → Current family members roster
  - glean://family/dashboard      → High-level paperwork health & deadline metrics
"""

import json
from backend import db
from backend.app import mcp
from backend.schemes import load_schemes


@mcp.resource(
    "glean://schemes",
    name="Government Schemes Catalog",
    description="Full official catalog of government schemes, age rules, required documents, and official portal links.",
    mime_type="application/json",
)
def get_schemes_catalog() -> str:
    """Return the entire catalog of schemes as formatted JSON."""
    schemes = load_schemes()
    return json.dumps(schemes, indent=2, ensure_ascii=False)


@mcp.resource(
    "glean://schemes/{scheme_id}",
    name="Scheme Policy & Checklist",
    description="Detailed scheme guidelines, document checklist, and application portal for a specific scheme ID.",
    mime_type="application/json",
)
def get_scheme_detail(scheme_id: str) -> str:
    """Return details for a specific scheme by ID."""
    schemes = load_schemes()
    target = scheme_id.strip().lower()
    for s in schemes:
        if s["id"].lower() == target:
            return json.dumps(s, indent=2, ensure_ascii=False)
    return json.dumps({"error": f"Scheme '{scheme_id}' not found."}, indent=2)


@mcp.resource(
    "glean://family/roster",
    name="Family Roster",
    description="Current active family members roster including relations, birth years, and employment/demographic statuses.",
    mime_type="application/json",
)
def get_family_roster() -> str:
    """Return active family members as JSON."""
    try:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT id, name, relation, birth_year, status FROM family_members ORDER BY name"
        ).fetchall()
        members = [dict(r) for r in rows]
        return json.dumps(members, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": f"Failed to fetch roster: {exc}"}, indent=2)


@mcp.resource(
    "glean://family/dashboard",
    name="Family Paperwork & Health Summary",
    description="Live metrics of tracked documents, urgent expirations, pending tasks, and qualifying scheme opportunities.",
    mime_type="application/json",
)
def get_family_dashboard_resource() -> str:
    """Return high-level family paperwork metrics as JSON."""
    try:
        conn = db.get_connection()
        total_members = conn.execute("SELECT COUNT(*) FROM family_members").fetchone()[0]
        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        pending_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 0").fetchone()[0]

        summary = {
            "total_members": total_members,
            "total_documents": total_docs,
            "pending_tasks": pending_tasks,
            "schemes_monitored": len(load_schemes()),
            "status": "operational",
        }
        return json.dumps(summary, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": f"Failed to fetch dashboard: {exc}"}, indent=2)
