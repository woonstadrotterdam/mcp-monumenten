"""Tests for the PDOK BAG WFS address lookup."""

import xml.etree.ElementTree as ET

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_monumenten.bag_wfs import build_address_filter
from mcp_monumenten.models import VerblijfsobjectMatch
from mcp_monumenten.tools import get_verblijfsobject_id

FES = "{http://www.opengis.net/fes/2.0}"

# Coolsingel 30, 3011 AD Rotterdam
COOLSINGEL_ID = "0599010000243626"


def test_filter_escapes_xml_in_user_strings() -> None:
    """User strings cannot break out of the FES literal."""
    street = "Cool</fes:Literal>&singel\"'"
    city = "<Rotterdam>"
    fes_filter = build_address_filter(
        street, "12", city, house_letter="<A>", house_suffix="&"
    )
    literals = {
        clause.findtext(f"{FES}ValueReference"): clause.findtext(f"{FES}Literal")
        for clause in ET.fromstring(fes_filter).iter(f"{FES}PropertyIsEqualTo")
    }
    assert literals == {
        "openbare_ruimte": street,
        "huisnummer": "12",
        "woonplaats": city,
        "huisletter": "<A>",
        "toevoeging": "&",
    }


# Live lookups against PDOK.


def _ids(matches: list[VerblijfsobjectMatch]) -> list[str]:
    return [m.bag_verblijfsobject_id for m in matches]


@pytest.mark.asyncio
async def test_live_postal_code_coolsingel_30() -> None:
    lookup = await get_verblijfsobject_id("30", postal_code="3011 ad")
    assert lookup.matches == [
        VerblijfsobjectMatch(
            bag_verblijfsobject_id=COOLSINGEL_ID,
            postcode="3011AD",
            huisnummer="30",
            straatnaam="Coolsingel",
            plaatsnaam="Rotterdam",
        )
    ]


@pytest.mark.asyncio
async def test_live_address_coolsingel_30() -> None:
    lookup = await get_verblijfsobject_id("30", street="Coolsingel", city="Rotterdam")
    assert _ids(lookup.matches) == [COOLSINGEL_ID]


@pytest.mark.asyncio
async def test_live_letter_and_suffix() -> None:
    """Stadhuisplein 30A-02 matches only that verblijfsobject."""
    lookup = await get_verblijfsobject_id(
        "30", postal_code="3012AS", house_letter="A", house_suffix="02"
    )
    assert _ids(lookup.matches) == ["0599010400031067"]
    assert lookup.matches[0].huisletter == "A"
    assert lookup.matches[0].huisnummertoevoeging == "02"


@pytest.mark.asyncio
async def test_live_suffix_without_letter() -> None:
    """Kortekade 30-02 matches by suffix alone."""
    lookup = await get_verblijfsobject_id("30", postal_code="3062GS", house_suffix="02")
    assert _ids(lookup.matches) == ["0599010000160810"]
    assert lookup.matches[0].huisletter is None


@pytest.mark.asyncio
async def test_live_without_suffix_includes_h() -> None:
    """Eerste Atjehstraat 35 is only registered as 35-H, which counts as no suffix."""
    lookup = await get_verblijfsobject_id("35", postal_code="1094KA")
    assert _ids(lookup.matches) == ["0363010000543453"]
    assert lookup.matches[0].huisnummertoevoeging == "H"


@pytest.mark.asyncio
async def test_live_without_letter_lists_existing_variants() -> None:
    """2e Middellandstraat 1 only has 1A-01, 1A-02 and 1B, so plain 1 is missing.

    The error names those variants so the model can ask or retry.
    """
    with pytest.raises(ToolError, match="No verblijfsobject found") as excinfo:
        await get_verblijfsobject_id("1", postal_code="3021BK")
    message = str(excinfo.value)
    assert "1A-01" in message
    assert "1A-02" in message
    assert "1B" in message


@pytest.mark.asyncio
async def test_live_nevenadres_by_postal_code() -> None:
    """Prinsengracht 263 is a nevenadres; the hoofdadres is Westermarkt 10."""
    lookup = await get_verblijfsobject_id("263", postal_code="1016GV")
    assert lookup.matches == [
        VerblijfsobjectMatch(
            bag_verblijfsobject_id="0363010012149124",
            postcode="1016GV",
            huisnummer="263",
            straatnaam="Prinsengracht",
            plaatsnaam="Amsterdam",
            nevenadres=True,
        )
    ]


@pytest.mark.asyncio
async def test_live_nevenadres_by_address() -> None:
    lookup = await get_verblijfsobject_id(
        "263", street="Prinsengracht", city="Amsterdam"
    )
    assert _ids(lookup.matches) == ["0363010012149124"]
    assert lookup.matches[0].nevenadres is True


@pytest.mark.asyncio
async def test_live_ligplaats_is_not_returned() -> None:
    """Aelbrechtskade 1, 3022HK is a ligplaats, not a verblijfsobject."""
    with pytest.raises(ToolError, match="No verblijfsobject found"):
        await get_verblijfsobject_id("1", postal_code="3022HK")
