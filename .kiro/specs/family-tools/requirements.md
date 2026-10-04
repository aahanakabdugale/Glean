# Requirements — Family Tools

## Overview
Six MCP tools for a family paperwork tracker backed by SQLite. Responses must be
short and plain enough to be read aloud by a voice assistant. Errors must be
friendly — no stack traces, no technical jargon.

---

## Functional Requirements

### FR-1 · add_family_member
- Accepts: `name` (string), `relation` (string), `birth_year` (integer), `status` (string).
- Adds the person to the `family_members` table.
- Returns a single short confirmation sentence, e.g. *"Added Maria (daughter)."*
- Validation rules (return a friendly error string for each):
  - `name` stripped and non-empty → *"Please provide a name."*
  - `relation` stripped and non-empty → *"Please provide a relation (e.g. daughter, parent)."*
  - `birth_year` must be 1900–current year → *"That birth year doesn't look right."*
  - `name` must be unique, case-insensitive — a second "maria" is rejected even if the
    stored name is "Maria" → *"Someone called <name> is already in the list."*
- `status` is free-text (no validation beyond being a string).

### FR-2 · list_family_members
- No parameters.
- Returns a plain-text list of all family members, one per line:
  `<name> (<relation>) — born <birth_year>, <status>`.
- If the table is empty, returns *"No family members added yet."*

### FR-3 · add_document
- Accepts: `doc_type` (string), `owner` (string — family member name, looked up
  case-insensitively), `expiry_date` (string, ISO 8601 date `YYYY-MM-DD`).
- Adds a row to the `documents` table, linked via the member's integer `id`
  (not by name string).
- Returns a short confirmation, e.g. *"Passport added for Maria, expires 2030-06-15."*
- Validation rules:
  - `doc_type` stripped and non-empty → *"Please provide a document type."*
  - `owner` must match an existing `family_members.name` (case-insensitive) →
    *"I don't know anyone called <owner>. Add them first."*
  - `expiry_date` must be a valid `YYYY-MM-DD` date (past dates are allowed) →
    *"That date doesn't look right. Please use YYYY-MM-DD format."*
- **Never store ID numbers, national identity numbers, passport numbers, or any
  unique personal identifier.** Only `doc_type`, `member_id`, and `expiry_date`
  are recorded.

### FR-4 · get_expiring_documents
- Accepts: `days` (integer — look-ahead window).
- Returns all documents whose `expiry_date` falls within the next `days` days from
  today (inclusive of today, inclusive of the end date).
- Each result line: `<doc_type> — <member name>, expires <expiry_date>`.
- If nothing expires in that window, returns *"No documents expiring in the next
  <days> day(s)."*
- Validation:
  - `days` must be ≥ 1 → *"Please give a number of days (at least 1)."*

### FR-5 · add_task
- Accepts: `title` (string), `due_date` (string, ISO 8601 `YYYY-MM-DD`),
  `member_id` (integer, optional — links the task to a specific family member).
- Adds a row to the `tasks` table with `done = 0`.
- Returns a short confirmation, e.g. *"Task added: Renew passport, due 2030-06-15."*
- Validation rules:
  - `title` stripped and non-empty → *"Please provide a task title."*
  - `due_date` must be a valid `YYYY-MM-DD` date (past dates are allowed) →
    *"That date doesn't look right. Please use YYYY-MM-DD format."*
  - If `member_id` is provided it must match an existing `family_members.id` →
    *"I don't know that family member. Check the id and try again."*

### FR-6 · list_upcoming_tasks
- Accepts: `days` (integer — look-ahead window).
- Returns all tasks where `done = 0` and `due_date` falls within the next `days`
  days from today (inclusive on both ends).
- Each result line: `<title> — due <due_date>` (append ` (<member name>)` when a
  member is linked).
- If nothing is due in that window, returns *"No tasks due in the next <days>
  day(s)."*
- Validation:
  - `days` must be ≥ 1 → *"Please give a number of days (at least 1)."*

---

## Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-1 | All tool responses are plain text, ≤ 2 sentences, suitable for text-to-speech. |
| NFR-2 | All error messages are friendly and actionable — never expose raw exceptions. |
| NFR-3 | The SQLite database file path is configurable via `GLEAN_DB_PATH` (default: `glean.db` in the working directory). |
| NFR-4 | Tests use pytest with a temporary in-memory SQLite database; they must not touch the production database. |
| NFR-5 | No sensitive personal data is stored — specifically no ID or document numbers of any kind. |
| NFR-6 | Tools must not close the DB connection — connection lifecycle is managed by the caller. |
| NFR-7 | `glean.db` must be listed in `.gitignore` so the database is never committed. |

---

## Out of Scope (this iteration)
- Editing or deleting records.
- Marking tasks as done.
- Document reminders / expiry notifications sent proactively.
- Authentication or multi-user access control.
- Any UI beyond the MCP tools themselves.
