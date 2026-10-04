# MMS Send-Failure Candidate-Cause Runbook (ordered)

Test causes in this order, one per turn, re-verifying after each change:

1. Airplane Mode ON → turn OFF.
2. Preferred network mode = 2G-only → set to 4G/5G preferred.
3. Retry send; if fail → APN MMSC blank / Not Set → reset APN, then reboot device.
4. Retry send; if fail → rule out non-causes explicitly:
   - Wi-Fi Calling OFF (not a blocker)
   - Messaging app SMS + Storage permissions granted (not a blocker)
5. Retry send; if fail → account-side check: compare data_used_gb vs data_limit_gb.
   - If used >= limit → explain overage, quote per-GB price and max refuel, get explicit confirmation, then refuel_data.
6. Retry send → declare resolution only on confirmed success.

Rules: never claim resolved without tool/device confirmation; never charge without explicit consent; keep prior correct settings applied.
