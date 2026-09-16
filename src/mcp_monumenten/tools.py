"""MCP tool implementations for BAG lookup and monumental status."""

import asyncio
from typing import Annotated, Any

import aiohttp
from mcp.server.mcpserver.exceptions import ToolError
from monumenten import MonumentenClient  # type: ignore[import-not-found]
from pydantic import Field

from .bag_queries import BAG_LV_ENDPOINT, build_address_query, build_postal_code_query
from .locatieserver import lookup_provincie
from .models import MonumentalStatus, VerblijfsobjectLookup, VerblijfsobjectMatch

_PROVINCIES_MET_PROVINCIAAL_MONUMENT = frozenset({"Noord-Holland", "Drenthe"})

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


def _binding_value(binding: dict[str, Any], key: str) -> str | None:
    """Read a SPARQL JSON binding value."""
    val = binding.get(key, {})
    if isinstance(val, dict):
        value = val.get("value")
        return str(value) if value is not None else None
    return None


async def _post_sparql(query: str) -> dict[str, Any]:
    """POST a SPARQL query to the BAG LV endpoint."""
    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with (
        aiohttp.ClientSession() as session,
        session.post(
            BAG_LV_ENDPOINT, headers=headers, data={"query": query}
        ) as response,
    ):
        if response.status != 200:
            raise ToolError(f"Error querying Kadaster endpoint: HTTP {response.status}")
        payload: dict[str, Any] = await response.json()
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
        sparql_query = build_postal_code_query(
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
        sparql_query = build_address_query(
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
        result = await _post_sparql(sparql_query)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"Error executing SPARQL query: {exc}") from exc

    bindings = result.get("results", {}).get("bindings", [])
    matches = [
        VerblijfsobjectMatch(
            bag_verblijfsobject_id=bag_id,
            postcode=_binding_value(binding, "postcode"),
            huisnummer=_binding_value(binding, "huisnummer"),
            huisletter=_binding_value(binding, "huisletter"),
            huisnummertoevoeging=_binding_value(binding, "huisnummertoevoeging"),
            straatnaam=_binding_value(binding, "straatnaam"),
            plaatsnaam=_binding_value(binding, "plaatsnaam"),
        )
        for binding in bindings
        if (bag_id := _binding_value(binding, "identificatie"))
    ]
    if not matches:
        raise ToolError(not_found)
    return VerblijfsobjectLookup(matches=matches)


def provinciaal_monument_for(provincie: str | None) -> bool | None:
    """False outside NH/Drenthe; null when the list exists or provincie is unknown."""
    if provincie is None or provincie in _PROVINCIES_MET_PROVINCIAAL_MONUMENT:
        return None
    return False


async def get_monumental_status(
    bag_verblijfsobject_id: BagVerblijfsobjectId,
) -> MonumentalStatus:
    """Get the monumental status of a verblijfsobject.

    Always mention the source for the Rijksmonument status if it is a
    Rijksmonument. (RCE = Rijksdienst voor het Cultureel Erfgoed.)
    Reply in the user's language. provinciaal_monument is false outside
    Noord-Holland and Drenthe; null there or when provincie is unknown.
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
        provinciaal_monument=provinciaal_monument_for(provincie),
    )
