# Connectivity / MMS Troubleshooting Checklist

## Tier 1 - Identity & baseline
- Verify account via phone number (get_customer_by_phone).
- Status bar: signal, network type (5G/4G/2G), data on/off, airplane mode.
- Network status: SIM active, cellular connected, mobile data, roaming, Wi-Fi.

## Tier 2 - MMS-specific
- APN name and MMSC URL present/correct.
- Wi-Fi Calling status.
- Messaging app permissions (SMS, storage). Apply missing permission, then RE-TEST.

## Tier 3 - Data-interfering settings
- Data saver / VPN off.
- Re-confirm airplane mode off and APN selected.
- Reset APN settings, then reboot; re-test data.

## Tier 4 - SIM
- SIM active, no Missing/Locked warning.

## Tier 5 - Account/line/plan (escalation)
- Resolve affected line; read line details, data usage, plan limit.
- If data_used_gb >= data_limit_gb: overage silently blocks data & MMS.
- Offer refuel (per-GB price, max allowed); confirm total before charging.

## Verification gate
- Fix is complete ONLY when a tool confirms speed test success AND MMS can send.
