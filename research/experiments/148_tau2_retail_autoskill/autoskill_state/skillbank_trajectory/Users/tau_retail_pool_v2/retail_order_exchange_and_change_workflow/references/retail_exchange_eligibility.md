# Retail Exchange/Modification Eligibility & Tool Chain

## Identity & Order Resolution
- Verify identity with (first_name, last_name, zip) OR email -> user_id.
- If no order ID: get_user_details(user_id) -> orders[]; let the customer select.
- Always confirm order.user_id matches the verified user_id.

## Eligibility Matrix (check order.status BEFORE writing)
| Operation       | Required status  | Error if violated                     |
|-----------------|------------------|---------------------------------------|
| Exchange item   | delivered        | "Non-delivered order cannot be exchanged" |
| Modify item     | pending          | "Non-pending order cannot be modified"    |

On a policy error: do not re-issue the same call; mark ineligible and continue with other items.

## Variant Resolution
- list_all_product_types (no args) -> {type_name: product_id}
- get_product_details(product_id) -> variants{item_id: {options, available, price}}
- Select item_id where options match the request AND available == true.

## Write Payload Contract
- exchange_item / modify_item: {order_id, item_ids[], new_item_ids[], payment_method_id}
- Use the order's own payment_method_id from get_order_details; never invent one.

## Escalation
- transfer_to_human(summary): include user_id, order_id, requested actions, and blocking reason.
- Offer escalation only after the customer consents.

## Hard Constraints
- Never fabricate order IDs, item IDs, user IDs, or payment method IDs.
- Never claim success before a confirming tool result.
- On identity lookup failure, request an alternative identifier.