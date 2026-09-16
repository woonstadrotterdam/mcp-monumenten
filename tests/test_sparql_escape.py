"""Unit tests for SPARQL escaping and query builders."""

import pytest

from mcp_monumenten.bag_queries import (
    build_address_query,
    build_postal_code_query,
    sparql_escape,
    sparql_integer,
    sparql_quoted,
)


def test_sparql_escape_quotes_and_backslashes() -> None:
    """Quotes and backslashes are escaped for SPARQL string literals."""
    assert sparql_escape(r'foo"bar\baz') == r'foo\"bar\\baz'


def test_sparql_quoted_wraps_escaped_value() -> None:
    """Quoted literals include surrounding double quotes."""
    assert sparql_quoted('Cool"singel') == '"Cool\\"singel"'


def test_sparql_integer_rejects_non_digits() -> None:
    """House numbers that are not digits cannot be interpolated as integers."""
    with pytest.raises(ValueError, match="house_number must be digits"):
        sparql_integer("30; DROP")


def test_postal_code_query_escapes_user_strings() -> None:
    """Postal-code queries quote untrusted strings and keep huisnummer numeric."""
    query = build_postal_code_query('3011"AD', "30", house_letter='A"B')
    assert 'bag:postcode "3011\\"AD"' in query
    assert "bag:huisnummer 30" in query
    assert 'bag:huisletter "A\\"B"' in query


def test_address_query_escapes_street_and_city() -> None:
    """Address queries quote street and city names."""
    query = build_address_query(r'Cool\singel', "12", 'Rotterdam"')
    assert 'bag:naam "Cool\\\\singel"' in query
    assert 'bag:naam "Rotterdam\\""' in query
    assert "bag:huisnummer 12" in query
