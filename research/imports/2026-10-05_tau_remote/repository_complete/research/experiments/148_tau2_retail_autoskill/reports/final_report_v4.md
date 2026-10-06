# 148 最终实验报告（v4 配对批次）：AutoSkill × τ²-bench Retail

- 生成时间：2026-10-04（北京时间）
- 状态：**v4 配对评测完成**（B0 无技能 160/160；B1 有技能 160/160）
- 本报告取代 `reports/experiment_report.md`（旧 GLM 消费批次）中关于"技能收益"的结论；旧报告与旧批次结果保留为历史，不删除。
- 数据来源：`runs/test_v4/no_skill.json`、`runs/test_v4/autoskill_library.json`、`reports/skill_read_audit_v4.json`、`ledger/requests.jsonl`

## 0. 结论摘要（TL;DR）

1. **B1（有技能）= 134/160 场 reward 1.0（均值 0.8375）；B0（无技能）= 126/160（均值 0.7875）。差值 +5.0pp。**
2. 配对（同 task 同 trial，160 对）：B1 更好 20、B0 更好 12、持平 128；确切符号检验双侧 p = 0.215；任务级 bootstrap 95% CI = [-2.5pp, +12.5pp]（含 0）。
3. 任务级（40 题）：改善 15、退步 7、持平 18；确切符号检验 p = 0.134。
4. **技能真实读取率 159/160 = 99.4%**（原生 `read` 工具真实打开 `skills/<name>/SKILL.md`，经 sqlite 原生事件与抽样直接复核）。这修复了此前两个批次（v1、v2 旧库）真实读取率为 0 的处置缺陷。
5. **结论口径**：方向为正、未达统计显著。本轮首先证明了"技能确实被读取并进入上下文"（处理强度），+5.0pp 只能作为初步正向证据；不能据此宣称"技能提升性能"已成立，也不能与 τ² 论文数字直接排名。

## 1. 实验设置（v4 批次）

| 项目 | 取值 |
|---|---|
| 基准 | τ²-bench v1.0.1（fc0055dc）retail 文本域；含 tau3 期 Task Quality 修订，不与论文数字直接可比 |
| 拆集 | 演化 70 题（采集）／测试 40 题（评测）；相关性审计见 `workflow_split_audit.md` |
| 评测规模 | 测试 40 题 × 4 trials × 2 组 = 320 场 |
| 消费者（agent） | deepseek-flash（DeepSeek 官方 API，经本地 8141 中继 consumer 路由） |
| 用户模拟器 | deepseek-flash（同一中继 user 路由） |
| 判分（NL assertions） | glm-4-flash（经 judge 路由；含 fence-strip 与重试补丁） |
| 技能嵌入/学习 | ecnu-embedding-small（仅用于 AutoSkill 技能学习，不参与评测） |
| 技能库 | `frozen_skills_v2/`：3 个流程型技能 + 27 个资源文件，sha256 清单（`frozen_skills_v2_manifest.json`），namespace `tau_retail_pool_v2`，extractor = AutoSkill 离线 agentic 轨迹路径，70/70 处理成功 |
| 技能注入机制 v6 | B1 首轮 prompt 顶部注 `Before acting, consult the store's reusable skills: $retail_order_exchange_and_change_workflow $retail_order_support_orchestration $retail_product_order_orchestration`；由 OpenClaw 原生 `read` 工具按需读取正文 |
| 两组的唯一差异 | B1 工作区含 `skills/`（冻结库）；B0 为空目录。工具、提示、harness、评分完全一致 |
| 运行质量 | 两组各 160 场均正常终止（全部 user_stop）；无基建失败、无 reward=None；最大并发 12 |

## 2. 主要结果

### 2.1 组统计

| 指标 | B0 无技能 | B1 有技能（frozen_skills_v2） |
|---|---|---|
| 完成场次 | 160 | 160 |
| 平均 reward | **0.7875** | **0.8375** |
| pass@1（单场 = 1.0 比例） | 78.75% | 83.75% |
| 非零场次 | 126 | 134 |
| 全 4 场全过任务 | 22/40 | 25/40 |
| 全 4 场全 0 任务 | 1/40 | 1/40 |
| 平均单场时长 | 468s | 601s |

### 2.2 配对（task, trial）

- 配对数 160；B1 更好 20 ／ B0 更好 12 ／ 持平 128
- 平均差（B1−B0）= **+0.05**；确切符号检验双侧 p = 0.215
- 任务级 bootstrap（10k 重采样）95% CI：**[-0.025, +0.125]**

### 2.3 任务级变化（40 题，按题均值）

- 改善 15 ／ 退步 7 ／ 持平 18（p = 0.134）
- 最大改善：task 64（0.25→1.0）、task 108（0.25→0.75）、task 100/101/102/36/49（0.75→1.0）、task 27（0→0.25）
- 最大退步：task 111/39/60（1.0→0.5）、task 38（0.25→0）、task 55/68/77（1.0→0.75）
- 完整逐题表：`reports/v4_paired_report.md`

## 3. 技能读取审计（处理强度验证）

- 方法：对每个 B1 会话归档的 OpenClaw sqlite（`openclaw_state_archive/agents/main/agent/openclaw-agent.sqlite`）只读扫描 `transcript_events`（assistant `toolCall`/`toolResult`）与 `trajectory_runtime_events`（`tool.call`），匹配真实 `read` 调用路径 `skills/<name>/SKILL.md`；脚本 `scripts/scan_skill_reads.py`，另用 `scripts/verify_skill_reads_direct.py` 抽样直接复核原始记录。
- 结果（v4 B1 已完成 160 场，sim↔session 按启动时间 ±300s 最近邻匹配，160/160 全部匹配）：
  - **真实读取技能的会话：159/160 = 99.4%**
  - 3 个技能各自被读取约 158–159 场（多数会话读完整个库）
  - 唯一未读取：task 32 trial 0（该场仍得 1.0）
  - 噪音：1 个会话读取了 OpenClaw 插件技能 browser-automation（库外，不计入）
- 对照（历史批次，同一方法）：v1 批 0/162、v2 旧库批 0/162（当时快照审计）。差异来自 v6 原生 `$技能` 引用：含引用的 188 个会话中 172 个真实读取（约 91%）；不含引用的会话基本不读。
- 直接复核样例（原始 sqlite）：task 102 trial 1、task 12 trial 1、task 62 trial 2 均检出 `read ... skills/<name>/SKILL.md` 的原生 toolCall 事件。

## 4. 修复链与历史（不覆盖旧负结果）

1. v1/v2 批次：技能仅出现在系统提示可读列表中，真实读取 0/160+（诊断见历史审计 `reports/skill_trigger_rate_v2.md`）。
2. 根因修复 v6：在首轮 prompt 中显式给出 `$技能名` 引用，OpenClaw 首轮播报"行动前读取被引用的 SKILL.md"；smoke 实测后进入 v4 全量。
3. v4 批次同时更换消费者与用户模拟器为 deepseek-flash（用户指定），两组同模型重跑，得到本报告结果。
4. 早期 GLM 消费批次的"无技能收益"结论（`reports/experiment_report.md`、`final_review_b0/b1.md`）保留为历史；其 0 读取缺陷已在 v6/v4 修复，因此旧的"无增益"不能作为最终结论，同理新 +5.0pp 也不能替代更大样本。

## 5. 限制与不可比声明

- τ²-bench v1.0.1 含 tau3 期修订（114 题 reward_basis/user_scenario 全面修订）：本结果与 τ² 论文排行榜数字**不可直接比较**。
- 判分模型为 glm-4-flash（代替原版 gpt-4o），判分偏差未知；NL 判分异常已以 fence-strip+重试兜底，仍有 1,037 次 judge 请求计入账本。
- 评测为单 seed（42），40 题 × 4 trials 的统计功效有限；配对 CI 含 0。
- B1 平均时长高 28%（601s vs 468s）：读技能与更长轨迹带来开销，速度—收益权衡未评估。
- 1 场未读取技能（task 32 trial 0）；1 场读取了库外插件技能。
- 技能库为 3 个流程型技能（AutoSkill 离线轨迹提取），非人类审核库；单库版本结论不外推到其他库。

## 6. 产物清单

| 产物 | 路径 |
|---|---|
| B0 结果 | `runs/test_v4/no_skill.json` |
| B1 结果 | `runs/test_v4/autoskill_library.json`（旧库 8 场单列 `autoskill_library_OLDlib_8partial.json`） |
| 技能读取审计 | `reports/skill_read_audit_v4.json` / `.md` |
| 配对统计 | `reports/v4_paired_summary.json` / `reports/v4_paired_report.md` |
| 扫描/配对/复核脚本 | `scripts/scan_skill_reads.py`、`scripts/paired_summary_v4.py`、`scripts/verify_skill_reads_direct.py`、`scripts/task_level_cuts_v4.py`、`scripts/cleanup_native_state.py` |
| 请求账本 | `ledger/requests.jsonl`（累计 36,359 次：consumer 20,253 / user 14,469 / judge 1,037 / autoskill 205 / embed 370 / plus 25） |
| 原生工具调用捕捉 | 7,350 次 |

## 7. 下一步建议（未实施，供讨论）

1. 扩大样本（追加 trials 或引入第二 seed）以收紧 CI，检验 +5pp 的稳健性。
2. 对改善/退步任务（64/108 vs 111/39/60）做逐场轨迹分析：技能读取后行为差异在哪一步。
3. 技能库消融：单技能/单文件移除，检验各技能贡献（当前会话基本读全库，无法区分单技能效应）。
4. 基线对照：可加入"技能只列不读"控件组，量化"可见但未用"的上界。
