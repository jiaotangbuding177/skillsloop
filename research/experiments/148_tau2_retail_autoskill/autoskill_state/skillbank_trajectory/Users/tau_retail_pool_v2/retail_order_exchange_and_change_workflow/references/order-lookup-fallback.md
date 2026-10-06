# Order Lookup Fallback Checklist

1. Confirm exchange intent and target product specifications.
2. Collect order ID and call `get_order_details`.
3. On `Order not found`, ask the customer to verify the ID once; retry only with a corrected ID.
4. If it still fails, explain possible causes and request an alternate identifier: purchase date, zip code, or email.
5. Perform identity lookup by name+zip (or email) to obtain `user_id`.
6. Call `get_user_details(user_id)` and review the `orders` list.
7. If no item ID is available, ask for product name/description, serial number, or receipt details.
8. If the item still cannot be identified, stop and escalate to human support; never fabricate IDs or claim an exchange is complete.
9. Summarize what was tried and what identifier is missing for the next agent.
