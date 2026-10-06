# Service Outage Diagnostic Runbook

## 1. Account-side checks (in order)
1. `get_customer_by_phone` -> customer_id, line_ids, bill_ids.
2. `get_details_by_id(line_id)` for EVERY line -> find `status: Suspended`.
3. `get_bills_for_customer(customer_id)` -> find the `Overdue` bill matching the suspended line.
4. `send_payment_request(customer_id, bill_id)` (after consent).
5. `get_details_by_id(bill_id)` -> require `status: Paid`.
6. `resume_line(customer_id, line_id)` -> re-fetch line -> require `status: Active`, `suspension_start_date: null`.

## 2. Device-side checks (only if service still fails after line is Active)
- Status bar: signal icons, data indicator, airplane icon.
- Network status: Airplane Mode, SIM status, cellular connection, signal, Mobile Data, roaming.

## 3. State -> action map
- SIM `missing` -> power off, remove, firmly reseat, power on, re-check.
- SIM `locked_pin` / PUK lock -> escalate (do not guess PIN).
- Airplane Mode ON -> ask user to disable, re-check.
- Mobile Data disabled while data-only complaint -> ask user to enable, re-check.
- All normal but still no service -> escalate with full summary.

## 4. Escalation summary template
- Customer id / name
- Affected line id + number
- Reported symptom
- Actions taken and their verified results
- Current blocking state
- Reason for handoff