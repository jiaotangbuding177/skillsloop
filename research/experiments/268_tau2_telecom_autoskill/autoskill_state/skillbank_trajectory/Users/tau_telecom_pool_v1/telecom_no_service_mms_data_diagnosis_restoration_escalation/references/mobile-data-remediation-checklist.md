# Mobile-Data Remediation Checklist (ordered)

Apply one item per turn; after each change, re-request status bar + network status and confirm the targeted field actually flipped.

1. Account/line sanity: account active, affected line active (not suspended), correct line selected when several exist.
2. Airplane Mode = ON -> instruct user to turn it OFF. Confirm: Airplane Mode OFF, cellular connection connected, network type present.
3. Mobile Data = disabled -> instruct user to turn it ON. Confirm: Mobile Data Enabled = Yes.
4. No signal / no network type despite airplane off -> network mode preference (e.g., force 5G/LTE), SIM reseat, reboot; then re-read.
5. Data Saver / per-app restrictions / VPN active -> disable and re-test.
6. Roaming OFF while the user is roaming -> enable roaming after confirming the line allows it.
7. APN missing or wrong -> reset to carrier default; then re-read.
8. Usage at or above plan limit (used >= data_limit_gb) -> offer data refuel or plan change; verify with get_data_usage afterward.
9. Connectivity restored -> ask for a speed test or page load; treat an Excellent rating as success.
10. Speed still poor after connectivity restored -> return to deeper network settings and escalate as needed.

Verification fields to capture on every readout: Airplane Mode, SIM Card Status, Cellular Connection, Cellular Signal, Cellular Network Type, Mobile Data Enabled, Data Roaming Enabled, Wi-Fi Radio, Wi-Fi Connected, battery.