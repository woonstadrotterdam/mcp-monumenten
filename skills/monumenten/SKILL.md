---
description: >
  Look up Dutch BAG verblijfsobject IDs and monumental status
  (rijksmonument, beschermd stadsgezicht, gemeentelijk monument).
  Use when the user asks about monumental status, heritage protection,
  BAG-IDs, monumentale status, erfgoed, or rijksmonumenten.
---

Use the Monumenten MCP tools. Prefer `postal_code` + `house_number` over street + city when both are available. Reply in the user's language (Dutch or English).

1. Call `get_verblijfsobject_id` first unless the user already provided a 16-digit BAG verblijfsobject ID.
2. If there are multiple matches, list them and ask which one to check. Do not guess.
3. Call `get_monumental_status` with the chosen `bag_verblijfsobject_id`.
4. For a rijksmonument, always cite the source (RCE = Rijksdienst voor het Cultureel Erfgoed).
