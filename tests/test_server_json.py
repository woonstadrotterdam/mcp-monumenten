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


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_agent_manifests_stay_in_step() -> None:
    """A version bump or copy edit must reach every client's manifest."""
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    reference = _load(".claude-plugin/plugin.json")
    for path in ("plugin.json", ".cursor-plugin/plugin.json", "gemini-extension.json"):
        manifest = _load(path)
        assert manifest["version"] == version, path
        for field in ("name", "description", "keywords"):
            assert manifest.get(field, reference[field]) == reference[field], (
                path,
                field,
            )


def test_mcp_configs_start_the_same_server() -> None:
    """Agent Plugins' mcp.json and Gemini repeat .mcp.json; keep them identical."""
    servers = _load(".mcp.json")["mcpServers"]
    assert _load("gemini-extension.json")["mcpServers"] == servers
    assert _load("mcp.json")["mcpServers"] == {
        name: {"type": "stdio", **server} for name, server in servers.items()
    }
