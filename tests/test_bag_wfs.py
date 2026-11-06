"""Tests for the PDOK BAG WFS address lookup."""

import xml.etree.ElementTree as ET
from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_monumenten.bag_wfs import (
    BAG_WFS_URL,
    TYPE_NAME,
    build_address_filter,
    build_get_feature_params,
    build_postal_code_filter,
    matches_from_payload,
)
from mcp_monumenten.models import VerblijfsobjectMatch
from mcp_monumenten.tools import _get_bag_wfs, get_verblijfsobject_id

FES = "{http://www.opengis.net/fes/2.0}"

# Coolsingel 30, 3011 AD Rotterdam
COOLSINGEL_ID = "0599010000243626"


def _clauses(fes_filter: str) -> list[ET.Element]:
    """Return the clauses inside the filter's top-level And."""
    root = ET.fromstring(fes_filter)
    assert root.tag == f"{FES}Filter"
    (and_,) = list(root)
    assert and_.tag == f"{FES}And"
    return list(and_)


def _equals(clauses: list[ET.Element]) -> dict[str, str]:
    """Map property name to literal for the PropertyIsEqualTo clauses."""
    result = {}
    for clause in clauses:
        if clause.tag == f"{FES}PropertyIsEqualTo":
            assert clause.get("matchCase") == "true"
            name = clause.findtext(f"{FES}ValueReference")
            literal = clause.findtext(f"{FES}Literal")
            assert name is not None
            result[name] = literal or ""
    return result


def _nulls(clauses: list[ET.Element]) -> set[str]:
    """Return property names of the top-level PropertyIsNull clauses."""
    return {
        clause.findtext(f"{FES}ValueReference") or ""
        for clause in clauses
        if clause.tag == f"{FES}PropertyIsNull"
    }


def _suffix_or(clauses: list[ET.Element]) -> ET.Element | None:
    """Return the Or clause used for 'no suffix or H'."""
    return next((c for c in clauses if c.tag == f"{FES}Or"), None)


def test_postal_code_filter_without_letter_or_suffix() -> None:
    """No letter means no letter; no suffix means no suffix or H."""
    clauses = _clauses(build_postal_code_filter("3011AD", "30"))
    assert _equals(clauses) == {"postcode": "3011AD", "huisnummer": "30"}
    assert _nulls(clauses) == {"huisletter"}
    or_ = _suffix_or(clauses)
    assert or_ is not None
    assert [c.tag for c in or_] == [
        f"{FES}PropertyIsNull",
        f"{FES}PropertyIsEqualTo",
    ]
    assert or_[0].findtext(f"{FES}ValueReference") == "toevoeging"
    assert or_[1].findtext(f"{FES}ValueReference") == "toevoeging"
    assert or_[1].findtext(f"{FES}Literal") == "H"


def test_postal_code_filter_with_letter_and_suffix() -> None:
    """A given letter and suffix are matched exactly."""
    clauses = _clauses(
        build_postal_code_filter("3012AS", "30", house_letter="A", house_suffix="02")
    )
    assert _equals(clauses) == {
        "postcode": "3012AS",
        "huisnummer": "30",
        "huisletter": "A",
        "toevoeging": "02",
    }
    assert _nulls(clauses) == set()
    assert _suffix_or(clauses) is None


def test_postal_code_filter_with_suffix_only() -> None:
    """A suffix without a letter still requires no letter."""
    clauses = _clauses(build_postal_code_filter("3062GS", "30", house_suffix="02"))
    assert _equals(clauses)["toevoeging"] == "02"
    assert _nulls(clauses) == {"huisletter"}


def test_address_filter_matches_street_and_city() -> None:
    """Address search matches openbare_ruimte and woonplaats exactly."""
    clauses = _clauses(build_address_filter("Coolsingel", "30", "Rotterdam"))
    assert _equals(clauses) == {
        "openbare_ruimte": "Coolsingel",
        "huisnummer": "30",
        "woonplaats": "Rotterdam",
    }


def test_filter_escapes_xml_in_user_strings() -> None:
    """User strings cannot break out of the FES literal."""
    street = "Cool</fes:Literal>&singel\"'"
    city = "<Rotterdam>"
    clauses = _clauses(
        build_address_filter(street, "12", city, house_letter="<A>", house_suffix="&")
    )
    assert _equals(clauses) == {
        "openbare_ruimte": street,
        "huisnummer": "12",
        "woonplaats": city,
        "huisletter": "<A>",
        "toevoeging": "&",
    }


def test_filter_rejects_non_digit_house_number() -> None:
    """House numbers must be digits."""
    with pytest.raises(ValueError, match="house_number must be digits"):
        build_postal_code_filter("3011AD", "30<")


def test_get_feature_params() -> None:
    """GetFeature asks the verblijfsobject layer for GeoJSON."""
    params = build_get_feature_params("<filter/>")
    assert params["typeNames"] == TYPE_NAME == "bag:verblijfsobject"
    assert params["outputFormat"] == "application/json"
    assert params["filter"] == "<filter/>"
    assert params["propertyName"].split(",") == [
        "identificatie",
        "postcode",
        "huisnummer",
        "huisletter",
        "toevoeging",
        "openbare_ruimte",
        "woonplaats",
    ]


def test_matches_from_payload_maps_fields() -> None:
    """WFS properties map to the tool output; empty strings become None."""
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "identificatie": COOLSINGEL_ID,
                    "postcode": "3011AD",
                    "huisnummer": 30,
                    "huisletter": "",
                    "toevoeging": "",
                    "openbare_ruimte": "Coolsingel",
                    "woonplaats": "Rotterdam",
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "identificatie": "0599010400031067",
                    "postcode": "3012AS",
                    "huisnummer": 30,
                    "huisletter": "A",
                    "toevoeging": "02",
                    "openbare_ruimte": "Stadhuisplein",
                    "woonplaats": "Rotterdam",
                },
            },
        ],
    }
    assert matches_from_payload(payload) == [
        VerblijfsobjectMatch(
            bag_verblijfsobject_id=COOLSINGEL_ID,
            postcode="3011AD",
            huisnummer="30",
            straatnaam="Coolsingel",
            plaatsnaam="Rotterdam",
        ),
        VerblijfsobjectMatch(
            bag_verblijfsobject_id="0599010400031067",
            postcode="3012AS",
            huisnummer="30",
            huisletter="A",
            huisnummertoevoeging="02",
            straatnaam="Stadhuisplein",
            plaatsnaam="Rotterdam",
        ),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"features": None},
        {"features": ["x"]},
        {"features": [{"properties": None}]},
        {"features": [{"properties": {"identificatie": ""}}]},
    ],
)
def test_matches_from_payload_skips_malformed(payload: dict[str, Any]) -> None:
    assert matches_from_payload(payload) == []


class _FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = payload

    async def json(self, content_type: str | None = "application/json") -> object:
        return self._payload

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[tuple[str, object]] = []

    def get(self, url: str, params: object = None) -> _FakeResponse:
        self.calls.append((url, params))
        return self._response

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.mark.asyncio
async def test_get_bag_wfs_http_error_is_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(_FakeResponse(503, {}))
    monkeypatch.setattr(
        "mcp_monumenten.tools.aiohttp.ClientSession", lambda *a, **k: session
    )
    with pytest.raises(ToolError, match="HTTP 503"):
        await _get_bag_wfs("<filter/>")
    assert session.calls[0][0] == BAG_WFS_URL


@pytest.mark.asyncio
async def test_get_bag_wfs_non_object_is_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(_FakeResponse(200, ["not", "geojson"]))
    monkeypatch.setattr(
        "mcp_monumenten.tools.aiohttp.ClientSession", lambda *a, **k: session
    )
    with pytest.raises(ToolError, match="unexpected response"):
        await _get_bag_wfs("<filter/>")


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
async def test_live_without_letter_excludes_lettered_addresses() -> None:
    """2e Middellandstraat 1 only has 1A-01, 1A-02 and 1B, so plain 1 is missing."""
    with pytest.raises(ToolError, match="No verblijfsobject found"):
        await get_verblijfsobject_id("1", postal_code="3021BK")


@pytest.mark.asyncio
async def test_live_ligplaats_is_not_returned() -> None:
    """Aelbrechtskade 1, 3022HK is a ligplaats, not a verblijfsobject."""
    with pytest.raises(ToolError, match="No verblijfsobject found"):
        await get_verblijfsobject_id("1", postal_code="3022HK")
