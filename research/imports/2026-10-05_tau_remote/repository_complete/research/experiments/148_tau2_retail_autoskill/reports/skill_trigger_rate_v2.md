# B1（autoskill_library）v2 批次「技能触发率」核验报告

- 核验对象：`runs/autoskill_library/task_*/<session_id>/`（B1 = autoskill_library，v2 批次，2026-10-03 12:30 起）
- 快照时间：2026-10-03 16:54（CST）。快照时 v2 评测仍在收尾：**159/160 场已完成，仅 task 74 trial 3 运行中**（其会话转录已做部分快照扫描，见 §1/§6；批次结束后可按同一方法复跑复核）
- 数据来源：各会话 `openclaw_state_archive/agents/main/agent/openclaw-agent.sqlite` 的 `transcript_events` 与 `trajectory_runtime_events`（只读打开）；对照物：v1 会话归档、078 实验 native read 归档
- **核心结论：v2 批次截至快照时点，Agent 真实发起技能读取的场次 = 0。触发率 0/162 = 0.0%（会话口径），0/159 = 0.0%（已完成 sim 口径）。v1 同方法对照亦为 0/162。此前 task 12/45 冒烟「SKILL.md 命中 16/18」结论不成立，为暴露假阳性（见 §5）。**

## 0. 术语与区分（本次核验的核心口径）

- **暴露（exposure）**：系统提示中 `<available_skills>` 列出技能的名称、描述与 SKILL.md 路径（OpenClaw 将其写入每个会话的 `skillsSnapshot` 系统提示快照）。这只表示"技能被列出"，人人都有。
- **触发（trigger，本报告的唯一统计对象）**：Agent 实际调用原生 `read` 工具读取 `workspace/skills/<skill>/SKILL.md`，且读取内容进入会话上下文。
- 仅"被列出"不计入触发率；只有"真实读取"计入。

## 1. 样本与数据

| 项目 | 数量 | 说明 |
|---|---|---|
| v2 B1 目标场数 | 160 | 40 任务 × 4 trials |
| v2 已完成 sim（结果文件） | 159 | `runs/test_v2/autoskill_library.json`；快照时 1 场（74.3）运行中 |
| v2 会话目录 | 183 | 含重试、被杀、空会话 |
| v2 有转录（sqlite）的会话 | 162 | 本次全部扫描（含 74.3 会话的部分快照） |
| 其中与已完成 sim 一一对应 | 159 | 按 task + 启动时间（±90s）匹配；0 个已完成 sim 缺会话 |
| 未匹配的已归档会话 | 3 | `d660d104`（task12 冒烟会话，sim 在 runs/smoke/）、`d1dde770`（task60 trial3 第 0 次尝试，中止后重试成功）、`3d6632ed`（74.3，运行中，部分快照） |
| 有轮次但无转录 | 1 | `7a57b733`（task45 冒烟，31 轮时被杀） |
| 0 轮空会话 | 20 | 12:39 被杀的第一波启动，未产生任何轮次 |
| v1 对照会话 | 162 | 全部有转录，全部扫描（0 读取，见 §4） |
| 阳性对照 | 078 native_read 归档 + 078 runs 抽样 13 个归档 | 见 §2 |

v2 协议事实核查（确认"修复已生效但读取仍为 0"）：

- v2 契约中确实已新增技能读取指令：**183/183** 个 v2 会话的 `workspace/AGENTS.md` 含 `Read applicable skills using your native read tool when useful.`（v1 为 162/162 不含）。
- 技能暴露为 100%：**162/162** 个有转录的 v2 会话，其 `skillsSnapshot` 均列出 5 个技能（另有 2 个插件技能 browser-automation / canvas 被列出；插件技能目录在 workspace 之外，`read` 工具 workspace-only 不可读）。

## 2. 检测方法（判据与验证）

对每个会话打开其归档 sqlite（`mode=ro`），从**两个相互独立的记录源**取证据：

1. `transcript_events`（会话转录；`event_json`，必要时对 `event_zstd` 做 zstandard 解压）：解析 `message` 事件 content parts（assistant 的 `toolCall` 与 `toolResult`）。
2. `trajectory_runtime_events`（运行时轨迹）：取 `type=tool.call` 事件的 `data.name` / `data.args`。
3. 辅助文本判据：对转录全文检索技能正文"独家特征串"（只出现在 SKILL.md 正文、不出现在系统提示技能清单里的字符串）。

判定规则：

- **R1（主判据）**：转录存在 assistant 消息 part `{"type":"toolCall","name":"read",...}`，且 `arguments.path` 指向某技能 SKILL.md；或在轨迹表中出现 `tool.call` 且 name=read。
- **R2（佐证）**：存在 `role=toolResult`、`toolName=read` 的结果且内容含技能正文特征串。
- **R3（兜底交叉）**：转录全文命中正文独家特征串，逐技能为：键盘技能 `Only consider mechanical keyboards`；库存 `Execute script: scripts/inventory_check.py`；订单查询 `Input: User ID, shipping address`；T恤查询 `t-shirt characteristics (color, size, style, material)`；大流程 `scripts/verify_customer.js` / `references/order_modification_policy.md` / `Must update shipping address, product specifications, and payment method as requested`；另加通用正文标题 `## Prompt` / `# Workflow` / `# Constraints & Style`。
- 任一技能满足 R1（或轨迹 name=read）即记该会话"触发"，按路径归属到具体技能。

方法验证：

- **阳性对照 A**：078 实验 `private/audit_094/native_archives/native_read_1790842993_0c697d12/openclaw-agent.sqlite`（同 OpenClaw 2026.9.7 harness）——同一解析器可检出 `read` 调用（`arguments={"path": "receipt.txt"}`）及其 toolResult；`trajectory_runtime_events` 中同时有 1 条 `tool.call`。证明证据源与解析器对原生 read 敏感。
- **阳性对照 B**：078 `runs/` 抽样 13 个归档另检出 4 例真实 read（`public_state.json` 等），形态一致。
- **阴性对照**：v1 全部 162 会话同方法扫描 → 0 读取（与既有 v1 复核结论一致）。

## 3. 结果

### 3.1 触发率

| 口径 | 分子/分母 | 触发率 |
|---|---|---|
| v2 有转录会话 | 0 / 162 | 0.0% |
| v2 已完成 sim（与转录 1:1 对应） | 0 / 159 | 0.0% |
| v1+v2 全部扫描会话 | 0 / 324 | 0.0% |

### 3.2 分技能统计（被读取的场次数）

| 技能 | v2 | v1 |
|---|---|---|
| retailorderlookup | 0 | 0 |
| retailinventorycheck | 0 | 0 |
| retailordermodificationlookup | 0 | 0 |
| retailordermodificationandcancellationprocedurewithpaymentassist | 0 | 0 |
| find-and-confirm-cheapest-mechanical-keyboard-exchange | 0 | 0 |
| （插件技能 browser-automation / canvas，参考） | 0 | 0 |

### 3.3 工具使用形态（无读取时的替代观察，仅描述）

- v2 全部 162 个会话的运行时轨迹共 **844** 次 `tool.call`，**全部**为 `retail__*`（16 种零售工具）；v1 770 次同样全部为 `retail__*`。**原生工具调用（read 等）计数为 0**。
- 没有任何 assistant/user 消息包含 "skill" 字样或 5 个技能名（0/162 会话）。
- 最"需要技能"的长会话同样 0 读取：task94 trial2（99 轮）、task55 trial2（100 轮）、task62 trial0（98 轮）、task64 trial3（20 轮但 117 事件）等。
- 交易类行为（认证、查单、退款/换货、改地址等）全部由模型直接调用 retail 工具完成，与技能读取无关。

### 3.4 读取时机与读取后行为

- 由于 0 次读取，读取时机（开局/中途）与读取后行为变化**无法报告（N/A）**。
- 不推断因果：本次只能给出"未发生读取"这一事实，不能据此评价技能的有用性或危害性。

## 4. 对照

- **v1 对照（同方法）**：162 个会话、770 次工具调用、0 次 read；技能正文特征串 0 命中。与既有 v1 结论一致（"暴露未使用"）。
- **v2 vs v1**：v2 新增了契约中的技能读取指令（183/183 会话），暴露面不变（100%），但行为上读取仍为 0——**契约修订未能在行为上生效（截至快照）**。

## 5. task 12/45 冒烟结论复核（更正）

原说法："task 12/45（最新会话）里 SKILL.md 命中 16/18 次，说明技能被真实读取"。**复核结果：不成立，应更正。**

- 冒烟产物 `runs/smoke/b1_skillread_check.json`：12:30:39 启动（tasks 12/45，各 1 trial）；只完成 task12 trial0 一场，随后冒烟进程于约 12:39 被后续批次启动杀掉，task45 未完成。
- task12 冒烟会话 `d660d104`（转录 58 事件、12 轮、8 次 retail 调用）：**read 调用 0、正文特征串 0、转录中 "SKILL.md" 字符串 0**。
- task45 冒烟会话 `7a57b733`：31 轮后被杀、无归档转录；其 31 个 turn 输出/诊断文件中无技能读取证据（对 "read" 的文本命中全部是 usage 字段 `cacheRead`）。
- **"16/18" 的复原（最可能口径）**：task12/45 共 20 个会话目录，剔除 2 个冒烟会话后为 18 个；其中 **16 个**的 sqlite 内含字节串 "SKILL.md"（恰为 16/18；未命中的 2 个是 12:39 被杀、无 sqlite 的空会话）。该字节串来自系统提示技能清单中的 location 路径（如 `.../workspace/skills/retailorderlookup/SKILL.md`；d660d104 的 skillsSnapshot 中出现 270 次），是**暴露**而非读取。
- 结论：冒烟应判定为"未检测到技能读取"；"SKILL.md 命中"只是清单路径与磁盘副本文件名的出现，不能作为读取证据。

## 6. 局限与不确定性

1. 1 个有轮次但无转录的会话无法做转录级核验：task45 冒烟 `7a57b733`（31 轮被杀；其 turn 级输出/诊断文件未见任何读取或正文证据）。运行中的 `3d6632ed`（74.3）已用其部分快照扫描（0 读取），但其 sim 未结束，快照后的读取不会被覆盖。
2. 快照后新增读取不会被覆盖：74.3 仍在运行，其后若发生读取需在批次结束后复跑本扫描（判据同 §2，全程可脚本化）。
3. 方法依赖 OpenClaw 自身的转录/轨迹记录；若某些情况下 read 记录缺失会漏报。缓解：两个独立记录源 + 078 阳性对照 + v1 已知负例；且正文特征串在全部 324 份转录中零命中（含 `## Prompt` 等通用标题），若正文以任何形式进入过上下文，R3 应有命中。
4. 触发率 0 的解释范围：仅说明"技能未被消费"，**不能**证明技能有/无效果，也不能排除"提示词/编排问题导致未触发"之外的其它机制原因。
5. 已知假阳性陷阱（后续核验务必避开）：
   - sqlite/目录中的 "SKILL.md" 字符串与文件（技能清单路径、workspace 技能副本）：v2 中 **162/162** 命中、task12/45 的 18 个非冒烟目录中 16 个命中——任何此类计数都在测"暴露"；
   - 子串 "skill"：实验路径 `/var/tmp/skillsloop148/...` 与组名 `autoskill_library` 天然出现；
   - 文本 "read"：usage 字段 `cacheRead` 等会误命中。

## 7. 结论与建议

- 截至 2026-10-03 16:54 快照：**v2 B1 技能触发率 = 0**（0/162 会话；0/159 已完成 sim；分技能全 0），与 v1 无差别。
- v2 的协议修订（新增"读技能"指令）截至快照未在行为上生效；B1 仍等价于"技能已暴露、从未被读取/应用"。
- 建议：若研究目标是"技能被消费"，应将"读取触发"作为独立机制问题先行处理并在新版协议中验证读取信号（可用本报告 §2 判据）；在此之前，B1 的任何指标差异都不能归因于技能效果。
- 待办：v2 批次（74.3）结束后复跑本扫描确认无新增读取，并将本结论并入实验总报告与记忆。

## 附录：复现要点

- 打开：`runs/autoskill_library/task_<id>/<session>/openclaw_state_archive/agents/main/agent/openclaw-agent.sqlite`（只读；runtime_py 含 zstandard）。
- 取数：`transcript_events`（`event_json` / zstd 解压 `event_zstd`）与 `trajectory_runtime_events`（`event_json`）。
- 判定：R1/R2/R3 与特征串见 §2；阳性对照见 §2（078），阴性对照见 §4（v1）。
