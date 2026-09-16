"""MCP server voor monumentale statussen in Nederland."""

from importlib.metadata import version

from .server import MonumentenMCP

__all__ = ["MonumentenMCP", "__version__"]
__version__ = version("mcp-monumenten")
