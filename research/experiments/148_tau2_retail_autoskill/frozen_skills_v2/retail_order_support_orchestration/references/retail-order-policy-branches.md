# Retail Order Eligibility Branch Checklist

Use after order lookup and before confirming a plan with the customer.

## Eligibility by item status
- Pending item: cancellation usually allowed; refund may apply; return typically not applicable yet.
- Delivered item: return/refund window applies; cancellation not allowed.
- Already cancelled/returned item: no further action; report state.

## Conditional branch patterns
- IF main item is NOT refundable/reorderable THEN cancel the accessory item (if pending).
- IF accessory cancellation is NOT possible THEN make no change to the retained item.
- Return requests are independent unless the customer chains them to another condition.

## Pre-write gate
1. Identity resolved (strong identifier).
2. Order fetched and items mapped to requested intents.
3. Eligibility determined per item.
4. Plan restated including all conditions.
5. Explicit customer confirmation received.

## Post-write reporting
- One line per action: action, item, status (completed / not eligible per policy / failed), reference or tracking id if any.
- Any failed action must include the next step offered to the customer.
