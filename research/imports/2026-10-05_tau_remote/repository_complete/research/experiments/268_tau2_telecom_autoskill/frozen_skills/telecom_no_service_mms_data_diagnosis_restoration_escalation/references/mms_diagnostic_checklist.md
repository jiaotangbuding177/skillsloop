# MMS Diagnostic & Remediation Checklist

## Diagnosis (always verify with tools, never assume)
1. Read status bar and run MMS send test.
2. Note signal state, network type (2G/3G/4G/5G), data enabled/disabled, airplane mode.
3. Read APN name and MMSC URL (set vs not set).
4. Read Wi-Fi Calling status.
5. Read messaging app permissions (storage, SMS, phone).

## Remediation order (one step at a time; confirm each before next)
1. Turn OFF Airplane Mode.
2. Reseat SIM card (if No Signal).
3. Enable Mobile Data.
4. Set Preferred Network Type to 4G/5G preferred (2G cannot carry MMS).
5. Reset APN settings so MMSC URL is restored, then reboot as a separate step.
6. Turn OFF Wi-Fi Calling.
7. Grant messaging app Storage permission.
8. Grant messaging app SMS permission.

## Account-side check (when device looks correct but MMS fails)
9. get_data_usage: if data_used_gb >= data_limit_gb, line is over allowance.
10. Explain refueling rate and cap; confirm amount + total cost + target line.
11. refuel_data(customer_id, line_id, gb_amount); re-verify with get_data_usage.
12. Final reboot + MMS test.

## Escalation
- After all steps fail, raise escalation with: customer/line IDs, symptom & duration, all attempted remediations and outcomes, refuel details & charge, and current device/network state.
