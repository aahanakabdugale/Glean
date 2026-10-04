# Friction Log

Honest notes on problems hit while building Glean, and how each was fixed.

## Day 1 (Sun Oct 4)

### 1. FastMCP import failed
- **Tool:** MCP Python SDK
- **What happened:** `pip install "mcp[cli]"` installed v2.3.0. `from mcp.server.fastmcp import FastMCP` raised ModuleNotFoundError.
- **Cause:** v2 renamed FastMCP to MCPServer. Most tutorials and AI answers still show the old name.
- **Fix:** `from mcp.server.mcpserver import MCPServer`.
- **Time lost:** ~10 min

### 2. Wrong shell for the activation command
- **Tool:** Windows terminal / Python venv
- **What happened:** Ran PowerShell commands (`Set-ExecutionPolicy`, `Activate.ps1`) in Command Prompt. Nothing happened, and the venv did not activate.
- **Fix:** In cmd, use `.venv\Scripts\activate.bat`.
- **Time lost:** ~5 min

### 3. VS Code terminal defaults to PowerShell
- **Tool:** VS Code
- **What happened:** The integrated terminal opened PowerShell while my notes used cmd syntax.
- **Fix:** Terminal dropdown, then Command Prompt, or use commands that work in both.
- **Time lost:** ~5 min

### 4. MCP Inspector needed a one-time install
- **Tool:** MCP Inspector (v2.9.0)
- **What happened:** `npx @modelcontextprotocol/inspector` asked to install the package before running. Node.js was required first.
- **Fix:** Typed `y` to proceed.
- **Time lost:** ~3 min

### 5. Inspector v2.9.0 UI differs from tutorials
- **Tool:** MCP Inspector
- **What happened:** It opens a server list with sample servers instead of the old connect form. The "Add server" form defaults to stdio, which would launch a new process instead of connecting to my running server.
- **Fix:** Chose Streamable HTTP and the URL `http://localhost:8000/mcp`.
- **Time lost:** ~10 min

### 6. .gitignore didn't work, .venv got staged
- **Tool:** Git / Windows shell
- **What happened:** `git add .` started adding thousands of files from `.venv`, with LF/CRLF warnings.
- **Cause:** `.gitignore` was written by a shell `echo` and wasn't read correctly (likely encoding).
- **Fix:** `git reset`, rewrote `.gitignore` from cmd, verified with `git check-ignore -v .venv`.
- **Time lost:** ~10 min

### 7. First push rejected (remote had commits)
- **Tool:** Git / GitHub
- **What happened:** `git push` was rejected with "fetch first".
- **Cause:** GitHub created an initial commit (LICENSE, README) when the repo was made, and I had also created empty LICENSE and README locally.
- **Fix:** `git pull --allow-unrelated-histories`, kept GitHub's versions of both files, then pushed.
- **Time lost:** ~10 min

### 8. kiro-cli not recognized right after install
- **Tool:** Kiro CLI (v2.27.1)
- **What happened:** `kiro-cli login` returned "not recognized as an internal or external command".
- **Cause:** The terminal was opened before the install finished, so PATH wasn't updated.
- **Fix:** Re-ran the PowerShell installer, then opened a new Command Prompt.
- **Time lost:** ~10 min

### 9. kirocrew command not on PATH after desktop install
- **Tool:** Kiro Crew (Windows desktop installer)
- **What happened:** `kirocrew token` returned "not recognized", and `where kirocrew` found nothing.
- **Cause:** The installer keeps the CLI inside its app folder and doesn't add it to PATH.
- **Fix:** Found `kirocrew.cmd` under `%LOCALAPPDATA%\Programs\KiroCrew\...\bin` and ran it with the full path.
- **Time lost:** ~10 min