"""Tests for BAG LV SPARQL queries."""

import aiohttp
import pytest

from mcp_monumenten.bag_queries import (
    BAG_LV_ENDPOINT,
    build_address_query,
    build_postal_code_query,
)

# Expected result for Coolsingel 30, 3011 AD, Rotterdam
EXPECTED_VERBLIJFSOBJECT_ID = "0599010000243626"


async def execute_sparql_query(query: str) -> dict:
    """Execute a SPARQL query against the BAG LV endpoint."""
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'query': query}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(BAG_LV_ENDPOINT, headers=headers, data=data) as response:
            assert response.status == 200, f"SPARQL query failed with status {response.status}"
            return await response.json()


@pytest.mark.asyncio
async def test_postal_code_search_coolsingel_30():
    """Test postal code search for Coolsingel 30, 3011AD returns correct verblijfsobject ID."""
    query = build_postal_code_query("3011AD", "30")
    result = await execute_sparql_query(query)
    
    bindings = result.get('results', {}).get('bindings', [])
    assert len(bindings) > 0, "No results returned for postal code search"
    
    ids = [b.get('identificatie', {}).get('value') for b in bindings if b.get('identificatie')]
    assert EXPECTED_VERBLIJFSOBJECT_ID in ids, f"Expected ID {EXPECTED_VERBLIJFSOBJECT_ID} not found in results: {ids}"


@pytest.mark.asyncio
async def test_address_search_coolsingel_30():
    """Test address search for Coolsingel 30, Rotterdam returns correct verblijfsobject ID."""
    query = build_address_query("Coolsingel", "30", "Rotterdam")
    result = await execute_sparql_query(query)
    
    bindings = result.get('results', {}).get('bindings', [])
    assert len(bindings) > 0, "No results returned for address search"
    
    ids = [b.get('identificatie', {}).get('value') for b in bindings if b.get('identificatie')]
    assert EXPECTED_VERBLIJFSOBJECT_ID in ids, f"Expected ID {EXPECTED_VERBLIJFSOBJECT_ID} not found in results: {ids}"


@pytest.mark.asyncio
async def test_postal_code_and_address_search_return_same_id():
    """Test that postal code and address search return the same verblijfsobject ID."""
    postal_query = build_postal_code_query("3011AD", "30")
    address_query = build_address_query("Coolsingel", "30", "Rotterdam")
    
    postal_result = await execute_sparql_query(postal_query)
    address_result = await execute_sparql_query(address_query)
    
    postal_bindings = postal_result.get('results', {}).get('bindings', [])
    address_bindings = address_result.get('results', {}).get('bindings', [])
    
    postal_ids = {b.get('identificatie', {}).get('value') for b in postal_bindings if b.get('identificatie')}
    address_ids = {b.get('identificatie', {}).get('value') for b in address_bindings if b.get('identificatie')}
    
    assert postal_ids == address_ids, f"Postal code IDs {postal_ids} != Address IDs {address_ids}"
    assert EXPECTED_VERBLIJFSOBJECT_ID in postal_ids, f"Expected ID {EXPECTED_VERBLIJFSOBJECT_ID} not found"


@pytest.mark.asyncio
async def test_result_contains_address_details():
    """Test that the result contains expected address details."""
    query = build_postal_code_query("3011AD", "30")
    result = await execute_sparql_query(query)
    
    bindings = result.get('results', {}).get('bindings', [])
    assert len(bindings) > 0, "No results returned"
    
    # Find the binding with our expected ID
    target_binding = None
    for b in bindings:
        if b.get('identificatie', {}).get('value') == EXPECTED_VERBLIJFSOBJECT_ID:
            target_binding = b
            break
    
    assert target_binding is not None, f"Could not find binding with ID {EXPECTED_VERBLIJFSOBJECT_ID}"
    
    # Check address details
    postcode = target_binding.get('postcode', {}).get('value')
    huisnummer = target_binding.get('huisnummer', {}).get('value')
    straatnaam = target_binding.get('straatnaam', {}).get('value')
    plaatsnaam = target_binding.get('plaatsnaam', {}).get('value')
    
    assert postcode == "3011AD", f"Expected postcode 3011AD, got {postcode}"
    assert huisnummer == "30", f"Expected huisnummer 30, got {huisnummer}"
    assert straatnaam == "Coolsingel", f"Expected straatnaam Coolsingel, got {straatnaam}"
    assert plaatsnaam == "Rotterdam", f"Expected plaatsnaam Rotterdam, got {plaatsnaam}"

