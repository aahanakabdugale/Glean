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