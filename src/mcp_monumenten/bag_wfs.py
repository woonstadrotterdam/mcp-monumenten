"""PDOK BAG WFS address lookup for verblijfsobjecten.

The ``bag:verblijfsobject`` layer has one feature per verblijfsobject with its
hoofdadres, so ligplaatsen, standplaatsen and nevenadressen never match.
"""

from html import escape
from typing import Any

from .models import VerblijfsobjectMatch

BAG_WFS_URL = "https://service.pdok.nl/kadaster/bag/wfs/v2_0"
TYPE_NAME = "bag:verblijfsobject"
MAX_FEATURES = 100
PROPERTY_NAMES = (
    "identificatie",
    "postcode",
    "huisnummer",
    "huisletter",
    "toevoeging",
    "openbare_ruimte",
    "woonplaats",
)

_FES_NS = "http://www.opengis.net/fes/2.0"


def _equal_to(name: str, value: str) -> str:
    """Return a case-sensitive FES equality clause with an escaped literal."""
    return (
        '<fes:PropertyIsEqualTo matchCase="true">'
        f"<fes:ValueReference>{name}</fes:ValueReference>"
        f"<fes:Literal>{escape(value)}</fes:Literal>"
        "</fes:PropertyIsEqualTo>"
    )


def _is_null(name: str) -> str:
    """Return a FES clause matching features without a value for ``name``."""
    return (
        f"<fes:PropertyIsNull><fes:ValueReference>{name}</fes:ValueReference>"
        "</fes:PropertyIsNull>"
    )


def _letter_suffix_clauses(
    house_letter: str | None,
    house_suffix: str | None,
) -> list[str]:
    """Build exact huisletter and toevoeging clauses.

    Without a house letter only addresses without one match. Without a suffix
    only addresses without one match, or with the suffix ``H`` (huis), which
    BAG uses for the ground-floor dwelling of the plain house number.
    """
    letter = (
        _equal_to("huisletter", house_letter)
        if house_letter
        else _is_null("huisletter")
    )
    suffix = (
        _equal_to("toevoeging", house_suffix)
        if house_suffix
        else f"<fes:Or>{_is_null('toevoeging')}{_equal_to('toevoeging', 'H')}</fes:Or>"
    )
    return [letter, suffix]


def _filter(clauses: list[str]) -> str:
    """Wrap clauses in a FES 2.0 filter with an ``And``."""
    return f'<fes:Filter xmlns:fes="{_FES_NS}"><fes:And>{"".join(clauses)}</fes:And></fes:Filter>'


def build_postal_code_filter(
    postal_code: str,
    house_number: str,
    house_letter: str | None = None,
    house_suffix: str | None = None,
) -> str:
    """Build a FES filter for postal code + house number search."""
    return _filter(
        [
            _equal_to("postcode", postal_code),
            _equal_to("huisnummer", house_number),
            *_letter_suffix_clauses(house_letter, house_suffix),
        ]
    )


def build_address_filter(
    street: str,
    house_number: str,
    city: str,
    house_letter: str | None = None,
    house_suffix: str | None = None,
) -> str:
    """Build a FES filter for street + house number + city search."""
    return _filter(
        [
            _equal_to("openbare_ruimte", street),
            _equal_to("huisnummer", house_number),
            _equal_to("woonplaats", city),
            *_letter_suffix_clauses(house_letter, house_suffix),
        ]
    )


def build_get_feature_params(fes_filter: str) -> dict[str, str]:
    """Build WFS 2.0 GetFeature query parameters for a FES filter."""
    return {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": TYPE_NAME,
        "outputFormat": "application/json",
        "propertyName": ",".join(PROPERTY_NAMES),
        "count": str(MAX_FEATURES),
        "filter": fes_filter,
    }


def _text(properties: dict[str, Any], key: str) -> str | None:
    """Read a feature property as text; empty values become None."""
    value = properties.get(key)
    if value is None or value == "":
        return None
    return str(value)


def matches_from_payload(payload: dict[str, Any]) -> list[VerblijfsobjectMatch]:
    """Parse a WFS GeoJSON FeatureCollection into verblijfsobject matches."""
    matches = []
    for feature in payload["features"]:
        properties = feature["properties"]
        matches.append(
            VerblijfsobjectMatch(
                bag_verblijfsobject_id=str(properties["identificatie"]),
                postcode=_text(properties, "postcode"),
                huisnummer=_text(properties, "huisnummer"),
                huisletter=_text(properties, "huisletter"),
                huisnummertoevoeging=_text(properties, "toevoeging"),
                straatnaam=_text(properties, "openbare_ruimte"),
                plaatsnaam=_text(properties, "woonplaats"),
            )
        )
    return matches
