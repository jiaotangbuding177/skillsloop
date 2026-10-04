# Roaming Mobile-Data Escalation Runbook

Use this when a first remediation (e.g., data refuel) does not restore connectivity. Work top-to-bottom and re-verify with the same objective test after each step.

## Layer 1 - Account / Line
- Confirm the affected line is Active (not Suspended).
- Compare `data_used_gb` vs `data_limit_gb`; if over limit, refuel and report charge.
- Confirm line `roaming_enabled` is true for international use.

## Layer 2 - Device Radio / Settings
- Airplane mode: toggle OFF (or toggle ON then OFF to force re-registration).
- Mobile data: enabled.
- Data Roaming: enable on device when traveling abroad even if the line already allows it.
- Network mode: prefer 5G/Auto; avoid a locked unusable band.

## Layer 3 - Deeper
- APN settings: verify correct operator APN; reset to default if unknown.
- Data Saver / per-app data permissions: ensure the browser/speed-test app is not restricted.
- SIM: reseat the SIM; confirm SIM status active.
- Reboot the device and retest.

## Verification Contract
- Every change must be followed by an objective check (speed test, connection test).
- Only report the issue as resolved after the objective check passes (e.g., Excellent rating).
- Never fabricate or assume tool/device outputs.