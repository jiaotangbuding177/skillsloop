# Exchange Workflow Checklist

1. Resolve identity (name + zip / email) -> user_id. No match: ask for an alternative identifier; never fabricate IDs.
2. Load order -> verify it belongs to the user; capture item_ids and payment_method_id.
3. Restate requested exchanges and any stated fallback preference.
4. For each item to change, fetch product variants; keep only option-matched AND available == true.
5. Present matching options (item_id + price); request confirmation of exact replacement item_ids.
6. Apply fallback rule for unavailable variants.
7. Submit exchange only after explicit confirmation.
8. Report new status + price difference; never claim success before the write tool succeeds.
