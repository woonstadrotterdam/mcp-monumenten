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
            "Provincial monument. false if provincie is known and is not "
            "Noord-Holland or Drenthe (those provinces do not designate them). "
            "null if provincie is Noord-Holland, Drenthe, or unknown: the list "
            "is not looked up. Mutually exclusive with rijksmonument and "
            "gemeentelijk_monument. If null, tell the user this was not checked, "
            "in the user's language."
        ),
    )
