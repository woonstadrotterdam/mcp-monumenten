"""Pydantic models for Monumenten MCP tool results."""

from pydantic import BaseModel, ConfigDict, Field


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
    provincie: str | None = Field(
        default=None,
        description=(
            "Current Dutch province of the verblijfsobject. "
            "Null if the provincie lookup failed."
        ),
    )
    rijksmonument: bool | None = None
    rijksmonument_bron: list[str] | None = None
    rijksmonument_nummer: str | None = None
    rijksmonument_url: str | None = None
    rijksbeschermd_gezicht: bool | None = Field(
        default=None,
        description=(
            "Nationally protected town or village scape "
            "(rijksbeschermd stads- of dorpsgezicht). "
            "false does not mean the address is outside a municipal or provincial "
            "beschermd stadsgezicht; those are not looked up."
        ),
    )
    rijksbeschermd_gezicht_naam: str | None = None
    gemeentelijk_monument: bool | None = None
    grondslag_gemeentelijk_monument: str | None = None
    provinciaal_monument: bool | None = Field(
        default=None,
        description=(
            "Provincial monument. Always null: this status is not looked up. "
            "It only exists in Noord-Holland and Drenthe, and is mutually exclusive "
            "with rijksmonument and gemeentelijk_monument. If provincie is one of "
            "those or unknown, and the other monument flags are not true, tell the "
            "user this was not checked, in the user's language. "
            "Do not report it as false."
        ),
    )
