# 多 Agent（群辩模式）历史实现分析

> **分析来源分支**：`feature--多agent模式`（最终提交 `094fee6d`，约 2026-05-18）  
> **当前开发分支**：`feature--多agent`  
> **本文目的**：梳理旧版多 Agent 的产品流程、技术实现、提示词结构与周边特殊处理，供新版开发参考。不涉及新版方案设计。

---

## 1. 结论速览

| 项 | 结论 |
|---|---|
| 实现位置 | **几乎全部在前端**（`apps/web`），`apps/api` **无**专用多 Agent / 群辩接口 |
| 对话通道 | 复用既有 ZClaw/EvoMind **SSE 流式发消息** API；每一轮发言 = 一次普通 `message` 请求 |
| 已落地能力 | 仅 **话题辩论**；头脑风暴 / 方案共创 / 自定义模式 UI 有入口但标「即将上线」 |
| UI 模式名 | 输入区 Tab：**独白模式** / **群辩模式**（记忆中的「群聊」= 代码里的 `group` / 文案「群辩」） |
| 内置角色 | **主持人、撰稿人、审稿人**（共 3 个，非仅前两个） |
| 编排上限 | 最多 **6 轮**；每轮后由模型输出 `CONTINUE:` / `END:` 决定是否继续 |
| 提示词 | 代码实现于 `topicDebatePrompts.ts`；仓库根目录另有设计样例 `多agent讨论提示词v1/v2/v3.md` |

---

## 2. 相关提交时间线（旧分支上的多 Agent 演进）

| 提交 | 说明 |
|---|---|
| `347b0638` | **初版**：辩论向导、编排器、提示词、`installedAgents` |
| `af667987` | 最多 6 轮 + AI 自行判断是否继续 |
| `5737a435` | 多 Agent 对话头像映射 |
| `1fbfa86b` | 多 Agent 对话导致新开对话的 bug 修复 |
| `6ca8f38d` | 提示词优化：总结要紧扣核心问题 |
| `193ee72f` | 群辩历史标题标记、用户气泡隐藏、收敛消息隐藏 |
| `6577c130` | 辩论结束后输入框可继续会话（会后追问） |
| `f4f965e6` | 发言呼吸动效、切换模式清空输入框、切换模式逻辑 |
| `094fee6d` | 选择辩论智能体弹窗 bug 修改（分支末次相关提交） |

---

## 3. 代码结构总览

核心目录：`apps/web/src/components/super-lobster/debate/`

```
debate/
├── DebateGroupWizard.tsx      # 群辩模式选择 → 选智能体 → 确认团队
├── DebateTeamInputChips.tsx   # 输入框上方团队头像条 + 发言呼吸动效
├── runTopicDebate.ts          # 话题辩论编排状态机（核心）
├── topicDebatePrompts.ts      # 全部角色提示词组装与解析
├── debateBuiltinRoles.ts      # 主持人 / 撰稿人 / 审稿人
├── debatePostChat.ts          # 会后追问提示词、标记、sessionStorage
├── debateMessageVisibility.ts # 历史/列表中隐藏编排 user 与收敛 assistant
├── debateSessionMarkers.ts    # 会话标题后缀 `_【群辩模式】`
├── debateSpeakerAvatars.ts    # 角色 → 头像映射
├── debateActiveSpeaker.ts     # displayValue → 当前发言 chip id
├── debateHistoryAgents.ts     # 从历史 transcript 反推参会智能体
└── __tests__/                 # 可见性、标记、提示词、会后追问单测
```

主页面集成：`SuperLobsterPage.tsx`（状态机、发送拦截、模式切换）  
输入区 Tab：`MessageInput.tsx`  
列表过滤：`MessageList.tsx` + `MessageBubble.tsx`  
历史标题展示：`ZclawShell.tsx` 对标题做 `stripDebateSessionTitleSuffix`  
资源：`/img/host.png`、`Writer.png`、`reader.png`、`speak.png`；`globals.css` 中呼吸动画

辅助：`apps/web/src/lib/installedAgents.ts`（智能体数据结构与可见列表构建）

---

## 4. 产品流程（用户视角）

### 4.1 独白模式（默认）

- `conversationMode = 'monologue'`
- 行为与普通单智能体/普通对话一致，不走辩论编排

### 4.2 切换到群辩模式

1. 用户在输入区工具栏点击 **「群辩模式」**
2. 系统 **清空当前对话工作区并开启新会话**（`resetConversationWorkspace`），toast：「已切换至群辩模式并开启新对话」
3. 打开 `DebateGroupWizard` 弹窗
4. 若用户 **关闭弹窗且未确认团队** → 自动退回 **独白模式**

再点一次「群辩模式」（已在 group）会再次打开向导。

切回独白：同样 reset 工作区 → 新会话，toast：「已切换至独白模式并开启新对话」。

### 4.3 群辩向导三步

| Step | 标题 | 行为 |
|---|---|---|
| `subtype` | 请选择群辩模式 | 四宫格：话题辩论（可用）、头脑风暴 / 方案共创 / 自定义（即将上线） |
| `agents` | 选择参与辩论的智能体 | 多选已安装智能体，**至少 2 名** |
| `confirm` | 确认辩论团队 | 展示：用户所选 + **主持人 / 撰稿人 / 审稿人**；点「完成」 |

「完成」后：

- `conversationMode = 'group'`
- `debateAwaitingTopic = true`
- 输入框占位改为：**请输入此次辩论主题**
- 输入框上方出现团队 chips（所选智能体 + 三个内置角色）

### 4.4 启动辩论 → 编排 → 结束 → 会后追问

1. 用户在输入框提交 **辩论主题**（不走普通发送文案）
2. 前端调用 `runTopicDebateFlow`，按阶段 **串行** 多次 `handleSend`
3. 编排进行中：输入锁定；可点「中止群辩编排」；当前发言者 chip **呼吸动效**
4. 结束后：toast「话题辩论已结束，可继续基于会议摘要提问」；进入 **会后自由问答**
5. 会后用户继续输入：默认单助手回答（带会议摘要上下文）；若命中「继续讨论 / 开启下一轮…」等关键词，则 **重新开启整场群辩编排**

---

## 5. 编排状态机（`runTopicDebateFlow`）

```
开场(主持人)
  → 解析/补抽「会议核心问题」(2～5 条)
  → loop 第 N 轮 (N = 1..≤6):
       各选中智能体依次发言
       → 主持人轮次小结
       → 会议摘要压缩
       → 【隐藏】收敛判断 CONTINUE / END
       → 若 CONTINUE 且未达上限：主持人过渡到下一轮
       → 若 CONTINUE 但已达 6 轮：主持人宣布达上限并结束循环
       → 若 END：结束循环
  → 撰稿人最终报告
  → 审稿人审核意见
  → 组装 finalSummary，返回 ok
```

### 5.1 每一步如何发消息

编排器不直接打 API，而是注入 `send`：

```ts
send({ requestBody, displayValue, uiHidden? })
```

在 `SuperLobsterPage.runDebateFromWizard` 中映射为：

| 字段 | 用途 |
|---|---|
| `requestMessageOverride` = `requestBody` | **真正发给后端的完整提示词**（含系统规则、主题、名单、角色任务） |
| `displayValue` | **本地 UI 用户气泡展示文案**（短标签，如 `【主持人】开场`） |
| `assistantAvatarSrc` | 按角色解析头像 |
| `sessionTitleOverride` | **仅首条**：`主题截断 + _【群辩模式】` |
| `uiHidden` | 收敛判断轮次：本地不展示助手正文（生成中仍显示「正在思考」） |
| `preserveConversationSkills` | 编排过程中不重置已选技能 |

要点：

- **后端收到并落库的是完整 `requestMessage`（隐藏提示词）**
- **前端本地列表里 user 气泡先显示的是短 `displayValue`**
- 历史会话从服务端拉取后，user 内容往往是 **完整提示词** → 必须靠 UI 策略隐藏（见第 8 节）

### 5.2 编排期 displayValue 一览

| 阶段 | displayValue 示例 |
|---|---|
| 开场 | `【主持人】开场` |
| 提取核心问题（兜底） | `【会议系统】提取核心问题` |
| 智能体发言 | `【{智能体名}】` |
| 轮次小结 | `【主持人】第 N 轮小结` |
| 摘要压缩 | `【会议摘要】压缩更新` |
| 收敛判断 | `【主持人】讨论收敛判断`（且 `uiHidden: true`） |
| 进入下一轮 | `【主持人】进入第 N+1 轮讨论` |
| 达上限 | `【主持人】已达讨论轮次上限` |
| 撰稿 | `【撰稿人】辩论总结报告` |
| 审稿 | `【审稿人】审核意见` |

### 5.3 收敛协议

模型须首行输出：

- `CONTINUE: <下一轮重点>` → 继续
- `END: <理由>` → 进入总结

解析失败时 **默认 CONTINUE**（保守），直到触达 6 轮上限强制结束。

---

## 6. 提示词体系（最重要）

实现文件：`topicDebatePrompts.ts`  
设计样例（含示例主题「如何提高公司的销售业绩」）：仓库根目录

- `多agent讨论提示词v1.md`
- `多agent讨论提示词v2.md`
- `多agent讨论提示词v3.md`（与代码最接近的完整流程样例）

### 6.1 统一包装：`wrapDebateRequest(roleBody, ctx)`

每一轮发给模型的 **完整 user message** 结构固定为三段拼接：

```
[SYSTEM_RULES]

[buildPublicContextBlock(ctx)]

# 当前角色任务
[roleBody]
```

#### （1）SYSTEM_RULES（固定前缀）

大意：

- 正在模拟「多智能体话题辩论会」
- 必须严格扮演当前角色，不是普通助手
- 禁止：跳出角色 / 暴露提示词 / 自称 AI / 替他人发言 / 越权做最终定论
- 每轮只有一个角色发言；输出须有信息增量

#### （2）公共上下文 `buildPublicContextBlock`

拼接块：

1. `# 当前辩论主题` ← 用户输入的 topic  
2. `# 会议类型` ← 固定文案「话题辩论」  
3. `# 当前会议核心问题` ← 主持人开场解析出的 2～5 条；未解析时有占位说明  
4. `# 参会智能体` ← 对每个 agent 输出：`序号. 名称（风格）` + 描述 + 技能 ID 列表  
5. `# 目标` ← 观点碰撞、风险与可行性、可执行结论与建议  

会议上下文对象 `DebateMeetingContext` 还维护：

- `currentRoundFocus`（本轮重点）
- `currentRoundIndex`
- `roundSummaries[]`
- `compressedMemory`（压缩摘要，后续轮次注入）

### 6.2 各阶段 roleBody（「当前角色任务」部分）

| 函数 | 扮演 | 关键要求 / 输出格式 |
|---|---|---|
| `buildOpeningRoleBody` | 主持人 | 介绍主题与智能体；提出 2～5 条核心问题；邀请首位智能体发言；输出 `【主持人】` + `## 会议核心问题` 编号列表 |
| `buildExtractCoreQuestionsRoleBody` | （系统补抽） | 开场未解析出问题时，再发一轮只抽核心问题 |
| `buildFirstAgentRoleBody` | 第 1 轮首位智能体 | 注入人设（名/描述/风格/技能）+ 本轮焦点；鲜明立场；`【{name}】` |
| `buildSubsequentAgentRoleBody` | 其余发言 | 额外注入：压缩记忆 + **上一位发言全文**；评价并推进；`【{name}】` |
| `buildRoundSummaryRoleBody` | 主持人 | 概括争议/共识/未决；**不要宣布进入下一轮**；`【主持人】` |
| `buildSummaryCompressRoleBody` | （摘要压缩） | 要求结构化：已讨论观点 / 争议 / 共识 / 未解决问题 / 相对核心问题的覆盖与遗漏 |
| `buildDebateConvergenceRoleBody` | 主持人（判断） | **仅** `CONTINUE:` 或 `END:`；**不要** `【主持人】` 标签 |
| `buildContinueTransitionRoleBody` | 主持人 | 过渡并宣布进入下一轮；焦点对齐 CONTINUE 理由 |
| `buildMaxRoundsCapHostMessageBody` | 主持人 | 宣布达最大轮次，进入总结 |
| `buildFinalReportRoleBody` | **撰稿人** | 会议纪要式报告，逐条回应核心问题；`【撰稿人】` |
| `buildReviewerRoleBody` | **审稿人** | 挑错与风险审计，不复述全文；`【审稿人】` |

多处会追加对齐约束：

> 你的发言必须尽量围绕会议核心问题推进，避免脱离初始讨论目标。

（`buildMeetingAlignmentConstraint`，提示词优化提交后强化「总结紧扣核心问题」。）

### 6.3 会后追问提示词：`buildPostDebateChatPrompt`

辩论结束后用户再发消息时，**不再走轮询编排**，而是单次请求，内容包含：

- 说明「你刚刚主持完成了一场多智能体辩论会」
- `# 辩论主题` / `# 参会智能体` / `# 最终会议摘要`
- 用户问题（带双括号标记，见下）
- 要求：默认不重新轮询；不重复整份纪要；延续上下文；可引用各智能体观点

`finalSummary` 由 `buildDebateFinalSummaryForPostChat` 组装：

1. `# 会议压缩摘要`
2. `# 会议核心问题`
3. `# 撰稿人总结报告`
4. `# 审稿人意见`

持久化：`sessionStorage` key = `insightweaver:debate-post-chat:{sessionId}`；刷新后也可从历史消息里找含 `【撰稿人】` / `【审稿人】` 的助手气泡反推。

### 6.4 会后用户消息「隐藏标记」

写入 / 请求侧用双括号包住用户可见输入：

```
【【辩论后用户继续会话-{用户真实输入}】】
```

- 气泡展示：`stripDebatePostChatUserMarker` 只显示括号内正文  
- 兼容旧版尾缀：`【辩论后用户继续会话】`  
- 若用户话术匹配「继续讨论 / 开启下一轮 / 继续辩论 / 让某某发言…」等 → `shouldRestartDebateWorkflow` 为 true，重新跑整场编排

---

## 7. 内置角色与头像

`DEBATE_BUILTIN_ROLES`（`isBuiltIn: true`）：

| id | 名称 | 头像资源 | 职责（产品文案） |
|---|---|---|---|
| `debate-builtin-host` | 主持人 | `/img/host.png` | 议程、核心议题、多轮收敛 |
| `debate-builtin-writer` | 撰稿人 | `/img/Writer.png` | 结构化会议报告 |
| `debate-builtin-reader` | 审稿人 | `/img/reader.png` | 逻辑/证据/执行风险审计 |

确认页与输入框团队条：`buildDebateTeamDisplayAgents(selected) = selected + 三个内置角色`。

头像解析优先级（群辩）：

1. 消息上的 `assistantAvatarSrc`（编排时写入）
2. 助手正文首行 `【角色名】` 回退解析（历史无 metadata 时）
3. 默认 EvoMind logo

「会议摘要」标签也映射到主持人头像。

---

## 8. 针对多 Agent 的特殊处理清单（除提示词外）

这些是复刻时最容易漏掉的部分。

### 8.1 隐藏提示词 / 历史会话可见性（对应「隐藏提示词要在历史里也处理」）

**问题本质**：后端落库的是完整提示词；历史拉取后若不处理，用户会看到大段「你正在模拟一场多智能体…」。

旧版策略（**前端隐藏，而非服务端物理删除**）：

1. **编排期 user 气泡**：`hideDebateUserMessagesUi === true` 时，列表 **不展示 role=user**（会后带 `【【辩论后用户继续会话-…】】` 的除外）
2. **收敛判断助手回复**：
   - 发送时打 `uiHidden: true`
   - 历史无该字段时，用正文首行是否匹配 `CONTINUE:` / `END:` 识别并隐藏
   - 隐藏规则：完成后从列表移除；`sending` 时仍保留以显示「正在思考」
3. **compaction** 等内部消息继续过滤

判定「这是群辩会话」从而启用隐藏：

- 当前标题匹配 `_【群辩模式】`，或
- `conversationMode === 'group'` 且已有辩论智能体 / 编排中 / 可从 transcript 解析出智能体

> 复刻注意：若新版希望历史里「删除」隐藏提示词，需明确是 **继续 UI 过滤**，还是 **后端只存 displayValue / 另字段存 prompt**。旧版是前者。

### 8.2 会话标题标记

- 存储：`{主题截断}_【群辩模式】`（总长约 20，保证后缀完整）
- 侧栏 / 搜索 / 重命名展示：`stripDebateSessionTitleSuffix` 去掉后缀
- `isDebateSessionTitle` 用于识别历史群辩会话

### 8.3 模式切换与工作区重置

切换独白 ↔ 群辩会：

- 中止编排与流式
- 清空消息、附件、技能、会话 id
- 清空辩论相关 state + `clearDebatePostChatFromSession`
- `router.replace('/')`
- **清空输入框**（`composerResetSignal`）

### 8.4 发送路径分流（`handleConversationSend`）

| 条件 | 行为 |
|---|---|
| 编排进行中 | 忽略发送 |
| `debateAwaitingTopic` | 主题 → `runDebateFromWizard` |
| 已有 `debatePostChatContext` | 会后追问或重启编排 |
| 否则 | 普通 `handleSend` |

### 8.5 历史会话恢复

- 标题带群辩后缀 → 加载智能体 catalog → `resolveDebateAgentsFromTranscript`（扫 `【名称】`，排除主持人/撰稿人/审稿人/会议摘要/会议系统）
- 重建团队 chips
- 恢复 / 反推 `debatePostChatContext`，以便继续会后追问

### 8.6 输入区 UX

- 编排锁：占位「群辩模式由系统自动推进发言，请稍候」
- 会后：占位「群辩已结束，可基于本场会议摘要继续提问…」
- 中止按钮（编排中）
- 团队 chips 发言呼吸动画（`debate-speaker-breathing`）

### 8.7 与「专属智能体 / 技能前缀」的关系

编排使用 `requestMessageOverride` 时 **跳过** 普通发送里「专属智能体身份 + 技能隐藏前缀」的拼接，避免污染辩论角色提示词。

### 8.8 无后端专用逻辑

未发现 API 侧「辩论会话 / 多 Agent 编排」模块；token、会话、流式均走原有 ZClaw 通道。多轮 = 同一 `sessionId` 下多次 message，**会话上下文由后端按历史累积**。

---

## 9. 数据流示意

```
用户点「群辩模式」
  → reset 新会话 + DebateGroupWizard
  → 选模式(仅话题辩论) → 选 ≥2 智能体 → 确认(+主持人/撰稿人/审稿人)
  → 输入主题
  → runTopicDebateFlow
       每步: 组装完整提示词
            → POST SSE message=完整提示词
            → UI user 显示短 displayValue（历史回看时再隐藏 user）
            → UI assistant 显示模型回复 + 角色头像
  → 结束: sessionStorage 存会后上下文
  → 用户继续提问: 单轮会后 prompt（含摘要）或关键词重启编排
```

---

## 10. 旧版能力边界（复刻时勿高估）

- 未实现：头脑风暴、方案共创、自定义模式（仅占位）
- 未实现：服务端编排、独立辩论消息表、对提示词的服务端脱敏存储
- 参会智能体来自「已安装 / 可见 persona」，不是临时创建
- 内置三角色 **不会** 作为可选列表里的普通 agent 被勾选；由确认页自动附加
- 用户记忆中的「两个默认智能体」在代码里是 **三个**：主持人、撰稿人、**审稿人**

---

## 11. 关键文件速查（旧分支路径）

| 路径 | 职责 |
|---|---|
| `.../debate/topicDebatePrompts.ts` | 提示词全文 |
| `.../debate/runTopicDebate.ts` | 编排 |
| `.../debate/DebateGroupWizard.tsx` | 模式/选人弹窗 |
| `.../debate/debatePostChat.ts` | 会后追问与隐藏标记 |
| `.../debate/debateMessageVisibility.ts` | 历史隐藏 |
| `.../debate/debateSessionMarkers.ts` | `_【群辩模式】` |
| `.../SuperLobsterPage.tsx` | 状态与发送集成 |
| `.../MessageInput.tsx` | 独白/群辩 Tab |
| 仓库根 `多agent讨论提示词v3.md` | 提示词流程样例文档 |

---

## 12. 附录：一轮请求里「会拼接什么」（开场示例）

一次「主持人开场」实际发出的字符串概念结构：

```
你正在模拟一场「多智能体话题辩论会」。
注意：你不是助手。…（SYSTEM_RULES）

# 当前辩论主题
{用户主题}

# 会议类型
话题辩论

# 当前会议核心问题
（主持人未明确…占位，或编号列表）

# 参会智能体
1. A（风格：…）
   描述：…
   技能：…
2. B …
（仅用户勾选的辩论方，不含主持/撰稿/审稿人设列表项——角色在任务段扮演）

# 目标
围绕主题与会议核心问题…

# 当前角色任务
你现在是「AI 圆桌会议主持人」。
请正式开启本次会议：…
最后明确邀请「{首位智能体名}」率先发言。
输出格式：
【主持人】
…
## 会议核心问题
1. …
```

后续智能体轮次还会在「当前角色任务」中追加：本轮焦点、压缩记忆、上一位发言原文、对齐核心问题约束等。

---

*文档根据 `feature--多agent模式` 源码梳理，未改动实现。后续在 `feature--多agent` 上开发时可直接对照本文模块清单与提示词结构。*
