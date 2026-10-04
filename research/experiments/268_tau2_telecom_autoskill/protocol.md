# 协议：AutoSkill × τ²-bench Telecom（文本域）

- 实验目录：`research/experiments/268_tau2_telecom_autoskill`
- 创建：2026-10-04；状态：**准备中**（管线自 148/267 适配，dev 联调后进入付费批次）
- 版本固定见 `versions.json`；分集审计见 `split_manifest.json` 与 `private/telecom_coverage_detail.json`

## 1. 目标与边界

目标：在 τ²-bench 文本 Telecom 域重复 148 的"多轮历史 → 官方 AutoSkill 沉淀 → 冻结技能库 → 无/有技能配对评测"基线。

用户已确认（2026-10-04）：telecom 用**当前 deepseek-flash**推进；接受 flash 级模型在本域绝对分可能很低的现实（域难度高、用户模拟器带 30 个工具），配对相对差为观察对象；banking_knowledge 暂缓（无官方 split）。

不做：与 148/267 相同的排除清单（voice/oracle/solo、训练、评议期技能更新、多 benchmark 混跑等）。

## 2. 版本固定与架构

- τ²-bench 固定 v1.0.1（`fc0055dc`）；vendor 由 148 同一 pinned checkout 逐字节复制；telecom 冻结数据（tasks_full/split/policy/manual/db/user_db）在 `inputs/` 并记录 sha256。
- 架构同 148/267（未改 vendor）：挂起-转发 MCP bridge（τ² 唯一执行工具调用）；消费者 OpenClaw；v6 原生 `$技能` 引用；判分补丁运行时生效；relay 独立端口 **8181**、独立 `ledger/`。
- 本域特点：奖励 100% 由 **ENV_ASSERTION**（状态断言）决定（2253 题）或 ENV_ASSERTION+ACTION（32 题）；**用户模拟器带 30 个用户侧工具**（模拟客户操作自己设备），消费者 13 个域工具。

## 3. 数据划分（以 `split_manifest.json` 为准）

- 官方 split：train 74 / test 40 / base 114（另有 small 20 子集，本实验不用；full 2285 不用）。
- 任务 ID 结构：`[类别]子问题路径[PERSONA:难度]`；类别 = mms_issue(49) / mobile_data_issue(36) / service_issue(29)；persona = None/Easy/Hard。
- **dev = 4**：每类别 1 题（seed=42 确定性），第 4 题 round-robin 回 mms；当前选定：
  - `[mms_issue]break_apn_mms_setting|data_mode_off|user_abroad_roaming_disabled_on[PERSONA:Hard]`
  - `[mobile_data_issue]airplane_mode_on|user_abroad_roaming_enabled_off[PERSONA:None]`
  - `[service_issue]airplane_mode_on|lock_sim_card_pin|unseat_sim_card[PERSONA:Hard]`
  - `[mms_issue]airplane_mode_on|...|user_abroad_roaming_disabled_off[PERSONA:Easy]`
- **演化集 = 其余 70 题**（每题 1 条）；**正式测试 = test 40 题**（4 trials × 2 组 = 320 场）。
- 审计发现：train/test 共享 19 个故障组件（airplane_mode_on、bad_network_preference 等，域内固有）；指令为类别级模板（模板数已记录）；test 类别全部被演化集覆盖。

## 4. 运行纪律（继承 148/267）

- 挂起-转发保证写操作只执行一次；ENV_ASSERTION 依赖环境状态，轨迹重放语义与 148 相同。
- 两组唯一差异是 `skills/`；失败如实记录；不伪造/覆盖/挑分；账本独立，上限 60,000/relay 实例。
- 磁盘与进程风险沿用 148 教训（C: 盘监控 + 安全清理脚本）。

## 5. 批次计划

1. dev 联调（4 题，含用户侧工具链验收）→ 2. 演化采集（70 题）→ 3. 学习与冻结 → 4. 配对评测（40×4×2=320 场）→ 5. 报告。

预计规模：dev 4 + 采集 70 + 评测 320 ≈ 394 场运行（与 148 同量级；单场时长可能更长）。
