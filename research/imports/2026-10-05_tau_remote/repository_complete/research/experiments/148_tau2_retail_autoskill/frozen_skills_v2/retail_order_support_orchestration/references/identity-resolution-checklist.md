# Identity Resolution & Order Lookup Checklist

## Identifier fallback ladder
1. Order ID (normalize: leading alpha prefix and/or `#`)
2. Account email
3. First name + last name + zip -> user_id

## After identity resolution
- Call `get_user_details(user_id)`.
- Compare the customer-supplied order ID against the returned `orders` array.
- If it does not match, correct the ID from the account list and re-verify.

## Anti-patterns (never do)
- Retry the identical failing order ID more than twice.
- Invent, guess, or pad an order ID.
- Claim a return/refund succeeded before a write tool returns success.
- Assert an order was 'cancelled' or 'never processed' as fact when the lookup merely failed.

## Loop-break rule
On the third identical failing attempt: stop, restate the limitation, and request a different identifier or human handoff.
