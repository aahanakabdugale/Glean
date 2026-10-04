from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Glean")


@mcp.tool()
def ping() -> str:
    """Check that the Glean server is alive."""
    return "Glean is running"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="streamable-http")