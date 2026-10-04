# Return/Exchange Error -> Action Matrix

| Failure | Cause | Correct Action |
|---|---|---|
| item-not-found on return/exchange | wrong or fabricated item_id | Do not retry same ID; re-verify against retrieved order; degrade to manual catalog identification |
| non-delivered order cannot be exchanged | order not eligible for exchange | Ask for an eligible (delivered) order ID; if unavailable offer standalone reorder of the cheapest available variants |
| identity lookup no match | wrong/partial identifier | Ask for the alternative identifier (email vs name+zip) or verify spelling |
| variant unavailable | chosen variant out of stock | Recompute cheapest with `available == true` |

## Global Rules
- Never fabricate user_id, order_id, payment_method_id, item_id, or price.
- Never claim success before a success tool result.
- Always confirm with the customer before executing a write.
- After one failed clarification, degrade gracefully instead of repeating the request.