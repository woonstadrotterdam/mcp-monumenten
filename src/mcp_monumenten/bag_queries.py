"""BAG LV SPARQL query builders."""

BAG_LV_ENDPOINT = "https://api.labs.kadaster.nl/datasets/bag/lv/services/baglv/sparql"


def sparql_escape(value: str) -> str:
    """Escape a value for use inside a SPARQL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def sparql_quoted(value: str) -> str:
    """Return a quoted, escaped SPARQL string literal."""
    return f'"{sparql_escape(value)}"'


def sparql_integer(value: str) -> str:
    """Return a SPARQL integer token from a digit string."""
    if not value.isdigit():
        raise ValueError(f"house_number must be digits, got {value!r}")
    return value


def _letter_suffix_clauses(
    house_letter: str | None,
    house_suffix: str | None,
) -> tuple[str, str, str, str]:
    """Build optional huisletter and huisnummertoevoeging SPARQL fragments."""
    letter_clause = (
        f"?nummeraanduiding bag:huisletter {sparql_quoted(house_letter)} ."
        if house_letter
        else ""
    )
    suffix_clause = (
        f"?nummeraanduiding bag:huisnummertoevoeging {sparql_quoted(house_suffix)} ."
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
        else (
            "FILTER NOT EXISTS { ?nummeraanduiding bag:huisnummertoevoeging ?_hs . "
            'FILTER(?_hs != "H") }'
        )
    )
    return letter_clause, suffix_clause, letter_filter, suffix_filter


def build_postal_code_query(
    postal_code: str,
    house_number: str,
    house_letter: str | None = None,
    house_suffix: str | None = None,
) -> str:
    """Build SPARQL query for postal code search."""
    huisnummer = sparql_integer(house_number)
    postcode = sparql_quoted(postal_code)
    letter_clause, suffix_clause, letter_filter, suffix_filter = _letter_suffix_clauses(
        house_letter, house_suffix
    )

    return f"""
PREFIX bag: <https://bag.basisregistraties.overheid.nl/def/bag#>
PREFIX nen3610: <http://modellen.geostandaarden.nl/def/nen3610#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?nummeraanduiding a bag:Nummeraanduiding ;
                    prov:specializationOf ?nummeraanduidingIri ;
                    bag:postcode {postcode} ;
                    bag:huisnummer {huisnummer} .

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
    house_letter: str | None = None,
    house_suffix: str | None = None,
) -> str:
    """Build SPARQL query for address search."""
    huisnummer = sparql_integer(house_number)
    straat = sparql_quoted(street)
    plaats = sparql_quoted(city)
    letter_clause, suffix_clause, letter_filter, suffix_filter = _letter_suffix_clauses(
        house_letter, house_suffix
    )

    return f"""
PREFIX bag: <https://bag.basisregistraties.overheid.nl/def/bag#>
PREFIX nen3610: <http://modellen.geostandaarden.nl/def/nen3610#>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?nummeraanduiding a bag:Nummeraanduiding ;
                    prov:specializationOf ?nummeraanduidingIri ;
                    bag:huisnummer {huisnummer} ;
                    bag:ligtAan ?openbareRuimteIri .

  ?openbareRuimte a bag:Openbareruimte ;
                  prov:specializationOf ?openbareRuimteIri ;
                  bag:naam {straat} ;
                  bag:ligtIn ?woonplaatsIri .

  ?woonplaats a bag:Woonplaats ;
              prov:specializationOf ?woonplaatsIri ;
              bag:naam {plaats} .

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
