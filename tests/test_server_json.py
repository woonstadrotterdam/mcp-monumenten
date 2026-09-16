"""Keep MCP Registry metadata aligned with the PyPI package."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_NAME = "io.github.woonstadrotterdam/mcp-monumenten"


def test_server_json_matches_package_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    server = json.loads((ROOT / "server.json").read_text())
    readme = (ROOT / "README.md").read_text()

    name = pyproject["project"]["name"]
    version = pyproject["project"]["version"]
    pypi = next(pkg for pkg in server["packages"] if pkg["registryType"] == "pypi")

    assert server["name"] == REGISTRY_NAME
    assert server["version"] == version
    assert pypi["identifier"] == name
    assert pypi["version"] == version
    assert pypi["runtimeHint"] == "uvx"
    assert pypi["transport"]["type"] == "stdio"
    assert f"mcp-name: {REGISTRY_NAME}" in readme
