"""Monumenten MCP server."""

from importlib.metadata import version

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .tools import get_monumental_status, get_verblijfsobject_id

_READ_ONLY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
)

_INSTRUCTIONS = (
    "Look up Dutch BAG verblijfsobject IDs, then monumental status. "
    "Prefer postal_code + house_number. For a rijksmonument, always cite the source "
    "(RCE = Rijksdienst voor het Cultureel Erfgoed)."
)


def _register_tools(mcp: MCPServer) -> None:
    """Register BAG and monumenten tools on the server."""
    mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)(get_verblijfsobject_id)
    mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)(get_monumental_status)


class MonumentenMCP(MCPServer):
    """MCP server for Dutch monumental status lookups."""

    def __init__(self, name: str = "Monumenten MCP") -> None:
        super().__init__(
            name,
            version=version("mcp-monumenten"),
            instructions=_INSTRUCTIONS,
        )
        _register_tools(self)
