import json
from typing import Optional

import aiohttp
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from monumenten import MonumentenClient


class MonumentenMCP(FastMCP):
    def __init__(self, name: str = "Monumenten MCP", port: int | None = None, host: str = "127.0.0.1",
        stateless_http: bool = False):
        
        # Build FastMCP constructor arguments, only including port if provided
        fastmcp_kwargs = {"name": name, "stateless_http": stateless_http, "host": host}
        if port is not None:
            fastmcp_kwargs["port"] = port

        super().__init__(**fastmcp_kwargs)
        self._register_tools()
        
    
    def _register_tools(self):
        """Register all tools for this MCP server."""
        
        @self.tool(
            annotations=ToolAnnotations(
                destructiveHint=False,
                readOnlyHint=True,
                openWorldHint=True,
                description="Get the ID of a verblijfsobject using address information. Provide either (postal_code + house_number) OR (street + house_number + city). Additional filters like house_letter and house_suffix can be provided for more precise matching.",
            ))
        async def get_verblijfsobject_id(
            house_number: str, 
            postal_code: Optional[str] = None, 
            street: Optional[str] = None, 
            city: Optional[str] = None,
            house_letter: Optional[str] = None,
            house_suffix: Optional[str] = None
        ) -> str:
            """
            Get the ID of a verblijfsobject using address information.
            
            Two search modes:
            1. By postal code: provide postal_code + house_number
            2. By full address: provide street + house_number + city
            
            Args:
                house_number: The house number (required) e.g. '30'
                postal_code: The postal code (optional, for mode 1) e.g. '1234AB'
                street: The street name (optional, for mode 2) e.g. 'Coolsingel'
                city: The city name (optional, for mode 2) e.g. 'Rotterdam'
                house_letter: The house letter, e.g. 'A' in '30A'
                house_suffix: The house number suffix/addition, e.g. '2' in '30-2'

            Returns:
                - Single identificatie string when exactly one match is found
                - "Ambiguous address" message including a JSON array of IDs when multiple matches are found
                - An explanatory message when no matches are found
            """
            
            # Validate input combinations
            if postal_code and (street or city):
                return "Error: Provide either postal_code OR (street + city), not both."
            
            if postal_code:
                # Mode 1: Search by postal code + house number
                if not postal_code.strip():
                    return "Error: postal_code cannot be empty when using postal code search."
                search_mode = "postal_code"
                
            elif street and city:
                # Mode 2: Search by street + house number + city
                if not street.strip() or not city.strip():
                    return "Error: street and city cannot be empty when using address search."
                search_mode = "address"
                
            else:
                return "Error: Provide either (postal_code + house_number) OR (street + house_number + city)."

            # Build SPARQL query based on search mode
            if search_mode == "postal_code":
                # Build conditional parts
                letter_clause = f'?adres imx:huisletter "{house_letter}" .' if house_letter else ''
                suffix_clause = f'?adres imx:huisnummertoevoeging "{house_suffix}" .' if house_suffix else ''
                letter_filter = '' if house_letter else 'FILTER NOT EXISTS { ?adres imx:huisletter ?_hl . }'
                suffix_filter = '' if house_suffix else 'FILTER NOT EXISTS { ?adres imx:huisnummertoevoeging ?_hs . FILTER(?_hs != "H") }'
                letter_bind = 'OPTIONAL { ?adres imx:huisletter ?huisletter . }'
                suffix_bind = 'OPTIONAL { ?adres imx:huisnummertoevoeging ?huisnummertoevoeging . }'
                
                sparql_query = f"""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX imx:  <http://modellen.geostandaarden.nl/def/imx-geo#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?adres prov:wasDerivedFrom ?verblijfsobjectIri ;
         imx:isHoofdadres true ;
         imx:postcode "{postal_code}" ;
         imx:huisnummer {house_number} .
  
  {letter_clause}
  {suffix_clause}

  {letter_filter}
  {suffix_filter}

  OPTIONAL {{ ?adres imx:postcode ?postcode . }}
  OPTIONAL {{ ?adres imx:huisnummer ?huisnummer . }}
  {letter_bind}
  {suffix_bind}
  OPTIONAL {{ ?adres imx:straatnaam ?straatnaam . }}
  OPTIONAL {{ ?adres imx:plaatsnaam ?plaatsnaam . }}

  BIND(STRAFTER(STR(?verblijfsobjectIri), "https://bag.basisregistraties.overheid.nl/id/verblijfsobject/") AS ?identificatie)
}}
""".strip()
            
            else:  # address mode
                # Build conditional parts
                letter_clause = f'?adres imx:huisletter "{house_letter}" .' if house_letter else ''
                suffix_clause = f'?adres imx:huisnummertoevoeging "{house_suffix}" .' if house_suffix else ''
                letter_filter = '' if house_letter else 'FILTER NOT EXISTS { ?adres imx:huisletter ?_hl . }'
                suffix_filter = '' if house_suffix else 'FILTER NOT EXISTS { ?adres imx:huisnummertoevoeging ?_hs . FILTER(?_hs != "H") }'
                letter_bind = 'OPTIONAL { ?adres imx:huisletter ?huisletter . }'
                suffix_bind = 'OPTIONAL { ?adres imx:huisnummertoevoeging ?huisnummertoevoeging . }'
                
                sparql_query = f"""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX imx:  <http://modellen.geostandaarden.nl/def/imx-geo#>

SELECT DISTINCT ?identificatie ?postcode ?huisnummer ?huisletter ?huisnummertoevoeging ?straatnaam ?plaatsnaam
WHERE {{
  ?adres prov:wasDerivedFrom ?verblijfsobjectIri ;
         imx:isHoofdadres true ;
         imx:straatnaam "{street}" ;
         imx:huisnummer {house_number} ;
         imx:plaatsnaam "{city}" .
  
  {letter_clause}
  {suffix_clause}

  {letter_filter}
  {suffix_filter}

  OPTIONAL {{ ?adres imx:straatnaam ?straatnaam . }}
  OPTIONAL {{ ?adres imx:huisnummer ?huisnummer . }}
  OPTIONAL {{ ?adres imx:plaatsnaam ?plaatsnaam . }}
  {letter_bind}
  {suffix_bind}
  OPTIONAL {{ ?adres imx:postcode ?postcode . }}

  BIND(STRAFTER(STR(?verblijfsobjectIri), "https://bag.basisregistraties.overheid.nl/id/verblijfsobject/") AS ?identificatie)
}}
""".strip()

            # Execute SPARQL query against Kadaster endpoint
            endpoint_url = "https://data.kkg.kadaster.nl/service/sparql"
            
            headers = {
                'Accept': 'application/sparql-results+json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'query': sparql_query}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint_url, headers=headers, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            bindings = result.get('results', {}).get('bindings', [])

                            if bindings:
                                def get_val(b, k):
                                    return b.get(k, {}).get('value')
                                full = [
                                    {
                                        'bag_verblijfsobject_id': get_val(b, 'identificatie'),
                                        'postcode': get_val(b, 'postcode'),
                                        'huisnummer': get_val(b, 'huisnummer'),
                                        'huisletter': get_val(b, 'huisletter'),
                                        'huisnummertoevoeging': get_val(b, 'huisnummertoevoeging'),
                                        'straatnaam': get_val(b, 'straatnaam'),
                                        'plaatsnaam': get_val(b, 'plaatsnaam'),
                                    }
                                    for b in bindings
                                ]
                                ids = [item['bag_verblijfsobject_id'] for item in full if item['bag_verblijfsobject_id']]
                                if not ids:
                                    if search_mode == "postal_code":
                                        return f"No verblijfsobject found for postal code {postal_code}, house number {house_number}"
                                    else:
                                        return f"No verblijfsobject found for address: {street} {house_number}, {city}. Postal code + house number usually works better."
                                if len(ids) == 1:
                                    return f"{json.dumps(full, ensure_ascii=False)}"
                               
                                return f"Ambiguous address: multiple results found: {json.dumps(full, ensure_ascii=False)}"
                            else:
                                if search_mode == "postal_code":
                                    return f"No verblijfsobject found for postal code {postal_code}, house number {house_number}"
                                else:
                                    return f"No verblijfsobject found for address: {street} {house_number}, {city}. Postal code + house number usually works better."
                        else:
                            return f"Error querying Kadaster endpoint: HTTP {response.status}"
            except Exception as e:
                return f"Error executing SPARQL query: {str(e)}"
            
        @self.tool(
            annotations=ToolAnnotations(
                destructiveHint=False,
                readOnlyHint=True,
                openWorldHint=True,
                description="Get the monumental status of a verblijfsobject using the bag_verblijfsobject_id",
            ))
        async def get_monumental_status(
            bag_verblijfsobject_id: str
        ) -> str:
            """
            Get the monumental status of a verblijfsobject
            
            Args: 
                bag_verblijfsobject_id: The ID of the verblijfsobject to get the monumental status of. Usually a number of 16-18 digits.

            Returns:
                A JSON object with the monumental status of the verblijfsobject
            """
            async with MonumentenClient() as client:
                result = await client.process_from_list([bag_verblijfsobject_id])
                return f"{json.dumps(result, indent=2)}. Always mention the source for the Rijksmonument status if it is a Rijksmonument. RCE = Rijksdienst voor het Cultureel Erfgoed."
