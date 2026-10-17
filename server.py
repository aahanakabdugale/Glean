"""
Glean MCP server entry point.

Starts a Streamable HTTP MCP server on http://GLEAN_HOST:GLEAN_PORT/mcp
(defaults: 127.0.0.1:8000).

Security layer (live on every request):
  - validate_token   → Bearer token or ?token= query param checked against
                       GLEAN_ACCESS_TOKEN env var.  When the var is unset the
                       server runs in open / dev mode (no token required).
  - validate_origin  → HTTP Origin header checked against a glob allowlist
                       (localhost and 127.0.0.1 on any port by default).
                       Requests without an Origin header are allowed so that
                       CLI tools and the MCP Inspector work out of the box.

Environment variables:
  GLEAN_ACCESS_TOKEN   Secret token clients must supply (omit for dev mode).
  GLEAN_HOST           Bind address  (default: 127.0.0.1).
  GLEAN_PORT           Port number   (default: 8000).
  GLEAN_DB_PATH        SQLite file   (default: glean.db).
"""

import logging
import os

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from backend import db
from backend.ambient import ambient_broker, evaluate_proactive_alerts
from backend.app import mcp
from backend.security import validate_origin, validate_token

import backend.tools      # noqa: F401  — side-effect: registers all 11 tools on mcp
import backend.resources  # noqa: F401  — side-effect: registers MCP resources on mcp
import backend.prompts    # noqa: F401  — side-effect: registers MCP prompts on mcp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Security middleware & browser fallbacks
# ---------------------------------------------------------------------------

class GleanSecurityMiddleware(BaseHTTPMiddleware):
    """Enforce token and Origin checks on incoming HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        # --- Favicon helper -------------------------------------------------
        if request.url.path == "/favicon.ico":
            return RedirectResponse("/favicon.svg")

        # --- Browser direct navigation to /mcp ------------------------------
        # If someone visits /mcp directly in a browser address bar (GET with Accept text/html),
        # return a helpful page directing them to the Web UI instead of a raw 400.
        if request.url.path == "/mcp" and request.method == "GET":
            accept = request.headers.get("accept", "")
            if "text/html" in accept and "text/event-stream" not in accept:
                html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Glean — MCP Protocol Endpoint</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: grid; place-items: center; min-height: 100vh; margin: 0; }
    .card { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 16px; padding: 36px; max-width: 520px; text-align: center; box-shadow: 0 12px 32px rgba(0,0,0,0.5); }
    h1 { font-size: 1.5rem; margin-top: 0; color: #38bdf8; }
    p { font-size: 0.95rem; color: #94a3b8; line-height: 1.6; }
    .btn { display: inline-block; margin-top: 18px; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; font-weight: 600; border-radius: 10px; transition: background 0.2s; }
    .btn:hover { background: #1d4ed8; }
    code { background: rgba(0,0,0,0.3); padding: 3px 6px; border-radius: 6px; font-family: monospace; color: #e2e8f0; }
  </style>
</head>
<body>
  <div class="card">
    <h1>⚡ Glean MCP Protocol Endpoint</h1>
    <p>You have reached the Streamable HTTP MCP transport endpoint (<code>http://127.0.0.1:8000/mcp</code>). Connect your MCP AI client, Claude Desktop, or MCP Inspector here.</p>
    <div style="display:flex; justify-content:center; gap:10px; margin: 16px 0; flex-wrap: wrap;">
      <span style="background: rgba(37,99,235,0.2); color:#60a5fa; border:1px solid #2563eb; border-radius:8px; padding:4px 10px; font-size:0.8rem; font-weight:600;">🛠️ 11 Tools</span>
      <span style="background: rgba(16,185,129,0.2); color:#34d399; border:1px solid #059669; border-radius:8px; padding:4px 10px; font-size:0.8rem; font-weight:600;">📦 4 Resources</span>
      <span style="background: rgba(168,85,247,0.2); color:#c084fc; border:1px solid #7c3aed; border-radius:8px; padding:4px 10px; font-size:0.8rem; font-weight:600;">📝 3 Prompts</span>
    </div>
    <p>To use the simulated <strong>Alexa+ Family Admin Web App</strong>, please visit the home page:</p>
    <a class="btn" href="/">Open Glean Web App →</a>
  </div>
</body>
</html>"""
                return HTMLResponse(html, status_code=200)

        # --- Origin check ---------------------------------------------------
        origin = request.headers.get("origin")
        origin_ok, origin_err = validate_origin(origin)
        if not origin_ok:
            logger.warning("Blocked request — bad origin: %s", origin)
            return JSONResponse(
                {"error": origin_err},
                status_code=403,
            )

        # --- Token check ----------------------------------------------------
        # Token validation guards the MCP endpoint (/mcp).
        # Static files (the web UI at / and /assets) do not require a token.
        if request.url.path.startswith("/mcp"):
            headers = dict(request.headers)
            query_params = dict(request.query_params)
            token_ok, token_err = validate_token(headers, query_params)
            if not token_ok:
                logger.warning("Blocked request — bad token from %s", request.client)
                return JSONResponse(
                    {"error": token_err},
                    status_code=401,
                )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def build_app():
    """Return the MCP Starlette ASGI app with security middleware applied."""
    host = os.environ.get("GLEAN_HOST", "127.0.0.1")
    app = mcp.streamable_http_app(host=host)

    # Wrap it: middleware is applied outermost-first so security runs before
    # any MCP processing.
    app.add_middleware(GleanSecurityMiddleware)

    # --- Proactive Ambient Push & SSE endpoints -------------------------
    async def ambient_events_endpoint(request: Request):
        q = ambient_broker.subscribe()
        return StreamingResponse(
            ambient_broker.event_generator(q),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    async def ambient_alerts_json(request: Request):
        alerts = evaluate_proactive_alerts()
        return JSONResponse({"alerts": alerts, "count": len(alerts)})

    app.add_route("/api/ambient/events", ambient_events_endpoint, methods=["GET"])
    app.add_route("/api/ambient/alerts", ambient_alerts_json, methods=["GET"])

    # Locate the built frontend (alexa-simulator/dist).
    # Allows judges to run `python server.py` directly without Node.js.
    here = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(here, "alexa-simulator", "dist")

    if os.path.isdir(dist_dir):
        # Mount built static assets directly on the MCP Starlette app
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
        logger.info("Serving Glean UI from %s", dist_dir)
    else:
        logger.info("alexa-simulator/dist not found — running in pure MCP mode")

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    host = os.environ.get("GLEAN_HOST", os.environ.get("HOST", "0.0.0.0"))
    port = int(os.environ.get("PORT", os.environ.get("GLEAN_PORT", "8000")))

    # Initialise the database (creates tables if they do not exist).
    db.init_db(db.get_connection())

    app = build_app()

    logger.info("Glean MCP server starting on http://%s:%d/mcp", host, port)
    uvicorn.run(app, host=host, port=port)