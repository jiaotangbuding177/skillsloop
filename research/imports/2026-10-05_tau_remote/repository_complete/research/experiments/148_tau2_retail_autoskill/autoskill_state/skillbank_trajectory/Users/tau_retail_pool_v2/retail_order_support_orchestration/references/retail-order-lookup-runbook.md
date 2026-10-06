# Retail Order Lookup Runbook

## Identity fallback chain
1. No order ID -> collect first_name, last_name, zip (or email).
2. identity_lookup(name, zip) -> user_id.
3. get_user_details(user_id) -> orders[].
4. Pick relevant order -> get_order_details(order_id).

## Guardrails
- Never invent order IDs; ask for another identifier on lookup failure.
- Confirm with the customer before any write (cancel/return/exchange).
- Only report completion after a tool success result.
- If the customer revokes the request, abandon the write.
