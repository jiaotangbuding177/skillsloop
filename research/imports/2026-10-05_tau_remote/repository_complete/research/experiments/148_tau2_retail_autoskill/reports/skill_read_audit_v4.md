# v4-B1 技能读取审计（真实原生 read 调用）

- 扫描目录：`/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs/autoskill_library`
- 会话数（含 turn_000 prompt）：543；其中有 sqlite 归档：523
- 首轮 prompt 含 `$技能` 引用（v6）：206/543
- **真实读取技能的会话：191/543 = 0.3517**（有归档口径：191/523 = 0.3652）

## 各技能被读取次数（会话口径）

- `retail_order_support_orchestration`: 172
- `retail_order_exchange_and_change_workflow`: 172
- `retail_product_order_orchestration`: 171
- `retailorderlookup`: 18
- `find-and-confirm-cheapest-mechanical-keyboard-exchange`: 17
- `retailordermodificationlookup`: 16
- `retailinventorycheck`: 16
- `retailordermodificationandcancellationprocedurewithpaymentassist`: 16
- `browser-automation`: 1

## 逐任务

| task | sessions | triggered | skills |
|---|---|---|---|
| task_100 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_101 | 14 | 6 | retail_order_exchange_and_change_workflow×6, retail_order_support_orchestration×6, retail_product_order_orchestration×6 |
| task_102 | 14 | 6 | retail_order_exchange_and_change_workflow×6, retail_order_support_orchestration×6, retail_product_order_orchestration×6 |
| task_108 | 14 | 6 | retail_order_exchange_and_change_workflow×6, retail_order_support_orchestration×6, retail_product_order_orchestration×6 |
| task_111 | 14 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_12 | 20 | 6 | find-and-confirm-cheapest-mechanical-keyboard-exchange×2, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×2, retailorderlookup×2, retailordermodificationandcancellationprocedurewithpaymentassist×2, retailordermodificationlookup×2 |
| task_17 | 14 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_18 | 15 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_26 | 14 | 5 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailorderlookup×1 |
| task_27 | 14 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_32 | 14 | 4 | retail_order_exchange_and_change_workflow×3, retail_order_support_orchestration×3, retail_product_order_orchestration×3, retailorderlookup×1 |
| task_33 | 13 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_36 | 14 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_38 | 14 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_39 | 13 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_40 | 13 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_42 | 13 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationlookup×1 |
| task_45 | 19 | 7 | find-and-confirm-cheapest-mechanical-keyboard-exchange×3, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×2, retailorderlookup×2, retailordermodificationandcancellationprocedurewithpaymentassist×3, retailordermodificationlookup×2 |
| task_49 | 15 | 5 | browser-automation×1, find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_5 | 14 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×3, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_51 | 13 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_53 | 13 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_55 | 13 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_56 | 13 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_60 | 14 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_61 | 13 | 5 | retail_order_exchange_and_change_workflow×5, retail_order_support_orchestration×5, retail_product_order_orchestration×5 |
| task_62 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_64 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_65 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_68 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_70 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_71 | 13 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_74 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_77 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_79 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_86 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_9 | 15 | 5 | find-and-confirm-cheapest-mechanical-keyboard-exchange×1, retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4, retailinventorycheck×1, retailorderlookup×1, retailordermodificationandcancellationprocedurewithpaymentassist×1, retailordermodificationlookup×1 |
| task_90 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_94 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |
| task_97 | 12 | 4 | retail_order_exchange_and_change_workflow×4, retail_order_support_orchestration×4, retail_product_order_orchestration×4 |

> 口径说明：本扫描覆盖 `runs/autoskill_library/` 下的**全部历史会话**（含 v1/v2 旧批次、smoke、被杀的未完成尝试），故总数为 543 且含旧库技能名。**正式 v4-B1 结论采用“已完成 160 场 sim ↔ 会话 ±300s 匹配”口径：159/160 = 99.4%**，见 `reports/final_report_v4.md` §3 与 `reports/v4_paired_summary.json` 的 skill_read 段。
