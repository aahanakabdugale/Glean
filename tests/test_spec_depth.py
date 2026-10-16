"""
Unit and integration tests for MCP Spec Depth:
- Resources (@mcp.resource)
- Resource Templates (@mcp.resource(".../{id}"))
- Prompts (@mcp.prompt)
"""

import json
import sqlite3
import pytest

import backend.db as glean_db
from backend.app import mcp
import backend.tools  # registers tools, resources, and prompts


@pytest.fixture
def db_conn(monkeypatch):
    """Isolated in-memory database for testing resources."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)

    # Insert sample member and document
    conn.execute(
        "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
        ("Chandler", "grandfather", 1950, "retired"),
    )
    conn.commit()

    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)
    yield conn


# ---------------------------------------------------------------------------
# Resources tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_resources():
    resources = await mcp.list_resources()
    uris = {r.uri for r in resources}
    assert "glean://schemes" in uris
    assert "glean://family/roster" in uris
    assert "glean://family/dashboard" in uris


@pytest.mark.anyio
async def test_list_resource_templates():
    templates = await mcp.list_resource_templates()
    template_uris = {t.uri_template for t in templates}
    assert "glean://schemes/{scheme_id}" in template_uris


@pytest.mark.anyio
async def test_read_schemes_resource():
    contents = await mcp.read_resource("glean://schemes")
    assert contents
    data = json.loads(contents[0].content)
    assert isinstance(data, list)
    scheme_ids = {s["id"] for s in data}
    assert "scss" in scheme_ids
    assert "ayushman_vay_vandana" in scheme_ids


@pytest.mark.anyio
async def test_read_scheme_detail_template():
    contents = await mcp.read_resource("glean://schemes/scss")
    assert contents
    data = json.loads(contents[0].content)
    assert data["id"] == "scss"
    assert "Senior Citizens Savings Scheme" in data["name"]
    assert "source_url" in data


@pytest.mark.anyio
async def test_read_scheme_detail_not_found():
    contents = await mcp.read_resource("glean://schemes/unknown_scheme_xyz")
    assert contents
    data = json.loads(contents[0].content)
    assert "error" in data


@pytest.mark.anyio
async def test_read_family_roster_resource(db_conn):
    contents = await mcp.read_resource("glean://family/roster")
    assert contents
    data = json.loads(contents[0].content)
    assert isinstance(data, list)
    names = [m["name"] for m in data]
    assert "Chandler" in names


@pytest.mark.anyio
async def test_read_family_dashboard_resource(db_conn):
    contents = await mcp.read_resource("glean://family/dashboard")
    assert contents
    data = json.loads(contents[0].content)
    assert "total_members" in data
    assert "total_documents" in data
    assert "pending_tasks" in data
    assert data["status"] == "operational"


# ---------------------------------------------------------------------------
# Prompts tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_prompts():
    prompts = await mcp.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert "annual_family_review" in prompt_names
    assert "onboard_family_member" in prompt_names
    assert "scheme_application_assistant" in prompt_names


@pytest.mark.anyio
async def test_annual_family_review_prompt():
    prompt = await mcp.get_prompt("annual_family_review")
    text = prompt.messages[0].content.text
    assert "Glean Family Paperwork AI Assistant" in text
    assert "get_family_dashboard" in text
    assert "get_expiring_documents" in text
    assert "check_scheme_eligibility" in text


@pytest.mark.anyio
async def test_onboard_family_member_prompt():
    prompt = await mcp.get_prompt(
        "onboard_family_member",
        {"name": "Aman", "relation": "son", "birth_year": 2005},
    )
    text = prompt.messages[0].content.text
    assert "Aman" in text
    assert "son" in text
    assert "2005" in text
    assert "add_family_member" in text
    assert "check_scheme_eligibility" in text


@pytest.mark.anyio
async def test_scheme_application_assistant_prompt():
    prompt = await mcp.get_prompt(
        "scheme_application_assistant",
        {"member_name": "Chandler", "scheme_id": "scss"},
    )
    text = prompt.messages[0].content.text
    assert "Chandler" in text
    assert "scss" in text
    assert "get_scheme_checklist" in text
    assert "plan_scheme_application" in text
