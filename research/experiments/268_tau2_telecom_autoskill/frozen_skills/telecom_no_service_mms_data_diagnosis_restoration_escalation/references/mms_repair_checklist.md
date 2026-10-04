# MMS Sending Repair Checklist

Apply ONE step per turn; confirm the result before moving on.

1. Airplane Mode OFF.
2. SIM status: if missing → reseat SIM card.
3. Network type: if degraded (e.g. 2G) → set preferred network mode to a 3G/4G/5G-capable option.
4. Mobile data: enable it.
5. APN settings: if MMSC URL not set → reset APN, reboot, then re-check APN to confirm MMSC URL is set.
6. Wi-Fi Calling: if ON → turn OFF.
7. Messaging app permissions: grant any missing required permission (e.g. sms).
8. Verify with can_send_mms().
9. If verification fails after all steps → escalate to human agent with a structured summary.

Escalation summary fields: customer id + line, symptom, completed remediations, current verification result, note that standard causes are exhausted.