# 分集与工作流覆盖审计（τ²-bench Retail v1.0.1 文本）

- 生成：2026-10-02，脚本 `scripts/audit_split.py`（可重跑）。
- 输入（冻结哈希见 `versions.json`）：`tasks.json` `8e03ebce…`、`split_tasks.json` `ed0580ec…`、`policy.md` `2c9652af…`、`db.json` `413a6516…`。
- 输出：`split_manifest.json`（公共摘要）、`private/workflow_coverage_detail.json`（逐题明细）。
- 声明：gold 动作名仅用于本研究者侧覆盖审计；其内容不流入 Collector、AutoSkill 或 Consumer 的任何输入。

## 1. 结构校验（全部通过）

- train 74 / test 40 / base 114；全部 ID 有效；train ∩ test = ∅；base = train ∪ test = 全部任务。
- test 中包含 task 5 与 task 9（后者按用户要求不得用于调提示/演示/生成技能）。

## 2. 操作类别覆盖（按主操作：cancel > return > exchange > modify_payment > modify_items > modify_address > escalate > read_only）

| 主类别 | train（74） | test（40） | 说明 |
| --- | --- | --- | --- |
| cancel | 13 | 5 | 取消未发货订单 |
| return | 19 | 6 | 已交付退货 |
| exchange | 17 | 10 | 已交付换货 |
| modify_payment | 0 | 1 | **演化侧完全无覆盖** |
| modify_items | 15 | 11 | 未发货改商品 |
| modify_address | 4 | 3 | 收货地址修改（pending 或用户地址） |
| escalate | 2 | 1 | 转人工 |
| read_only | 4 | 3 | 以查询/确认收尾 |

要点：除 `modify_payment` 外，test 的每个主类在演化集都有同类任务可作学习材料；`modify_payment`（test task 40）在 train 与演化集都不存在，B1 不可能从历史中学到该类操作，报告时单列。

## 3. dev 选择（seed=42，确定性）

规则：按主操作分桶，桶顺序 [cancel, return, exchange, modify_payment, modify_items, modify_address]；对每桶的升序 train id 用 `random.Random(42)` 洗牌取首个；取满 4 个为止。结果：

| dev | 类别 | 涉及动作 |
| --- | --- | --- |
| 69 | cancel | cancel_pending_order |
| 28 | return | return_delivered_order_items |
| 8 | exchange | exchange_delivered_order_items |
| 112 | modify_items | modify_order_items（含 modify_address 复合） |

演化集 = train − dev = 70 题（id 列表见 `split_manifest.json`）。dev 仅用于管线联调，不进入正式统计。

## 4. 相关性发现（官方划分并非按订单/场景隔离）

1. **订单交叉**：45 个订单 ID 同时出现在 train 与 test；**29/40** test 题与 train 共享至少一个订单。例：
   - `#W6390527`：train {6,7,8} ↔ test {5,9}
   - `#W5490111`、`#W7387996`：train {10,11,13,14} ↔ test {12}
   - 无共享订单的 11 题：39, 40, 64, 65, 74, 77, 79, 90, 100, 102, 108
2. **近似同题改写**（同动作签名且指令相似度 ≥0.5）：train 93 ↔ test 94（**0.993**，同 exchange 签名）；train 72 ↔ test 71（0.831）；train 96 ↔ test 97（0.791）；train 6/7/8 ↔ test 9（0.685/0.755/0.710，同订单族）。
3. **用户维度**：从 gold 参数抽取到的 `user_*` 字面键在 train/test 间无共享（0 组）。该检查只覆盖字面出现 user_* 的参数，不是完整的用户级隔离证明。
4. **共同环境**：同域公共政策、官方工具集与同一初始 `db.json` 为两组共同环境；按用户要求不因此排除，但在报告与解读中保留。

## 5. 局限

- 官方划分为"同域相关但不同题"，同订单族/近似题的存在意味着 B1 的收益可能部分来自同族相关迁移；不得当作跨域泛化证据。
- 技能若携带个案参数（订单号等）可能在共享订单族上直接命中，冻结清单中单列诊断，不当作通用方法。
- 本审计为程序化轻量检查（动作名集合、difflib 文本相似度、参数键抽取），不是穷尽人工核对；如需更强的语义去重需另立方法与预算。
- task 9 未用于调提示、演示或生成技能；本目录目前未接触该题。

## 6. 对实验设计的含义

- 演化 70 题覆盖 test 8 个主类中的 7 个；报告需附按主分类的任务数与成绩分项。
- 主指标仍按"题"聚合（B0/B1 配对），不按订单族合并；同族效应在讨论部分单独说明。
- `modify_payment` 与"无共享订单"的 11 题可预先标记为最接近分布外（OOD）的测试子集，补充报告但不改主口径。
