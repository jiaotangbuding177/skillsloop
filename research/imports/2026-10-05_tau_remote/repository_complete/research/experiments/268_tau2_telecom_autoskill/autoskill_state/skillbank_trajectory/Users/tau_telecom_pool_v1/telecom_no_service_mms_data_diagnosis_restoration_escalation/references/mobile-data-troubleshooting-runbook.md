# Mobile Data Troubleshooting Runbook

## Ordered Remediation Ladder (verify after each step)
1. Airplane Mode OFF (kills all cellular).
2. Preferred network mode -> 4G/5G preferred (2G is too slow).
3. Roaming enabled on the confirmed line (free where stated).
4. Data cap: compare used GB vs plan limit; if over, offer refuel (state price/GB and max GB, get consent).
5. Device config: APN correct, VPN OFF, Data Saver OFF.
6. Airplane Mode toggle ON->OFF, then reboot to force network re-registration.
7. Re-run the user-visible test (speed test / browsing).

## Diagnostic Data To Pull
- Customer record -> line_ids.
- Each line: status, plan_id, device_id, roaming_enabled, data_used_gb, data_refueling_gb, suspension dates.
- Plan: data_limit_gb, price, refuel max/price.
- Device: activated, eSIM-capable, activation state.
- Data usage: used vs limit, refuel balance, cycle end.
- Bills: only to rule out a payment-blockage hypothesis (Draft refuel charge = no separate payment needed).

## Escalation Summary Template
"Customer <id>, line <id>, location/roaming context. No data connectivity despite: roaming enabled, network mode 4G/5G (good signal), data refueled (was over plan cap), APN correct, VPN off, Data Saver off, airplane mode toggled, device rebooted. Line Active, contract valid. Speed test still reports 'No Connection.' Needs investigation beyond available tools."

## Failure-Avoidance Rules
- Never assert the issue is resolved before the user's test confirms it.
- Never repeat a failing step; change hypothesis and re-inspect state.
- Never mutate a line the user has not confirmed.
- Escalate instead of looping once the ladder is exhausted.