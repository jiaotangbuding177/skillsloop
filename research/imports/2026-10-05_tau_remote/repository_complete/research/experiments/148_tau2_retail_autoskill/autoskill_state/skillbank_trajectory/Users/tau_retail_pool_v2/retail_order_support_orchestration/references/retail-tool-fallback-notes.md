# Retail Tool Fallback Notes

## Tool signatures
- find_user_id_by_name_zip(first_name, last_name, zip)
- find_user_id_by_email(email)
- get_user_details(user_id) -> { name, address, email, payment_methods, orders }
- modify_user_address(user_id, address1, address2, city, state, country, zip)  # PROFILE level only, no order_id
- list_all_product_types() -> { product_name: product_id }
- get_product_details(product_id) -> { name, product_id, variants: { key: { item_id, options, available, price } } }
- get_item_details(item_id) -> single item
- exchange_delivered_order_items(order_id, item_ids, new_item_ids, payment_method_id)

## Fallback ladder
1. Identity: name+zip -> email
2. Address write: order-level attempt is unsupported -> fall back to modify_user_address (profile) with customer consent
3. Item resolve: get_item_details(item_id) -> list_all_product_types + get_product_details(product_id)
4. Order resolve: on 'Order not found', re-confirm the order id with the customer; do NOT invent ids or repeat the same failing call; escalate/report if unresolved

## Confirm-before-write checklist
- Address text echoed and confirmed
- Cheapest AVAILABLE variant (available == true, min price) selected and confirmed
- payment_method_id taken from get_user_details
- Completion reported only after a success tool result
