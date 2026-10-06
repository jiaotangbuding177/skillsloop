# Retail Return/Refund Runbook

## Identifier resolution order
1. order_id (best)
2. email
3. first_name + last_name + zip

## Pre-write checklist
- [ ] Customer confirmed the target order
- [ ] Requested items mapped to real item_ids from get_order_details
- [ ] Refund payment_method_id confirmed

## Error playbook
- 'Some item not found' -> re-fetch get_order_details, re-map item_ids, retry ONCE.
- Repeated failure -> escalate to human agent; never claim completion.
- Lookup miss -> request alternative identifier.

## Hard rules
- No fabricated order_id/item_id/payment_method_id.
- No refund claim before tool success.
