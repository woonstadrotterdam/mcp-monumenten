"""Dev helper that exposes a module-level MCP server for `mcp run`."""

from mcp_monumenten.server import MonumentenMCP

mcp = MonumentenMCP(name="Monumenten MCP")

if __name__ == "__main__":
    mcp.run()
