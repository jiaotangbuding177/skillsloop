# No-Service Triage Playbook

## Order of operations
1. Verify identity: get_customer_by_phone -> customer_id + line_ids.
2. Enumerate lines: get_details_by_id for every line_id; record status, contract_end_date, suspension_start_date.
3. Classify the failing line: Active vs Suspended (or other non-active state).
4. If Suspended, classify cause:
   - Overdue bill -> possibly remediable via payment path.
   - contract_end_date in the past -> contract-end suspension; agent cannot lift; escalate.
5. Re-check state via get_details_by_id after any change before reporting success.

## Optional device/network remediation (only when no account-level block applies)
- Confirm airplane mode is off.
- Confirm correct network mode preference.
- Verify APN settings are intact.
- Check app/network permissions and data-saver settings.
- Confirm roaming status matches the customer's location.
- Reseat the SIM and reboot the device.
- Re-verify via tools after each step; never assume a fix without confirmation.

## Escalation checklist
- customer_id, affected line_id, root cause, governing policy/date constraint, customer request.
- Do not include unnecessary PII or raw payloads.
