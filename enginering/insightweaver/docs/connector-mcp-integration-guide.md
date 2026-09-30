# 连接器是怎么"接"进来的？——13 个连接器（MCP / 第三方服务）接入流程详解

> 读者对象：想快速搞懂 InsightWeaver 连接器体系的人。
> 写作原则：用大白话讲清楚"谁、在什么时候、把什么、放到了哪里"，再给代码坐标，方便你按图索骥。
> 代码基线：`feature/wtcfix`（2026-09）。代码是唯一真相，本文档描述与代码冲突时以代码为准。

---

## 0. 一句话结论

平台本身**不保存你的第三方账号密码**，也不把第三方数据搬进自己的数据库。

连接器做的事只有一件：**帮你在"你的 AI 智能体（Agent）住的沙箱"里，把"授权凭证 + 操作手册 + 工具脚本"三样东西放好**。放好之后，聊天时 Agent 自己就会照着操作手册、拿着你的凭证去调用第三方（飞书/腾讯会议/邮箱……）干活。

整个接入体系可以用一句话概括：

> **授权搬运工 + 文件协议**：用户把第三方授权交给我们 → 我们原样转交到 Agent 的沙箱工作区（凭证文件）→ 顺手把"技能包（SKILL）"和"操作指南（memory 文件）"也装进去 → Agent 每次会话自动加载指南，按需用凭证调用第三方官方 CLI / MCP / OpenAPI / IMAP-SMTP。

---

## 1. 先说清楚两个口径问题

### 1.1 到底是 13 个还是 14 个连接器？

代码里实际存在的是：

- **13 个第三方业务连接器**（后端各占一个 `apps/api/src/*-connector/` 目录）：
  飞书 feishu、企业微信 wecom、钉钉 dingtalk、腾讯会议 wemeet、腾讯文档 tencent-docs、金山文档 kdocs、ima、网易邮箱 netease-mail、QQ 邮箱 qq-mail、GetNote getnote、企查查 qcc、Canva canva、Gitee 企业版 gitee-ent。
- **1 个聚合服务** `connector-status-aggregate`（不接第三方，只负责把 13 家的连接状态一次性汇总给前端面板）。

所以"连接器相关目录"共 14 个。产品口径（[`docs/evomind-technical-architecture.md`](./evomind-technical-architecture.md) 第 2.4 节、4.7 节）写的"第三方连接器 14 个 / 连接器 ×14"，是把上面 13+1 一起算了；聊天框里的连接器面板（`ConnectorsPanel`）实际渲染 **13 张卡片**。本文按 13 家业务连接器 + 1 个聚合来写。

> 提示：代码里若干注释（聚合 controller/hook 顶部）还写着"12 个"，是早期只聚合 12 家时留下的陈旧注释，实际代码已收编 13 家（canva、gitee-ent 是后加的）。

### 1.2 连接器和"MCP"是什么关系？项目里 MCP 有三种不同含义

这是最容易混的地方。同一个仓库里 "MCP" 出现在三个完全不同的场景：

| 场景 | 角色 | 说明 | 代码位置 |
|---|---|---|---|
| ① 连接器走"厂商官方 MCP 服务" | 客户端 | Canva、Gitee 企业版、企查查、腾讯文档等厂商对外提供官方 MCP 服务（HTTPS + Token）。用户去厂商控制台拿 Token 贴进平台，平台用 MCP `initialize` 握手探测 Token 是否有效 | 各 `*-mcp.client.ts`、`*-openapi.client.ts` |
| ② 行业研究工具（与连接器无关） | 客户端 | 行业研究"大纲/正文"两个自建 MCP 服务（`MCP_OUTLINE_URL`/`MCP_CONTENT_URL` 等），供报告 Agent 调工具 | `apps/api/src/mcp/`（mcp-session/tool-registry） |
| ③ 沙箱内的官方 CLI | 非 MCP | 腾讯会议 `tmeet`、企业微信 `wecom-cli`、钉钉 `dws`、金山 `kdocs-cli`、飞书 `lark-cli` 是厂商发布的 CLI 程序，不是 MCP。Agent 在沙箱里直接执行它们 | 各 `*-orchestrator.ts`、`*-cli.runner.ts` |

你问的"14 个连接器 MCP 服务"，准确说法是：**13 个连接器里，一部分（Gitee 企业版、腾讯文档、Canva、企查查）接的是厂商官方 MCP/OpenAPI 服务；其余走厂商官方 CLI 或邮箱协议**。它们共享同一套"接入流程设计"，本文 5、6 两节拆开讲。

---

## 2. 三个底层心法（看懂这套设计的钥匙）

### 心法一：凭证"零平台化"——平台不当地址簿，只当搬运工

除了极少数例外（见下），连接器一律 **0 张新表、凭证不进数据库、不进日志、不进接口响应**。

- 用户填的 Token/授权码，只在后端内存里过一手，然后**写进 Agent 沙箱的工作区文件**（如 `connectors/qq-mail.json`）；
- 平台侧判断"是否已连接"，就是**去沙箱读凭证文件在不在**；
- 解绑 = **删掉沙箱里的凭证文件**（双路径都删，best-effort）。

为什么敢这么干？因为凭证的最终消费者是 Agent，不是平台。平台存一份还要多做一层加密、泄露面反而更大。少数例外：

- **飞书**：平台需要"代管 App 凭证 + 自动续期 refreshToken"，因此走 `SecretCryptoService` 加密落库，还带"refresh 锁"防止一次性 refreshToken 并发刷新互相顶掉（`feishu-connector.service.ts`）。
- **企业微信 / 腾讯会议**：DB 里只存**状态元数据**（如 `lastSyncedAt`、用户昵称），凭证本身由 CLI 自管。

### 心法二：沙箱 = Agent 的"家"。一切下发物都是文件

每个用户在企业里，都有一个自己的 Agent 运行环境（代码里叫 **KM 实例 / 企业上下文沙箱**，`enterpriseOpenClawInstanceId` 指的就是它）。平台后端通过 `ZclawKmAgentClient`（`apps/api/src/zclaw/zclaw-km-agent.client.ts`）以 HTTP 操作这个环境的四类"文件侧"：

| 沙箱内位置 | 放什么 | 平台调用（`ZclawService` 封装，`zclaw.service.ts`） |
|---|---|---|
| **托管技能**（managed skill） | 每个连接器的"上岗手册"SKILL.md 等文件 | `putManagedSkillInEnterpriseContext` / `updatePersonalSkillMetadataInEnterpriseContext` |
| **工作区文件** | 凭证文件、脚本 bundle、CLI 状态文件（都在 `connectors/` 目录下） | `writeWorkspaceFileInEnterpriseContext` / `read…` / `delete…` / `stat…` |
| **长时记忆文件** | `qq-mail.md`、`wecom.md` 等"操作指南"，Agent **每个会话都加载** | `writeMemoryFileInEnterpriseContext` |
| **记忆索引**（MEMORY.md） | 一行索引：`- [QQ 邮箱操作指南](qq-mail.md) — …` | `appendMemoryIndexInEnterpriseContext`（幂等，含标记行则跳过） |

这四类"文件"构成了连接器的全部能力下发面。**没有注册中心、没有配置表、没有热插拔框架**——就是"把文件放到 Agent 每天上班都看得见的地方"。

> "沙箱在哪？"：`resolveZclawTargetForUser(userId, enterpriseId)` 会把（用户,企业）解析成一个目标实例（个人 scope 或企业 scope），`runWithTarget` 用 AsyncLocalStorage 让后续请求都打到该实例。所以连接器天然是 **用户级 × 企业上下文** 的（请求头 `x-enterprise-id` 决定当前企业）。

### 心法三：连接 = 授权 + 验证；验证不通过就回滚，不留垃圾

所有连接器都是同一个"连接三步曲"：

1. **拿授权**（范式不同：粘贴 / OAuth 回调 / 设备码扫码，见第 5 节）；
2. **写沙箱**（凭证文件 + skill + 指南，幂等可重放）；
3. **探测验证**（真的拿凭证去第三方试一下），**失败则清理刚写的凭证**再报错。

探测方式各家不同，但都是"低副作用探一下"：

- 官方 MCP 服务类：发一个 JSON-RPC `initialize` 握手（如 `canva-mcp.client.ts`、`qcc-mcp.client.ts`、`gitee-ent` 的 HTTP 直调），200+正常返回即 Token 有效；401/403 判为凭证无效；
- 邮箱类：用授权码做一次 SMTP `verify`（`qq-mail-script-runner.ts`）；
- 沙箱 CLI 类：连接后让 Agent 在沙箱里跑 `tmeet auth status` / `kdocs-cli auth status` 之类，把结果写回文件，平台读文件判断。

> 有意思的细节：**平台不做第三方数据的大规模同步**（不把飞书消息/邮箱全文拉进自家 DB）。"sync service"里的 sync，指的是把上面那些文件同步进沙箱（凭证/skill/指南），以及企业切换时重新同步——不是数据同步。Agent 要用数据时，是**按需实时调第三方**。

---

## 3. 全局架构图

```
┌────────────┐   ① 点"连接器"   ┌────────────────────────── 平台后端 apps/api ──────────────────────────┐
│ 用户浏览器  │ ───────────────▶ │ 聊天页 MessageInput ──▶ ConnectorsPanel（13 张卡片）                    │
│            │                  │        │                                                              │
│  (扫码/授权 │   ② 授权交互      │  各 *-connector 模块（13 个，NestJS 模块自治）                           │
│   页面/弹窗)│ ◀─────────────── │   controller(HTTP) → service(业务) → sync(写沙箱) → probe(探测)          │
└────┬───────┘                  │        │                    │                                         │
     │ ③ 授权结果               │        │                    │ ④ 文件协议：写/读/删                       │
     ▼                          │        │                    ▼                                         │
┌───────────┐   (浏览器回跳)    │   ┌───────────────────────────────────────────┐                     │
│ 厂商 OAuth │ ◀────────────────│   │ KM Agent 沙箱（每个 用户×企业 一个实例）      │                     │
│ 授权服务   │                  │   │  ├─ managed skills：SKILL.md（上岗手册）      │                     │
│ 官方 MCP   │◀── ⑥ Agent 按需调用│  │  ├─ 记忆：MEMORY.md 索引 + xxx.md 操作指南    │                     │
│ 官方 OpenAPI│── 凭证/脚本/CLI ─▶ │  │  ├─ 工作区 connectors/：凭证 json、脚本 js、 │                     │
│ 官方 CLI    │                  │   │  │    CLI 配置目录、pending/标记文件          │                     │
│ IMAP/SMTP   │                  │   │  └─ 沙箱内 shell：可装 CLI、跑 node 脚本       │                     │
└───────────┘                  │   └───────────────────────────────────────────┘                     │
                              │        │  ⑤ 状态查询：凭证文件在不在？聚合降级                          │
                              └────────┴──▶ GET /connector-statuses（connector-status-aggregate）──▶ UI │
```

参与方只有四个，永远只在这四者之间流转：

1. **用户浏览器**——负责"人肉授权"（贴 Token、扫码、点同意）；
2. **平台后端（apps/api）**——流程编排者，但不持有凭证；
3. **KM Agent 沙箱**——凭证/手册/脚本的"家"，也是最终干活的地方；
4. **第三方厂商**（飞书/腾讯/Canva/…）。

---

## 4. 一次连接的通用生命周期

不管哪家连接器，宏观上都走这 8 步（差异只在第 1 步"怎么拿到授权"）：

```
[1] 拿授权     用户粘贴 Token / 跳 OAuth 授权 / 扫码（设备码、浏览器 URL）…各家不同
[2] 后端校验   格式清洗（去控制字符/首尾空白、域名白名单、长度上限）→ 再探测前的基本校验
[3] 写沙箱     凭证 → connectors/<name>[-<enterpriseId>].json（双路径，内容一致）
[4] 下发资产   skill 包（SKILL.md）+ 操作指南（记忆文件）+ MEMORY.md 索引行 + 脚本 bundle
[5] 探测验证   initialize 握手 / SMTP verify / CLI status —— 失败则删掉 [3][4] 的东西并报错
[6] 状态可见   UI 显示已连接；此后 GET /connector-statuses 每次都读沙箱文件判断
[7] 日常使用   Agent 会话里自动加载指南 → 读凭证 → 注入环境变量 → 跑脚本/CLI → JSON 结果回话
[8] 解绑       删沙箱凭证文件（best-effort），skill/指南尽量保留或一并移除
```

**日常使用的闭环（第 7 步展开）**，以 QQ 邮箱为例（真实文案来自 `qq-mail-connector-sync.service.ts` 里的 `QQ_MAIL_MEMORY_GUIDE`）：

1. 用户发消息："帮我看看今天有没有新邮件"；
2. Agent 会话启动时加载了 MEMORY.md，里面有一行索引指向 `qq-mail.md`；
3. Agent 读指南，知道：凭证在 `connectors/qq-mail.json`（先看企业专属文件），
4. Agent 用 `sed` 从凭证文件取出 email 和 authCode 注入环境变量（**禁止写进对话/日志**）；
5. 执行 `node connectors/qq-mail-scripts/imap-light.js check`，得到 JSON 结果；
6. 发信前必须先向用户复述收件人/主题/附件并等确认（防误发）；
7. 指南还要求：执行写操作前校验凭证文件里的 `enterpriseId` 与当前会话企业一致（多企业共享实例时的安全隔离）。

> 也就是说：**"接入"不是开发一个接口让前端调，而是写一份"Agent 也能读懂的手册 + 能跑的脚本"，把 Agent 变成那个第三方系统的熟练操作员。**

---

## 5. 13 家连接器，按"授权方式"分四类

这是理解各家差异的关键。授权方式决定了整个连接的交互长什么样。

### A 类 · 浏览器 OAuth 回调式 —— 目前只有 Canva

代表：**Canva**（`canva-connector/`）。用户点"连接"→ 浏览器新窗口去 Canva 授权页 → 授权完 Canva 302 跳回平台 → 平台换 Token。

时序（代码注释原话，`canva-connector.service.ts` / `canva-oauth.client.ts`）：

```
init：DCR 动态注册 OAuth 客户端（无需预配 env，0 env）→ PKCE 生成 code_verifier/challenge
     → state 随机≥128bit，存 Redis（TTL 5min，单次消费=读取即删）→ 返回授权 URL
回调：Canva 302 到公开端点 /canva-connector/auth/callback（无 JWT，所以独立 controller，
     安全全靠 state）→ 消费 state → code 换 token → MCP initialize 探测（canva-mcp.client.ts）
     → 写沙箱凭证（双路径）+ 下发 skill；任一步失败不写凭证/清理 → 返回自关 HTML 页面
     （window.close() 弹窗场景 / 兜底提示直开场景）
状态：读沙箱凭证文件（存在=connected，缺失=unbound，沙箱不可达也降级 unbound 不抛 500）
解绑：删沙箱凭证文件（best-effort）
```

关键点：**回调端点不能带 JWT**（浏览器直跳），所以是公开端点 + `state` 一次性会话保安全；会话里绑定了 userId/enterpriseId/PKCE verifier/clientId。

### B 类 · 官方 CLI + 沙箱内 Agent 编排授权（设备码/扫码/浏览器登录）

代表：**腾讯会议（tmeet）、企业微信（wecom-cli）、钉钉（dws）、金山文档（kdocs-cli）、飞书（lark-cli，变体）**。

这类是"零粘贴"的：用户不用填任何 Token，打开平台给的授权 URL/二维码，用手机或浏览器确认即可。但授权动作发生在**沙箱内部**——因为凭证要落在沙箱里给 Agent 用，平台干脆让 Agent 自己去完成授权。

**核心机制：平台用"hidden 消息"指挥沙箱里的 Agent 干活**（`wemeet-connector-orchestrator.ts` 是最好的一篇教材）：

- 平台往沙箱发一条**隐藏编排指令**（合成会话 ID 如 `hidden-wemeet-*`，**不写数据库**；会话创建后缓存复用，避免每次 10-20s 建会话）；
- 指令内容是一段自然语言+bash，让 Agent 去：装官方 CLI（`npm install -g @tencentcloud/tmeet`）→ 后台起 `tmeet auth login --no-browser` → 轮询日志提取授权 URL → **把 URL 写回工作区文件** `connectors/wemeet-pending.json`；
- 平台**不阻塞等 Agent 回复**（短超时通道只等首事件），而是后台任务轮询 pending 文件，拿到 URL 再返回给前端渲染授权弹窗；
- 授权完成后，Agent 侧监控脚本把 `{"status":"Logged in","userName":…}` 写回 pending 文件，平台 5 秒轮询读到即视为已连接。

围绕这套"文件回传协议"，编排器里还设计了大量细节，读代码时你会看到：

| 机制 | 文件 | 作用 |
|---|---|---|
| 授权 URL/状态回传协议 | `connectors/wemeet-pending.json` | Agent ↔ 平台的"信箱" |
| 在途准备状态 | `connectors/wemeet-init-state.json` | `preparing/ready/error`，5 分钟窗口；防止关弹窗重开时重复装环境 |
| CLI 标记 | `connectors/tmeet-cli-installed.json` | 存在 → 走快速通道，跳过 skill 重装 |
| 快/慢双通道 | `FAST_INSTRUCTION` / `INSTALL_INSTRUCTION` | 先发短指令试 CLI 是否已装；报 `cli-not-found` 再发安装指令 |
| 后台授权监控 | 沙箱内 nohup 轮询 `auth status` | 授权完成秒级回传，不用再驱动一次 Agent |
| cancel / revoke | `CANCEL_INSTRUCTION` / `REVOKE_INSTRUCTION` | 清 pending、杀后台 login 进程、`auth logout` + 删配置目录 |

各家 CLI 不同、交互载体不同（腾讯会议给浏览器 URL、企业微信/钉钉出二维码、金山文档出浏览器登录 URL），但骨架完全一致。飞书略有不同（**变体**）：它是平台"豆包式零配置"——应用凭证由平台/企业统一配置，甚至支持一键代建应用（`feishu-app-registration.store.ts`），Device Flow 设备码扫码，token 自动续期且加密落库（一次性 refreshToken + 并发刷新锁），另需把 `lark-cli` 相关技能下发沙箱。

> 演进注记：wemeet 服务文件顶部注释还写着"后端服务器 spawn tmeet"——那是早期"平台本地起 CLI"的旧方案，现已被 orchestrator 的"沙箱内编排"取代（模块注释：替代本地 spawn）。读代码时以 orchestrator 为准。

### C 类 · 页面粘贴"官方 MCP Token / OpenAPI 凭证"式（千问同款配置弹窗）

代表：**Gitee 企业版（MCP 组织令牌）、腾讯文档（MCP Token）、企查查（API Key）、ima（Client ID + API Key）、GetNote（Client ID + API Key）**。

交互最简单：聊天框里点连接 → 弹"千问同款配置弹窗" → 用户去厂商控制台生成凭证贴回来 → 提交。后端流程（模块注释原话）：

```
用户页面粘贴凭证 → 格式校验/清洗 → 后端内存中转写沙箱凭证文件（connectors/<name>.json 双路径）
→ 下发 skill（如 Gitee 下发 gitee-ent-connection skill + 操作指南）
→ 探测验证：MCP initialize / OpenAPI 配额端点 / HTTP 直调官方 MCP 底层 API
→ 凭证平台不落库、0 张新表
```

这就是用户问题里"连接器 MCP 服务"最典型的一类：**厂商（Gitee/腾讯文档/企查查）对外提供的是官方 MCP 服务，我们的连接器负责"接进来"**——管理 Token、验证 Token、把技能和凭证放进沙箱。Token 有效期/scope 管理在厂商侧，平台不做 token 刷新（Canva 的 OAuth 除外，Canva 是平台托管刷新；Gitee/腾讯文档/企查查 Token 过期了用户重新贴）。

### D 类 · IMAP/SMTP 邮箱授权码式

代表：**QQ 邮箱（qq.com/foxmail.com）、网易邮箱（163/126/yeah.net）**。

用户填"邮箱地址 + 16 位授权码"（网页端生成，非登录密码）。这类没有官方 MCP/CLI 可编排，平台直接下发**收发双脚本**到沙箱工作区：

- `connectors/qq-mail-scripts/smtp.bundle.js`（发信：HTML/附件/抄送/密送）
- `connectors/qq-mail-scripts/imap-light.js`（收信/搜索/读详情/列文件夹）

探测 = 用授权码做 SMTP verify；失败清理。域名单白校验（qq 系只收 `@qq.com/@foxmail.com`，别的引导去网易连接器）。

> 为什么脚本要 bundle 成单文件下发？注释给了答案：**超托管 skill 单文件大小上限**，所以脚本走"工作区文件通道"而不是塞进 skill。

### 13 家 × 授权方式速查

| 类别 | 连接器 | 用户在 UI 做什么 | 凭证去向 |
|---|---|---|---|
| A 浏览器 OAuth | Canva | 新窗口点允许 | 沙箱凭证文件（平台不落库） |
| B 沙箱内 CLI 授权 | 腾讯会议、企业微信、钉钉、金山文档 | 开授权 URL / 扫码 | CLI 配置目录（沙箱内，如 `connectors/tmeet-<enterpriseId>/`）；飞书特殊：平台加密落库 |
| C 粘贴凭证 | Gitee 企业版、腾讯文档、企查查、ima、GetNote | 贴 MCP Token / API Key | 沙箱凭证文件（平台不落库） |
| D 邮箱授权码 | QQ 邮箱、网易邮箱 | 贴邮箱+授权码 | 沙箱凭证文件（平台不落库） |

---

## 6. 后端代码地图：一个连接器 = 一个自治模块

所有连接器目录（`apps/api/src/<name>-connector/`）结构高度统一，形成了事实上的"模块模板"：

| 文件（× = 全部 13 家有，△ = 部分有） | 职责 | 一眼判断方法 |
|---|---|---|
| `*-connector.module.ts` × | NestJS 模块：头部注释就是该连接器的**完整流程说明**（阅读入口） | 13 家注释风格一致，均写明"凭证不落库/0 张新表"或例外 |
| `*-connector.controller.ts` × | HTTP 层：连接/状态/解绑 + 授权轮询端点；挂 `JwtAuthGuard` + `ZclawEnterpriseContextInterceptor`（读 `x-enterprise-id`） | 头部注释 = 该类授权方式的说明书 |
| `*-connector.service.ts` × | 业务编排：连接三步曲（写沙箱→下发→探测→失败清理）、getStatus、revoke | 注释里常带状态机说明 |
| `*-connector-sync.service.ts` × | **沙箱同步服务**：凭证文件写/读/删（双路径）、skill+指南+记忆索引下发；常量区定义了沙箱内路径约定 | `connectors/<name>[-<enterpriseId>].json` |
| `*-connector-skill.ts` × | 构建 SKILL 包（`buildXxxSkillBundle()` 返回 files 数组）+ 操作指南正文 + MEMORY.md 索引行 | skill 描述会随系统提示加载，是 Agent 行为引导的可靠通道 |
| `*-orchestrator.ts` △ | 沙箱内编排授权（wecom/dingtalk/kdocs/wemeet）：hidden 指令 + 文件回传协议 | 常定义 pending/init-state/marker 路径常量 |
| `*-oauth.client.ts` / `*-openapi.client.ts` / `*-mcp.client.ts` △ | 与厂商协议层：OAuth 换 token、OpenAPI 调用、MCP initialize 探测 | 探测专用 client 注释常写"仅验证 token 有效性" |
| `*-script-runner.ts` / `*-imap-light.ts` / `*-smtp-bundle.ts` / `*-cli.runner.ts` △ | 沙箱内可执行脚本的生成器/本地探测执行 | 邮箱双脚本、CLI 引导 |
| `*-device-session.store.ts` / `*-auth-session.store.ts` △ | 设备码/授权会话的临时存储（Redis） | 带 TTL + 单次消费 |
| `*-app-registration.store.ts` △ | 平台代建应用（飞书） | — |

**路径约定（读代码时反复出现，务必记住）**：

- 凭证文件在沙箱工作区：`connectors/<name>.json`；
- **企业专属**副本：`connectors/<name>-<enterpriseId>.json`（双路径、内容一致）。原因：**多个企业可能共享同一个 KM 实例**，企业专属文件名保证互不覆盖；Agent 按"当前会话企业"优先读专属文件，读不到再读通用文件；
- CLI 配置目录：`connectors/tmeet-<enterpriseId>`、`connectors/wecom-<enterpriseId>` 等（通过 `TMEET_CLI_CONFIG_DIR` 等环境变量重定向）；
- 记忆指南：`<name>.md`（根级，Agent 每会话加载），MEMORY.md 追加索引行（含标记行则跳过，幂等）；
- 授权回传协议文件：`connectors/<name>-pending.json`、`<name>-init-state.json`、CLI 安装标记 `connectors/<name>-cli-installed.json`。

**模块注册**：13 个模块 + McpModule 等在 `apps/api/src/app.module.ts` 统一 import，模块间无共享注册表——`connector-status-aggregate` 是唯一"横切"模块，直接依赖 13 个 connector service。

---

## 7. 前端闭环：一个面板 + 一个聚合接口

- **入口**：聊天输入框的"连接器"按钮（`MessageInput.tsx` 里 `t('connector')`），打开 `ConnectorsPanel`（在 `FeishuConnectorDialog.tsx` 里导出，仿技能库面板结构，卡片网格两列，对齐 WorkBuddy 布局）。
- **13 张卡片**：每张卡片是一个 `<XxxConnectorEntryCard>`（各连接器自己的 Dialog 文件导出），卡片显示连接状态，点击打开对应连接弹窗（授权 URL 弹窗 / 扫码框 / 粘贴配置弹窗）。
- **状态数据**：`useConnectorStatuses` hook（`apps/web/src/hooks/useConnectorStatuses.ts`）打开面板时调一次 **`GET /connector-statuses`** 聚合接口（后端 `Promise.allSettled` 并发查 13 家 getStatus，单家失败降级 `{bound:false,status:'error'}` 不阻断其余）；前端带 SWR 缓存（有缓存先渲染+后台刷新）+ in-flight 请求去重，按企业隔离缓存；连接/解绑成功后 `invalidate()` 失效重拉。
- **授权中的推进**：授权 URL/二维码就绪后，前端 5 秒轮询 status；后端"惰性推进"（如 wemeet 单次读 pending 文件就返回，不重复驱动 Agent）；失败显示原因卡片，允许重试（如飞书"重新绑定"）。
- **企业切换**：前端监听 `ACTIVE_ENTERPRISE_CHANGED_EVENT`，切换企业后面板按新企业重新拉状态——对应后端"企业切换沙箱同步与吊销"的逻辑。

---

## 8. 数据与安全底线（设计红线）

1. **凭证不落库**（0 张新表）是默认项：凭证只在内存中转 → 写沙箱；例外明确且最小：飞书加密存储（需代管刷新）、wecom/wemeet 仅状态元数据。
2. **凭证不进日志、不进错误信息、不进响应体**：错误统一转"友好文案"（如 QQ 邮箱的"去网页端重新生成授权码"）。
3. **清洗**：Token/授权码粘贴常带隐藏控制字符，写入前一律去控制字符+trim（多个 client 都有 eslint-disable 注释说明）。
4. **探测失败即回滚**：先写后探，失败删已写凭证，避免沙箱残留无效凭证。
5. **沙箱不可达降级**：状态查询时沙箱挂了返回 unbound，不抛 500 阻塞面板。
6. **多企业隔离**：企业专属凭证文件 + Agent 操作前校验凭证内 `enterpriseId`。
7. **OAuth 安全**：state 随机 ≥128bit、Redis TTL 5 分钟、单次消费；公开回调端点不含敏感逻辑。
8. **防误操作**：邮箱发信前 Agent 必须复述并等用户确认。
9. **并发防护**：飞书 refresh 锁（一次性 refreshToken 防并发）、wemeet status 2s 短缓存（防弹窗多轮询打爆）、init 互斥锁（同一用户企业只允许一个授权在途）。

---

## 9. 常见疑问（Q&A）

**Q1：为什么要费劲把凭证写进沙箱文件，而不是平台数据库存一份？**
因为凭证的消费者是沙箱里的 Agent（它要注入环境变量跑 CLI），不是平台接口。存平台 = 多一层中转多一个泄露面；写沙箱 = Agent 直接可用，平台只用"文件在不在"判断状态，顺带实现了 0 张新表。

**Q2：为什么"授权"这种交互也要让沙箱里的 Agent 去跑？**
因为授权产物（CLI 登录态/配置目录/密钥链）必须落在沙箱里。让 Agent 在沙箱里完成授权，凭证从出生就在沙箱，平台全程不碰。这就是 B 类连接器用 hidden 指令编排的动机。

**Q3：hidden 消息是什么？会不会污染聊天记录？**
hidden 会话 ID 形如 `hidden-wemeet-*`，合成会话不写库，指令走"短超时通道"只等首事件确认送达；Agent 在沙箱执行并把结果写回工作区文件，平台读文件拿结果。相当于平台给 Agent 发"私聊任务"，不占用户会话。

**Q4：连接器会定时把第三方数据同步进平台吗？**
不会。sync service 同步的是"凭证+技能+指南"进沙箱（以及企业切换时的重同步），不是第三方业务数据。数据查询全部是 Agent 按需实时调用第三方（这既是隐私设计也是架构简化）。

**Q5：换企业/换沙箱实例了怎么办？**
每个连接器在授权和状态查询时都带 enterpriseId；企业切换时后端做"沙箱同步"（把凭证/skill 发到新企业上下文实例）或按需吊销。凭证文件双路径 + 企业专属命名就是为了多企业共享实例时互不污染。

**Q6：`mcp/` 目录和连接器什么关系？**
没关系（是容易误会的重名）。`apps/api/src/mcp/` 是行业研究功能的自研 MCP 客户端（大纲/正文两个外部 MCP 服务、SSE 会话、工具注册缓存），与 13 个连接器是完全独立的两条线。

---

## 10. 13+1 速查表（一页纸）

| # | 连接器 | 目录 | 授权范式 | 用户操作 | 探测 | 主要能力（来自产品文案摘录） |
|---|---|---|---|---|---|---|
| 1 | 飞书 | feishu-connector | B 变体（设备码扫码，平台代建/代管应用） | 一键创建应用→扫码 | OAuth 换取+探测 | 即时通讯、日历、云文档、表格、Base、知识库、审批、OKR 等全产品（lark-cli） |
| 2 | 企业微信 | wecom-connector | B（wecom-cli 扫码） | 企业微信 App 扫码选组织+机器人 | CLI 授权探测 | 消息、日程、通讯录、文档表格、会议、邮件、微盘、待办 |
| 3 | 钉钉 | dingtalk-connector | B（dws 扫码） | 钉钉 App 扫码 | CLI 授权探测 | 消息、DING、待办、文档、知识库、钉盘、AI 听记纪要、OA 审批等 23 域 |
| 4 | 腾讯会议 | wemeet-connector | B（tmeet 设备码） | 浏览器打开授权 URL 登录 | `auth status` | 会议全生命周期、云录制纪要、参会报告、会中呼叫/踢出 |
| 5 | 腾讯文档 | tencent-docs-connector | C（MCP Token 粘贴） | 贴 MCP Token | OpenAPI 探测 | 智能文档/Excel/PPT/思维导图/流程图创建编辑、空间目录、搜索 |
| 6 | 金山文档 | kdocs-connector | B（kdocs-cli 浏览器授权） | 浏览器登录 WPS | CLI 授权探测 | WPS 文档/表格/PPT/PDF、云盘、AI PPT、个人知识库 |
| 7 | ima | ima-connector | C（OpenAPI 凭证粘贴） | 贴 Client ID + API Key | OpenAPI 探测 | 知识库查询/整理、笔记读写、网页/公众号导入、全文搜索、AI 摘要 |
| 8 | 网易邮箱 | netease-mail-connector | D（IMAP/SMTP 授权码） | 贴邮箱+授权码 | SMTP verify | 收发邮件、搜索、附件下载（163/126/yeah.net） |
| 9 | QQ 邮箱 | qq-mail-connector | D（IMAP/SMTP 授权码） | 贴邮箱+16 位授权码 | SMTP verify | 收发邮件、搜索、读详情（qq.com/foxmail.com） |
| 10 | GetNote | getnote-connector | C（OpenAPI 凭证粘贴） | 贴 Client ID + API Key | OpenAPI 探测 | 笔记管理、语义搜索、知识库整理、图片上传 |
| 11 | 企查查 | qcc-connector | C（API Key 粘贴） | 贴 API Key（Bearer 前缀可省） | MCP initialize | 工商信息、股权结构、风险核验、法律法规/司法案例检索 |
| 12 | Canva | canva-connector | A（OAuth PKCE 回调） | 新窗口允许授权 | MCP initialize | 按描述生成海报/PPT、编辑设计、素材、品牌资源、多格式导出 |
| 13 | Gitee 企业版 | gitee-ent-connector | C（MCP 组织令牌粘贴） | 贴 MCP 组织令牌 | MCP initialize（HTTP 直调） | 工作项、Pull Request、仓库/成员/标签、Scrum 迭代 |
| +1 | 状态聚合 | connector-status-aggregate | —（非连接器） | — | — | `GET /connector-statuses` 并发聚合 13 家状态，失败降级 |

---

## 11. 想深入时去哪读（阅读路线）

按"先懂骨架、再钻细节"的顺序：

1. 任意一个 `*-connector.module.ts` 的头部注释 —— 该连接器流程的最浓缩版本；
2. `qq-mail-connector` 全家（最短最完整：module → sync → service → skill）—— 页面版/邮箱类模板；
3. `wemeet-connector-orchestrator.ts` —— B 类沙箱编排的完整教材（pending 文件协议、快慢双通道、幂等在途）；
4. `canva-connector`（oauth client + callback controller + mcp client）—— A 类 OAuth 回调 + MCP 探测模板；
5. `zclaw/zclaw.service.ts` 的"EnterpriseContext"系列方法 + `zclaw-km-agent.client.ts` —— 沙箱文件通道底层；
6. `connector-status-aggregate/` + `apps/web/src/hooks/useConnectorStatuses.ts` —— 状态闭环；
7. 需求侧设计文档：`docs/wemeet-connector-plan.md`（首版方案，含飞书对照表）、`docs/wemeet-connector-cli-plan.md`（v2 沙箱 CLI 方案，讲清了 Skill 下发与 agent 集成）、`docs/evomind-technical-architecture.md`（4.7 连接器生态）。

---

*本文档由代码阅读整理而成，示例时序均引用真实代码注释；如与最新代码有出入，请以代码为准并顺手更新本文档。*
