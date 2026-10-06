# Mobile Data Remediation Checklist
Use in order; stop when verified by status bar + speed/connection test.

1. Account/line lookups
- `get_customer_by_phone(phone_number)` -> customer_id, line_ids, account_status.
- `get_details_by_id(line_id)` for each candidate line -> status, plan_id, device_id, data_used_gb, roaming_enabled, suspension_start_date.
- `get_details_by_id(plan_id)` -> plan name, data_limit_gb.
- `get_data_usage(customer_id, line_id)` -> data_used_gb, data_limit_gb, cycle_end_date.

2. Account-level rule-outs
- Account not Active? Stop device diagnostics; surface account status.
- Line Suspended? Surface suspension date; do not treat as a handset setting issue.
- data_used_gb >= data_limit_gb? Explain cap/refueling options.

3. Device diagnostics (one step per turn for overwhelmed users)
- Status bar: airplane mode, signal strength, network type (2G/3G/4G/5G), data enabled, data saver.
- Airplane Mode ON -> turn OFF; re-check.
- Network type 2G / poor -> set preferred network mode `4g_5g_preferred`; re-check.
- Data saver ON -> disable; re-check.
- Mobile data disabled -> enable; re-check.
- Roaming required/off -> align `roaming_enabled` with line and location.
- APN incorrect -> correct APN per carrier; reboot.
- SIM/device issue -> reseat SIM, reboot, test another device.

4. Verification
- Ask user to load a data page or run a speed test.
- Confirm speed/connection quality before closing.
- Only close after tool/customer verification.

5. Close/refer
- Summarize root cause(s), change(s), verified outcome.
- If unresolved, list remaining candidates and next escalation path.