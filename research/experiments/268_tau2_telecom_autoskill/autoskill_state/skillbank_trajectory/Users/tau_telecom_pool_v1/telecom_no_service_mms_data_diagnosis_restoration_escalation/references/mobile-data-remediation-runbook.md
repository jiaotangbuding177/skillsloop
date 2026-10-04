# Mobile Data Remediation Runbook

## Ordered Ladder (change one item per step, re-measure each time)
1. Airplane Mode ON → OFF.
2. Preferred Network Mode limited to 2G/3G → set to 4G/5G-inclusive value (`4g_5g_preferred`, `4g_only`).
3. Data Saver ON → OFF (restricts background data and can suppress throughput).
4. VPN connected → disconnect (encrypted tunnel adds overhead, reduces throughput).
5. APN profile correct → SIM reseat → device reboot.
6. Plan data cap / data refueling exhausted → advise top-up or plan change.

## Carrier-Side Pre-Checks
- Verify identity (phone number or customer ID) before any account action.
- Enumerate all `line_ids`; inspect each with the detail lookup.
- If the user is roaming and the matching Active line has `roaming_enabled: false`, offer to enable roaming (confirm cost and get consent).
- A Suspended or contract-ended line never explains the reported working number; state this explicitly.

## Expected Status-Bar Signatures
- Healthy: signal Excellent, network type 5G/4G, mobile data Enabled, no Data Saver, no VPN.
- Blocked connectivity: Airplane Mode ON ⇒ cellular connection `no_service`, network type `none`.

## Verification Contract
- Never declare resolution from a settings change alone.
- Require a tool-confirmed status snapshot and/or Speed Test Result after each change.
- Success = measured rating meets the user's stated target (e.g. 'Excellent').
