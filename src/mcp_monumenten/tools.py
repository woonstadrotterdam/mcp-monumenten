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
from .locatieserver import (
    address_variants,
    lookup_provincie,
    nevenadres_docs,
    search_addresses,
)
from .models import MonumentalStatus, VerblijfsobjectLookup, VerblijfsobjectMatch

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
_MAX_VARIANTS_IN_ERROR = 20

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
        # MapServer reports filter errors as an XML ExceptionReport with HTTP 200,
        # which fails to parse here and becomes a ToolError in the caller.
        payload: dict[str, Any] = await response.json(content_type=None)
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

    normalized_postal_code = None
    if postal_code:
        normalized_postal_code = _normalize_postal_code(postal_code)
        fes_filter = build_postal_code_filter(
            normalized_postal_code, house_number, house_letter, house_suffix
        )
        not_found = (
            "No verblijfsobject found for postal code "
            f"{normalized_postal_code}, house number {house_number}."
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
            f"No verblijfsobject found for address: {street} {house_number}, {city}."
        )
    else:
        raise ToolError(
            "Provide either (postal_code + house_number) OR "
            "(street + house_number + city)."
        )

    try:
        matches = matches_from_payload(await _get_bag_wfs(fes_filter))
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"Error querying PDOK BAG WFS: {exc}") from exc

    if matches:
        return VerblijfsobjectLookup(matches=matches)

    # The WFS only has hoofdadressen. The Locatieserver also has nevenadressen,
    # and tells which huisletter and toevoeging variants exist.
    docs = await search_addresses(
        house_number=house_number,
        postal_code=normalized_postal_code,
        street=None if normalized_postal_code else street,
        city=None if normalized_postal_code else city,
    )
    nevenadressen = nevenadres_docs(docs, house_letter, house_suffix)
    if nevenadressen:
        return VerblijfsobjectLookup(
            matches=[_nevenadres_match(doc) for doc in nevenadressen]
        )
    raise ToolError(_not_found_message(not_found, docs, normalized_postal_code))


def _nevenadres_match(doc: dict[str, Any]) -> VerblijfsobjectMatch:
    """Build a match from a Locatieserver nevenadres document."""

    def text(key: str) -> str | None:
        value = doc.get(key)
        return None if value is None or value == "" else str(value)

    return VerblijfsobjectMatch(
        bag_verblijfsobject_id=str(doc["adresseerbaarobject_id"]),
        postcode=text("postcode"),
        huisnummer=text("huisnummer"),
        huisletter=text("huisletter"),
        huisnummertoevoeging=text("huisnummertoevoeging"),
        straatnaam=text("straatnaam"),
        plaatsnaam=text("woonplaatsnaam"),
        nevenadres=True,
    )


def _not_found_message(
    not_found: str, docs: list[dict[str, Any]], postal_code: str | None
) -> str:
    """Add the existing huisletter and toevoeging variants to a not-found error."""
    variants = address_variants(docs)
    if not variants:
        if postal_code is None:
            return f"{not_found} Postal code + house number usually works better."
        return not_found
    shown = ", ".join(variants[:_MAX_VARIANTS_IN_ERROR])
    if len(variants) > _MAX_VARIANTS_IN_ERROR:
        # The Locatieserver returns at most 100 rows, so a count could be short.
        shown += " and more"
    return (
        f"{not_found} These addresses with this house number do exist: {shown}. "
        "Ask the user which one they mean, then pass its letter as house_letter "
        "and the part after the hyphen as house_suffix (30A-02: house_letter 'A', "
        "house_suffix '02')."
    )


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
