# Mobile Data Troubleshooting Playbook

## Diagnostic Order
1. Identify customer by phone or customer ID.
2. List lines; select the affected line.
3. Fetch line details, plan details, and data usage.
4. Compare data_used_gb vs data_limit_gb; check status and roaming.
5. Check device data mode via user-reported status bar.
6. Choose remediation: refuel data (with cost/quantity confirmation) or plan change.
7. Apply refuel_data and confirm returned charge/new allowance.
8. Guide device reboot and enable mobile data; obtain status bar readout.
9. Verify speed test or browsing result.
10. Summarize and close.

## Tool Contracts
- get_customer_by_phone(phone_number) -> customer_id, line_ids, account_status
- get_details_by_id(id) -> line or plan fields (status, plan_id, data_used_gb, data_refueling_gb, roaming_enabled, suspension_start_date, data_limit_gb, per-GB price)
- get_data_usage(customer_id, line_id) -> data_used_gb, data_limit_gb, data_refueling_gb, cycle_end_date
- refuel_data(customer_id, line_id, gb_amount) -> message, new_data_refueling_gb, charge

## Failure-Avoidance Lessons
- Always verify tool state before and after changes; never claim resolution from assumptions.
- Obtain explicit confirmation of quantity and cost before refueling.
- Treat a suspended line separately; do not promise data restoration until the suspension is addressed.
- If a refuel tool errors, report it honestly and do not fabricate success.
- After any change, require user-verified status bar and speed test before closing.