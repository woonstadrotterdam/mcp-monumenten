"""PDOK Locatieserver lookup for the current provincie of a verblijfsobject."""

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
