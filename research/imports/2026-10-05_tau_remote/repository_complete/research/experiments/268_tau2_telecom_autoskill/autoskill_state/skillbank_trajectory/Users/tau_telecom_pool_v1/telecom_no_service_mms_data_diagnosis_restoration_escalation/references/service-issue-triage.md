# 'No Service' Line Triage Checklist

1. Capture symptom from customer (status bar: signal / data / battery).
2. `get_customer_by_phone` → anchor `customer_id`, `line_ids`, `bill_ids`.
3. `get_details_by_id` for EVERY line → find `status = Suspended`; record `suspension_start_date`, `contract_end_date`.
4. `get_bills_for_customer` → find `Overdue` bill; map via `line_items`.
5. Consent → `send_payment_request(customer_id, bill_id)`.
6. After customer accepts → re-fetch bills → confirm `status = Paid`.
7. Eligibility gate: if `contract_end_date` is in the past → cannot lift; explain and transfer. Else lift suspension.
8. Verify and close, or emit `###TRANSFER###`.

Policy notes: a line may be suspended for an overdue bill OR an ended contract; an ended contract blocks self-service restoration even after the bill is paid.