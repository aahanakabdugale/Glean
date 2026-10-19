# Glean — AI Family Admin Agent (Alexa+ Track)

> **Autonomous multi-generational family paperwork manager, deadline sentinel, and government scheme eligibility routing engine.**

[![Track: Alexa+](https://img.shields.io/badge/Track-Alexa%2B-blue?style=flat-square)](https://devpost.com)
[![Mini Challenge: AWS Builder](https://img.shields.io/badge/AWS%20Builder-Kiro%20Crew%20Integrated-FF9900?style=flat-square&logo=amazon-aws)](docs/aws-builder.md)
[![MCP: Streamable HTTP](https://img.shields.io/badge/MCP-Streamable%20HTTP-059669?style=flat-square)](http://127.0.0.1:8000/mcp)
[![Tests: 259 Passing](https://img.shields.io/badge/Tests-259%20Passing-brightgreen?style=flat-square)](tests/)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

---

## 🌟 The Problem & The Vision

In every household, one family member quietly bears the exhausting cognitive load of managing everyone's paperwork: passports, driving licenses, insurance policies, pension accounts, and healthcare registrations. Documents expire unnoticed, renewal windows pass with penalties, and older parents and grandparents miss out on critical government welfare schemes they are legally entitled to receive simply because the rules are buried in bureaucratic jargon.

**Glean transforms Alexa into a proactive, multi-generational Family Administrator.** 

Instead of waiting for panicked questions after a deadline is missed, Glean:
1. **Audits Family Documents Continuously:** Tracks expirations and detects prerequisite document bottlenecks before appointments.
2. **Routes Welfare Schemes Automatically:** Matches elderly and working family members against statutory government benefit schemes in **India (IN)** and the **United States (US)**.
3. **Forecasts Approaching Eligibility:** Alerts families 36 months before milestone birthdays (e.g. Medicare at 65 or Ayushman Vay Vandana at 70) so paperwork can be pre-assembled.
4. **Orchestrates Major Life Events:** Generates phased transition plans and dated tasks for events like Retirement, Higher Education, or Relocation.
5. **Pushes Ambient Proactive Alerts:** Broadcasts urgent upcoming deadlines via Server-Sent Events (SSE) directly to the Alexa screen and chime.

---

## 🏗️ Architecture & How It Works

Glean is built on the **Model Context Protocol (MCP)** using official Python SDK (`MCPServer`) over **Streamable HTTP**. Alexa+ (or Claude Desktop, Kiro CLI, or any MCP-capable client) acts as the cognitive brain, calling Glean's 17 specialized tools as needed.

```
       ┌────────────────────────────────────────────────────────┐
       │   User (Natural Voice / Ambient Screen / Web Chat)     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │   Alexa+ / Simulated Voice Ring (Svelte + Web Speech)  │
       └───────────────────────────┬────────────────────────────┘
                                   │  Streamable HTTP (/mcp)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        Glean MCP Server (Starlette + FastMCP)          │
       │                                                        │
       │  • Security Guardrails (Origin check, Token, PII strip)│
       │  • Ambient Event Broker (Server-Sent Events / SSE)     │
       │  • 17 MCP Tools, 4 MCP Resources, 3 MCP Prompts        │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
                      ▼                          ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │   SQLite Local Vault   │      │ Global Policy Engine   │
       │ (Family, Docs, Tasks)  │      │ (India & US Schemes)   │
       └────────────────────────┘      └────────────────────────┘
```

---

## ⚡ Quick Start: Run Locally in Under 2 Minutes

Glean comes with a pre-compiled frontend distribution inside `alexa-simulator/dist`. You only need Python 3.11+ — no Node.js or cloud setup is required to run the full experience!

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/Glean.git
cd Glean

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Seed Fake Demo Data
Populates a multi-generational demo family (Chandler, Amy, Justin, Riley, Jace, Gwen) with 18 realistic sample documents and upcoming deadlines:
```bash
python seed_demo_data.py --reset
```

### 3. Launch the Server
```bash
python server.py
```
Open your browser to:
* **Interactive Alexa+ Web App:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Streamable HTTP MCP Transport:** [http://127.0.0.1:8000/mcp](http://127.0.0.1:8000/mcp)
* **Live SSE Ambient Stream:** [http://127.0.0.1:8000/api/ambient/events](http://127.0.0.1:8000/api/ambient/events)

---

## 🛠️ The 17 MCP Tools

Glean equips the AI with an extensive suite of administrative capabilities:

| Category | Tool | Functionality |
|---|---|---|
| **Roster** | `add_family_member` | Registers a family member with relation, birth year, and status. |
| | `remove_family_member` | Deletes a member and cascades cleanup of associated records. |
| | `list_family_members` | Returns the entire family roster with age and status. |
| | `reset_family_roster` | Restores canonical 6-member demo household roster. |
| **Documents** | `add_document` | Stores document type and expiration date (never ID numbers). |
| | `get_expiring_documents` | Scans for documents expiring within *N* days, ranked by urgency. |
| **Tasks & Deadlines** | `add_task` | Creates dated administrative action items. |
| | `complete_task` | Marks tasks as completed and logs history. |
| | `list_upcoming_tasks` | Returns upcoming paperwork deadlines with overdue detection. |
| **Welfare Schemes** | `check_scheme_eligibility` | Evaluates eligibility across Indian and US statutory schemes. |
| | `get_scheme_checklist` | Generates document prerequisites and official portal links. |
| | `plan_scheme_application` | Creates an end-to-end multi-step application preparation plan. |
| **Synthesis & Briefing** | `family_brief` | Produces an executive spoken brief of all urgent household matters. |
| | `get_family_dashboard` | Aggregates all household metrics into structured card data. |
| **Advanced Agentic** | `orchestrate_life_event` | Plans phased 90-day roadmaps for Retirement, College, or Relocation. |
| | `audit_document_dependencies` | Performs topological sorting to find prerequisite document blockers. |
| | `simulate_bureaucratic_conflicts` | Detects red-tape cycles and suggests alternate affidavit routes. |
| | `trigger_proactive_ambient_alert` | Emits immediate Server-Sent Events to trigger Alexa chime and badge. |
| | `explain_for_generation` | Synthesizes dialect-tuned explanations (Grandparent vs Student). |

---

## 🌍 Global Multi-Jurisdiction Policy Engine

Glean implements **Policy-as-Data** in `data/schemes.json`. Rules, statutory prerequisites, document checklists, and official government endpoints are configured declaratively.

Users and judges can toggle between **`🌐 All Regions`**, **`🇮🇳 India`**, and **`🇺🇸 United States`** via the UI top dock or by asking voice questions to Alexa:

| Jurisdiction | Program / Policy | Statutory Gate | Target Persona | Official Portal |
|---|---|---|---|---|
| 🇺🇸 **US** | **Medicare (Parts A & B)** | `min_age: 65` | Chandler (76), Amy (73) | [usa.gov/medicare](https://www.usa.gov/medicare) |
| 🇺🇸 **US** | **Social Security Retirement (OASI)** | `min_age: 62` | Chandler, Amy (claimed); Justin (58, almost eligible at 62) | [usa.gov/what-is-social-security](https://www.usa.gov/what-is-social-security) |
| 🇺🇸 **US** | **SNAP (Food Assistance)** | `low_income` | Needs-based assistance (~130% FPL) | [usa.gov/food-stamps](https://www.usa.gov/food-stamps) |
| 🇺🇸 **US** | **401(k) / IRA Catch-Up (SECURE 2.0)** | `min_age: 50, employed` | Justin (58), Riley (54) | [irs.gov](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-catch-up-contributions) |
| 🇮🇳 **IN** | **Ayushman Vay Vandana Card (AB PM-JAY)** | `min_age: 70` | Universal senior health coverage (₹5 Lakh cover) | [beneficiary.nha.gov.in](https://beneficiary.nha.gov.in) |
| 🇮🇳 **IN** | **Senior Citizens Savings Scheme (SCSS)** | `min_age: 60` | Post office / bank sovereign savings | [indiapost.gov.in](https://www.indiapost.gov.in) |
| 🇮🇳 **IN** | **Atal Pension Yojana (APY)** | `18 <= age <= 40` | Disqualified if income tax payer | [pfrda.org.in](https://pfrda.org.in) |
| 🇮🇳 **IN** | **Sukanya Samriddhi Yojana (SSY)** | `max_age: 10, girl_child` | Girl-child education & savings (max 2/family) | [indiapost.gov.in](https://www.indiapost.gov.in) |
| 🇮🇳 **IN** | **PM Kisan Samman Nidhi (PM-KISAN)** | `18+, farmer` | Direct farmer income support | [pmkisan.gov.in](https://pmkisan.gov.in) |
| 🇮🇳 **IN** | **IGNOAPS (Maharashtra)** | `min_age: 65, bpl` | Low-income old-age pension | [sjsa.maharashtra.gov.in](https://sjsa.maharashtra.gov.in) |
| 🇮🇳 **IN** | **PMJJBY & PMSBY** | `18-50` / `18-70` | Low-cost life and accidental disability insurance | [jansuraksha.gov.in](https://www.jansuraksha.gov.in) |

### Temporal "Almost Eligible" Forecasting
Citizens within **36 months** of milestone criteria are not rejected with an empty response. Glean places them into an `almost_eligible` state, reporting the exact countdown in months and scheduling proactive document preparation tasks so families are ready on day one.

---

## 🔒 Security & Privacy Posture

* **Zero Sensitive ID Storage:** Glean **never** stores Social Security Numbers (SSN), Aadhaar numbers, PANs, voter IDs, or banking credentials. Only document *names* (`Passport`, `Health Insurance Card`) and expiration dates exist in the database.
* **Regex Input Sanitization:** All incoming user prompts and tool parameters pass through strict regular expression sanitizers in `backend/security.py` that intercept and reject national ID patterns before database queries execute.
* **SQL Injection Boundaries:** Keyword guards with strict word-boundary delimiters prevent SQL manipulation while allowing standard conversational vocabulary (e.g. *"selection"*, *"update"*).
* **Network & Origin Security:**
  - `validate_token`: Optional Bearer token protection for production deployments via `GLEAN_ACCESS_TOKEN`.
  - `validate_origin`: Strict Origin allowlist preventing cross-site request forgery and unauthorized browser hijacking.

---

## 🤝 AI Assistance & Pair Programming (Google DeepMind Antigravity)

This project was built with the active assistance of **Google DeepMind Antigravity** as the primary autonomous AI pair programming agent:

1. **System Architecture & MCP Protocol Engineering:**
   - Designed the FastMCP 2.x server integration, Starlette middleware pipeline, and Streamable HTTP endpoint setup.
   - Architected the topological sort graph algorithm (Kahn's algorithm) for cycle detection in document dependency chains.
2. **Frontend UI & Interactive Data Visualizations:**
   - Engineered the Svelte single-page application, custom SVG Alexa Voice Ring with interactive Orb state machine, and Web Speech API synthesis integration.
   - Built interactive DAG components (`DependencyGraphDAG.svelte`, `ConflictSimulatorDAG.svelte`, `LifeEventDAG.svelte`) for visual red-tape auditing.
   - Refined UI ergonomics: designed frosted sticky header scroll protection and high-visibility live protocol trace badges (`Traces(n)`).
3. **Comprehensive Testing & Evaluation Benchmarks:**
   - Created the full 259-test automated test suite across unit, integration, and security layers.
   - Developed `eval_scenarios.py` implementing 17 real-world multi-generational benchmark scenarios testing edge-case bureaucratic handling.

---

## 🚀 AWS Builder Mini Challenge (Kiro Crew Integration)

Glean actively leveraged **Kiro Crew** (AWS's open-source agent workspace) and **Kiro CLI** during development to pioneer a spec-driven, multi-agent development workflow. Full details and logs are preserved in [`docs/aws-builder.md`](docs/aws-builder.md).

### 1. Spec-Driven Development
Before tool implementation began, Kiro Crew was used to author structured specifications stored directly in the repository:
- `.kiro/specs/family-tools/requirements.md` — Functional specifications, validation constraints, and non-goals.
- `.kiro/specs/family-tools/design.md` — SQLite schema definitions, parameter contracts, and error formats.
- `.kiro/specs/family-tools/tasks.md` — 15-step task breakdown with strict "done when" acceptance criteria.
- `.kiro/specs/almost-eligible/` — Specification for 36-month temporal scheme eligibility forecasting.

### 2. Parallel Subagent Sessions
Separate Kiro Crew sessions were deployed as independent subagents:
- **Test Generation Subagent:** Generated boundary and validation tests in `tests/test_schemes_extra.py`, expanding test coverage from 53 to 73 initial tests without manual revisions.
- **Documentation Subagent:** Synthesized plain-English policy documentation in `docs/schemes.md`.

### 3. Persistent Cross-Session Context
Kiro Crew maintained context across days:
- Correctly recalled design conventions (such as birth-year-only arithmetic for senior citizen age determination) without re-prompting.
- Documented friction points and fixes in [`docs/friction-log.md`](docs/friction-log.md), capturing real engineering insights regarding path resolution, Starlette middleware wrapping, and SQLite thread safety.

---

## 🧪 Testing & Verification Scorecard

### Run Automated Tests
```bash
pytest
```
```text
============================= 259 passed in 1.40s =============================
```
* **100% Green Unit & Integration Coverage:** Roster, documents, tasks, schemes, security guards, token auth, origin validation, ambient SSE streaming, and speech normalization.

### Run Multi-Generational Scenario Benchmark
```bash
python eval_scenarios.py
```
```text
========================================================================================
GLEAN AGENTIC SCENARIO EVALUATION BENCHMARK
Target: Multi-Generational Family Paperwork Administration & Scheme Routing
========================================================================================
 [PASS] Scenario 01: Super Senior Health Coverage (Grandpa Chandler, Age 76)   (0.3ms)
 [PASS] Scenario 02: Low-Income Senior Pension Check (Grandma with BPL)        (0.4ms)
 [PASS] Scenario 03: Temporal Eligibility / Almost Eligible (Father Justin)    (0.2ms)
 [PASS] Scenario 04: Working Mother Insurance Audit (Mother Riley, Age 54)     (0.2ms)
 [PASS] Scenario 05: Young Adult Pension & Life Cover (Son Jace, Age 26)       (0.2ms)
 [PASS] Scenario 06: Girl Child Education & Savings (Young Daughter, Age 6)    (0.3ms)
 [PASS] Scenario 07: Rural / Agricultural Support (Farmer Uncle, Age 42)       (0.2ms)
 [PASS] Scenario 08: Urgent Passport Expiry & Renewal Alert (Emergency)        (2.6ms)
 [PASS] Scenario 09: Overdue Task Tracking & Deadline Escalation               (0.1ms)
 [PASS] Scenario 10: Multi-Step Scheme Application Planning                    (0.6ms)
 [PASS] Scenario 11: Security & Privacy Guardrails (Aadhaar & Injections)      (0.0ms)
 [PASS] Scenario 12: Whole-Family Admin Dashboard & Roster Synthesis           (0.3ms)
 [PASS] Scenario 13: Autonomous Life-Event Orchestrator (Retirement 90-Day)    (0.3ms)
 [PASS] Scenario 14: Document Dependency & Bottleneck Graph Audit (Blockers)   (0.4ms)
 [PASS] Scenario 15: Bureaucratic Conflict Simulation & Red-Tape Optimization  (0.2ms)
 [PASS] Scenario 16: Proactive Ambient Push & Temporal Event Watcher           (1.2ms)
 [PASS] Scenario 17: Cross-Generational Voice Dialect Engine (Dialect Tuning)   (0.4ms)
----------------------------------------------------------------------------------------
BENCHMARK RESULT: 17 / 17 SCENARIOS PASSED (100.0% ACCURACY)
Average Execution Latency: 0.5ms | Security Violations Caught: 2/2 | Data Leaks: 0
========================================================================================
```

---

## 🔌 Connecting to External MCP Clients

### Claude Desktop Configuration
Add Glean to your `claude_desktop_config.json`:
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
Test all 17 tools and streamable HTTP resources in real time:
```bash
npx @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp
```

---

## 📜 License & Compliance

* **License:** MIT License — see [`LICENSE`](LICENSE) for complete terms.
* **No Real PII:** All default personas, document dates, and household relationships are synthetic fixtures created exclusively for demonstration and testing.
* **Non-Affiliation Notice:** All scheme names, program acronyms, and government portal links belong to their respective statutory authorities (e.g. Government of India, US Federal Government). Glean provides preliminary organizational guidance and does not replace official legal or administrative counsel.
