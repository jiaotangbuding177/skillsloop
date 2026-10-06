# 协议：AutoSkill × τ²-bench Airline（文本域）

- 实验目录：`research/experiments/267_tau2_airline_autoskill`
- 创建：2026-10-04；状态：**准备中**（管线自 148 适配，dev 联调后进入付费批次）
- 版本固定见 `versions.json`；分集审计见 `split_manifest.json` 与 `private/airline_coverage_detail.json`

## 1. 目标与不做什么

目标：在 τ²-bench 文本 Airline 域重复 148 的"多轮历史 → 官方 AutoSkill 沉淀 → 冻结技能库 → 同一 Agent 无/有技能配对评测"基线，回答：

1. 从多轮历史沉淀的 skills 是否提高相关新任务的完成率？
2. 在结果不变差的情况下，是否减少沟通与重复操作？

用户已确认（2026-10-04）：airline 与 telecom 两域用**当前 deepseek-flash** 作为消费者与用户模拟器推进；banking_knowledge 暂缓（无官方 train/test 划分）。不预设涨分；空库、未读取技能、持平或下降都如实报告。

不做：SkillsLoop 轨迹恢复算法、Trace2Skill、人工切碎/交错对话、模型训练、评测期技能更新、多 benchmark 混跑；不做 voice/audio-native、oracle-plan（llm_agent_gt）、no-user/solo（llm_agent_solo）。

## 2. 版本固定与架构（沿用 148，差异计列）

- τ²-bench 固定 v1.0.1（`fc0055dc`）；vendor 由 148 的同一 pinned checkout 逐字节复制（排除 .git），本目录 `inputs/` 保存 airline 冻结数据并记录 sha256。
- 架构同 148（未改 vendor）：**挂起-转发 MCP bridge**（τ² 唯一执行工具调用）+ OpenClaw 消费者 + v6 原生 `$技能` 首轮引用；判分补丁（judge 模型替换、fence-strip、重试）在本进程运行时生效。
- 与 148 的差异（本实验新增）：`run_wrapper.py` 增加 `TAU2_RETAIL_DOMAIN`（默认 "airline"）；`openclaw_config.py` 按域选择角色文本与 MCP 服务名；relay 使用独立端口 8180 与独立 `ledger/`（不与 148 混账）。
- airline 评分：50/50 题为 `[DB, COMMUNICATE]`；COMMUNICATE 为 vendor 内字符串匹配（无判分模型调用）；NL assertions 若存在走 glm-4-flash（同 148）。

## 3. 数据划分（以 `split_manifest.json` 为准）

- 官方 split：train 30 / test 20 / base 50；结构校验通过（ID 有效、train∩test=∅、base=∪）。
- **dev = 4**：`{42: cancel, 21: update_flights, 20: book, 12: update_baggages}`（seed=42 按主操作分桶，优先 cancel>update_flights>book>update_baggages>update_passengers；确定性选择，不看 test）。dev 只用于管线联调与验收，不进入正式统计。
- **演化集 = 其余 26 题**，每题采集 1 条完整运行。
- **正式测试 = test 全部 20 题**，每题每组 4 次独立运行（B0/B1 配对，同 trial 同 seed=42）。
- 审计发现（详见 manifest）：4 个 user、14 个 reservation 跨 train/test 共享（官方划分非按实体隔离）；train 15 ↔ test 16 动作签名相同且指令相似度 0.849（近似改写）；test 中 5 题的 primary 类别在演化集无覆盖（`read_only/escalate` 边缘类，报告单列）。
- 暴露纪律：gold action 名仅用于本审计；本目录未接触 test 数据内容以外的信息，采集阶段只看演化集。

## 4. 运行纪律（继承 148）

- 工具调用由 τ² orchestrator 唯一执行（挂起-转发），写操作天然只执行一次；轨迹重放 DB 判分要求原生 tool_calls 完整入 τ² 消息记录。
- 两组的唯一差异是 `skills/` 目录（B1 = 冻结库；B0 = 空）；同一 prompt/harness/评分。
- 失败如实记录：基建失败与模型失败分开；不伪造、不覆盖、不挑分重跑；账本独立、请求上限 60,000/relay 实例。
- 磁盘/进程风险沿用 148 教训：C: 盘随 vhdx 膨胀监控 + `scripts/cleanup_native_state.py` 安全回收（仅删闲置>40 分钟且已归档副本）。

## 5. 付费批次计划（按顺序）

1. **dev 联调**：4 题 ×1 trial（`runs/dev/no_skill.json`），验收管线（含原生技能读取与工具执行）。
2. **演化采集**：26 题 ×1（`runs/collect/evolution.json`），Collector 无技能。
3. **学习与冻结**：AutoSkill 离线轨迹路径 → `frozen_skills/` + manifest（namespace 按域新建）。
4. **配对评测**：test 20 题 ×4 trials ×2 组 = 160 场（`runs/test/no_skill.json`、`runs/test/autoskill_library.json`）。
5. **分析**：同 148（`scan_skill_reads.py` 域内扫描、`paired_summary_v4.py` 适配、技能读取率、逐题差异）。

## 6. 请求账本与预算

- 本目录 `ledger/requests.jsonl` 独立记账；relay 上限 60,000/实例；预计规模按 148 单位成本估计：每次运行约 90 请求（consumer+user），judge 视 NL 断言量。
- 预估：dev 4 + 采集 26 + 评测 160 ≈ 190 场运行。
