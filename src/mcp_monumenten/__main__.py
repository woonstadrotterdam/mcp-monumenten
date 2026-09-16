#!/usr/bin/env python3
"""MCP Monumenten Server entry point.

This allows the package to be run directly with:
uvx mcp-monumenten

or

python -m mcp_monumenten
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv  # type: ignore[import-not-found]

from mcp_monumenten.server import MonumentenMCP


def setup_logging(transport_mode: str = "stdio") -> logging.Logger:
    """Configure logging; stdio logs go to stderr so they cannot corrupt the wire."""
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()

    if transport_mode == "stdio":
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO), handlers=[handler], force=True
    )
    return logging.getLogger(__name__)


def main() -> None:
    """Run the MCP Monumenten server."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="MCP Monumenten Server")
    parser.add_argument(
        "--name", default="Monumenten MCP", help="Name for the MCP server"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run server with streamable HTTP transport instead of stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP server port (default: 8000, only used with --http)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP server host (default: 127.0.0.1, only used with --http)",
    )
    parser.add_argument(
        "--stateless",
        action="store_true",
        help="Run HTTP server in stateless mode (only used with --http)",
    )

    args = parser.parse_args()
    transport_mode = "http" if args.http else "stdio"

    mcp = MonumentenMCP(name=args.name)
    logger = setup_logging(transport_mode)

    logger.info("Starting MCP Monumenten Server")
    logger.info(f"Name: {args.name}")
    logger.info(f"Transport: {'HTTP' if args.http else 'stdio'}")
    if args.http:
        logger.info(f"Host: {args.host}:{args.port}")
        logger.info(f"Stateless: {args.stateless}")
        logger.info("MCP endpoint: /mcp")

    try:
        if args.http:
            mcp.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                stateless_http=args.stateless,
            )
        else:
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Shutting down server...")


if __name__ == "__main__":
    main()
