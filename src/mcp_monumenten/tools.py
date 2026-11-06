"""MCP tool implementations for BAG lookup and monumental status."""

import asyncio
from typing import Annotated, Any

import aiohttp
from mcp.server.mcpserver.exceptions import ToolError
from monumenten import MonumentenClient  # type: ignore[import-not-found]
from pydantic import Field

from .bag_wfs import (
    BAG_WFS_URL,
    build_address_filter,
    build_get_feature_params,
    build_postal_code_filter,
    matches_from_payload,
)
from .locatieserver import lookup_provincie
from .models import MonumentalStatus, VerblijfsobjectLookup

HouseNumber = Annotated[
    str,
    Field(description="The house number, e.g. '30'", pattern=r"^[1-9]\d{0,4}$"),
]
PostalCode = Annotated[
    str | None,
    Field(
        description="Dutch postal code for search mode 1, e.g. '1234AB'",
        pattern=r"^[1-9]\d{3}\s?[A-Za-z]{2}$",
    ),
]
StreetName = Annotated[
    str | None, Field(description="Street name for search mode 2, e.g. 'Coolsingel'")
]
CityName = Annotated[
    str | None, Field(description="City name for search mode 2, e.g. 'Rotterdam'")
]
HouseLetter = Annotated[
    str | None, Field(description="House letter, e.g. 'A' in '30A'")
]
HouseSuffix = Annotated[
    str | None,
    Field(description="House number suffix/addition, e.g. '2' in '30-2'"),
]
_TIMEOUT = aiohttp.ClientTimeout(total=15)

BagVerblijfsobjectId = Annotated[
    str,
    Field(
        description="The verblijfsobject ID (16 digits)",
        pattern=r"^\d{16}$",
    ),
]


def _normalize_postal_code(postal_code: str) -> str:
    """Normalize a Dutch postal code to uppercase without spaces."""
    return postal_code.replace(" ", "").upper()


async def _get_bag_wfs(fes_filter: str) -> dict[str, Any]:
    """Run a GetFeature request on the PDOK BAG WFS and return the GeoJSON."""
    async with (
        aiohttp.ClientSession(timeout=_TIMEOUT) as session,
        session.get(
            BAG_WFS_URL, params=build_get_feature_params(fes_filter)
        ) as response,
    ):
        if response.status != 200:
            raise ToolError(f"Error querying PDOK BAG WFS: HTTP {response.status}")
        # MapServer reports filter errors as an XML ExceptionReport with HTTP 200.
        payload = await response.json(content_type=None)
    if not isinstance(payload, dict):
        raise ToolError("Error querying PDOK BAG WFS: unexpected response")
    return payload


async def get_verblijfsobject_id(
    house_number: HouseNumber,
    postal_code: PostalCode = None,
    street: StreetName = None,
    city: CityName = None,
    house_letter: HouseLetter = None,
    house_suffix: HouseSuffix = None,
) -> VerblijfsobjectLookup:
    """Get verblijfsobject ID using address.

    Use postal_code + house_number OR street + house_number + city.
    Additional filters like house_letter and house_suffix can be provided
    for more precise matching.
    """
    if postal_code and (street or city):
        raise ToolError("Provide either postal_code OR (street + city), not both.")

    if postal_code:
        normalized_postal_code = _normalize_postal_code(postal_code)
        fes_filter = build_postal_code_filter(
            normalized_postal_code, house_number, house_letter, house_suffix
        )
        not_found = (
            "No verblijfsobject found for postal code "
            f"{normalized_postal_code}, house number {house_number}"
        )
    elif street and city:
        if not street.strip() or not city.strip():
            raise ToolError(
                "street and city cannot be empty when using address search."
            )
        fes_filter = build_address_filter(
            street, house_number, city, house_letter, house_suffix
        )
        not_found = (
            f"No verblijfsobject found for address: {street} {house_number}, {city}. "
            "Postal code + house number usually works better."
        )
    else:
        raise ToolError(
            "Provide either (postal_code + house_number) OR "
            "(street + house_number + city)."
        )

    try:
        payload = await _get_bag_wfs(fes_filter)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"Error querying PDOK BAG WFS: {exc}") from exc

    matches = matches_from_payload(payload)
    if not matches:
        raise ToolError(not_found)
    return VerblijfsobjectLookup(matches=matches)


async def get_monumental_status(
    bag_verblijfsobject_id: BagVerblijfsobjectId,
) -> MonumentalStatus:
    """Get the monumental status of a verblijfsobject.

    Always mention the source for the Rijksmonument status if it is a
    Rijksmonument. (RCE = Rijksdienst voor het Cultureel Erfgoed.)
    Reply in the user's language. provinciaal_monument is not looked up.
    """
    try:
        async with MonumentenClient() as client:
            result, provincie = await asyncio.gather(
                client.process_from_list([bag_verblijfsobject_id]),
                lookup_provincie(bag_verblijfsobject_id),
            )
    except Exception as exc:
        raise ToolError(f"Error fetching monumental status: {exc}") from exc

    status = result.get(bag_verblijfsobject_id)
    if not isinstance(status, dict):
        raise ToolError(
            f"No monumental status found for verblijfsobject {bag_verblijfsobject_id}"
        )
    status = dict(status)
    status.pop("provincie", None)
    status.pop("provinciaal_monument", None)
    return MonumentalStatus(
        bag_verblijfsobject_id=bag_verblijfsobject_id,
        **status,
        provincie=provincie,
        provinciaal_monument=None,
    )
