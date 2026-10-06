# 源码与接口审计（逐步更新）

对象：τ²-bench `fc0055dc`（v1.0.1）、AutoSkill `94c47ca`、OpenClaw `2026.9.7`。
原则：只读核验官方源码；**本实验不改 vendor**，全部适配在实验目录内实现并在此登记。

## 1. τ²-bench（`vendor/tau2-bench` @ v1.0.1）

### 1.1 Agent 接口（适配器必须实现）

- 文档：`src/tau2/agent/README.md`；基类 `HalfDuplexAgent`（`src/tau2/agent/base_agent.py:52`）。
- 必须实现：`get_init_state(message_history) -> State`、`generate_next_message(message, state) -> (AssistantMessage, State)`；构造参数 `tools: list[Tool]`、`domain_policy: str`。
- 注册：`registry.register_agent_factory(factory, name)`（`src/tau2/registry.py:106`），CLI `tau2 run --domain retail --agent <name>`；工厂可从 kwargs 收到 `llm`、`llm_args`、`task`。
- 参考实现：`src/tau2/agent/llm_agent.py`。

### 1.2 通信协议与工具执行（决定桥接设计）

- 消息规则（`orchestrator.py:360-391`）：agent 每条消息**要么文本、要么工具调用**（不可兼有）；工具调用必须由环境返回对应 ToolMessage。
- 主循环：`orchestrator.py:823 step()`；`:881-892` 工具分支 → `_execute_tool_calls`（`:313`）→ `environment.get_response(tool_call)`。
- 环境执行：`src/tau2/environment/environment.py:465 get_response` → `make_tool_call` + `sync_tools`；异常被包成 `error=True` 的 ToolMessage（不中断模拟，计入 `max_errors`）。
- 工具 schema：`src/tau2/environment/tool.py:24 openai_schema`（官方 OpenAI 函数 schema）；Retail 工具定义 `src/tau2/domains/retail/tools.py`：
  - 读：find_user_id_by_name_zip / find_user_id_by_email / get_order_details / get_product_details / get_item_details / get_user_details / list_all_product_types
  - 写：cancel_pending_order / exchange_delivered_order_items / return_delivered_order_items / modify_pending_order_items / modify_pending_order_address / modify_user_address / modify_pending_order_payment
  - 通用：calculate / transfer_to_human_agents

### 1.3 评分（原生）

- 入口：`src/tau2/evaluator/evaluator.py:88 evaluate_simulation`；按 `task.evaluation_criteria.reward_basis` 组合分项（`:196-267`）。
- Retail reward_basis（实测 114 题）：DB+NL_ASSERTION ×112、仅 DB ×2；**无任何题把 ACTION 计入主分**（`actions` 仅重放构建目标库/诊断）。
- 环境判分：`evaluator_env.py:85-94` —— 预测环境由**轨迹重放**（`set_state(message_history=..., strict=True)`）重建；因此工具调用与结果必须完整进入 τ² 消息记录且与重放严格一致（`strict=True` 时输出不一致会抛错）。
- NL assertions：`evaluator_nl_assertions.py`，judge 默认 `DEFAULT_LLM_NL_ASSERTIONS = "gpt-4.1-2025-04-14"`（`src/tau2/config.py:24`）。**需替换为可用资源并在运行时补丁；属适配，报告单列。**
- 其它配置：NL assertions 还有 `DEFAULT_LLM_ENV_INTERFACE`（env 断言用，retail 未用）；user simulator 默认 `DEFAULT_LLM_USER = gpt-4.1-2025-04-14`（CLI `--user-llm` 可覆盖）。

### 1.4 运行参数（CLI 摘录，`docs/cli-reference.md`）

- `--task-ids`（指定题目）、`--task-split-name`（默认 base）、`--num-tasks`、`--num-trials`（默认 1）、`--seed`（默认 300，本实验固定 42/42+i）、`--max-steps`（默认 200）、`--max-errors`（默认 10）、`--max-retries`（默认 3，仅基础设施错误重试）、`--retry-delay`（默认 1.0）、`--timeout`（默认无，本实验 900s）。
- 禁用项定位：oracle-plan = `llm_agent_gt`（cli-reference.md:340）；no-user = `llm_agent_solo`（:333）；workflow-policy = `telecom-workflow` 域名变体（:352）。

### 1.5 数据/任务要点

- `data/tau2/domains/retail/`：`tasks.json`（114）、`split_tasks.json`（train 74/test 40/base 114）、`policy.md`、`db.json`、`task_issues/`（官方登记的 task 4/5/7 运行问题记录，含用户 stop 与 action_check 明细）。
- v1.0.1 == main（`5bfa7e37`）的 retail 文本数据与文本路径；τ³ 修订集中在 commit `01e812d`。

## 2. AutoSkill（115 检出 @ `94c47ca`，复用）

- 离线对话路径：`autoskill/offline/conversation/extract.py`；SDK `import_openai_conversations`。
- 输入：OpenAI 格式会话（`.json/.jsonl`，messages 结构）；证据结构 = "Primary User Questions（主证据）+ Full Conversation（上下文参考）"；助手侧工件不作为技能证据（方法差异如实保留）。
- 检索/维护：需要 **embeddings provider**（相似技能搜索与合并判定）；LLM provider 支持通用 OpenAI 兼容 URL（README §6.5）。
- 存储：`SkillBank/Users/<user_id>/...`、`Common/`、`vectors/`、`index/`。
- 本实验只用上述 core 路径；不启用 AutoSkill4Doc / AutoSkill4OpenClaw / SkillEvo / trajectory 提取。

## 3. OpenClaw（`runtime_linux/openclaw` @ 2026.9.7）

- 消费者调用形态（复用 078 桥接）：`node openclaw.mjs agent --local --session-id <uuid> --message-file <file> --json --timeout <s>`，配置经 `OPENCLAW_CONFIG_PATH`。
- 工具接入：**原生 MCP 服务器**（`docs/tools/mcp.md`；config `mcp.servers.<name> = {url|command, transport, requestTimeoutMs, toolFilter}`）；本地 streamable-http 即可，无需 OAuth。
- 技能：workspace 原生 skills 发现与 read；本实验禁用 bundled skills（同 078 形态 `skills.allowBundled` 占位）。
- 审批/策略：`docs/tools/exec-approvals.md`、`permission-modes.md`（本实验不依赖审批路径）。

## 4. 适配改动清单（全部在实验目录内；vendor 不改）

| # | 文件（计划） | 作用 | 状态 |
| --- | --- | --- | --- |
| 1 | `scripts/tau2_openclaw_agent.py` | 自定义 HalfDuplex agent：会话管理、挂起-转发、消息记录 | ✅ 已实现；单测 10/10 通过 |
| 2 | `scripts/mcp_retail_bridge.py` | MCP（streamable HTTP, mcp 2.2.0）工具桥：官方 schema、挂起-转发、对账 | ✅ 已实现；单测覆盖超时/错误结果 |
| 3 | `scripts/openclaw_config.py` | 每次运行的 `openclaw.json` 生成（MCP 服务器、模型、tool policy、skills） | ✅ 已实现；dry-run 核验 |
| 4 | `scripts/run_wrapper.py` | 注册 agent、替换 judge 模型常量、驱动 tau2 runner | ✅ 已实现；dry-run 通过（4 题/16 工具） |
| 5 | `scripts/collect.py` / `scripts/evaluate.py` | 采集与配对评测编排（含重试记录） | 由 run_wrapper 的 collect/evaluate 相位承担 |
| 6 | `scripts/canonicalize.py` | 原生事件流 → AutoSkill 输入（A/B/C 隔离、q/r、q_init/h/o 视图） | 待实现（P5 之后的准备项） |
| 7 | 复用 078：预算中继等 | 全角色模型请求记账/上限（新账本，不混 078 数据） | 待接入（P3 前） |
| 8 | 进度页/巡检 | 沿用 115 形态的只读进度与健康探针 | 待接入 |

### 语义细节（已用单测固定）

- τ² 环境返回的**错误工具结果**按原生语义处理：错误文本正常回注给模型（记入 ledger `result_error`），网桥本身不失败。
- 工具调用进入 τ² 消息记录的路径：适配器返回 `AssistantMessage.tool_calls`（无文本），τ² `_execute_tool_calls` 唯一执行，`ToolMessage.id == call.id` 保证对账。
- OpenClaw 运行工作区在 Linux FS（`/var/tmp/skillsloop148/<hash>`）；每次启动把隔离的公开工作区（AGENTS.md + skills）复制到原生工作区（同 078 形态），`/mnt/d` 不支持 fs-safe 原子重命名。
- MCP 服务器 `stateless_http=True` + SSE 响应；`requestTimeoutMs=900s` 覆盖挂起等待；会话在 stop() 时归档到 `openclaw_state_archive/`。

### 追加（2026-10-02，dev 真实联调实测修复）

1. **/mnt/d (9p) 子进程挂起**：OpenClaw 子进程若把 stdout/stderr 指向 /mnt/d、或从 /mnt/d 加载 node_modules，会阻塞在 `p9_client_rpc`（实测各卡 >2 分钟不推进）。修复：运行时（node + openclaw 2026.9.7）改用 Linux FS 副本 `/var/tmp/skillsloop078/...`（078 既有拷贝，只读复用）；提示词/日志/工作区/状态目录全部落 Linux FS，进程退出后再 `sync()` 回拷会话目录。
2. **Tool Search 紧凑面**：OpenClaw 对未显式配置 `tools.toolSearch` 的 embedded run 自动启用结构化 Tool Search（实测日志 "cataloged 17 tools behind compact prompt surface"；弱模型不会直接调用零售工具）。修复：生成配置显式 `tools.toolSearch: false`，恢复原生直接 schema（17 个工具：16 零售 + read）。
3. **实测证据（dev）**：原生工具调用被挂起-转发捕获并回注 τ²：`find_user_id_by_name_zip(first_name=Emma,last_name=Smith,zip=10192)` → `emma_smith_8564`；`get_user_details(user_id=emma_smith_8564)` → 真实用户 JSON；`find_user_id_by_email(isabella.johansson@example.com)` → 原生错误文本 "Error: User not found"（按原生语义回注，网桥不失败）。模型在多轮中继续调用，turn_000/001 均正常完成。
