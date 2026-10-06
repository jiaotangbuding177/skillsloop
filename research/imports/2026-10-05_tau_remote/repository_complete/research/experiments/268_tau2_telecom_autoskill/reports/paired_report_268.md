# v4 配对评测报告：B0（无技能）vs B1（frozen_skills_v2 + 原生 $技能引用）

- 生成时间：2026-10-05T04:45:08
- B0 文件：`runs/test/no_skill.json`；B1 文件：`runs/test/autoskill_library.json`（results file mtime 2026-10-05T03:51:23）

## 组统计

| 指标 | B0 无技能 | B1 有技能 |
|---|---|---|
| 完成场次 | 160 | 160 |
| 平均奖励 | 0.7937 | 0.7438 |
| pass@1（单场=1.0 比例） | 0.7937 | 0.7438 |
| 任务数 | 40 | 40 |
| 任务均值（先平均再汇总） | 0.7937 | 0.7438 |
| 全 4 场全过任务 | 22 | 17 |
| 全 4 场全 0 任务 | 1 | 0 |
| 平均时长(s) | 749.4 | 776.2 |

## 配对（同 task 同 trial）

- 配对数：160；B1 更好 23；B0 更好 31；持平 106
- 平均差（B1−B0）：-0.05
- 精确符号检验双侧 p：0.340891
- 任务级 bootstrap 95% CI：-0.1625 ~ 0.0563

## 技能读取（真实原生 read 调用）

- B1 完成场次：160；匹配到会话：160（未匹配 0）
- 其中真实读取技能的会话：160（匹配口径 1.0）
- 读写技能次数（会话口径）：{'telecom_no_service_mms_data_diagnosis_restoration_escalation': 160, 'browser-automation': 1}

## 逐任务

| task | B0 均值 | B1 均值 | Δ(B1−B0) | B0 n | B1 n |
|---|---|---|---|---|---|
| [mms_issue]airplane_mode_on|bad_network_preference|bad_wifi_calling|break_apn_mms_setting|break_app_both_permissions|unseat_sim_card|user_abroad_roaming_enabled_off[PERSONA:Hard] | 0.25 | 1.0 | 0.75 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_network_preference|bad_wifi_calling|break_apn_mms_setting|break_app_sms_permission|data_mode_off|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_disabled_on[PERSONA:None] | 0.25 | 0.75 | 0.5 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_network_preference|bad_wifi_calling|break_apn_mms_setting|break_app_storage_permission|data_mode_off|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_disabled_on[PERSONA:Easy] | 0.25 | 0.75 | 0.5 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_network_preference|break_app_both_permissions|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_disabled_on[PERSONA:Hard] | 0.25 | 0.75 | 0.5 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_network_preference|break_app_storage_permission|data_mode_off|user_abroad_roaming_enabled_off[PERSONA:Easy] | 0.5 | 0.25 | -0.25 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_wifi_calling|break_app_both_permissions|data_mode_off|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_enabled_off[PERSONA:None] | 0.75 | 0.25 | -0.5 | 4 | 4 |
| [mms_issue]airplane_mode_on|bad_wifi_calling|user_abroad_roaming_enabled_off[PERSONA:Easy] | 1.0 | 0.25 | -0.75 | 4 | 4 |
| [mms_issue]airplane_mode_on|break_app_both_permissions[PERSONA:Hard] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [mms_issue]airplane_mode_on|break_app_both_permissions|data_usage_exceeded|user_abroad_roaming_disabled_off[PERSONA:None] | 0.75 | 0.75 | 0.0 | 4 | 4 |
| [mms_issue]bad_network_preference|bad_wifi_calling|break_app_sms_permission|data_mode_off|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_enabled_off[PERSONA:Easy] | 1.0 | 0.5 | -0.5 | 4 | 4 |
| [mms_issue]bad_network_preference|break_app_both_permissions[PERSONA:Easy] | 1.0 | 0.75 | -0.25 | 4 | 4 |
| [mms_issue]bad_network_preference|break_app_sms_permission|user_abroad_roaming_disabled_on[PERSONA:Hard] | 0.25 | 0.5 | 0.25 | 4 | 4 |
| [mms_issue]bad_network_preference|data_mode_off|user_abroad_roaming_disabled_on[PERSONA:None] | 0.0 | 0.5 | 0.5 | 4 | 4 |
| [mms_issue]bad_wifi_calling|break_apn_mms_setting|break_app_both_permissions|data_mode_off|data_usage_exceeded|user_abroad_roaming_disabled_off[PERSONA:None] | 0.75 | 0.5 | -0.25 | 4 | 4 |
| [mms_issue]break_apn_mms_setting|user_abroad_roaming_enabled_off[PERSONA:Hard] | 0.75 | 0.25 | -0.5 | 4 | 4 |
| [mms_issue]break_app_sms_permission|data_mode_off[PERSONA:None] | 1.0 | 0.75 | -0.25 | 4 | 4 |
| [mobile_data_issue]airplane_mode_on|bad_network_preference|bad_vpn|data_mode_off|data_saver_mode_on|data_usage_exceeded|user_abroad_roaming_enabled_off[PERSONA:Easy] | 0.5 | 0.75 | 0.25 | 4 | 4 |
| [mobile_data_issue]airplane_mode_on|bad_network_preference|data_mode_off|data_saver_mode_on[PERSONA:Hard] | 1.0 | 0.25 | -0.75 | 4 | 4 |
| [mobile_data_issue]airplane_mode_on|data_mode_off|data_saver_mode_on|data_usage_exceeded|user_abroad_roaming_enabled_off[PERSONA:Hard] | 1.0 | 0.25 | -0.75 | 4 | 4 |
| [mobile_data_issue]airplane_mode_on|data_saver_mode_on|user_abroad_roaming_disabled_on[PERSONA:None] | 0.75 | 0.75 | 0.0 | 4 | 4 |
| [mobile_data_issue]bad_network_preference|bad_vpn|data_mode_off|data_saver_mode_on|data_usage_exceeded|user_abroad_roaming_enabled_off[PERSONA:Easy] | 0.75 | 0.75 | 0.0 | 4 | 4 |
| [mobile_data_issue]bad_network_preference|bad_vpn|data_saver_mode_on|data_usage_exceeded|user_abroad_roaming_disabled_off[PERSONA:Easy] | 1.0 | 0.5 | -0.5 | 4 | 4 |
| [mobile_data_issue]bad_network_preference|bad_vpn|user_abroad_roaming_disabled_off[PERSONA:Hard] | 0.75 | 0.75 | 0.0 | 4 | 4 |
| [mobile_data_issue]bad_vpn|data_mode_off|data_usage_exceeded|user_abroad_roaming_disabled_off[PERSONA:None] | 1.0 | 0.75 | -0.25 | 4 | 4 |
| [mobile_data_issue]data_saver_mode_on|user_abroad_roaming_enabled_off[PERSONA:Easy] | 1.0 | 0.5 | -0.5 | 4 | 4 |
| [service_issue]airplane_mode_on|break_apn_settings|contract_end_suspension|lock_sim_card_pin[PERSONA:None] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|break_apn_settings|contract_end_suspension|lock_sim_card_pin|unseat_sim_card[PERSONA:Easy] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|break_apn_settings|lock_sim_card_pin|overdue_bill_suspension[PERSONA:Hard] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|break_apn_settings|lock_sim_card_pin|unseat_sim_card[PERSONA:None] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|break_apn_settings|overdue_bill_suspension[PERSONA:None] | 0.75 | 1.0 | 0.25 | 4 | 4 |
| [service_issue]airplane_mode_on|contract_end_suspension|lock_sim_card_pin|unseat_sim_card[PERSONA:Hard] | 0.75 | 1.0 | 0.25 | 4 | 4 |
| [service_issue]airplane_mode_on|lock_sim_card_pin[PERSONA:Easy] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|lock_sim_card_pin|overdue_bill_suspension[PERSONA:Easy] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]airplane_mode_on|overdue_bill_suspension[PERSONA:None] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]break_apn_settings|contract_end_suspension|lock_sim_card_pin[PERSONA:Hard] | 0.75 | 1.0 | 0.25 | 4 | 4 |
| [service_issue]break_apn_settings|contract_end_suspension|lock_sim_card_pin|unseat_sim_card[PERSONA:Hard] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]break_apn_settings|lock_sim_card_pin[PERSONA:None] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]break_apn_settings|lock_sim_card_pin|overdue_bill_suspension[PERSONA:Easy] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]contract_end_suspension|unseat_sim_card[PERSONA:Hard] | 1.0 | 1.0 | 0.0 | 4 | 4 |
| [service_issue]overdue_bill_suspension|unseat_sim_card[PERSONA:Easy] | 1.0 | 1.0 | 0.0 | 4 | 4 |
