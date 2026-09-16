"""Pydantic models for Monumenten MCP tool results."""

from pydantic import BaseModel, ConfigDict


class VerblijfsobjectMatch(BaseModel):
    """A BAG verblijfsobject that matched an address search."""

    bag_verblijfsobject_id: str
    postcode: str | None = None
    huisnummer: str | None = None
    huisletter: str | None = None
    huisnummertoevoeging: str | None = None
    straatnaam: str | None = None
    plaatsnaam: str | None = None


class VerblijfsobjectLookup(BaseModel):
    """Address lookup result from BAG LV."""

    matches: list[VerblijfsobjectMatch]


class MonumentalStatus(BaseModel):
    """Monumental status for one verblijfsobject."""

    model_config = ConfigDict(extra="allow")

    bag_verblijfsobject_id: str
    rijksmonument: bool | None = None
    rijksmonument_bron: list[str] | None = None
    rijksmonument_nummer: str | None = None
    rijksmonument_url: str | None = None
    rijksbeschermd_gezicht: bool | None = None
    rijksbeschermd_gezicht_naam: str | None = None
    gemeentelijk_monument: bool | None = None
    grondslag_gemeentelijk_monument: str | None = None
