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
from starlette.responses import JSONResponse
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette

from glean import db
from glean.app import mcp
from glean.security import validate_origin, validate_token

import glean.tools  # noqa: F401  — side-effect: registers all 9 tools on mcp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Security middleware
# ---------------------------------------------------------------------------

class GleanSecurityMiddleware(BaseHTTPMiddleware):
    """Enforce token and Origin checks on every incoming HTTP request."""

    async def dispatch(self, request: Request, call_next):
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
    """Return the Starlette ASGI app with security middleware applied."""
    # Build the raw MCP Starlette app
    host = os.environ.get("GLEAN_HOST", "127.0.0.1")
    mcp_app = mcp.streamable_http_app(host=host)

    # Wrap it: middleware is applied outermost-first so security runs before
    # any MCP processing.
    mcp_app.add_middleware(GleanSecurityMiddleware)

    # Locate the built frontend (simulator/dist).
    # Judges run `python server.py` with no Node.js — this makes it work.
    here = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(here, "simulator", "dist")

    routes = [Mount("/mcp", app=mcp_app)]

    if os.path.isdir(dist_dir):
        # Serve the Glean UI at /
        routes.append(
            Mount("/", app=StaticFiles(directory=dist_dir, html=True), name="static")
        )
        logger.info("Serving Glean UI from %s", dist_dir)
    else:
        logger.warning(
            "simulator/dist not found — run `cd frontend && npm run build` to build the UI."
        )

    return Starlette(routes=routes)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    host = os.environ.get("GLEAN_HOST", "127.0.0.1")
    port = int(os.environ.get("GLEAN_PORT", "8000"))

    # Initialise the database (creates tables if they do not exist).
    db.init_db(db.get_connection())

    app = build_app()

    logger.info("Glean MCP server starting on http://%s:%d/mcp", host, port)
    uvicorn.run(app, host=host, port=port)