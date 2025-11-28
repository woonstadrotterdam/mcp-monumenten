"""BAG LV SPARQL query builders."""

from typing import Optional

# BAG LV endpoint
BAG_LV_ENDPOINT = "https://api.labs.kadaster.nl/datasets/bag/lv/services/baglv/sparql"


def build_postal_code_query(
    postal_code: str,
    house_number: str,
    house_letter: Optional[str] = None,
    house_suffix: Optional[str] = None,
) -> str:
    """Build SPARQL query for postal code search."""
    letter_clause = (
        f'?nummeraanduiding bag:huisletter "{house_letter}" .' if house_letter else ""
    )
    suffix_clause = (
        f'?nummeraanduiding bag:huisnummertoevoeging "{house_suffix}" .'
        if house_suffix
        else ""
    )
    letter_filter = (
        ""
        if house_letter
        else "FILTER NOT EXISTS { ?nummeraanduiding bag:huisletter ?_hl . }"
    )
    suffix_filter = (
        ""
        if house_suffix
        else 'FILTER NOT EXISTS { ?nummeraanduiding bag:huisnummertoevoeging ?_hs . FILTER(?_hs != "H") }'
    )

    return f"""
PREFIX bag: <https://bag.basisregistraties.overheid.nl/def/bag#>
PREFIX nen3610: <http://modellen.geostandaarden.nl/def/nen3610#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?nummeraanduiding a bag:Nummeraanduiding ;
                    prov:specializationOf ?nummeraanduidingIri ;
                    bag:postcode "{postal_code}" ;
                    bag:huisnummer {house_number} .

  ?verblijfsobject a bag:Verblijfsobject ;
                   bag:heeftAlsHoofdadres ?nummeraanduidingIri ;
                   nen3610:identificatie ?identificatie .

  {letter_clause}
  {suffix_clause}

  {letter_filter}
  {suffix_filter}

  OPTIONAL {{ ?nummeraanduiding bag:postcode ?postcode . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisnummer ?huisnummer . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisletter ?huisletter . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisnummertoevoeging ?huisnummertoevoeging . }}

  OPTIONAL {{
    ?nummeraanduiding bag:ligtAan ?openbareRuimteIri .
    ?openbareRuimte prov:specializationOf ?openbareRuimteIri ;
                    bag:naam ?straatnaam .
    OPTIONAL {{
      ?openbareRuimte bag:ligtIn ?woonplaatsIri .
      ?woonplaats prov:specializationOf ?woonplaatsIri ;
                  bag:naam ?plaatsnaam .
    }}
  }}
}}
""".strip()


def build_address_query(
    street: str,
    house_number: str,
    city: str,
    house_letter: Optional[str] = None,
    house_suffix: Optional[str] = None,
) -> str:
    """Build SPARQL query for address search."""
    letter_clause = (
        f'?nummeraanduiding bag:huisletter "{house_letter}" .' if house_letter else ""
    )
    suffix_clause = (
        f'?nummeraanduiding bag:huisnummertoevoeging "{house_suffix}" .'
        if house_suffix
        else ""
    )
    letter_filter = (
        ""
        if house_letter
        else "FILTER NOT EXISTS { ?nummeraanduiding bag:huisletter ?_hl . }"
    )
    suffix_filter = (
        ""
        if house_suffix
        else 'FILTER NOT EXISTS { ?nummeraanduiding bag:huisnummertoevoeging ?_hs . FILTER(?_hs != "H") }'
    )

    return f"""
PREFIX bag: <https://bag.basisregistraties.overheid.nl/def/bag#>
PREFIX nen3610: <http://modellen.geostandaarden.nl/def/nen3610#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?nummeraanduiding a bag:Nummeraanduiding ;
                    prov:specializationOf ?nummeraanduidingIri ;
                    bag:huisnummer {house_number} ;
                    bag:ligtAan ?openbareRuimteIri .

  ?openbareRuimte a bag:Openbareruimte ;
                  prov:specializationOf ?openbareRuimteIri ;
                  bag:naam "{street}" ;
                  bag:ligtIn ?woonplaatsIri .

  ?woonplaats a bag:Woonplaats ;
              prov:specializationOf ?woonplaatsIri ;
              bag:naam "{city}" .

  ?verblijfsobject a bag:Verblijfsobject ;
                   bag:heeftAlsHoofdadres ?nummeraanduidingIri ;
                   nen3610:identificatie ?identificatie .

  {letter_clause}
  {suffix_clause}

  {letter_filter}
  {suffix_filter}

  OPTIONAL {{ ?nummeraanduiding bag:postcode ?postcode . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisnummer ?huisnummer . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisletter ?huisletter . }}
  OPTIONAL {{ ?nummeraanduiding bag:huisnummertoevoeging ?huisnummertoevoeging . }}
  OPTIONAL {{ ?openbareRuimte bag:naam ?straatnaam . }}
  OPTIONAL {{ ?woonplaats bag:naam ?plaatsnaam . }}
}}
""".strip()
