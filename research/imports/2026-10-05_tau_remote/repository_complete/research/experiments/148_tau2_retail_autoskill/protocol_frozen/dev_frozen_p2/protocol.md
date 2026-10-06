# 协议：AutoSkill × τ²-bench Retail（文本域）

- 实验目录：`research/experiments/148_tau2_retail_autoskill`
- 创建：2026-10-02；状态：**不付费准备中**（预算与部分模型角色待用户确认，见 `blockers.md`）。
- 版本固定见 `versions.json`；机器可读参数见 `experiment.yaml`；分集审计见 `split_manifest.json` 与 `workflow_split_audit.md`。

## 1. 目标与不做什么

目标：在 τ²-bench 文本 Retail 域，用固定 Agent 采集多轮协作历史（Collector），经官方 AutoSkill 核心 offline conversation 路径沉淀并维护为一个冻结技能库，然后同一 Agent（原生 OpenClaw 消费者＋官方政策/工具/用户模拟器）在 test 上做 B0（无技能）/ B1（冻结库）配对评测，用 benchmark 原生结果回答：

1. 从多轮历史沉淀的 skills 是否提高相关新任务的完成率？
2. 在结果不变差的情况下，是否减少沟通与重复操作？

不预设涨分；空库、未读取技能、持平或下降都如实报告。本轮只做 AutoSkill 基线，不做：SkillsLoop 轨迹恢复算法、Trace2Skill、人工切碎/交错对话、模型训练、评测期技能更新、多 benchmark 混跑。

## 2. 版本固定与 τ³ 辨析（重要）

- 固定 **τ²-bench v1.0.1**（commit `fc0055dc`，2026-07-22）。核验（2026-10-02）：Retail 文本数据与 main@`5bfa7e37` **逐字节一致**（`tasks.json`/`split_tasks.json` sha256 相同；v1.0.1→main 的提交仅涉及 voice/leaderboard）。
- v1.0.1 属 **τ³ 时代版本**：Retail 任务含 τ³ "Task Quality" 修订（commit `01e812d`）——全部 114 题的 `evaluation_criteria` 有改动（`reward_basis` 显式设定）、21 题 `user_scenario.instructions` 修订。**这不是 τ² 论文的设置，本轮成绩不得与旧论文分数直接排名。**
- 禁用：voice/audio-native、banking_knowledge、oracle-plan（`llm_agent_gt`）、no-user/solo（`llm_agent_solo`）、workflow-policy 变体（telecom-workflow）。
- AutoSkill 固定 `ECNU-ICALK/AutoSkill` commit `94c47ca`（2026-05-10），只用核心 offline conversation 路径；不混用 AutoSkill4Doc、SkillEvo、trajectory 提取器。

## 3. 数据划分（以实际 split 文件为准）

- `train` 74 / `test` 40 / `base` 114；结构校验通过（ID 有效、train∩test=∅、base=∪）。
- **dev = 4 题**：`{69: cancel, 28: return, 8: exchange, 112: modify_items}`；选择规则见 `experiment.yaml`（seed=42，按主操作分桶，优先 cancel>return>exchange>modify_payment>modify_items>modify_address）。dev 只用于管线联调与验收，不进入正式统计。
- **演化集 = 其余 70 题**，每题采集 1 条完整运行。
- **正式测试 = test 全部 40 题**，每题每组 4 次独立运行（B0/B1 配对，同 trial 同 seed）。
- 审计发现（详见 `workflow_split_audit.md`）：45 个订单 ID 跨 train/test 共享（官方划分并非按订单隔离）；train 93 与 test 94 指令相似度 0.993（近似同题改写）；test 的 `modify_payment` 主类在演化集无覆盖（test 40 无对应学习材料）；test task 9 与 train 6/7/8 同动作签名（相关但不同题）。
- **task 9 使用禁令**：不得用于调提示、强制演示或生成技能；若本地以任何方式接触过，必须披露。本目录当前未接触。

## 4. 接入架构（OpenClaw ↔ τ² ↔ 官方环境）

```
官方 τ² orchestrator / 用户模拟器
   ↕（Agent 接口：get_init_state / generate_next_message，半双工文本）
自定义 tau2 agent 适配器（本实验实现，注册名 openclaw_retail）
   ↕（挂起-转发协议：每条恰好一次）
OpenClaw 2026.9.7 原生会话（同 session 跨轮持续）
   ↕（原生 MCP 工具调用，官方 schema）
本进程 MCP 工具桥（streamable HTTP, 127.0.0.1）
   ↕
官方 Retail 环境（τ² 进程内，orchestrator 执行）
```

**关键约束来源（已核验 v1.0.1 源码）**：orchestrator 规定 agent 每条消息**要么是文本、要么是工具调用**；工具调用由 orchestrator 执行（`Environment.get_response`）；**DB 判分从轨迹重放工具调用**（`EnvironmentEvaluator` 用 `set_state(message_history=..., strict=True)` 重建预测库），因此工具调用必须以原生协议进入 τ² 消息记录，且记录结果须与重放严格一致。

**挂起-转发设计（待实现）**：OpenClaw 通过原生 MCP 服务器看到官方 Retail 工具 schema；当模型发起工具调用时，MCP 处理器**不执行、不立即返回**，而是把调用交给适配器；适配器把它作为 `AssistantMessage(tool_calls=[...])` 返回给 τ²；**τ² orchestrator 执行**（唯一一次真实执行，记录 ToolMessage）；结果送回 MCP 处理器并返回给 OpenClaw 同一会话；OpenClaw 继续，直到产出面向用户的文本——该文本作为 `AssistantMessage(content=...)` 返回 τ²，模拟用户继续回应。要点：
- 业务写操作只执行一次（唯一执行者是 τ² env），另存 call_id/参数/返回/状态 hash 对账（`ledger/`）。
- 技能读取（`read`）是本地技能工具，不进入业务环境，但计入资源；不与 Retail 业务工具混淆。
- 不把工具调用改成"文本 JSON 再正则解析"；不绕过官方评分直接读写 db.json。
- 每次运行独立 OpenClaw session/state/workspace；不跨任务共享聊天或缓存结果。
- B0/B1 配置与工具完全相同，只有 skills 目录差别；禁用 bundled skills。

## 5. 采集（Collector）

- 无学习技能的固定 Collector，在 70 题演化集各跑 1 条；同一适配器/模型/政策/工具；每题重置环境与 Agent 状态。
- 保留：实际初始用户话语、全部后续用户澄清/修改/确认、助手公开回答、真实工具调用/返回/错误、实际可见结果、原生结束原因。
- **三层隔离**：A `learner_visible`（用户话语、助手公开回复、工具结果）→ 才进 AutoSkill；B `simulator_private`（用户私有任务说明、未说出要求）；C `evaluator_private`（参考动作、目标状态、评分答案）。B 信息只有在用户实际说出后才以该条发言进入 A；完整 DB diff 不放入 A。
- 原生事件流先保存（raw/），再生成 `q/r` 与 `q_init/h/o` 兼容视图（canonical/）；不补造隐藏推理；成功、失败、拒绝、单轮/多轮都保留；不反复采样凑理想轨迹。
- 若用户参与很少，先检查结束机制并报告实际分布。

## 6. AutoSkill 生成与冻结

- 官方 offline conversation 路径：完整会话 → 技能提取 → 检索已有技能 → add/merge/discard → 维护**同一个** `tau_retail_pool` 空 namespace。
- 禁止导入示例 SkillBank / Common / 旧 Co-Gym 技能 / Codex 全局技能；不每题建小库；不用自写总结 Prompt 替代官方机制；不预做任务恢复或工作流聚类；数据转换只处理角色、顺序、格式与可见性。
- 记录实际传给模型的内容（窗口/截断/去重）、逐条新增/合并/丢弃与来源、费用；不强制非空；不按测试表现人工改技能；个案参数（如训练订单号）单列诊断；发现测试答案泄漏立即隔离该批。
- 导出 `frozen_skills/` + `frozen_skills_manifest.json`（逐文件 sha256），测试期间不维护、不更新。

## 7. 评测（B0/B1 配对）

- 同一 Agent 配置；B1 将冻结库放入 workspace 原生 skills 目录（启动只给名称/描述/入口，Agent 自主决定是否读取），B0 空目录。
- 禁止：正文塞 system prompt、人工选题配技能、隐藏类别召回、宿主扫描冒充 Agent 读取、跨任务共享 scratchpad。
- 记录：技能曝光、正文读取（含 hash）、方法被遵循的迹象，分列统计。
- 四次 trial 独立重复：不携带前次错误、反思、用户反馈或工作区状态。
- 评分：沿用原生 reward（`reward_basis` 全量 114 为 DB，112 为 DB+NL_ASSERTION）；`actions` 检查仅诊断，不进入主分（无任何 Retail 题把 ACTION 计入 reward）。确定性检查（DB）与 LLM 检查（NL assertions）分别说明。
- 主指标：平均原生 reward、pass^1、pass^4（trial 足够时）、任务数/运行数/可评分数/异常数；直接调用官方 metrics 代码。基础设施错误按原生口径排除时，公开被排除的数量、原因与分母；不重跑直到成功，不挑高分。

## 8. 协作投入与成本（补充指标）

初始请求后用户消息数、非终止用户消息数、业务工具调用/错误数、技能读取次数、各角色 tokens/费用、运行耗时。工具调用 ≠ 用户回合；必要澄清不叫返工。先报整批质量与投入，配对开销只作补充；不造新综合指标，不把模拟轮数换算人工时。

## 9. 执行顺序、冻结与预算

1. ~~版本与源码核验~~（已完成）→ 2. ~~分集与覆盖审计~~（已完成）→ 3. **工具/模拟/评分 dev 测试与适配器实现（不付费部分进行中）** → 4. 少量预定演化任务采集与 AutoSkill 接线检查（dev，需资源确认）→ 5. dev 验证整库发现与自主读取 → 6. **预算获准后冻结本协议**（hash 入 `protocol_frozen/`）→ 7. 70 题演化采集 → 8. AutoSkill 生成并冻结正式库 → 9. 40 题 × 2 组 × 4 trial 配对测试 → 10. 原生指标与资源统计 → 11. 中文报告。

- 预算未确认期间只做不付费工作；**任何付费运行（含 dev 真实联调）在用户确认资源与硬上限后启动**。
- 正式 test 开始后修改实现必须形成新版本与可比批次，不得旧 B0 与新 B1 混比。
- 若出现调用失效、模拟器不继续、评分无法回放、技能目录不可读，先修复基础问题再扩大实验；预跑负结果不自动等于停止全部研究。

## 10. 交付物（目录对照用户清单）

`README.md`（复算命令）、`protocol.md`/`experiment.yaml`/`versions.json`、`split_manifest.json`/`workflow_split_audit.md`、`source_audit.md`、`raw/evolve/`、`canonical/evolve/`、`autoskill_input/`、`autoskill_state/`、`frozen_skills/`+manifest、`runs/no_skill/`、`runs/autoskill_library/`、`reports/{per_task.csv,summary.json,experiment_report.md,blockers.md}`、`ledger/`、`tests/`。

单元测试至少覆盖：分集隔离、角色正确、工具只执行一次、用户能继续回应、终止协议、业务状态回放一致、技能可读、原始文件越界防护、测试期间库不变。mock 仅用于单测。

## 11. 风险与限制（待报告时如实引用）

- 模拟器/判分模型若用 GLM-5.3-Flash（待确认）属**适配**，与官方推荐模型（gpt-4o）不同；不与不同配置的成绩直接排名。
- 官方 train/test 共享订单与近似题（见审计）；技能可能携带个案参数——单列诊断，不当作通用方法。
- test `modify_payment` 无演化侧覆盖；该题组的学习材料缺失应显式说明。
- AutoSkill 的 conversation 路径以用户话语为主要证据、助手为上下文（方法差异如实保留）。
- 费用/usage 未知处不填 0；缺档单列。
