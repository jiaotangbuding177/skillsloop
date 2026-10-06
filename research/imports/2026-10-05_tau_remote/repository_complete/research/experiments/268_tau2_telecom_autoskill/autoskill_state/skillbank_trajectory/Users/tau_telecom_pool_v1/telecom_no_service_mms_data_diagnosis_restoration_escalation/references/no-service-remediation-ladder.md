# No-Service Remediation Ladder
Apply in order; re-verify with diagnostics after each step and stop at the first fix.

1. Airplane Mode ON -> turn OFF, re-check status bar.
2. SIM status missing/locked -> power off, eject tray, clean/reseat SIM, power on, re-check.
3. Network mode / preferred network -> set to auto.
4. APN settings -> recheck and correct missing/incorrect fields.
5. Data saver / per-app data permissions -> enable for needed apps.
6. Roaming required -> enable roaming only if applicable.
7. Reboot device -> re-check network status.
8. Line-level checks: confirm line status Active and no suspension_start_date; if suspended, follow reactivation path.

Verification gate: only declare resolved when the diagnostic shows restored signal, a network type, and data enabled.

Fallbacks: accept any provided identifier if DOB unavailable; issue checks one at a time if the customer can only do one action per turn.
