# MMS Troubleshooting Checklist

## Phase 1 - Verify
- get_customer_by_phone(phone_number) -> customer_id, line_ids
- get_details_by_id(id) for each line -> pick ACTIVE line matching reported number
- If abroad and roaming_enabled=false -> enable_roaming(customer_id, line_id)

## Phase 2 - Baseline device state
- check_network_status -> account for Airplane Mode, SIM status, network type, signal, data
- check_apn_settings -> confirm APN name and MMSC URL

## Phase 3 - Remediate ONE at a time (verify after each)
1. Airplane Mode ON -> set OFF
2. SIM missing -> reseat_sim_card
3. Network < 3G (e.g. 2G) -> set_network_mode(4g_5g_preferred)
4. Wi-Fi Calling ON -> set_wifi_calling(OFF)
5. check_app_permissions('messaging') -> confirm storage + sms granted

## Phase 4 - Verify fix
- Attempt send / can_send_mms()
- If fail: re-check check_apn_settings (MMSC URL)

## Phase 5 - Escalate
- If still failing after all checks: transfer_to_human_agent(summary)
- summary must list each remediation + verified result + current failing check

## Lessons
- Confirm every change with a tool before claiming progress.
- Do not batch device changes; sequence them when the customer handles one action at a time.
- Only act on the active line; skip suspended lines.