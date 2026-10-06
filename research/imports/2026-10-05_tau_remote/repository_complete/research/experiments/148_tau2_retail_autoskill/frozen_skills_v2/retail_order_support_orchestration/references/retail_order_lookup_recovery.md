# Retail Order Lookup Recovery Checklist

- Resolve identity before any order operation.
- Verify order existence with get_order_details before every write.
- On 'Order not found': re-confirm the id with the customer, retry at most once.
- After two failures: stop; propose an account-level alternative and ask consent.
- Never fabricate order ids, tracking numbers, or addresses.
- Never claim success before the tool result payload shows the change.
- Unresolvable retrieval requests: give self-service paths (email/notifications, customer support).
