"""Keep MCP Registry metadata aligned with the PyPI package."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_NAME = "io.github.woonstadrotterdam/monumenten"


def test_server_json_matches_package_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    server = json.loads((ROOT / "server.json").read_text())
    readme = (ROOT / "README.md").read_text()

    name = pyproject["project"]["name"]
    version = pyproject["project"]["version"]
    pypi = next(pkg for pkg in server["packages"] if pkg["registryType"] == "pypi")

    assert server["name"] == REGISTRY_NAME
    assert server["version"] == version
    assert len(server["description"]) <= 100
    assert pypi["identifier"] == name
    assert pypi["version"] == version
    assert pypi["runtimeHint"] == "uvx"
    assert pypi["transport"]["type"] == "stdio"
    assert f"mcp-name: {REGISTRY_NAME}" in readme

    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    cursor_plugin = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text())
    assert plugin["version"] == version
    assert marketplace["plugins"][0]["version"] == version
    assert cursor_plugin["version"] == version
    assert cursor_plugin["mcpServers"] == "./.mcp.json"


def test_agent_manifests_match_package_metadata() -> None:
    """Codex, Copilot CLI and Gemini CLI manifests stay in step with the package."""
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    claude_plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    claude_mcp = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]

    # Agent Plugins 1.0 (Codex and Copilot CLI): root plugin.json + mcp.json.
    plugin = json.loads((ROOT / "plugin.json").read_text())
    assert plugin["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert plugin["name"] == claude_plugin["name"]
    assert plugin["version"] == version
    assert plugin["description"] == claude_plugin["description"]

    portable_mcp = json.loads((ROOT / "mcp.json").read_text())
    assert portable_mcp["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    )
    assert portable_mcp["mcpServers"] == {
        name: {"type": "stdio", **server} for name, server in claude_mcp.items()
    }

    codex_marketplace = json.loads(
        (ROOT / ".agents/plugins/marketplace.json").read_text()
    )
    entry = codex_marketplace["plugins"][0]
    assert entry["name"] == plugin["name"]
    assert entry["source"] == {"source": "local", "path": "./"}
    assert {"installation", "authentication"} <= entry["policy"].keys()
    assert entry["category"]

    gemini = json.loads((ROOT / "gemini-extension.json").read_text())
    assert gemini["name"] == plugin["name"]
    assert gemini["version"] == version
    assert gemini["description"] == claude_plugin["description"]
    assert gemini["mcpServers"] == claude_mcp
