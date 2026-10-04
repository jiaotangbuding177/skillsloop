# Mobile Data Troubleshooting Runbook

## Diagnostic order
1. Identify account (phone number or name+DOB) -> customer_id, line_ids.
2. Fetch each line: status, plan_id, roaming_enabled, suspension_start_date.
3. Fetch data usage vs plan limit -> rule out throttling/exhaustion.
4. Fetch plan details -> included data, roaming allowance.

## Authoritative fixes (server-side)
- enable_roaming when line is roaming-capable but flag is off.

## Device-side remediation order
1. Reboot device to pick up network settings.
2. Disable VPN (can throttle traffic).
3. Set preferred network mode to 4g_5g_preferred (fallback 4g_only).
4. Toggle airplane mode on/off.
5. Check data saver and APN settings.

## Verification checkpoints
- After every change: re-read status bar + re-run speed test.
- Success = strong 4G/5G signal and speed test rated excellent.
- Never claim resolved without verification evidence.

## Common root causes
- Stuck on 2G network mode.
- VPN active and throttling.
- Roaming disabled while abroad.
- Data limit exhausted.
- Line suspended.