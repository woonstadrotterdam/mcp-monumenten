#!/usr/bin/env python3
"""
MCP Monumenten Server Entry Point

This allows the package to be run directly with:
uvx mcp-monumenten

or

python -m mcp_monumenten
"""
import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from mcp_monumenten.server import MonumentenMCP


def setup_logging(transport_mode: str = "stdio"):
    """Setup logging configuration based on transport mode."""
    # Configure logging to stderr to avoid interfering with stdio protocol
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()

    # In stdio mode, we must use stderr to avoid interfering with protocol
    # In HTTP mode, we can be more flexible
    if transport_mode == "stdio":
        handler = logging.StreamHandler(sys.stderr)
        # More minimal format for stdio mode
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:
        handler = logging.StreamHandler(sys.stdout)
        # More detailed format for HTTP mode
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO), handlers=[handler], force=True
    )

    return logging.getLogger(__name__)


def main():
    """Main entry point for the MCP Monumenten Server"""
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

    # Setup logging based on transport mode
    transport_mode = "http" if args.http else "stdio"
    logger = setup_logging(transport_mode)

    # Create the MCP server with appropriate transport settings
    # Only pass port if HTTP mode is enabled
    server_kwargs = {
        "name": args.name,
        "host": args.host,
        "stateless_http": args.stateless,
    }

    # Only add port if we're using HTTP transport
    if args.http:
        server_kwargs["port"] = args.port

    mcp = MonumentenMCP(**server_kwargs)

    # Log configuration info
    logger.info("Starting MCP Monumenten Server")
    logger.info(f"Name: {args.name}")
    logger.info(f"Transport: {'HTTP' if args.http else 'stdio'}")
    if args.http:
        logger.info(f"Host: {args.host}:{args.port}")
        logger.info(f"Stateless: {args.stateless}")

    # Run the server
    try:
        mcp.run(transport="streamable-http" if args.http else "stdio")
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        # Clean up the server resources
        if hasattr(mcp, "close"):
            asyncio.run(mcp.close())


if __name__ == "__main__":
    main()