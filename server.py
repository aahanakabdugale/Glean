from glean import db
from glean.app import mcp
import glean.tools  # noqa: F401  (importing registers the tools)


@mcp.tool()
def ping() -> str:
    """Check that the Glean server is alive."""
    return "Glean is running"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


if __name__ == "__main__":
    db.init_db(db.get_connection())
    mcp.run(transport="streamable-http")