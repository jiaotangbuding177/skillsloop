# Retail Return & Refund Runbook

1. Identifier ladder: email -> order ID -> (first_name + last_name + zip).
2. Resolve user_id, then load account details (orders, payment_methods).
3. Map refund destination to an exact payment_method_id (credit_card vs gift_card).
4. Confirm item ID + destination with the customer before the write.
5. Write failure handling: 'item not found' -> re-request correct item ID -> verify -> retry once.
6. Persistent failure -> apologize and escalate to a human agent; never fabricate success or IDs.
