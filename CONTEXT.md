# Monumenten

Heritage statuses of an address that matter for woningwaardering: rijksmonument, provinciaal monument, gemeentelijk monument, and rijksbeschermd stads- of dorpsgezicht.

## Language

**Provincie**:
The current Dutch province in which the verblijfsobject lies.
_Avoid_: BAG-ID prefix, historical gemeente-at-creation, province inferred from woonplaats name

**Provinciaal monument**:
A provincial heritage designation that currently exists only in Noord-Holland and Drenthe. Mutually exclusive with rijksmonument and gemeentelijk monument. Relevant for woningwaardering. Looked up in the map services of both provinces; null when a service could not be reached.
_Avoid_: Treating an unreachable provincial service as “not a provincial monument”

**Rijksmonument**:
A national heritage designation. Mutually exclusive with provinciaal monument and gemeentelijk monument.

**Voorbescherming (rijksmonument)**:
The draft designation of a rijksmonument has been sent, but the monument is not yet in the rijksmonumentenregister (Kadaster grondslagcode EWD). Not a rijksmonument, and not relevant for woningwaardering.
_Avoid_: Counting voorbescherming as rijksmonument

**Niet bepaald**:
A status that could not be determined because a source did not answer. Shown as null.
_Avoid_: Treating null as false

**Gemeentelijk monument**:
A municipal heritage designation. Mutually exclusive with rijksmonument and provinciaal monument.

**Rijksbeschermd stads- of dorpsgezicht**:
A nationally protected town or village scape. Relevant for woningwaardering. May overlap with a monument designation.
_Avoid_: beschermd stadsgezicht (ambiguous)

**Gemeentelijk beschermd stads- of dorpsgezicht**:
A municipally protected town or village scape (for example in Amsterdam). Not looked up; not relevant for woningwaardering.
_Avoid_: Treating rijksbeschermd gezicht as covering this

**UNESCO-werelderfgoed**:
A World Heritage listing. May overlap with a monument designation.
