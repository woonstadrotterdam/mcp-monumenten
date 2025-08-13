from mcp_monumenten.server import MonumentenMCP

mcp = MonumentenMCP(name="Monumenten MCP", stateless_http=True)

if __name__ == "__main__":
    mcp.run()