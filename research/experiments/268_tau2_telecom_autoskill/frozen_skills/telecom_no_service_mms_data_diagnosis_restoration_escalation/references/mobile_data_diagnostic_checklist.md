# Mobile Data Diagnostic Checklist

Order of checks (stop when cause confirmed):
1. Line status (active vs. suspended).
2. Data used vs. limit (over limit → offer refuel at quoted per-GB price, respect max cap).
3. Roaming enabled while user is at home (not traveling).
4. Device network status: airplane mode, SIM active, signal strength, network type (2G/4G/5G), mobile data enabled.
5. Data Saver mode (common throttle cause).
6. Reboot network services.
7. Re-run speed test; only close as resolved when the target speed/status is confirmed.

Guardrails:
- Confirm any chargeable change before executing.
- Never claim resolution before tool output verifies it.
- Sequence device actions one at a time if the user can only do one thing per turn.
