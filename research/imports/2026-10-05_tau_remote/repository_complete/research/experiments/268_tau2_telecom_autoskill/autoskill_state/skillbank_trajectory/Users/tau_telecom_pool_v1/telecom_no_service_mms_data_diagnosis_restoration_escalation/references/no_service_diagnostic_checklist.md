# No-Service Diagnostic Checklist

## A. Account / billing branch (tool-side)
1. `get_customer_by_phone(phone_number)` -> confirm identity and collect `customer_id`, `line_ids`, `bill_ids`.
2. `get_details_by_id(line_id)` for each line -> locate the line with `status: Suspended` (record `suspension_start_date`).
3. `get_bills_for_customer(customer_id)` -> find `status: Overdue`, match `line_items` to the suspended line.
4. Offer payment request; on consent `send_payment_request(customer_id, bill_id)`.
5. After customer pays, `get_details_by_id(bill_id)` -> require `status: Paid`.
6. `resume_line(customer_id, line_id)` -> require returned `status: Active`.

## B. Device branch (customer-executed, one step per turn)
1. Status bar check.
   - Airplane mode icon -> instruct turning airplane mode OFF -> re-check status bar.
2. Network status check -> read SIM card status.
   - `missing` -> instruct reseating the SIM -> re-run network status check.
   - `locked_pin` (or any PIN/PUK/security lock) -> escalate to human agent.
3. If signal returns after reboot/reseat, confirm service and close.

## C. Escalation summary template
- Customer id / name, affected phone number / line id
- Root cause (e.g. overdue bill suspension, SIM security lock)
- Actions taken and verified results
- Blocking condition and requested specialised help