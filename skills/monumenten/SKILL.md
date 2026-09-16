---
description: >
  Look up WWS-relevant monumental status of a Dutch address
  (rijksmonument, rijksbeschermd stads- of dorpsgezicht, gemeentelijk monument;
  provincial monument and municipal cityscape are not looked up).
  Use when the user asks about monumentale status, erfgoed, BAG-IDs,
  rijksmonumenten, woningwaardering, monumental status, or provincial monuments.
---

Use the Monumenten MCP tools. Prefer `postal_code` + `house_number` over street + city when both are available. Reply in the user's language.

1. Call `get_verblijfsobject_id` first unless the user already provided a 16-digit BAG verblijfsobject ID.
2. If there are multiple matches, list them and ask which one to check. Do not guess.
3. Call `get_monumental_status` with the chosen `bag_verblijfsobject_id`.
4. For a rijksmonument, always cite the source (RCE = Rijksdienst voor het Cultureel Erfgoed).
5. Structured fields are facts. Phrase them in the user's language. `provinciaal_monument` is not looked up (`null`). `rijksbeschermd_gezicht` is the national cityscape only.
