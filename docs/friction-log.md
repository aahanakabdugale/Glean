# Glean Technical Friction Log

Honest, technically precise engineering logs detailing architectural obstacles, race conditions, protocol mismatches, and layout edge cases encountered during the design and implementation of Glean, and the exact fixes deployed.

---

### 1. FastMCP v2 SDK Package Refactor: `MCPServer` Migration & Streamable HTTP
- **Component:** Model Context Protocol (MCP) Python SDK (v2.3.0) / Starlette
- **What happened:** Initializing the server using legacy documentation (`from mcp.server.fastmcp import FastMCP`) threw `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`. Furthermore, stdio pipeline examples failed to establish bidirectional IPC when interfaced with the browser client.
- **Root cause:** The MCP Python SDK underwent a major architectural refactor in v2.x: `FastMCP` was renamed and consolidated into `mcp.server.mcpserver.MCPServer`, and raw stdio pipe defaults were superseded by Streamable HTTP / Server-Sent Events (`/mcp` and `/sse`) endpoints for web agent integration.
- **Fix:** Refactored server bootstrap in [`backend/app.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/app.py) to import `from mcp.server.mcpserver import MCPServer`, instantiated `mcp = MCPServer(name="glean-server")`, and mounted the ASGI application directly onto the Uvicorn event loop.
- **Impact & Time lost:** ~20 min.

---

### 2. SQLite Cross-Thread Access Violations in Worker Thread Pools
- **Component:** SQLite3 Storage Engine / Python `anyio.to_thread` / MCP Resource Handlers
- **What happened:** Invoking asynchronous MCP resource endpoints (e.g. `@mcp.resource("family://roster")` or `@mcp.resource("tasks://upcoming")`) triggered fatal runtime crashes: `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`.
- **Root cause:** FastMCP dispatches synchronous tool and resource handler functions into worker thread pools using `anyio.to_thread.run_sync`. SQLite connection objects initialized on the main event loop thread reject operations originating from foreign thread IDs by default.
- **Fix:** Configured database connection factory in [`backend/db.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/db.py) with `sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)`, enabled write-ahead logging (`PRAGMA journal_mode=WAL;`), and wrapped queries in scoped context managers.
- **Impact & Time lost:** ~15 min.

---

### 3. PII Sanitization Regex Over-Matching on Aadhaar & Numeric Metadata
- **Component:** [`backend/security.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/security.py) / Security Gateway Sanitizer
- **What happened:** Valid citizen prompts containing standard numbers (e.g. `"My annual income is 120000 and vehicle number is 4455"`) or 4-digit birth years were rejected with `400 Bad Request: PII detected in query`.
- **Root cause:** A naive Aadhaar pattern (`\d{12}`) matched contiguous digit substrings without word boundaries or leading digit constraints, colliding with timestamps, currency quantities, and task ID strings.
- **Fix:** Rewrote Aadhaar detector with strict Verhoeff/UIDAI specifications: `\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b` (Aadhaar numbers cannot begin with 0 or 1). Added negative lookaheads and expanded unit coverage in [`tests/test_security.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/tests/test_security.py) ensuring birth years and financial values pass freely.
- **Impact & Time lost:** ~25 min.

---

### 4. SQL Injection Guard Collisions on Natural Bureaucratic Vocabulary
- **Component:** [`backend/security.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/security.py) / Input Validation Guard
- **What happened:** Benign user requests such as `"My document selection is ready"` or `"Update user preferences"` triggered false-positive SQL injection alarms and aborted tool invocation.
- **Root cause:** Substring pattern matching on SQL verbs (`SELECT`, `UPDATE`, `DROP`, `UNION`) evaluated without token boundaries, catching English prefixes and suffixes inside words like *selection*, *update*, and *dropbox*.
- **Fix:** Enforced word boundary anchors with mandatory delimiter lookaheads: `\b(SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER)\b\s+`. Added unit assertions confirming standard conversational bureaucratic sentences never trigger injection alerts.
- **Impact & Time lost:** ~15 min.

---

### 5. Temporal Eligibility Discontinuities & Leap-Year Age Boundaries
- **Component:** [`backend/schemes.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/schemes.py) & [`backend/tools.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/tools.py) (`check_scheme_eligibility`)
- **What happened:** Schemes with strict age gates (e.g., *Indira Gandhi National Old Age Pension Scheme* at age 60) classified citizens aged 58 or 59 as flatly ineligible with empty recommendations, creating dead ends for forward planning.
- **Root cause:** Age calculation using integer division `(today - dob).days // 365` introduced drift over leap years and evaluated eligibility as a binary step function rather than a predictive horizon.
- **Fix:** Refactored age calculation to exact calendar delta resolution and introduced an `almost_eligible` qualification state: candidates within a 36-month window receive eligibility forecasting, a remaining-months counter, automated document preparation reminders, and synthesized spoken hints.
- **Impact & Time lost:** ~30 min.

---

### 6. Cyclic Dependency Deadlocks in Bureaucratic Prerequisite Chains
- **Component:** [`backend/tools.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/tools.py) (`audit_document_dependencies`)
- **What happened:** Querying document requirements for complex multi-agency applications triggered `RecursionError: maximum recursion depth exceeded`.
- **Root cause:** Indian administrative rules exhibit circular prerequisite dependencies between documents across jurisdictions (e.g. *Ration Card requires Domicile Certificate*, while *Domicile Certificate requires Family Ration Card*). Naive depth-first search graph traversal recursed indefinitely.
- **Fix:** Implemented Kahn's algorithm for topological sorting equipped with cycle detection (in-degree tracking and visited sets). When a mutual dependency cycle is detected, Glean marks the circular edge as a "Bureaucratic Conflict", suggests alternative affidavit routes, and renders a non-blocking resolution DAG.
- **Impact & Time lost:** ~35 min.

---

### 7. Life Event Orchestrator State Clashes During Batch Phase Transitions
- **Component:** [`backend/tools.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/tools.py) (`orchestrate_life_event`) / State Machine
- **What happened:** Processing multi-step life transitions (e.g. "Senior Citizen Transition" encompassing pension enrollment, healthcare cards, and transport concessions) produced duplicate task records and corrupted phase dependency links.
- **Root cause:** Multiple asynchronous tool sub-tasks attempted batch insertion into the `tasks` and `life_event_plans` tables concurrently without an atomic database transaction, leading to race conditions on phase status transitions.
- **Fix:** Wrapped plan generation in an immediate transaction block (`BEGIN IMMEDIATE`), structured phases into deterministic sequence tiers (`identity` $\to$ `entitlement` $\to$ `subsidy`), and enforced idempotency checks on `(user_id, task_title)` compound keys.
- **Impact & Time lost:** ~30 min.

---

### 8. Mixed Dialect & Hinglish Entity Extraction Fallthrough
- **Component:** [`backend/voice_dialect.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/voice_dialect.py) / Code-Switching Tokenizer
- **What happened:** Voice queries mixing regional vernacular and English (e.g., *"Meri car insurance renewal baaki hai, Justin ke liye check karo"*) failed intent parsing and defaulted to generic scheme search.
- **Root cause:** The entity extraction pipeline only matched standard formal English terms, discarding regional loan words (`gaadi`, `bima`, `chachi`, `pension`, `dakhila`) and colloquial phrasing.
- **Fix:** Engineered a bilingual dialect lexicon with phonetic normalization for Hindi, Tamil, Telugu, and Bengali administrative terminology. Mapped colloquial synonyms directly into canonical MCP tool arguments and entity keys.
- **Impact & Time lost:** ~40 min.

---

### 9. Ambient Event Daemon Blocking FastAPI/Starlette Event Loop
- **Component:** [`backend/ambient.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/ambient.py) / Proactive Alert Daemon
- **What happened:** Enabling periodic proactive background checks caused intermittent 600-1200ms latency spikes on incoming conversational HTTP requests.
- **Root cause:** The ambient task monitoring loop executed synchronous SQLite table scans directly within the root `asyncio` event loop thread instead of offloading I/O operations.
- **Fix:** Offloaded ambient polling execution to thread workers using `await asyncio.to_thread(db.get_ambient_alerts)` and introduced an adaptive sleep cadence that scales polling frequency based on deadline proximity.
- **Impact & Time lost:** ~20 min.

---

### 10. Optimistic UI Desynchronization on Task Completion Toggles
- **Component:** [`frontend/src/components/results/UpcomingTasks.svelte`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/components/results/UpcomingTasks.svelte) & [`backend/tools.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/tools.py)
- **What happened:** Checking off a completed task (e.g., *"Vehicle insurance renewal check"*) updated the UI checkbox optimistically, but switching between Dashboard and Chat views reverted the task back to `pending`.
- **Root cause:** The Svelte view modified internal component state without dispatching a persistent mutation to the SQLite database via an MCP tool call.
- **Fix:** Created the `mark_task_completed(task_id, completed_by)` MCP tool in the backend, added the `completed_at` timestamp column to the `tasks` schema, and wired the Svelte checkbox to dispatch an immediate background RPC call with automatic error rollback.
- **Impact & Time lost:** ~25 min.

---

### 11. Stale Reactive Store State on Dynamic Family Member Additions
- **Component:** [`frontend/src/lib/store.js`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/lib/store.js) & [`frontend/src/components/SettingsPanel.svelte`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/components/SettingsPanel.svelte)
- **What happened:** Adding or updating a household member in the Settings Panel did not update the Header user-switcher or Dashboard eligibility cards without a manual browser refresh.
- **Root cause:** The `familyProfiles` store was populated only during initial application mount, lacking a subscription hook or reactive invalidation trigger upon backend mutations.
- **Fix:** Implemented a centralized `refreshFamilyRoster()` store coordinator that invalidates and re-evaluates `@mcp.resource("family://roster")` dynamically upon completing any member addition, edit, or deletion in [`SettingsPanel.svelte`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/components/SettingsPanel.svelte).
- **Impact & Time lost:** ~20 min.

---

### 12. Protocol Trace Visualizer Exception on Non-Standard Tool Payloads
- **Component:** [`frontend/src/lib/traceExplain.js`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/lib/traceExplain.js) & [`frontend/src/components/TracesView.svelte`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/components/TracesView.svelte)
- **What happened:** The Protocol Traces inspector threw unhandled exceptions (`TypeError: Cannot read properties of undefined (reading 'split')`) when viewing traces of tool calls that terminated with raw Python tracebacks.
- **Root cause:** `traceExplain.js` assumed incoming trace payloads strictly adhered to standard `{ status: 'success', data: {...} }` schemas, failing on string exceptions, aborted connections, or non-JSON payloads.
- **Fix:** Engineered defensive type guards and an error normalizer in `traceExplain.js` that sanitizes raw server exceptions and converts technical stack traces into plain-English conversational summaries.
- **Impact & Time lost:** ~20 min.

---

### 13. Vite Svelte Compiler Unused CSS Selector Warnings in Production Build
- **Component:** Vite Bundler / `@sveltejs/vite-plugin-svelte`
- **What happened:** Production build (`npm run build`) produced recurring compiler warnings: `Unused CSS selector ".check-icon"` and `Unused CSS selector ".chevron.open"` across multiple results components.
- **Root cause:** Lucide-Svelte SVG icons rendered as child components had legacy CSS classes targeted directly in parent scoped stylesheets, which the Svelte compiler flagged as dead code.
- **Fix:** Cleaned up obsolete static selectors, applied `:global()` scope modifiers to dynamically manipulated SVG wrappers, and pruned orphaned classes across all components, achieving zero compiler warnings.
- **Impact & Time lost:** ~15 min.

---

### 14. Translucent Glassmorphism Stacking Context Clipping in Dark/Light Modes
- **Component:** CSS Glassmorphism / `backdrop-filter: blur(10px)` / [`frontend/src/components/Header.svelte`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/components/Header.svelte)
- **What happened:** Opening dropdown menus from the center floating dock resulted in subpixel border clipping, blurry text edges, and backdrop color bleed in dark mode.
- **Root cause:** Combining `backdrop-filter` with transformed parent containers (`transform: translate(-50%, -50%)`) created an isolated stacking context and layout bounds that clipped absolute children.
- **Fix:** Detached the dropdown menus onto dedicated coordinate layers, applied explicit z-index tiers (`z-index: 100`), and defined high-contrast surface tokens (`--dock-bg`, `--dock-border`, `--dock-active-bg`) with fallback opaque color definitions.
- **Impact & Time lost:** ~25 min.

---

### 15. PWA Manifest Asset Resolution & MIME-Type Mismatches on Dev Server
- **Component:** Web App Manifest / Static Assets / [`frontend/public/manifest.json`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/public/manifest.json)
- **What happened:** Browser inspection reported `Manifest: property 'icons[0].src' ignored, could not fetch icon` and mobile simulator installations failed.
- **Root cause:** `manifest.json` referenced icon files using root-relative paths that failed resolution under Vite's multi-directory dev server configuration on Windows.
- **Fix:** Corrected all icon references in `manifest.json` to absolute root paths, generated complete PNG asset resolutions (192x192, 512x512, apple-touch-icon), and mirrored static assets into both `frontend/public/` and `alexa-simulator/dist/`.
- **Impact & Time lost:** ~15 min.

---

### 16. Root Typography Scaling (`html { font-size: 17px }`) & Layout Overflow
- **Component:** [`frontend/src/tokens.css`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/tokens.css) & [`frontend/src/app.css`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/app.css)
- **What happened:** Increasing the root font scale from `16px` to `17px` (+6.25%) caused text truncation in dock pill buttons, misaligned SVG icon baselines, and horizontal overflow in modal dialogues.
- **Root cause:** Component stylesheets combined fluid `rem` font sizing with hardcoded pixel container heights (`height: 32px`), causing text labels to overflow container bounds upon scaling.
- **Fix:** Audited and refactored container dimensions across `Header.svelte`, `SettingsPanel.svelte`, and `QuickChips.svelte`; raised pill button heights from `32px` to `34px`/`38px` and harmonized all font sizes via centralized tokens in `tokens.css`.
- **Impact & Time lost:** ~30 min.

---

### 17. CORS Preflight & Missing `Access-Control-Expose-Headers` for `mcp-session-id`
- **Component:** FastMCP HTTP Transport / [`frontend/src/lib/mcp.js`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/lib/mcp.js) & [`backend/security.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/security.py)
- **What happened:** In browser testing, `ensureSession()` repeatedly executed `initialize` handshakes on every single tool call rather than reusing the established session ID. The client console reported `sessionId: null`, causing tool executions to be treated as stateless anonymous requests.
- **Root cause:** FastMCP returns the active session identifier inside a custom HTTP response header `mcp-session-id`. Under browser Cross-Origin Resource Sharing (CORS) rules, custom response headers are masked from the Fetch API (`response.headers.get('mcp-session-id')`) unless explicitly allowed via the `Access-Control-Expose-Headers` preflight header. In addition, development environments swapping between `localhost` and `127.0.0.1` failed strict string origin matching.
- **Fix:** Configured Starlette CORS middleware to explicitly emit `Access-Control-Expose-Headers: mcp-session-id, Content-Type`, and implemented origin canonicalization in [`backend/security.py`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/backend/security.py) and [`frontend/src/lib/mcp.js`](file:///c:/Users/ADMIN/Desktop/PROJECT/Glean/frontend/src/lib/mcp.js) to transparently reconcile `localhost` with `127.0.0.1`.
- **Impact & Time lost:** ~25 min.
