"""PDOK Locatieserver lookups.

Used for the current provincie of a verblijfsobject, and as a fallback when the
BAG WFS has no hoofdadres for an address: for nevenadressen, and for the
huisletter and toevoeging variants that do exist.
"""

import re
from typing import Any

import aiohttp

LOCATIESERVER_FREE_URL = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
_TIMEOUT = aiohttp.ClientTimeout(total=5)


def provincienaam_from_payload(payload: dict[str, Any]) -> str | None:
    """Read provincienaam from a Locatieserver free-search JSON body."""
    docs = payload.get("response", {}).get("docs", [])
    if not isinstance(docs, list) or not docs:
        return None
    first = docs[0]
    if not isinstance(first, dict):
        return None
    name = first.get("provincienaam")
    if isinstance(name, str) and name.strip():
        return name
    return None


async def lookup_provincie(bag_verblijfsobject_id: str) -> str | None:
    """Return the current provincie for a BAG verblijfsobject, or None."""
    params = [
        ("q", "*:*"),
        ("fq", "type:adres"),
        ("fq", f"adresseerbaarobject_id:{bag_verblijfsobject_id}"),
        ("fl", "provincienaam"),
        ("rows", "1"),
    ]
    try:
        async with (
            aiohttp.ClientSession(timeout=_TIMEOUT) as session,
            session.get(LOCATIESERVER_FREE_URL, params=params) as response,
        ):
            if response.status != 200:
                return None
            payload = await response.json()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return provincienaam_from_payload(payload)


# A BAG object ID has the object type in digits 5-6: 01 is a verblijfsobject,
# 02 a ligplaats and 03 a standplaats.
_VERBLIJFSOBJECT_TYPE = "01"
_MAX_ADDRESS_DOCS = 100


def _solr_phrase(value: str) -> str:
    """Quote a value as a Solr phrase."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _is_verblijfsobject(doc: dict[str, Any]) -> bool:
    object_id = doc.get("adresseerbaarobject_id")
    return isinstance(object_id, str) and object_id[4:6] == _VERBLIJFSOBJECT_TYPE


def _text(doc: dict[str, Any], key: str) -> str | None:
    value = doc.get(key)
    if value is None or value == "":
        return None
    return str(value)


async def search_addresses(
    *,
    house_number: str,
    postal_code: str | None = None,
    street: str | None = None,
    city: str | None = None,
) -> list[dict[str, Any]]:
    """Return the hoofd- and nevenadressen of verblijfsobjecten for a house number.

    Matches postal code or street + city loosely (the Locatieserver tokenizes
    them); callers match exactly. Returns an empty list if the lookup fails.
    """
    params = [
        ("q", "*:*"),
        ("fq", "type:adres"),
        ("fq", f"huisnummer:{house_number}"),
        (
            "fl",
            "adresseerbaarobject_id,adrestype,postcode,huisnummer,huisletter,"
            "huisnummertoevoeging,straatnaam,woonplaatsnaam",
        ),
        ("rows", str(_MAX_ADDRESS_DOCS)),
    ]
    if postal_code:
        params.append(("fq", f"postcode:{_solr_phrase(postal_code)}"))
    else:
        params.append(("fq", f"straatnaam:{_solr_phrase(street or '')}"))
        params.append(("fq", f"woonplaatsnaam:{_solr_phrase(city or '')}"))
    try:
        async with (
            aiohttp.ClientSession(timeout=_TIMEOUT) as session,
            session.get(LOCATIESERVER_FREE_URL, params=params) as response,
        ):
            if response.status != 200:
                return []
            payload = await response.json()
        docs = payload["response"]["docs"]
    except Exception:
        return []
    return [
        doc
        for doc in docs
        if isinstance(doc, dict)
        and _is_verblijfsobject(doc)
        and _text(doc, "huisnummer") == house_number
        and (postal_code is None or doc.get("postcode") == postal_code)
        and (street is None or doc.get("straatnaam") == street)
        and (city is None or doc.get("woonplaatsnaam") == city)
    ]


def nevenadres_docs(
    docs: list[dict[str, Any]],
    house_letter: str | None,
    house_suffix: str | None,
) -> list[dict[str, Any]]:
    """Keep the nevenadressen that match the huisletter and toevoeging exactly.

    Same rules as the WFS filter: no house letter means none, no suffix means
    none or ``H``.
    """
    matches = []
    for doc in docs:
        if doc.get("adrestype") != "nevenadres":
            continue
        letter = _text(doc, "huisletter")
        suffix = _text(doc, "huisnummertoevoeging")
        if letter != house_letter:
            continue
        if house_suffix is None and suffix not in (None, "H"):
            continue
        if house_suffix is not None and suffix != house_suffix:
            continue
        matches.append(doc)
    return matches


def _natural_key(label: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", label)]


def address_variants(docs: list[dict[str, Any]]) -> list[str]:
    """Return the distinct house numbers with letter and suffix, e.g. ``30A-02``."""
    labels = set()
    for doc in docs:
        label = f"{_text(doc, 'huisnummer')}{_text(doc, 'huisletter') or ''}"
        suffix = _text(doc, "huisnummertoevoeging")
        labels.add(f"{label}-{suffix}" if suffix else label)
    return sorted(labels, key=_natural_key)
