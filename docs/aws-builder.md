# AWS Builder Mini Challenge — How Kiro Was Used in Glean

## 1. Tools Used

- **Kiro CLI v2.27.1** — used as the primary coding assistant throughout the
  project: generating code, running tests, and writing documentation from the
  terminal.
- **Kiro Crew (desktop app, latest installer as of Oct 4 2026)** — used for
  spec-driven development, parallel subagent tasks, and persistent memory across
  sessions. All sessions ran locally; no AWS account or cloud credits were
  consumed.

---

## 2. Use 1: Spec-Driven Development

Before writing a single line of code, I asked Kiro Crew to draft three spec
files from the project's PRD: `requirements.md`, `design.md`, and `tasks.md`.
These live in `.kiro/specs/family-tools/` and are committed to the repo.

The specs captured validation rules (e.g. no ID numbers stored, friendly error
strings), the SQLite schema, tool contracts with exact return formats, and a
15-task breakdown with "done when" acceptance criteria. Having these files meant
every tool function had a spec to implement against, and tests had a spec to
verify against. It reduced the number of mid-session clarifications I had to
make.

---

## 3. Use 2: Parallel Subagents for Tests and Docs

I used two separate Crew sessions (treated as independent subagents) in the same
work block:

- **Session A — schemes tests:** asked to read `glean/schemes.py` and
  `data/schemes.json`, then write `tests/test_schemes_extra.py` covering boundary
  ages, empty/unknown tags, and result shape. It produced 20 new tests. The
  schemes test suite went from **8 tests** (`test_schemes.py`) to **28 tests**
  after this session.
- **Session B — schemes docs:** asked to write `docs/schemes.md` in plain
  English: field descriptions, rule keys, the three statuses, a usage example,
  and a disclaimer. It produced a 77-line reference file.

Total test count before Crew sessions: **53 tests** (45 in `test_tools.py` + 8 in
`test_schemes.py`). After Crew wrote `test_schemes_extra.py` (20 new tests), the
total rose to **73 tests** — all passing (confirmed with `pytest --tb=no -q`).

---

## 4. Use 3: Persistent Memory Across Sessions

Crew carries context between sessions via its dashboard DM thread.

**Recalled correctly:** on Day 2, when I asked Crew to write the eligibility
tests, it correctly remembered that the project uses `age = today.year -
birth_year` (birth-year-only arithmetic, no month/day precision) and wrote the
boundary tests against that behaviour without me re-explaining it.

**Needed correction:** in an earlier session Crew drafted a task spec for
`add_task` that accepted a `member_id` integer parameter. The actual
implementation later shifted to an `owner` name string (looked up
case-insensitively). Crew did not automatically update its understanding of the
parameter signature across sessions; I had to re-read the design file and correct
the prompt before the test session.

---

## 5. What Worked Well

- **Setup speed:** the spec files were ready in one session, covering 15 tasks
  with acceptance criteria. That took roughly 20 minutes of prompting.
- **Test generation quality:** both test sessions (tools and schemes) produced
  tests that passed on the first run with zero edits. The boundary age
  calculations and the monkeypatch fixture were correct straight away.
- **Staying in the project:** the `[PROJECT]` scope in Crew meant file reads and
  searches stayed inside the Glean directory without extra instruction.

---

## 6. What Needs Work

- **PATH not set after install:** `kirocrew` was not on PATH after the desktop
  installer ran. Had to find `kirocrew.cmd` manually under
  `%LOCALAPPDATA%\Programs\KiroCrew\...\bin` and run it with the full path.
  ~10 min lost. (Friction log entry 9.)
- **`kiro-cli` also not on PATH until terminal restart:** same issue — the
  terminal opened before the installer updated PATH. (Friction log entry 8.)
- **Credit usage is opaque:** there is no in-app indicator of how many of the
  50 free monthly credits have been used. I had to be conservative and avoid
  running large sessions unnecessarily.
- **No task-parallelism UI:** Crew does not have a built-in parallel task runner
  that I could trigger from the dashboard. The "parallel subagents" in Use 2 were
  two sequential sessions; I ran them one after the other, not truly at the same
  time.

---

## 7. Onboarding Experience

Getting from zero to a working Crew session took about **45 minutes** on Day 1,
not counting the time spent on the venv and MCP SDK issues that were unrelated to
Kiro.

Steps that worked smoothly: downloading the desktop installer, signing in with a
GitHub account, opening the dashboard, starting a chat.

Blockers: `kiro-cli` not on PATH until a new terminal was opened (10 min),
`kirocrew` not on PATH at all (10 min, had to use full path). Both are captured in
`docs/friction-log.md` entries 8 and 9.

---

## 8. Would You Build With It Again?

Yes — the spec-driven workflow and the ability to have a coding session that
already knows the project's file layout saved more time than the PATH setup lost.


---

## 9. Security Review (Kiro-assisted)

Kiro was used to generate `glean/security.py` and `tests/test_security.py` in a
single session. The three helpers and their findings:

- **`validate_token`** — guards the server with a Bearer token checked against
  `GLEAN_ACCESS_TOKEN`. When the env var is absent the guard is a no-op (dev
  mode). Uses `hmac.compare_digest` to avoid timing attacks. 12 tests cover dev
  mode, prod mode, header casing, and the query-param fallback.

- **`validate_origin`** — checks the HTTP Origin header against a glob-pattern
  allowlist (default: localhost and 127.0.0.1 on any port). Absent Origin is
  allowed so CLI tools are not blocked. A key finding: `fnmatch` glob
  `http://localhost:*` does **not** match `http://localhost.evil.com:80` — the
  dot acts as a literal character, so subdomain spoofing is blocked correctly.
  10 tests.

- **`sanitize_input`** — rejects PII patterns (12-digit Aadhaar in three
  formats, Indian passport, PAN, voter ID), SQL injection keywords (with `\b`
  word boundaries to avoid blocking words like "selection"), and inputs over 500
  characters. 27 tests; all 49 security tests pass.

FastMCP v2.3.0 does not expose a first-class middleware hook directly on the
FastMCP instance, so the security helpers are wired in as a custom Starlette
`BaseHTTPMiddleware` (`GleanSecurityMiddleware`) wrapping `mcp.streamable_http_app`
in `server.py`. Origin validation protects all incoming routes, and Bearer token / query
token checks guard the `/mcp` endpoint while allowing static UI assets to serve smoothly.
All 49 security unit tests and end-to-end middleware checks pass.
