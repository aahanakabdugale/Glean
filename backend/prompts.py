"""
Glean MCP Prompts — Model Context Protocol spec-depth prompt templates.

Exposes standard agentic workflows as first-class MCP prompts that AI clients,
Claude Desktop, and the MCP Inspector can discover and trigger with typed arguments:
  - annual_family_review
  - onboard_family_member
  - scheme_application_assistant
"""

from glean.app import mcp


@mcp.prompt(
    "annual_family_review",
    description="Comprehensive audit of all family paperwork, expiring documents, pending deadlines, and government scheme opportunities.",
)
def annual_family_review_prompt(focus_member: str = "") -> str:
    """Prompt template for conducting an annual or quarterly family paperwork review."""
    target = f" with special focus on {focus_member}" if focus_member else ""
    return (
        f"You are the Glean Family Paperwork AI Assistant. Please conduct a thorough family paperwork audit{target}.\n\n"
        "Follow these steps:\n"
        "1. Call `get_family_dashboard` to inspect overall family health, tracked documents, and pending deadlines.\n"
        "2. Call `get_expiring_documents(days=60)` to identify all documents requiring immediate renewal or appointment booking.\n"
        "3. Check government scheme eligibility for eligible senior or adult family members (using `check_scheme_eligibility`), "
        "highlighting both 'May be eligible' and 'Coming up soon (Almost Eligible)' opportunities.\n"
        "4. Synthesize your findings into a clear, spoken-friendly action plan grouped by: Urgent Actions, Upcoming Deadlines, and Long-Term Government Benefits."
    )


@mcp.prompt(
    "onboard_family_member",
    description="Guided onboarding flow to add a new family member, register essential documents, and evaluate government benefits.",
)
def onboard_family_member_prompt(name: str, relation: str = "family member", birth_year: int = 2000) -> str:
    """Prompt template for onboarding a new family member."""
    return (
        f"You are helping onboard a new family member to Glean: {name} ({relation}, born {birth_year}).\n\n"
        "Follow this workflow:\n"
        f"1. Confirm registration by calling `add_family_member(name='{name}', relation='{relation}', birth_year={birth_year})`.\n"
        f"2. Check government scheme eligibility right away using `check_scheme_eligibility(name='{name}')`.\n"
        f"3. Advise the user on standard paperwork to register for {name} based on their age (such as Aadhaar, Passport, PAN Card, Health Insurance, or Voter ID).\n"
        f"4. Ask if they have any upcoming expiry dates for {name}'s documents to track."
    )


@mcp.prompt(
    "scheme_application_assistant",
    description="Step-by-step checklist and application plan for a family member applying to a specific government scheme.",
)
def scheme_application_assistant_prompt(member_name: str, scheme_id: str) -> str:
    """Prompt template for guiding a family member through a government scheme application."""
    return (
        f"You are assisting {member_name} in applying for government scheme '{scheme_id}'.\n\n"
        "Follow this structured assistance plan:\n"
        f"1. Call `get_scheme_checklist(scheme='{scheme_id}')` to retrieve the official document requirements, state rules, and portal links.\n"
        f"2. Call `check_scheme_eligibility(name='{member_name}')` to verify {member_name}'s current and temporal eligibility status.\n"
        f"3. Call `plan_scheme_application(member_name='{member_name}', scheme='{scheme_id}')` to create document-gathering and submission tasks with appropriate deadlines.\n"
        "4. Summarize the required documents and application portal link in plain, reassuring language with the official disclaimer."
    )
