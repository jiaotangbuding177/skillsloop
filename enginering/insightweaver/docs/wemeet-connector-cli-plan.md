# InsightWeaver 腾讯会议连接器落地方案 v2.0（方案 X：沙箱 CLI 直连）

> 版本：v2.0 ｜ 日期：2026-08-21 ｜ 状态：**已定案（用户选定方案 X）**
> 方案 X：每个用户沙箱（OpenClaw 实例）内装官方 tmeet CLI，子 agent 直接操作腾讯会议——**零新表、零管理员配置、零自建应用、零平台后端模块**。
> 演进说明：生产若需"身份自有/平台可控"，参考 `docs/wemeet-connector-plan.md`（v1.2，自建应用路线），本文件为当前落地主方案。
> 事实依据：WorkBuddy tmeet 连接器接入指南（`C:\Users\44112\WorkBuddy\2026-08-18-12-41-07\腾讯会议连接器接入指南.md`）、tmeet 连接器定义与 SKILL（`C:\Users\44112\.workbuddy\connectors-marketplace\connectors\tmeet\`）、`@tencentcloud/tmeet` v1.0.15（MIT，GitHub TencentCloud/tencentmeeting-cli）。

---

## 0. 结论先行（TL;DR）

| 项 | 结论 |
|---|---|
| **接入方式** | 每个用户沙箱内 `npm install -g @tencentcloud/tmeet`，子 agent 用 tmeet 命令操作腾讯会议；用户授权走 OAuth2 **设备码**（`tmeet auth login --no-browser`） |
| **凭证管理** | 凭证由 tmeet 自管，AES-256-GCM 加密存沙箱本地 `~/.tmeet/`，**平台不落库、无感知** |
| **数据库** | **0 张新表**（不建 `EnterpriseWemeetAppConfig`、不建 `UserWemeetConnection`） |
| **平台侧改动** | 仅 2 处：① Skill 下发（`wemeet-connection` + 操作指南，复用飞书 sync 通道）；② `builtin-meeting-assistant` 激活（skillKeys 占位替换） |
| **管理员操作** | **零**——无配置表、无管理页 |
| **前置门槛** | **零**——无需开发者认证、无需 OAuth 应用申请、无需回调（复用 tmeet 内置官方凭证） |
| **工作量** | 后端 ~0.5–1 人日 + 沙箱验证 0.5 人日 |
| **最大风险** | 应用身份归属 **WorkBuddy 官方**——生产长期依赖他人凭证（详见 §9 风险 1） |

**一句话**：把 WorkBuddy 的 tmeet 连接器"复制"进每个用户的 OpenClaw 沙箱——Skill 引导 + CLI 直连，平台只负责把 skill 装进沙箱。

---

## 1. 背景与目标

### 1.1 为什么是方案 X

- 产品侧 `builtin-meeting-assistant`（会议助手）agent 已占位（`apps/api/src/agents/builtin-agent-catalog.ts:570`），`skillKeys` 声明 `"Tencent Meeting"` 但无实际能力——需补齐。
- 用户诉求明确：**不需要管理员配置，只需要每个用户沙箱内的子 agent 都可以连接**。方案 X 正好零配置满足。
- 事实基础：官方 CLI `@tencentcloud/tmeet` 存在（设备码授权、凭证本地加密、能力完整），与飞书 lark-cli 同构；WorkBuddy 已验证这条链路可用。

### 1.2 目标与非目标

| 目标（本次交付） | 非目标（明确不做） |
|---|---|
| 每个用户沙箱子 agent 可连接腾讯会议（设备码授权） | 平台侧连接管理（连接状态表/统一吊销/管理员 UI） |
| 会议生命周期：创建/查询/修改/取消、受邀成员管理 | 平台侧 token 存储与续期（凭证在沙箱，tmeet 自管） |
| 录制/纪要：列表、播放地址、智能纪要、转写 | 自建腾讯会议应用 / 开发者认证（生产演进见 v1.2） |
| 参会报告、会中控制（呼叫/踢出）、通讯录反查（严格限定） | Webhook 事件订阅、直播长尾配置 |
| `builtin-meeting-assistant` 激活 | 与飞书 skill 的联合编排 |

---

## 2. 总体架构

### 2.1 结构图

```
┌─────────────────────── insightweaver 平台 ───────────────────────┐
│  wemeet-connector-sync.service.ts（新增，轻量）                    │
│     └─ putManagedSkillInEnterpriseContext  → wemeet-connection    │
│     └─ writeMemoryFileInEnterpriseContext  → wemeet.md 操作指南    │
│  builtin-agent-catalog.ts：skillKeys "Tencent Meeting" → "wemeet-connection" │
└───────────────────────────────────────────────────────────────────┘
                        │ skill 下发（企业初始化/开通时）
                        ▼
┌──────────── 用户沙箱（OpenClaw 实例，per-user 隔离） ────────────┐
│  @tencentcloud/tmeet（npm 全局安装）                             │
│  子 agent：tmeet auth login --no-browser   ← 输出授权 URL        │
│            用户浏览器授权（meeting.tencent.com，300s 内）        │
│  凭证落沙箱 ~/.tmeet/（AES-256-GCM 加密，tmeet 自管）            │
│  子 agent：tmeet meeting +create / record / report / control …  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 与飞书连接器的模式对比（关键差异）

| 维度 | 飞书（现有） | 腾讯会议（方案 X） |
|---|---|---|
| CLI | lark-cli（官方） | **tmeet（官方，@tencentcloud/tmeet）** |
| 授权 | 平台发起设备流 + 平台存 token | **沙箱内 `tmeet auth login`，凭证在沙箱本地，平台无感知** |
| 凭证下发 | 平台解密后写 `connectors/feishu.json` | **不下发**——tmeet 自管 `~/.tmeet/` |
| Skill 安装时机 | 连接完成后下发 | **沙箱初始化即安装**（无平台连接态，改为"先装 skill、用时再授权"） |
| 新表 | UserFeishuConnection + EnterpriseFeishuAppConfig | **0 张** |
| 管理员 | 配置飞书应用（app-config 管理页） | **零** |

---

## 3. 沙箱内连接流程（核心时序）

### 3.1 首次连接（agent 引导）

```
用户对子 agent 说：「帮我开个 2 点的评审会」
        │
        ▼
agent 检查：tmeet auth status
        │
        ├─ Logged in → 直接进入 §3.2
        │
        └─ Not logged in（user config is empty）
             │
             ▼
        agent 设置环境变量（首次登录必做，无需询问用户）：
        TMEET_AGENT=OpenClaw（或 insightweaver 平台名）
        TMEET_MODEL=<当前模型名>
        │
        ▼
        agent 执行 tmeet auth login --no-browser（前台、阻塞 ≤300s）
        │
        ▼
        agent 把授权 URL 完整展示给用户，提示尽快在浏览器完成
        │
        ▼
        用户在浏览器打开 meeting.tencent.com 授权页 → 登录 → 授权
        │
        ▼
        CLI 自动轮询成功 → 凭证加密落盘 ~/.tmeet/ → Logged in
        │
        ▼
        agent 继续执行创建会议
```

### 3.2 已连接（日常使用）

```
agent 直接执行 tmeet 命令（--format json 机器可解析）
  tmeet meeting +create / tmeet meeting +list / tmeet record +list …
失败（token 过期）→ tmeet 自动刷新；刷新失效 → 提示用户在平台/沙箱重新授权
```

### 3.3 必须遵守的操作约束（对齐 tmeet 官方 SKILL）

| 约束 | 说明 |
|---|---|
| `auth login` 必须**前台运行** | 阻塞 ≤300s，后台方式（`&`）脱离控制终端会导致凭证写入失败 |
| 首次登录/切换模型必须设 `TMEET_AGENT` + `TMEET_MODEL` | 否则报错；设值时**不要询问用户**（agent 自行按当前上下文填写） |
| 已登录再 login | 报 `user has been initialized`，先 `logout` 再重登 |
| 未登录执行业务命令 | 报 `user config is empty`，先引导授权 |
| 授权 URL 必须完整展示给用户 | 不得省略；300s 超时作废需重新发起 |
| Hermes / 无默认浏览器场景 | 不要执行 `auth login`，改为告知用户在终端手动执行 |

---

## 4. Skill 设计（wemeet-connection）——核心交付物

### 4.1 skill 元信息

| 项 | 值 |
|---|---|
| skillKey | `wemeet-connection`（对齐 `feishu-connection` 命名） |
| 安装 | `npm install -g @tencentcloud/tmeet@latest`（metadata 声明 node 依赖，bin: tmeet） |
| 能力描述（注入系统提示） | 见 §4.3 |
| references | `references/wemeet-auth.md`、`wemeet-meeting.md`、`wemeet-record.md`、`wemeet-report.md`、`wemeet-contact.md`、`wemeet-control.md`、`wemeet-tshoot.md`（排障：日志导出/反馈，对应 §6 tshoot 模块） |

### 4.2 SKILL.md 全文草案

```markdown
---
name: wemeet-connection
description: 使用用户授权的腾讯会议账号操作会议：创建/查询/修改/取消会议、管理受邀成员、
  查询参会报告、获取云录制与智能纪要/转写、会中呼叫/踢出成员。用户要求腾讯会议相关操作时直接执行
  （tmeet CLI 优先）；回答时先说明能做什么，不主动提及授权流程等技术细节，仅在实际操作失败
  （未连接/未授权）时引导用户完成腾讯会议连接。
metadata: {"clawdbot":{"emoji":"📅"},"openclaw":{"emoji":"📅","install":[{"id":"node","kind":"node","package":"@tencentcloud/tmeet","bins":["tmeet"],"label":"Install tmeet (node)"}]}}
---

# wemeet-connection

以当前用户身份操作腾讯会议。凭证由 tmeet CLI 自管（~/.tmeet/，AES-256-GCM 加密），
已登录即为已授权；未登录时按「首次连接」章节引导用户授权。

## 用户询问「能否操作腾讯会议」时的回答

直接展示能力列表，不主动提及凭证/授权技术细节：

> 可以的。我能通过腾讯会议相关能力：
> **会议**：创建/查询/修改/取消会议（支持快速会议、预约会议、周期性会议），管理受邀成员
> **录制与纪要**：云录制列表、播放地址、智能纪要、转写详情与搜索
> **参会报告**：参会人列表、等候室成员记录、导出参会明细
> **会中控制**：呼叫成员入会、踢出会议成员
> 有具体需求直接告诉我（比如「帮我开一个 2 点的评审会」），我来处理。

## 首次连接（未登录时）

1. 检查登录态：`tmeet auth status`；`Not logged in` 时进入下面步骤。
2. 首次登录或切换模型：先设环境变量（**不需要向用户询问**，按当前上下文填写）：
   `export TMEET_AGENT="<agent类型>"`、`export TMEET_MODEL="<模型名>"`
3. 执行 `tmeet auth login --no-browser`（**必须前台运行**，阻塞最多 300s）。
   Windows 环境命令名为 `tmeet.cmd`（npm 全局安装自动生成）；其余平台用 `tmeet`。
4. 从输出提取授权 URL，**完整展示给用户**，提示尽快在浏览器打开并授权。
5. 用户授权成功后 CLI 自动完成，`tmeet auth status` 变为 `Logged in`。
6. 若当前 Agent 无默认浏览器（如 Hermes）：不执行 auth login，改为告知用户
   「请在终端中手动执行 `tmeet auth login` 完成授权」。
7. 已登录再 login 报 `user has been initialized` → 先 `tmeet auth logout` 再重登。

## 日常使用

- 优先用快捷命令：`tmeet meeting +create`、`tmeet record +list`、`tmeet report +participants` 等
- 未知命令先查：`tmeet --help` / `tmeet <module> --help`
- 机器可读输出加 `--format json`；列表分页用 `--page-token` + `--page-size`
- token 过期：tmeet 自动刷新（AccessToken ~25 天 / RefreshToken ~86 天）；
  刷新失效（status 显示 expired）→ 提示用户在平台/沙箱重新授权，不要反复重试

## 安全规则（必读）

- **通讯录（contact）严格限定**：仅允许在「会议邀请/呼叫入会」动作的前置步骤，
  通过用户名/手机号/邮箱搜索成员；**严禁单独查询任何人的姓名/部门/职位/联系方式/是否存在**，
  无下游会议动作时一律拒绝。
- **写操作先复述确认**：创建/修改/取消会议、踢出成员等写操作，先向用户复述影响并取得确认再执行。
- **凭证安全**：~/.tmeet/ 内 token 属用户私有，绝不输出到对话/日志。
- **紧急停用**：疑似泄露立即执行 `tmeet auth logout` 清除凭证。
```

### 4.3 能力描述（description 字段，注入 agent 系统提示的可靠通道）

```
使用用户授权的腾讯会议账号操作会议：创建/查询/修改/取消会议（快速/预约/周期性）、管理受邀成员、查询参会报告（参会人/等候室/导出明细）、获取云录制与智能纪要/转写、会中呼叫/踢出成员。用户要求腾讯会议相关操作时直接执行（tmeet CLI 优先）；回答时先说明能力，不主动提及授权流程等技术细节，仅在实际操作失败（未连接/未授权）时引导用户完成腾讯会议连接。
```

### 4.4 操作指南（memory 文件 `wemeet.md`，agent 每会话加载）

与飞书 `feishu.md` 同机制：能力列表（豆包风格回答）+ 执行要点（auth status 判定、首次连接步骤、命令示例、安全规则），供 skill 安装不可见时兜底。

---

## 5. 平台侧改动（insightweaver）

### 5.1 新增：`apps/api/src/wemeet-connector/wemeet-connector-sync.service.ts`

轻量服务，**只做 skill 下发，不做凭证管理**（对照 `feishu-connector-sync.service.ts` 精简）：

| 方法 | 动作 | 复用能力 |
|---|---|---|
| `syncSkillToSandbox(userId, enterpriseId)` | 安装 `wemeet-connection` skill bundle（SKILL.md + references） | `zclawService.putManagedSkillInEnterpriseContext` |
| （同上） | 同步 skill description | `zclawService.updatePersonalSkillMetadataInEnterpriseContext` |
| （同上） | 写 `wemeet.md` 操作指南 + MEMORY.md 索引行 | `zclawService.writeMemoryFileInEnterpriseContext` / `appendMemoryIndexInEnterpriseContext` |
| `removeSkillFromSandbox(userId, enterpriseId)` | 停用时卸载 skill + 删操作指南（best-effort） | 对应 delete 方法 |

**触发时机**（与飞书的关键差异）：飞书是"连接成功后下发"；方案 X **没有平台连接态**，改为**沙箱开通时即安装**（幂等，重复调用无害）：

- **新增沙箱**：挂接 `ZclawService.provision()`（`zclaw.service.ts:587`，`ensureAgentInstanceForCurrentScope` 成功后）→ 用户开通沙箱即装 skill。
- **存量用户补装**：provision 只覆盖新建沙箱，历史沙箱收不到 skill——必须另设一个幂等补装触发点（如会议助手 agent 启用时、或用户登录时 reconcile），保证存量用户也能收到。

### 5.2 修改：`builtin-agent-catalog.ts`

- `builtin-meeting-assistant.skillKeys`：`"Tencent Meeting"`（占位）→ `"wemeet-connection"`（真实 skillKey）。
- 其余字段（名称/描述/capabilities）不动。

### 5.3 明确不做

| 项 | 原因 |
|---|---|
| Prisma 新表 / 迁移 | 凭证在沙箱本地，平台无状态 |
| 管理页 / admin controller | 用户明确不需要管理员配置 |
| OAuth client / token 续期服务 | tmeet 自管 |
| 凭证下发（connectors/wemeet.json） | 不需要，tmeet 自管 ~/.tmeet/ |

---

## 6. 能力清单（tmeet → 业务能力）

| 模块 | 能力 | 会议助手场景 |
|---|---|---|
| meeting | 创建/查询/更新/取消，周期性会议，受邀成员管理 | 「帮我开 2 点评审会」「查我明天有哪些会」 |
| record | 录制列表、播放地址、智能纪要、转写详情与搜索 | 「把昨天的录制纪要整理一下」 |
| report | 参会人列表、等候室记录、导出参会明细（异步任务） | 「谁没来参加上周的会」 |
| contact | 通讯录检索（**严格限定**会议邀请/呼叫前置） | 「邀请张三进这个会」（按姓名搜手机号） |
| control | 呼叫成员入会、踢出会议成员 | 「把李四踢出会议」 |
| tshoot | 导出本地日志（过滤时间/打包 zip）、反馈上报 | 排障 |
| auth | login / logout / status | 连接/解绑 |

---

## 7. 落地步骤（分阶段 + 验收）

### M1 Skill 下发通道（0.5 人日）

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | 写 `wemeet-connector-skill.ts`（SKILL.md + references bundle，§4 草案落地） | lint 通过 |
| 2 | 写 `wemeet-connector-sync.service.ts`（§5.1）+ module 注册 | 单测：调用 zclawService mock 断言 skill 安装/描述/记忆写入 |
| 3 | 挂接 `ZclawService.provision()`（`zclaw.service.ts:587`，agent 开通成功后）安装 skill；存量沙箱另设幂等补装触发点（如会议助手 agent 启用时） | 真实沙箱内出现 skill 与 `wemeet.md`；存量用户沙箱补装生效 |

### M2 会议助手激活（0.5 人日）

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | `builtin-agent-catalog.ts` skillKeys 替换（`"Tencent Meeting"` → `"wemeet-connection"`；`validateSkillKeysForEnterprise` 为空实现无校验风险） | 目录更新生效；前端 agent 详情 skill 展示正常（`mapDisplayAgent.ts:25` 按远程 skill 列表过滤，skill 安装后应显示 `wemeet-connection`，未命中时回退原始 key） |
| 2 | 沙箱内手测完整链路 | 子 agent 对话：「帮我开个 2 点评审会」→ 引导授权 → 创建成功返回 join_url |

> **M2 测试依赖**：使用用户**个人腾讯会议账号**（手机号验证后登录授权）。个人版部分接口受限（如邀请参会者），验收用例按实际授权能力选取（创建/查询/取消会议、录制列表等），受限能力在操作指南中标注。**前置检查**：沙箱验证时确认 `TMEET_CLI_CONFIG_DIR` + `TMEET_CLI_DATA_DIR` 指向持久化目录后，重建沙箱可免重授权（该缓解依赖自定义路径语义，官方 README 未直接保证，需实测确认）。

### M3 验证与收尾（0.5 人日）

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | 全链路回归 | `pnpm lint` + `pnpm build`（含 @insightweaver/api TS 编译）通过 |
| 2 | 补测试 | `wemeet-connector-sync.service.test.ts`（skill bundle 内容断言、幂等断言） |
| 3 | 文档收尾 | 本方案标记"已落地"，记录沙箱验证截图/日志 |

---

## 8. 风险与注意事项

| 风险 | 等级 | 说明与对策 |
|---|---|---|
| **身份归属 WorkBuddy 官方应用** | **高** | tmeet 内置固定 clientId（官方凭证）；WorkBuddy 侧轮换凭证/加风控即全平台失效。**对策**：验证期可接受；产品化前评估演进到 v1.2 方案 Y（自建应用） |
| 沙箱重建丢凭证 | 中 | `~/.tmeet/` 随沙箱重建丢失 → 用户需重新授权一次。**对策**：将 `TMEET_CLI_CONFIG_DIR`（凭证/用户配置目录，默认 `~/.tmeet/`）+ `TMEET_CLI_DATA_DIR`（加密数据目录）均指向持久化目录（如工作区 `connectors/tmeet/`）；或接受"重建后重连"并写入操作指南。**注意**：自定义路径语义未经官方文档明确保证，落地前需在沙箱实测确认 |
| 授权 300s 超时 | 中 | 用户未及时完成授权即作废。**对策**：agent 明确提示时限；超时重新发起 |
| 多企业共享同一实例 | 中 | 一个沙箱多企业场景下凭证只有一个（~/.tmeet/ 单实例）。**对策**：与飞书 enterpriseId 专属文件策略对齐评估——按企业切换 `TMEET_CLI_CONFIG_DIR`（如 `connectors/tmeet-<enterpriseId>/`）实现隔离；当前按"每用户单凭证"假设 |
| contact 滥用 | 中 | 通讯录反查严格限定会议邀请/呼叫场景。**对策**：SKILL.md 明令 + 拒绝规则 |
| 免费账号能力限制 | 低 | tmeet 走用户自己的账号，能力取决于账号版本（个人版部分接口受限如邀请参会者）；按实际授权开放 |
| 环境变量缺失 | 低 | 首次登录报错。**对策**：SKILL.md 明确 agent 自行设置 TMEET_AGENT/TMEET_MODEL，不询问用户 |

---

## 9. 工作量汇总

| 阶段 | 后端(人日) | 验证(人日) | 依赖 |
|---|---|---|---|
| M1 Skill 下发通道 | 0.5 | — | 无（纯代码） |
| M2 会议助手激活 | 0.5 | 0.5 | M1 |
| M3 验证收尾 | 0.5 | — | M2 |
| **合计** | **1.5** | **0.5** | — |

**总投入约 2 人日**，无外部依赖（不需要腾讯侧任何申请）。

---

## 10. 生产演进（当"身份自有/平台可控"成为硬要求时）

切换到 `docs/wemeet-connector-plan.md`（v1.2 自建应用路线）：
- insightweaver 注册用户级应用（开发者实名 + OAuth 内测预约/或企业版密钥对）；
- 平台持有应用凭证（env），沙箱内改为「平台凭证 + 设备码」或 fork tmeet CLI（MIT）注入自有凭证；
- 届时新增 `UserWemeetConnection`（用户 token 持久化）并补管理侧能力。
