# Order Cancellation Runbook

1. Collect item -> order_id mapping for all items in the request.
2. Confirm scope (partial vs whole order) and get explicit customer confirmation.
3. Call cancel_pending_order(order_id, reason).
4. Success -> report cancellation and end.
5. Failure ('Order not found') -> ask customer to re-verify ID; retry once.
6. Second failure -> explain, propose human-agent transfer, call transfer tool only after consent.
7. Never fabricate order IDs; never claim cancellation or transfer without a successful tool result.
8. Transfer summary must include: customer identity, attempted order_id, observed error, requested action.
