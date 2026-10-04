# Tasks — Family Tools

Each task is self-contained and should take under an hour.
Work top-to-bottom; later tasks depend on earlier ones being done.

---

## T-01 · Database layer — schema & connection helper
**File:** `glean/db.py`

- Add `get_connection(db_path: str | None = None) -> sqlite3.Connection` that
  reads `GLEAN_DB_PATH` env var (default `"glean.db"`), opens the file, and
  sets `row_factory = sqlite3.Row` and `isolation_level = None` (autocommit).
- Add `init_db(conn)` that runs the `CREATE TABLE IF NOT EXISTS` and
  `CREATE UNIQUE INDEX IF NOT EXISTS` statements for `family_members` and
  `documents` (see design.md schema).
- **Do not close `conn` inside any helper** — connection lifecycle is the caller's
  responsibility.
- **Done when:** `python -c "from glean.db import get_connection, init_db; init_db(get_connection(':memory:'))"` exits with no error.

---

## T-02 · FastMCP instance
**File:** `glean/app.py` (new file)

- Create `mcp = FastMCP("Glean")`.
- This file has no other imports from `glean/`; it exists purely to break the
  circular-import chain.
- **Done when:** `python -c "from glean.app import mcp; print(mcp)"` exits with no error.

---

## T-03 · Tool — `add_family_member`
**File:** `glean/tools.py`

- `from glean.app import mcp` (not from `server.py`).
- Implement `add_family_member(name, relation, birth_year, status)` as an
  `@mcp.tool` function.
- Validate in order: non-empty name, non-empty relation, valid birth year, unique
  name (case-insensitive SELECT before INSERT).
- Insert into `family_members`; return short confirmation.
- Do not call `conn.close()`.
- **Done when:** T-05 tests for this tool all pass.

---

## T-04 · Tool — `list_family_members`
**File:** `glean/tools.py`

- Implement `list_family_members()` as an `@mcp.tool` function.
- Query all rows ordered by `name COLLATE NOCASE`; format each as
  `"<name> (<relation>) — born <birth_year>, <status>"`.
- Return lines joined by `\n`, or `"No family members added yet."` when empty.
- Do not call `conn.close()`.
- **Done when:** T-05 tests for this tool all pass.

---

## T-05 · Tests — member tools
**File:** `tests/test_tools.py`

Write a `db_conn` fixture that:
1. Opens `sqlite3.connect(":memory:")`, sets `row_factory = sqlite3.Row`.
2. Calls `init_db(conn)`.
3. Monkeypatches `glean.db.get_connection` to return `conn`.
4. Yields `conn` (does **not** close it — pytest tears it down).

Tests to write:
- `test_add_member_happy_path` — return string contains the name.
- `test_add_member_empty_name` — blank name returns a friendly error.
- `test_add_member_empty_relation` — blank relation returns a friendly error.
- `test_add_member_bad_birth_year` — year 1800 returns a friendly error.
- `test_add_member_duplicate_name` — adding "Maria" twice (second time as "maria")
  returns the duplicate error.
- `test_list_members_empty` — returns the "no members" string.
- `test_list_members_one` — after adding one member, list contains their name.
- `test_list_members_multiple` — after adding two members, both appear.

- **Done when:** `pytest tests/test_tools.py -k "member"` passes with no failures.

---

## T-06 · Tool — `add_document`
**File:** `glean/tools.py`

- Implement `add_document(doc_type, owner, expiry_date)` as an `@mcp.tool` function.
- Validate in order: non-empty `doc_type`, owner exists (case-insensitive lookup),
  valid ISO date (past dates are fine).
- Resolve owner name → `member_id`; store `member_id` in `documents`, not the name.
- Use the stored capitalisation of the member's name in the reply.
- Do not call `conn.close()`.
- **Done when:** T-07 tests for this tool all pass.

---

## T-07 · Tests — document tool
**File:** `tests/test_tools.py`

Reuse the `db_conn` fixture from T-05.

Tests to write:
- `test_add_document_happy_path` — adds a member, then a document; return string
  contains the stored capitalisation of the name and the expiry date.
- `test_add_document_empty_doc_type` — blank `doc_type` returns a friendly error.
- `test_add_document_unknown_owner` — unknown owner returns the "Add them first" error.
- `test_add_document_owner_case_insensitive` — member stored as "Maria", owner
  passed as "maria"; document is added successfully.
- `test_add_document_bad_date` — malformed date returns the format error.
- `test_add_document_past_date_allowed` — a past expiry date (e.g. 2000-01-01) is
  accepted.
- `test_no_id_numbers_stored` — `PRAGMA table_info(documents)` returns no column
  with a name containing `"id_number"`, `"passport"`, or `"national"`.
- `test_documents_stores_member_id` — after adding a document, query the `documents`
  table and assert `member_id` is an integer matching the member's row `id`.

- **Done when:** `pytest tests/test_tools.py -k "document"` passes with no failures.

---

## T-08 · Wire tools into server
**File:** `server.py`

- `import glean.tools` (side-effect import registers tools on the `mcp` instance).
- `from glean.app import mcp`.
- `from glean.db import get_connection, init_db`.
- Call `init_db(get_connection())` at startup before starting uvicorn.
- Read `GLEAN_HOST` (default `"127.0.0.1"`) and `GLEAN_PORT` (default `8000`) from
  env vars.
- **Done when:** `python server.py` starts without error and the three tools appear
  when a client lists available tools.

---

## T-09 · Add glean.db to .gitignore
**File:** `.gitignore`

- Open (or create) `.gitignore` at the project root.
- Add a line `glean.db` if it is not already present.
- **Done when:** `git check-ignore -v glean.db` prints a match.

---

## T-10 · Full test run & README update
**Files:** `tests/`, `README.md`

- Run `pytest` from the project root; all tests must pass.
- Add a short section to `README.md` covering:
  - How to install dependencies (`pip install -r requirements.txt`).
  - How to run the server (`python server.py`).
  - The `GLEAN_DB_PATH` env var and the `127.0.0.1` default host.
  - The no-ID-numbers rule (one sentence).
- **Done when:** `pytest` exits green and `README.md` has the four points above.
