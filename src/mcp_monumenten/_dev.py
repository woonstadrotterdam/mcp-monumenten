"""Dev helper that exposes a module-level MCP server for `mcp run`."""

from mcp_monumenten.server import SERVER_NAME, MonumentenMCP

mcp = MonumentenMCP(name=SERVER_NAME)

if __name__ == "__main__":
    mcp.run()
