# MMS Remediation Checklist (apply one step at a time, verify after each)

| # | Condition to check | Action | Verification |
|---|---|---|---|
| 1 | Airplane Mode ON | Turn Airplane Mode OFF | Re-read status bar |
| 2 | Data disabled | Turn Mobile Data ON | Confirm data enabled |
| 3 | SIM status = missing | Reseat SIM card | Confirm SIM active |
| 4 | Network type 2G or lower | Set network mode to 4G/5G preferred | Confirm 4G/5G + signal |
| 5 | Roaming disabled (line) | enable_roaming(customer_id, line_id) | Confirm roaming enabled |
| 6 | Roaming disabled (device) | Turn on device data roaming | Confirm roaming ON |
| 7 | MMSC URL not set | Reset APN settings, then reboot | Confirm MMSC URL set |
| 8 | Wi-Fi Calling ON | Turn Wi-Fi Calling OFF | Confirm OFF |
| 9 | Messaging app lacks storage permission | Grant storage permission | Confirm permission granted |

After each row: have the customer re-test MMS. If still failing after row 9, escalate to a human agent with a full action summary.