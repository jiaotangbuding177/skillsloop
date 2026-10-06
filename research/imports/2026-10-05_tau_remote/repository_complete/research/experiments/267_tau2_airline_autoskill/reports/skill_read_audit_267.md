# v4-B1 技能读取审计（真实原生 read 调用）

- 扫描目录：`runs/autoskill_library`
- 会话数（含 turn_000 prompt）：82；其中有 sqlite 归档：82
- 首轮 prompt 含 `$技能` 引用（v6）：82/82
- **真实读取技能的会话：82/82 = 1.0**（有归档口径：82/82 = 1.0）

## 各技能被读取次数（会话口径）

- `airline_reservation_cancellation_refund_policy_check`: 82

## 逐任务

| task | sessions | triggered | skills |
|---|---|---|---|
| task_13 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_16 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_18 | 6 | 6 | airline_reservation_cancellation_refund_policy_check×6 |
| task_19 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_2 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_22 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_24 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_25 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_26 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_29 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_30 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_31 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_32 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_35 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_37 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_44 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_45 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_48 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_6 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
| task_8 | 4 | 4 | airline_reservation_cancellation_refund_policy_check×4 |
