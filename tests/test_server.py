"""In-memory MCP Client tests for Monumenten tools."""

from typing import Any

import pytest
from mcp import Client

from mcp_monumenten.models import VerblijfsobjectLookup, VerblijfsobjectMatch
from mcp_monumenten.server import MonumentenMCP

COOLSINGEL_BINDING = {
    "identificatie": {"value": "0599010000243626"},
    "postcode": {"value": "3011AD"},
    "huisnummer": {"value": "30"},
    "straatnaam": {"value": "Coolsingel"},
    "plaatsnaam": {"value": "Rotterdam"},
}


async def _fake_sparql_single(_query: str) -> dict[str, Any]:
    return {"results": {"bindings": [COOLSINGEL_BINDING]}}


class _FakeMonumentenClient:
    async def __aenter__(self) -> "_FakeMonumentenClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def process_from_list(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        bag_id = ids[0]
        return {
            bag_id: {
                "rijksmonument": True,
                "rijksmonument_bron": ["RCE"],
                "rijksmonument_nummer": "12345",
                "rijksmonument_url": (
                    "https://monumentenregister.cultureelerfgoed.nl/monumenten/12345"
                ),
                "rijksbeschermd_gezicht": False,
                "rijksbeschermd_gezicht_naam": None,
                "gemeentelijk_monument": False,
                "grondslag_gemeentelijk_monument": None,
                "provinciaal_monument": False,
            }
        }


def _error_text(result: Any) -> str:
    return "".join(block.text for block in result.content)


async def _fake_zuid_holland(_bag_id: str) -> str:
    return "Zuid-Holland"


async def _fake_no_provincie(_bag_id: str) -> None:
    return None


@pytest.mark.asyncio
async def test_get_verblijfsobject_id_single_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A single BAG match returns structured matches and is not an error."""
    monkeypatch.setattr("mcp_monumenten.tools._post_sparql", _fake_sparql_single)
    async with Client(MonumentenMCP(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_verblijfsobject_id",
            {"house_number": "30", "postal_code": "3011AD"},
        )

    assert result.is_error is False
    assert result.structured_content is not None
    lookup = VerblijfsobjectLookup.model_validate(result.structured_content)
    assert lookup.matches == [
        VerblijfsobjectMatch(
            bag_verblijfsobject_id="0599010000243626",
            postcode="3011AD",
            huisnummer="30",
            straatnaam="Coolsingel",
            plaatsnaam="Rotterdam",
        )
    ]


@pytest.mark.asyncio
async def test_get_verblijfsobject_id_mixed_modes_is_error() -> None:
    """Postal code and street together is a tool error, not a successful string."""
    async with Client(MonumentenMCP(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_verblijfsobject_id",
            {
                "house_number": "30",
                "postal_code": "3011AD",
                "street": "Coolsingel",
                "city": "Rotterdam",
            },
        )

    assert result.is_error is True
    assert "not both" in _error_text(result)


@pytest.mark.asyncio
async def test_get_monumental_status_unwraps_bag_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monumental status is returned for the requested verblijfsobject."""
    monkeypatch.setattr(
        "mcp_monumenten.tools.MonumentenClient",
        lambda: _FakeMonumentenClient(),
    )
    monkeypatch.setattr("mcp_monumenten.tools.lookup_provincie", _fake_zuid_holland)
    async with Client(MonumentenMCP(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_monumental_status",
            {"bag_verblijfsobject_id": "0599010000243626"},
        )

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["bag_verblijfsobject_id"] == "0599010000243626"
    assert result.structured_content["rijksmonument"] is True
    assert result.structured_content["rijksmonument_bron"] == ["RCE"]
    assert result.structured_content["provincie"] == "Zuid-Holland"
    assert result.structured_content["provinciaal_monument"] is None
    assert "notitie" not in result.structured_content


@pytest.mark.asyncio
async def test_get_monumental_status_without_provincie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing provincie does not fail the monumental status lookup."""
    monkeypatch.setattr(
        "mcp_monumenten.tools.MonumentenClient",
        lambda: _FakeMonumentenClient(),
    )
    monkeypatch.setattr("mcp_monumenten.tools.lookup_provincie", _fake_no_provincie)
    async with Client(MonumentenMCP(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_monumental_status",
            {"bag_verblijfsobject_id": "0599010000243626"},
        )

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["rijksmonument"] is True
    assert result.structured_content["provincie"] is None
    assert result.structured_content["provinciaal_monument"] is None
    assert "notitie" not in result.structured_content


@pytest.mark.asyncio
async def test_get_verblijfsobject_id_no_matches_is_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty SPARQL results are tool errors so the model can retry."""

    async def empty(_query: str) -> dict[str, Any]:
        return {"results": {"bindings": []}}

    monkeypatch.setattr("mcp_monumenten.tools._post_sparql", empty)
    async with Client(MonumentenMCP(), raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_verblijfsobject_id",
            {"house_number": "30", "postal_code": "3011AD"},
        )

    assert result.is_error is True
    assert "No verblijfsobject found" in _error_text(result)
