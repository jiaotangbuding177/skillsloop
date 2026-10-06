# MMS Diagnostic Ladder (device -> network -> config -> carrier)

Run layers in order; after every change re-run check_status_bar + check_network_status and only close after can_send_mms() succeeds.

## Layer 1 — Account/line
- get_customer_by_phone -> get_customer_by_id (account_status, line_ids, selected line, symptom).

## Layer 2 — Radio/SIM
- Symptom: Airplane Mode ON, SIM 'missing', no_service.
- Fix: turn Airplane Mode OFF; reseat_sim_card().
- Pass: airplane OFF, SIM 'active', connection 'connected'.

## Layer 3 — Network capability
- Symptom: 2G / no 3G+; Mobile Data Disabled.
- Fix: set network mode 4g_5g_preferred (or 4g_only); enable Mobile Data.
- Pass: 4G/5G, data enabled.

## Layer 4 — MMS config
- check_apn_settings(): MMSC URL must be set (not 'Not Set') -> reset_apn_settings() then reboot_device().
- Wi-Fi Calling must be OFF -> toggle_wifi_calling().
- check_app_permissions('messaging'): needs BOTH sms and storage -> grant_app_permission(app_name='messaging', permission='storage').
- Pass: MMSC set, Wi-Fi Calling OFF, sms+storage granted.

## Layer 5 — Carrier provisioning
- If can_send_mms() fails and data shows enabled but 'No Connection': get_details_by_id (line, plan) + get_data_usage.
- If data_used_gb >= data_limit_gb -> data cut off; confirm amount & price, refuel_data(customer_id, line_id, gb_amount) respecting max addable.
- Pass: can_send_mms() returns success.

## Guardrails
- Never claim resolved without can_send_mms() success.
- APN reset only applies after reboot.
- Get consent and state exact charge before billable actions.