---
description: Look up Dutch BAG verblijfsobject IDs and whether an address is a rijksmonument, in a protected cityscape, or a municipal monument. Use when the user asks about monumental status, heritage protection, or BAG IDs for a Dutch address.
---

Use the Monumenten MCP tools. Prefer `postal_code` + `house_number` over street + city when both are available.

1. Call `get_verblijfsobject_id` first unless the user already provided a 16-digit BAG verblijfsobject ID.
2. If there are multiple matches, list them and ask which one to check. Do not guess.
3. Call `get_monumental_status` with the chosen `bag_verblijfsobject_id`.
4. For a rijksmonument, always cite the source (RCE = Rijksdienst voor het Cultureel Erfgoed).
