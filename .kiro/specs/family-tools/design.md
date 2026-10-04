# Design — Family Tools

## Architecture

```
Client (Claude / any MCP host)
        │  MCP (Streamable HTTP)
        ▼
   server.py        — imports glean.tools (registers tools), calls init_db, starts uvicorn
        │
   glean/app.py     — creates the single FastMCP instance (`mcp`)
        │
   glean/tools.py   — imports `mcp` from glean.app; defines @mcp.tool functions
        │
   glean/db.py      — get_connection(), init_db(), query helpers
        │
   SQLite file  (path from GLEAN_DB_PATH env var, default: glean.db)
```

`glean/app.py` owns the `FastMCP` instance so that `tools.py` can import it
without creating a circular dependency with `server.py`.

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS family_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    relation   TEXT    NOT NULL,
    birth_year INTEGER NOT NULL,
    status     TEXT    NOT NULL
);

-- UNIQUE constraint on name (case-insensitive via COLLATE NOCASE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_family_members_name
    ON family_members (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type    TEXT    NOT NULL,
    member_id   INTEGER NOT NULL REFERENCES family_members(id),
    expiry_date TEXT    NOT NULL   -- ISO 8601, e.g. 2030-06-15
    -- NO id numbers, passport numbers, or any unique personal identifiers
);
```

`documents` links to `family_members` via `member_id` (foreign key). The tool
still accepts an owner *name* and resolves it to an `id` with a
case-insensitive lookup before inserting.

---

## Module Layout

```
glean/
  app.py       — mcp = FastMCP("Glean")  ← single source of truth for the MCP instance
  db.py        — get_connection(), init_db(), helpers
  tools.py     — from glean.app import mcp; @mcp.tool definitions
server.py      — from glean import tools (side-effect: registers tools)
               — calls init_db(get_connection()), starts uvicorn
```

---

## Tool Contracts

### `add_family_member(name, relation, birth_year, status) → str`

```
Validation (in order):
  1. name.strip() == ""          → "Please provide a name."
  2. relation.strip() == ""      → "Please provide a relation (e.g. daughter, parent)."
  3. birth_year < 1900 or
     birth_year > current year   → "That birth year doesn't look right."
  4. SELECT id FROM family_members WHERE name = ? COLLATE NOCASE
     → row exists                → "Someone called <name> is already in the list."

Happy path:
  INSERT INTO family_members (name, relation, birth_year, status) VALUES (...)
  return f"Added {name.strip()} ({relation.strip()})."

Note: do NOT call conn.close() — the caller owns the connection.
```

### `list_family_members() → str`

```
SELECT * FROM family_members ORDER BY name COLLATE NOCASE;

Empty  → "No family members added yet."
Rows   → one line per member:
         "<name> (<relation>) — born <birth_year>, <status>"
         joined with "\n"
```

### `add_document(doc_type, owner, expiry_date) → str`

```
Validation (in order):
  1. doc_type.strip() == ""      → "Please provide a document type."
  2. SELECT id, name FROM family_members WHERE name = ? COLLATE NOCASE
     → no row                    → "I don't know anyone called <owner>. Add them first."
  3. datetime.date.fromisoformat(expiry_date) raises ValueError
                                 → "That date doesn't look right. Please use YYYY-MM-DD format."
     (past dates are accepted)

Happy path:
  member_id = row["id"]
  display_name = row["name"]   ← use the stored capitalisation in the reply
  INSERT INTO documents (doc_type, member_id, expiry_date) VALUES (...)
  return f"{doc_type.strip().title()} added for {display_name}, expires {expiry_date}."

Note: do NOT call conn.close() — the caller owns the connection.
```

---

## Error Handling Strategy

All tool functions catch unexpected exceptions at the top level and return a plain
string. Raw exceptions are logged to stderr; they are never returned to the caller.

```python
try:
    ...
except Exception as exc:
    logger.error("add_document failed: %s", exc)
    return "Something went wrong. Please try again."
```

---

## Testing Strategy

- **pytest** with an `":memory:"` SQLite database.
- A `db_conn` fixture creates the in-memory DB, calls `init_db`, and monkeypatches
  `glean.db.get_connection` to return it for the duration of the test.
- Tool functions are called directly (not via HTTP); the monkeypatch means they
  use the test DB transparently.
- Tests never call `conn.close()` — the fixture tears down naturally after the test.
- Tests cover: happy path, each validation error, empty list, duplicate name
  rejection, past expiry date acceptance, and the no-ID-stored schema invariant.

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GLEAN_DB_PATH` | `glean.db` | Path to the SQLite file |
| `GLEAN_HOST` | `127.0.0.1` | Bind address for uvicorn |
| `GLEAN_PORT` | `8000` | Port for uvicorn |

---

## New Table — tasks

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT    NOT NULL,
    due_date  TEXT    NOT NULL,   -- ISO 8601, e.g. 2030-06-15
    member_id INTEGER REFERENCES family_members(id),  -- nullable
    done      INTEGER NOT NULL DEFAULT 0              -- 0 = pending, 1 = done
);
```

`member_id` is nullable — a task does not have to belong to a specific person.
`done` uses integer 0/1 (SQLite has no boolean type).

---

## New Tool Contracts

### `get_expiring_documents(days: int) → str`

```
Validation:
  1. days < 1  → "Please give a number of days (at least 1)."

Query:
  today     = datetime.date.today()
  cutoff    = today + datetime.timedelta(days=days)

  SELECT d.doc_type, fm.name, d.expiry_date
  FROM   documents d
  JOIN   family_members fm ON fm.id = d.member_id
  WHERE  d.expiry_date BETWEEN date(today) AND date(cutoff)
  ORDER  BY d.expiry_date

Empty  → f"No documents expiring in the next {days} day(s)."
Rows   → one line per document:
         "<doc_type> — <name>, expires <expiry_date>"
         joined with "\n"

Note: do NOT call conn.close().
```

### `add_task(title: str, due_date: str, member_id: int | None = None) → str`

```
Validation (in order):
  1. title.strip() == ""                    → "Please provide a task title."
  2. datetime.date.fromisoformat(due_date)
     raises ValueError                      → "That date doesn't look right. Please use YYYY-MM-DD format."
     (past dates are accepted)
  3. member_id is not None
     AND SELECT id FROM family_members WHERE id = member_id → no row
                                            → "I don't know that family member. Check the id and try again."

Happy path:
  INSERT INTO tasks (title, due_date, member_id, done) VALUES (?, ?, ?, 0)
  return f"Task added: {title.strip()}, due {due_date}."

Note: do NOT call conn.close().
```

### `list_upcoming_tasks(days: int) → str`

```
Validation:
  1. days < 1  → "Please give a number of days (at least 1)."

Query:
  today   = datetime.date.today()
  cutoff  = today + datetime.timedelta(days=days)

  SELECT t.title, t.due_date, fm.name
  FROM   tasks t
  LEFT JOIN family_members fm ON fm.id = t.member_id
  WHERE  t.done = 0
  AND    t.due_date BETWEEN date(today) AND date(cutoff)
  ORDER  BY t.due_date

Empty  → f"No tasks due in the next {days} day(s)."
Rows   → one line per task:
         "<title> — due <due_date>"           (no member linked)
         "<title> — due <due_date> (<name>)"  (member linked)
         joined with "\n"

Note: do NOT call conn.close().
```
