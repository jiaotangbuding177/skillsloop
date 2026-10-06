# Retail Order Exchange Runbook

## Identity resolution ladder
1. order_id -> get_order_details
2. email -> find_user_id_by_email
3. first_name + last_name + zip -> find_user_id_by_name_zip
4. user_id -> get_user_details (orders list + payment_methods)

## Known tool errors and responses
- "Order not found": ask for an alternative identifier; do not retry the same id.
- "User not found" / empty email: escalate to name+zip.
- "The new item id should be different from the old item id": variant not directly selectable; propose modifying the order with a distinct available variant matching the requested option, re-confirm, then retry.

## Pre-write checklist
- Target order confirmed by the customer.
- Target item id retrieved via get_item_details and available.
- New variant id differs from the old item id.
- payment_method_id matches the customer's stated preference.
- Explicit customer confirmation captured before the write.

## Post-write reporting fields
- order id, changed item/option, unchanged items, payment method, order status, further action needed (usually none; confirmation email is sent).
