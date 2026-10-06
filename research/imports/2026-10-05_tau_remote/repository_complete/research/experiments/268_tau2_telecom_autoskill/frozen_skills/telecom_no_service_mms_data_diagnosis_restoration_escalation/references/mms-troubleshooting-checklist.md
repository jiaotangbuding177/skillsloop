# MMS Failure Diagnostic Checklist (dependency order)

1. Account verification: phone number -> customer_id + line_ids.
2. Affected line identified (status Active, not Suspended, roaming entitlement noted).
3. Status bar / network status: airplane mode OFF, SIM present, cellular connected, network type known, mobile data ON.
4. Data path: data usage below limit (get_data_usage).
5. MMS re-test after each change.
6. APN settings: MMSC URL present and correct; APN reset followed by device reboot; re-verify after reboot.
7. Wi-Fi Calling turned OFF (known MMS interference).
8. Messaging app permissions: storage and sms granted.
9. Roaming layer: if abroad, line roaming enabled AND device data roaming ON.
10. Final proof: can_send_mms returns success.
11. Close with itemized cause/fix recap and any condition to maintain.
