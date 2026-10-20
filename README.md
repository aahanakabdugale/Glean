# Glean on Alexa+ | Family Paperwork Assistant


Project submitted to: **Build, Ship, Shape: Amazon Developer Hackathon**  
Track: **Alexa+**  
 Try Glean : [https://glean-alexa.onrender.com/](https://glean-alexa.onrender.com/)

---

## Overview

In multi-generational households, administrative paperwork represents an invisible but heavy burden. Passports, driving licenses, insurance cards, vehicle registrations, tax filings, and pension accounts are dispersed across family members with mismatched expiration cycles.

Glean transforms Alexa into a proactive, intelligent Family Paperwork Assistant. Operating over the Model Context Protocol (MCP) and Streamable HTTP, Glean continuously audits document validity, alerts households to pending expirations, evaluates entitlement to statutory welfare schemes across the United States and India, forecasts milestone eligibility up to 36 months ahead, audits prerequisite document dependencies using topological graph sorting, and pushes urgent ambient notices to the Alexa screen and audio chime.

---

## Problem and Solution

### The Problem

1. **Cognitive Overload and Fragmentation:** One household member usually shoulders the administrative overhead of tracking documents for children, spouses, aging parents, and grandparents. Paperwork is kept across disparate folders, portals, and physical drawers.
2. **Silent Expirations and Missed Windows:** Critical documents such as passports, vehicle registrations, and health insurance policies expire without sufficient lead time, resulting in emergency renewal surcharges, missed travel dates, or coverage gaps.
3. **Unclaimed Welfare and Statutory Benefits:** Governments in the United States and India offer numerous social welfare, healthcare, and savings schemes (such as Medicare, SNAP, Ayushman Bharat PM-JAY, Senior Citizens Savings Scheme, and Atal Pension Yojana). However, millions of eligible citizens miss out because qualification criteria, means tests, and required paperwork are buried in complex legal documentation.
4. **Bureaucratic Red-Tape Deadlocks:** Families frequently schedule in-person renewal appointments only to be turned away because a secondary prerequisite document (such as a domicile certificate or updated utility bill) was missing or expired.
5. **Reactive Rather Than Proactive Voice Interfaces:** Traditional smart home assistants wait passively for explicit voice commands and lack the longitudinal context required to foresee deadlines or life transitions.

### The Solution Built

Glean provides an autonomous, multi-generational paperwork sentinel engineered for the Alexa+ ecosystem:

1. **Continuous Family Document Sentinel:** Audits document validity across all household members, tracking expiration windows and calculating precise urgency rankings without storing sensitive identity numbers.
2. **Dual-Jurisdiction Welfare Scheme Routing:** Evaluates household profiles against statutory benefit schemes across both the United States and India, providing eligibility determinations, prerequisite checklists, and official government application endpoints.
3. **Temporal "Almost Eligible" Forecasting:** Identifies family members within a 36-month horizon of statutory milestone birthdays (such as Medicare at 65, or Ayushman Vay Vandana at 70), calculating remaining countdowns and queuing pre-application paperwork checklists before the milestone occurs.
4. **Topological Dependency Auditing and Conflict Simulation:** Runs Kahn's algorithm over prerequisite document graphs to surface blocker bottlenecks before appointments, and detects circular bureaucratic deadlocks with automated affidavit recommendations.
5. **Autonomous Life Event Orchestration:** Constructs phased, actionable 90-day roadmaps for milestone transitions including Retirement, Higher Education, and Inter-State Relocation.
6. **Ambient Proactive Push Channels:** Emits real-time Server-Sent Events (SSE) to trigger ambient screen badges and audio chimes on the Alexa interface whenever urgent deadlines or newly triggered welfare opportunities emerge.

---

## System Architecture

Glean is built on the Model Context Protocol (MCP) using the official Python SDK over Streamable HTTP. Alexa+ acts as the primary cognitive reasoning agent, querying Glean's 17 administrative tools, 4 resources, and 3 prompt templates over HTTP/SSE.



### High-Level Architecture Flow

```
+-------------------------------------------------------------------------+
|                  User & Client Touchpoint Layer                         |
|      Natural Voice  |  Ambient Touch Screen  |  Interactive Web Chat    |
+------------------------------------+------------------------------------+
                                     |
                                     | Voice Utterance / User Intent
                                     v
+-------------------------------------------------------------------------+
|                Alexa+ / Simulated Voice Ring Interface                  |
|    Svelte 5 Reactive Client  |  Web Speech API  |  Proactive Audio Chime|
+------------------------------------+------------------------------------+
                                     |
                                     | Streamable HTTP (/mcp & /api/ambient/events)
                                     v
+-------------------------------------------------------------------------+
|             Glean MCP Server Engine (Starlette + FastMCP)               |
|                                                                         |
|  - Security & Privacy Gateway (Origin Check, Bearer Token, PII Strip)   |
|  - Ambient Event Broker (Server-Sent Events / SSE Push)                 |
|  - 17 MCP Tools, 4 MCP Resources, 3 MCP Prompts                         |
|  - Kahn's Algorithm Topological Dependency Graph Engine                 |
|  - Cross-Generational Dialect & Speech Normalizer                       |
+-------------------+---------------------------------+-------------------+
                    |                                 |
                    v                                 v
+---------------------------------------+ +-------------------------------+
|          SQLite Local Vault           | |     Global Policy Engine      |
|  - Family Roster (Synthetic Profiles) | |  - US Statutory Schemes       |
|  - Document Metadata & Expirations    | |  - Indian Statutory Schemes   |
|  - Actionable Tasks & Life Events     | |  - 36-Month Temporal Horizon  |
+---------------------------------------+ +-------------------------------+
```

---

## Tech Stack

| Layer / Category | Technology | Purpose and Implementation Details |
|---|---|---|
| AI Protocol Standard | Model Context Protocol (MCP) | FastMCP 2.x server running over Streamable HTTP and SSE transports |
| Backend Framework | Python 3.11+ / Starlette / Uvicorn | High-performance asynchronous ASGI application serving MCP and HTTP |
| Database Engine | SQLite 3 (WAL Mode) | Local, zero-cloud data vault with Write-Ahead Logging and thread-safe sessions |
| Frontend Interface | Svelte 5 / Vite | Reactive single-page application simulating the Alexa+ ambient screen interface |
| Styling and Layout | Tailwind CSS / Custom CSS | Modern clean design with frosted glass accents and high-visibility status badges |
| Voice and Audio | Web Speech API (Recognition and Synthesis) | In-browser speech-to-text, text-to-speech audio, and proactive chime synthesis |
| Real-Time Ambient Push | Server-Sent Events (SSE) | Event-driven push pipeline connecting background alerts to client interfaces |
| Graph Algorithms | Kahn's Algorithm (Topological Sort) | Prerequisite document cycle detection and bottleneck resolution |
| Deployment and Hosting | Render (Render Web Service) | Production ASGI hosting managed via Procfile and render.yaml |
| Automated Testing | Pytest / AnyIO | 261 automated unit, integration, protocol, and security boundary tests |
| Evaluation Benchmark | Python Custom Benchmark (`eval_scenarios.py`) | 17 multi-generational real-world scenarios testing accuracy and latency |
| Spec-Driven Agent Workspace | AWS Kiro Crew / Kiro CLI | Multi-agent specification authoring, task decomposition, and friction logging |
| AI Pair Programming | Google DeepMind Antigravity | Autonomous system architecture, protocol engineering, and test creation |

---

## Global Scope: US and Indian Statutory Schemes

Glean features a declarative Policy-as-Data architecture defined in `data/schemes.json`. Rules, statutory prerequisites, document checklists, and official government endpoints are configured independently of the core application code.

Users can toggle jurisdictions or query schemes across the United States and India:

| Jurisdiction | Program / Policy | Statutory Gate | Target Persona / Impact | Official Government Endpoint |
|---|---|---|---|---|
| United States | Medicare (Parts A & B) | Minimum age 65 | Senior health insurance coverage (Hospital and Medical) | https://www.usa.gov/medicare |
| United States | Social Security Retirement (OASI) | Minimum age 62 | Monthly earned retirement benefits | https://www.usa.gov/what-is-social-security |
| United States | SNAP (Supplemental Nutrition Assistance) | Income threshold (~130% FPL) | Nutritional assistance for low-income households | https://www.usa.gov/food-stamps |
| United States | 401(k) / IRA Catch-Up (SECURE 2.0) | Minimum age 50, employed | Increased tax-advantaged annual retirement contributions | https://www.irs.gov |
| India | Ayushman Vay Vandana Card (AB PM-JAY) | Minimum age 70 | Universal senior healthcare coverage up to 5 Lakh INR annually | https://beneficiary.nha.gov.in |
| India | Senior Citizens Savings Scheme (SCSS) | Minimum age 60 | Sovereign government savings backed by Indian Post / Banks | https://www.indiapost.gov.in |
| India | Atal Pension Yojana (APY) | Age 18 to 40, non-taxpayer | Guaranteed monthly pension tier for unorganized sector | https://www.pfrda.org.in |
| India | Sukanya Samriddhi Yojana (SSY) | Maximum age 10, girl child | High-interest sovereign savings for girl child education | https://www.indiapost.gov.in |
| India | PM Kisan Samman Nidhi (PM-KISAN) | Age 18+, landholder farmer | Direct income support of 6,000 INR per year in three tranches | https://pmkisan.gov.in |
| India | IGNOAPS (Old Age Pension) | Minimum age 65, BPL status | Direct financial assistance for below-poverty-line seniors | https://sjsa.maharashtra.gov.in |
| India | PMJJBY & PMSBY | Age 18-50 (Life) / 18-70 (Accident) | Low-cost annual life and accidental disability insurance | https://www.jansuraksha.gov.in |

### Temporal 36-Month Forecasting

Rather than delivering binary rejections to citizens approaching milestone eligibility gates, Glean calculates temporal proximity. Individuals within 36 months of a milestone threshold are placed in an `almost_eligible` state. Glean reports the remaining countdown in months, highlights required prerequisites, and proactively creates document preparation tasks before the eligibility date arrives.

---

## The 17 MCP Tools

Glean equips Alexa+ with a suite of administrative capabilities partitioned across six functional domains:

| Category | Tool Name | Description |
|---|---|---|
| Family Roster | `add_family_member` | Registers a family member with relation, birth year, and status. |
| Family Roster | `remove_family_member` | Deletes a member and cleans up associated document and task records. |
| Family Roster | `list_family_members` | Returns the entire household roster with calculated ages and statuses. |
| Family Roster | `reset_family_roster` | Restores the canonical 6-member synthetic demo household. |
| Documents | `add_document` | Records document category and expiration date (excludes ID numbers). |
| Documents | `get_expiring_documents` | Scans for documents expiring within a given window, ranked by urgency. |
| Tasks & Deadlines | `add_task` | Creates dated administrative action items. |
| Tasks & Deadlines | `complete_task` | Marks administrative tasks as completed and records history. |
| Tasks & Deadlines | `list_upcoming_tasks` | Retrieves pending paperwork deadlines with overdue detection. |
| Welfare Schemes | `check_scheme_eligibility` | Evaluates eligibility across United States and Indian statutory policies. |
| Welfare Schemes | `get_scheme_checklist` | Generates required document checklists and official application links. |
| Welfare Schemes | `plan_scheme_application` | Produces an end-to-end phased application roadmap. |
| Briefing & Synthesis | `family_brief` | Produces an executive natural-language briefing of urgent household matters. |
| Briefing & Synthesis | `get_family_dashboard` | Aggregates all household metrics into structured card view data. |
| Agentic Workflows | `orchestrate_life_event` | Plans phased 90-day roadmaps for Retirement, College, or Relocation. |
| Agentic Workflows | `audit_document_dependencies` | Performs topological sorting to detect prerequisite document blockers. |
| Agentic Workflows | `simulate_bureaucratic_conflicts` | Detects red-tape cycles and suggests alternate affidavit routes. |

---

## Security and Privacy Posture

Family administrative data requires strict confidentiality and privacy guarantees:

- **Zero Sensitive ID Storage:** Glean never stores Social Security Numbers (SSN), Aadhaar numbers, Permanent Account Numbers (PAN), passport serial numbers, or banking credentials. Only document categories (such as `Passport` or `Health Insurance Card`) and expiration dates are stored in the database.
- **Regex Input Sanitization:** All incoming queries and parameters pass through regular expression sanitizers in `backend/security.py` that intercept national ID patterns before database operations occur.
- **SQL Injection Defenses:** Structured parameter binding is used for all queries, complemented by keyword boundary validation to prevent injection while permitting standard bureaucratic phrasing.
- **Network Boundaries:** Supports bearer token verification via `GLEAN_ACCESS_TOKEN` and strict Origin header validation via `GLEAN_ALLOWED_ORIGINS` to guard against cross-origin requests.

---

## AWS Builder Challenge Integration

Glean actively leveraged **Kiro Crew** (AWS's open-source agent workspace) and **Kiro CLI** during development to establish a spec-driven, multi-agent development workflow. Comprehensive documentation and session logs are available in [`docs/aws-builder.md`](docs/aws-builder.md).

### 1. Spec-Driven Development
Before writing implementation code, structured specifications were authored and reviewed:
- `.kiro/specs/family-tools/requirements.md`: Functional boundaries, validation constraints, and non-goals.
- `.kiro/specs/family-tools/design.md`: SQLite schema definitions, parameter contracts, and error structures.
- `.kiro/specs/family-tools/tasks.md`: Phased task breakdown with strict acceptance criteria.
- `.kiro/specs/almost-eligible/`: Specifications for 36-month temporal scheme eligibility forecasting.

### 2. Parallel Subagent Sessions
Specialized subagent sessions were deployed to handle distinct engineering tasks:
- **Test Generation Subagent:** Generated boundary and validation tests in `tests/test_schemes_extra.py`, expanding automated test coverage from 53 to 73 initial test assertions.
- **Documentation Subagent:** Synthesized plain-language policy references in `docs/schemes.md`.

### 3. Persistent Cross-Session Context
Kiro Crew preserved architectural context across development sessions:
- Retained design conventions (such as birth-year arithmetic for age calculations) across sessions without re-prompting.
- Documented friction points and resolution steps in [`docs/friction-log.md`](docs/friction-log.md), capturing insights on path resolution, Starlette middleware integration, and SQLite concurrency.

---

## Technical Friction Log

Glean maintains a detailed engineering friction log documenting architectural obstacles, root causes, and exact code-level resolutions. For full details, see [`docs/friction-log.md`](docs/friction-log.md).

Key challenges addressed during development include:

1. **FastMCP v2 SDK Migration:** Migrated from legacy import structures to `mcp.server.mcpserver.MCPServer` and adapted to Streamable HTTP and SSE transport standards.
2. **SQLite Cross-Thread Concurrency:** Resolved thread ownership exceptions when FastMCP dispatched resource handlers across thread pools by configuring `check_same_thread=False` and enabling Write-Ahead Logging (`WAL`).
3. **PII Sanitization Over-Matching:** Refined Aadhaar detection regexes to comply with Verhoeff/UIDAI specifications (`\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b`), eliminating false positives on financial figures and birth years.
4. **SQL Keyword Collisions:** Replaced substring matching with strict word-boundary delimiters (`\b(SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER)\b\s+`) so that conversational words such as "selection" or "update" pass without alarms.
5. **Temporal Age Boundaries:** Addressed leap-year age calculation drift and replaced binary eligibility rejections with a 36-month `almost_eligible` forecasting horizon.
6. **Cyclic Prerequisite Deadlocks:** Handled circular dependencies in administrative paperwork requirements by implementing Kahn's algorithm for topological sorting, detecting cycles, and proposing affidavit-based resolutions.
7. **Life Event State Transitions:** Ensured atomic multi-step database insertions for 90-day life event plans using deterministic sequence tiers and explicit transactions.
8. **Dialect and Code-Switching Tokenization:** Built a bilingual vocabulary normalizer to map colloquial and regional terminology into canonical MCP tool arguments.

---

## Instructions to Run the Project Locally

Glean includes a pre-compiled frontend distribution in `alexa-simulator/dist`. Running the full application locally requires only Python 3.11+.

### Prerequisites
- Python 3.11 or higher
- Git
- Modern web browser (Chrome, Edge, or Firefox)

### Step 1: Clone the Repository
```bash
git clone https://github.com/askabdugale/Glean.git
cd Glean
```

### Step 2: Set Up Virtual Environment
On Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed Demo Data
Populate the database with a synthetic multi-generational family roster (Chandler, Amy, Justin, Riley, Jace, Gwen) and 18 realistic sample documents and deadlines:
```bash
python seed_demo_data.py --reset
```

### Step 5: Launch the Server
```bash
python server.py
```

The application will start on `http://127.0.0.1:8000`.

### Accessible Endpoints
- **Interactive Alexa+ Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Streamable HTTP MCP Transport:** [http://127.0.0.1:8000/mcp](http://127.0.0.1:8000/mcp)
- **Live SSE Ambient Event Stream:** [http://127.0.0.1:8000/api/ambient/events](http://127.0.0.1:8000/api/ambient/events)

---

## Verification and Testing

### Running Automated Pytest Suite
Execute the 261 automated tests covering tools, resources, security guards, token validation, origin filtering, and dialect parsing:
```bash
pytest
```
Expected output:
```text
============================= 261 passed in 2.49s =============================
```

### Running the Multi-Generational Evaluation Benchmark
Execute the 17-scenario evaluation benchmark testing real-world household administrative situations:
```bash
python eval_scenarios.py
```
Expected output:
```text
========================================================================================
GLEAN AGENTIC SCENARIO EVALUATION BENCHMARK
Target: Multi-Generational Family Paperwork Administration & Scheme Routing
========================================================================================
 [PASS] Scenario 01: Super Senior Health Coverage (Grandpa Chandler, Age 76)   (0.4ms)
 [PASS] Scenario 02: Low-Income Senior Pension Check (Grandma with BPL)        (0.4ms)
 [PASS] Scenario 03: Temporal Eligibility / Almost Eligible (Father Justin)    (0.2ms)
 [PASS] Scenario 04: Working Mother Insurance Audit (Mother Riley, Age 54)     (0.2ms)
 [PASS] Scenario 05: Young Adult Pension & Life Cover (Son Jace, Age 26)       (0.2ms)
 [PASS] Scenario 06: Girl Child Education & Savings (Young Daughter, Age 6)    (0.3ms)
 [PASS] Scenario 07: Rural / Agricultural Support (Farmer Uncle, Age 42)       (0.2ms)
 [PASS] Scenario 08: Urgent Passport Expiry & Renewal Alert (Emergency)        (2.4ms)
 [PASS] Scenario 09: Overdue Task Tracking & Deadline Escalation               (0.1ms)
 [PASS] Scenario 10: Multi-Step Scheme Application Planning                    (0.5ms)
 [PASS] Scenario 11: Security & Privacy Guardrails (Aadhaar & Injections)      (0.0ms)
 [PASS] Scenario 12: Whole-Family Admin Dashboard & Roster Synthesis           (0.5ms)
 [PASS] Scenario 13: Autonomous Life-Event Orchestrator (Retirement & 90-Day Transition) (0.5ms)
 [PASS] Scenario 14: Document Dependency & Bottleneck Graph Audit (Blocker Cascade) (0.6ms)
 [PASS] Scenario 15: Bureaucratic Conflict Simulation & Red-Tape Optimization  (0.3ms)
 [PASS] Scenario 16: Proactive Ambient Push & Temporal Event Watcher           (1.8ms)
 [PASS] Scenario 17: Cross-Generational Voice Dialect Engine (Grandparent vs Student) (0.6ms)
----------------------------------------------------------------------------------------
BENCHMARK RESULT: 17 / 17 SCENARIOS PASSED (100.0% ACCURACY)
Average Execution Latency: 0.5ms | Security Violations Caught: 2/2 | Data Leaks: 0
========================================================================================
```

---

## External MCP Client Integration

### Claude Desktop Configuration
Add Glean as an MCP server in your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "glean": {
      "command": "python",
      "args": ["-m", "server"],
      "cwd": "C:/path/to/Glean"
    }
  }
}
```

### Official MCP Inspector
Inspect and interact with all 17 tools and streamable HTTP endpoints in real time:
```bash
npx @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp
```

---

## AI Assistance Disclosure

This project was developed with the assistance of **Google DeepMind Antigravity** serving as the autonomous AI pair programmer:

1. **System Architecture and Protocol Engineering:** Designed the FastMCP 2.x server integration, Starlette middleware pipeline, and Streamable HTTP endpoint structure.
2. **Graph Algorithms and Conflict Detection:** Implemented Kahn's algorithm for topological sorting to audit document prerequisites and detect cyclic bureaucratic bottlenecks.
3. **Frontend and Ambient Interface:** Built the Svelte single-page application, custom SVG Alexa Voice Ring with state management, and Web Speech API synthesis integration.
4. **Testing and Verification Suites:** Authored the comprehensive 261-test automated suite and the 17-scenario benchmark harness in `eval_scenarios.py`.

---

## Open Source License

Glean is licensed under the open source **MIT License**. For complete terms and permissions, see the [`LICENSE`](LICENSE) file in the root repository directory.

All default family personas, document dates, and household relationships are synthetic data created exclusively for testing and demonstration purposes.

---

## Hackathon Project Statement

This project was created and submitted for the **Build, Ship, Shape: Amazon Developer Hackathon** under the **Alexa+** track. All architectural decisions, MCP tool implementations, scheme routing logic, and ambient notifications were developed specifically to advance proactive, multi-generational household assistance within the Alexa+ developer ecosystem.
