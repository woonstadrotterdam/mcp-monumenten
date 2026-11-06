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


_NULL_IS_UNDETERMINED = (
    "null means the status could not be determined because a source did not "
    "answer; tell the user it was not determined, in the user's language. "
    "Do not report it as false."
)


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
    rijksmonument: bool | None = Field(
        default=None,
        description=f"National monument (rijksmonument). {_NULL_IS_UNDETERMINED}",
    )
    rijksmonument_bron: list[str] | None = None
    rijksmonument_nummer: str | None = None
    rijksmonument_url: str | None = None
    rijksmonument_voorbescherming: bool | None = Field(
        default=None,
        description=(
            "Voorbescherming of a rijksmonument (Kadaster grondslagcode EWD): the "
            "draft designation has been sent, but the monument is not yet in the "
            "rijksmonumentenregister. This is not a rijksmonument and does not "
            f"count as one for woningwaardering. {_NULL_IS_UNDETERMINED}"
        ),
    )
    rijksbeschermd_gezicht: bool | None = Field(
        default=None,
        description=(
            "Nationally protected town or village scape "
            "(rijksbeschermd stads- of dorpsgezicht). "
            "false does not mean the address is outside a municipal or provincial "
            "beschermd stadsgezicht; those are not looked up. "
            f"{_NULL_IS_UNDETERMINED}"
        ),
    )
    rijksbeschermd_gezicht_naam: str | None = None
    gemeentelijk_monument: bool | None = Field(
        default=None,
        description=(
            "Municipal monument (gemeentelijk monument). Includes municipal "
            "monuments under voorbescherming: the Kadaster does not distinguish "
            f"them. {_NULL_IS_UNDETERMINED}"
        ),
    )
    grondslag_gemeentelijk_monument: str | None = None
    provinciaal_monument: bool | None = Field(
        default=None,
        description=(
            "Provincial monument. Only Noord-Holland and Drenthe designate them; "
            "elsewhere this is false. Looked up in the provincial map services. "
            "null means the service of the province could not be reached; tell "
            "the user it was not determined, in the user's language. "
            "Do not report it as false."
        ),
    )
    provinciaal_monument_omschrijving: str | None = Field(
        default=None,
        description=(
            "Description of the provincial monument: number and name in Drenthe, "
            "only the category in Noord-Holland."
        ),
    )
