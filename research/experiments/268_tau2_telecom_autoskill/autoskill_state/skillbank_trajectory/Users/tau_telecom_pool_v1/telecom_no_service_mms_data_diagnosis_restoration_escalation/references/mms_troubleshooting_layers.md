# MMS Failure Escalation Layers

Apply in order; re-test sending after each layer and only advance on continued failure.

1. Account/line state
   - Resolve account, confirm active line, check `roaming_enabled`.
   - If abroad and roaming disabled -> enable roaming.
2. Device refresh
   - Restart device; pick up new network settings.
3. Device diagnostics
   - Status bar icons, signal bars, network type, airplane mode, mobile data, Wi-Fi.
   - SIM card status.
4. SIM remediation
   - If SIM missing -> reseat SIM; confirm signal returns.
5. Messaging configuration
   - APN name and MMSC URL presence.
   - Wi-Fi Calling status (usually not the MMS cause when OFF).
6. App permissions
   - Messaging app needs `storage` (access photos) and `sms` (send).
   - Grant any missing permission, then re-test.
7. Confirmation
   - Only close after a send test reports success; recap all changes.

Guardrails:
- Re-test after every change; never declare fixed on assumption.
- Do not touch unrelated/suspended lines without explicit consent.
- Re-fetch state on tool error before retrying.