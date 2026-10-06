# No-Service Troubleshooting Checklist

1. Authenticate: phone number / customer ID / name+DOB.
2. Look up customer -> collect customer_id and line_ids.
3. Fetch each line's details; find the reported line and its status.
4. Fetch bills; check for overdue/suspended billing.
5. If reported line is Active and billing clear -> treat as device/network-side.
6. Device checks (ONE per turn, verify result each time):
   - Status bar: airplane mode icon, signal bars, network type, data status.
   - If airplane mode ON: disable it, re-check status bar.
   - Network status screen: SIM card status, cellular connection/signal/network type, mobile data, roaming, Wi-Fi.
7. Interpret results against known causes:
   - Airplane mode ON -> disable.
   - No signal + SIM locked_pin -> requires SIM PIN unlock -> escalate.
   - No signal + correct network mode but no service -> escalate.
8. Never claim resolution before diagnostics show restored service.
9. Escalate with: customer identity, affected line + status, symptom, diagnostics performed.
