# Monumenten

Heritage statuses of an address that matter for woningwaardering: rijksmonument, provinciaal monument, gemeentelijk monument, and rijksbeschermd stads- of dorpsgezicht.

## Language

**Provincie**:
The current Dutch province in which the verblijfsobject lies.
_Avoid_: BAG-ID prefix, historical gemeente-at-creation, province inferred from woonplaats name

**Provinciaal monument**:
A provincial heritage designation that currently exists only in Noord-Holland and Drenthe. Mutually exclusive with rijksmonument and gemeentelijk monument. Relevant for woningwaardering. Outside those provinces the value is false. In Noord-Holland and Drenthe it is not looked up (`null`).
_Avoid_: Treating an unchecked Noord-Holland or Drenthe list as “not a provincial monument”

**Rijksmonument**:
A national heritage designation. Mutually exclusive with provinciaal monument and gemeentelijk monument.

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
