# Retail Order Cancellation Reversal Checklist

- [ ] Order ID available? If not, collect first_name + last_name + zip (or email).
- [ ] Identity lookup returned a valid user_id.
- [ ] get_user_details returned the target order_id.
- [ ] get_order_details confirms status == 'cancelled'.
- [ ] Customer confirmed the restore (order ID, items, timing, refund implications).
- [ ] Reversal write tool called and returned success.
- [ ] Final reply states order ID and true outcome.

Safety rules:
- Never fabricate an order ID.
- Never claim completion before a success tool result.
- If identity lookup fails, ask for an alternative identifier and retry.
- If status is not 'cancelled', do not write; explain policy instead.