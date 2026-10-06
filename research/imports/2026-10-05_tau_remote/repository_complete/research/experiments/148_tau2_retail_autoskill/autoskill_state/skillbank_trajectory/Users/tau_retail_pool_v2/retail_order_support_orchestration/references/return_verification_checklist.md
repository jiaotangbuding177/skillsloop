# Retail Return Verification Checklist
- [ ] Accepted identifier: order ID / email / name+zip (zip alone is invalid)
- [ ] user_id resolved via directory lookup
- [ ] Orders + payment methods retrieved from account details
- [ ] Exact item_ids read from order details (never guessed)
- [ ] Items grouped correctly by order_id
- [ ] Refund payment_method_id confirmed by customer
- [ ] Explicit customer confirmation captured before any write
- [ ] Return tool executed per order
- [ ] Completion reported ONLY on tool success

# Common failure mode
Repeated 'Some item not found' means item_ids are wrong or attached to the wrong order_id. Do not retry the identical payload; re-read order details and split the return by order.
