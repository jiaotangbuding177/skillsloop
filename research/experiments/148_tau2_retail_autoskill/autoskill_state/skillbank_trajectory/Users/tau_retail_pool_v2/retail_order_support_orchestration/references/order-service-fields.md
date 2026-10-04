# Order & User Object Reference

## get_order_details(order_id) response
- order_id, user_id
- status: pending | shipped | delivered | cancelled
- address: {address1, address2, city, state, country, zip}
- items[]: {name, product_id, item_id, price, options}
- payment_history[]: {transaction_type: payment | refund, amount, payment_method_id}
- cancel_reason, exchange_items, exchange_new_items, return_items

## cancel_pending_order(order_id, reason)
Valid only when status == pending. Success response sets status=cancelled and appends a refund entry to payment_history.

## Order-level address update
Failure string to expect on a non-pending order: "Non-pending order cannot be modified". Do not retry the same call.

## modify_user_address(user_id, address1, address2, city, state, country, zip)
User-level fallback. Returns the user profile with the updated address and the list of owned order IDs.

## Policy matrix
| Order status | Cancel | Change address |
| pending      | yes    | yes (user-level fallback if order-level fails) |
| shipped      | no     | no |
| delivered    | no     | no |
| cancelled    | n/a    | no |

## Amount rules
- Final total = sum(items[].price).
- Refund amount = amount of the refund entry in payment_history.
- No address-change fee exists unless a tool response explicitly shows one.
