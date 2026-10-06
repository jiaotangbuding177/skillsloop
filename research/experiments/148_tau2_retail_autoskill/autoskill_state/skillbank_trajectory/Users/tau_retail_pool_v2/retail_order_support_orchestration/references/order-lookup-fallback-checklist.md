# Order Lookup Fallback Checklist

1. Receive order ID → call order-lookup tool with the exact string.
2. On `Order not found`:
   - Apologize once, request email OR full name (+ zip if offered).
   - If email unavailable → call identity tool with first_name, last_name, zip → obtain user_id.
   - Call account-details tool with user_id.
   - Compare claimed order against the returned orders list.
3. If claimed order is present → check return/refund eligibility → confirm exact item and refund destination with the customer → perform write → report verified result.
4. If claimed order is absent → state the mismatch factually, ask the customer to re-verify the order ID or provide a receipt reference.

## Hard Rules
- Never invent, auto-correct, or guess an order ID.
- Never claim a refund/return completed without a successful write tool result.
- Never assert an order does not exist solely because a lookup failed.
- If identity resolution fails, request an alternative identifier instead of guessing.