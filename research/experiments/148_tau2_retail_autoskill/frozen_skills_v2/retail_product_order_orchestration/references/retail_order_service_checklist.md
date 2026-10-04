# Retail Order Service Checklist

## Before any write
- Identity loaded via `get_user_details`? (user_id or email confirmed)
- Address: customer-stated vs on-file compared line by line; mismatches flagged.
- Product: category resolved to a real ID via `list_all_product_types`; no invented IDs.
- Customer explicitly confirmed product + shipping address.

## Failure rules
- No order ID known -> search by resolved product ID in the user's order list; never fabricate.
- No matching order -> say so; offer new order or alternative search.
- Lookup empty -> ask for alternative identifier (email/zip).
- Tool error -> retry once, then report failure; never claim unverified success.

## After write
- Re-read profile/order state to confirm the change.
- Summarize real order ID (if any), product, and shipping address.