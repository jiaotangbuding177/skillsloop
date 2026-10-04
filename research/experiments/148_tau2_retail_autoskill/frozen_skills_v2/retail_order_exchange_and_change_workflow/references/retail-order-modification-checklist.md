# Retail Order Modification Checklist

## Before the write
- [ ] Product type confirmed via `list_all_product_types`.
- [ ] Variant data pulled via `get_product_details` (never answer counts from the type list).
- [ ] Each candidate variant matches ALL requested attributes; unavailable variants flagged, not counted as options.
- [ ] `item_id` values copied verbatim from tool output.
- [ ] Customer identity resolved (primary identifier or a fallback identifier).
- [ ] Order located and status is pending/modifiable; non-modifiable statuses declined with policy explanation.
- [ ] Exact target specs restated to the customer and explicitly confirmed.

## After the write
- [ ] Modification tool call returned success.
- [ ] Order re-read to confirm the change actually persisted.
- [ ] Final reply states only the tool-verified outcome and offers further help.

## Never do
- Never invent product_id / order_id / item_id.
- Never claim success without a successful write result.
- Never accept a second-hand "it was done" assertion without verifying via a read.
