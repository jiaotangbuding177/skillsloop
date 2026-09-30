# InsightWeaver 腾讯会议（Wemeet）连接器落地方案

> ⚠️ **2026-08-21 定案更新**：用户选定**方案 X（沙箱 CLI 直连，零配置）**，当前落地以 `docs/wemeet-connector-cli-plan.md`（v2.0）为准；本文件（v1.2，自建应用路线）保留作为**生产演进参考**（身份自有/平台可控时启用）。
> 版本：v1.2 ｜ 日期：2026-08-21 ｜ 状态：已被 v2.0（方案 X）取代为演进参考
> v1.1 修正：核实官方文档后**推翻"企业开发者认证"门槛说法**——实为"开发者实名认证"（个人可实名）；新增关键事实「OAuth 2.0 第三方应用目前内测、预约登记审核制」，接入路径扩为 A/B/C 三条。
> v1.2 修正（依据 WorkBuddy tmeet 连接器接入指南 + @tencentcloud/tmeet v1.0.15 源码核实）：①**推翻"腾讯会议无官方 CLI"**——官方 CLI `@tencentcloud/tmeet` 存在（MIT 开源，OAuth2 **设备码**授权，凭证 AES-256-GCM 加密），与 lark-cli 同构；②授权方式由"Authorization Code + 回调"改为**设备码（RFC 8628）**，与飞书一致、**无需回调 URL**；③新增 §3.1「复用官方 tmeet vs 自建应用」身份对比——WorkBuddy 指南"纯用户授权"成立的前提是 **tmeet CLI 内置 WorkBuddy 官方应用固定凭证**（不支持自定义 client），insightweaver 作为独立第三方无法直接复用其身份。
> 关联文档：`docs/mcp-agent-plan.md`、`docs/mcp-autonomous-integration.md`（MCP 集成先例）、`apps/api/src/feishu-connector/`（本方案直接复用的模式源）、`C:\Users\44112\.workbuddy\connectors-marketplace\connectors\tmeet\`（WorkBuddy tmeet 连接器定义与 SKILL）

---

## 0. 结论先行（TL;DR）

| 项 | 结论 |
|---|---|
| **接入方式** | 复用现有 `feishu-connector` 模式，新增 `wemeet-connector` 模块（OAuth2 **设备码授权** + 凭证加密存储 + Skill 下发沙箱），与飞书**完全同构**：官方 CLI 已存在（`@tencentcloud/tmeet`），授权无需回调页 |
| **"要不要认证"（关键澄清）** | **取决于用谁的应用身份**：复用 WorkBuddy 官方 tmeet（腾讯内部已注册）→ 用户侧纯授权、零门槛，但身份/数据归属 WorkBuddy，insightweaver 不能作为自有产品能力复用；**自建应用** → 需一次性开发者实名认证（个人可做）+ OAuth 应用申请（内测预约制），此后用户侧体验与指南一致（设备码扫码即连） |
| **工作量** | 参照飞书连接器（~2,559 行代码）：后端 ~1,800 行 + Web ~600 行 + Skill/Agent ~300 行，约 2 个迭代 |
| **落地节奏** | M0 路径/身份确认（自建应用 or 复用）+ 凭证准备 → M1 连接能力（设备码 + 凭证）→ M2 会议 API（创建/查询/取消/参会者/录制/纪要）→ M3 技能化（Skill 下发 + `builtin-meeting-assistant` 激活） |
| **最终效果** | 用户在工作台绑定自己的腾讯会议账号后，可对话式完成「创建会议、查会议详情、拉参会成员、看录制/纪要」；产品侧会议助手 agent 由占位变为可用 |

**关键决策（默认采纳，可在评审时推翻）**：
1. **首选自建应用 + OAuth2 设备码授权**（用户级），体验对齐飞书/WorkBuddy 指南；自建需一次性实名认证 + OAuth 应用申请。若内测预约周期不可控，降级为**企业内部开发（Secret 鉴权，企业版/商业版密钥对）**，无审核排队（详见 §3.1）。
2. **复用飞书连接器的全部骨架**：`service / oauth.client / store / admin.controller / skill` 五件套，逐文件改写，不新建范式。
3. **CLI 策略修正**：官方 CLI `@tencentcloud/tmeet` 存在且与 lark-cli 同构——但**内置固定应用凭证、不支持自定义 client**（源码核实）。因此 agent 侧 Skill 采用**双模式**：自研/自建设备流优先；若未来 CLI 支持自定义应用或 fork 改造（MIT），再切 CLI 模式（对齐 lark-cli）。

---

## 1. 背景与目标

### 1.1 为什么现在接

- 产品侧 `builtin-meeting-assistant`（会议助手）agent **已占位**（`apps/api/src/agents/builtin-agent-catalog.ts:570`），`skillKeys` 已声明 `"Tencent Meeting"`，但该 skill 无任何实际能力实现——接入是**补齐已承诺能力**，不是新需求。
- 平台已跑通"连接器"范式：飞书（完整落地）、企微/钉钉（UI 已有 Dialog）。腾讯会议是自然补位，复用成本低。

### 1.2 目标与非目标

| 目标（本次交付） | 非目标（明确不做） |
|---|---|
| 用户级 OAuth 绑定腾讯会议账号 | 腾讯会议客户端内嵌 SDK / 会中实时能力 |
| 会议生命周期：创建 / 查询 / 修改 / 取消 | 直播、同声传译、报名等长尾配置（API 预留字段，不做 UI） |
| 参会成员查询、录制文件列表 | Webhook 事件订阅（v2 单独排期） |
| agent 技能化：Skill 下发 + 会议助手激活 | 与飞书 skill 的联合编排（如"会议后自动发纪要"） |

---

## 2. 现状盘点（复用资产）

| 资产 | 位置 | 现状 | 本次动作 |
|---|---|---|---|
| 会议助手 agent 占位 | `apps/api/src/agents/builtin-agent-catalog.ts:570` | `skillKeys` 含 `"Tencent Meeting"`，能力为空 | 保留占位，接入真实 skillKey 后激活 |
| 飞书连接器（模式源） | `apps/api/src/feishu-connector/`（2,559 行） | 完整：OAuth + 加密存储 + 状态机 + skill 下发 | **逐文件复制改写**为 wemeet 版 |
| 三方连接数据模型 | `packages/db/prisma/schema.prisma` | `UserFeishuConnection` / `UserWecomConnection` / `UserDingtalkConnection` | 新增 `UserWemeetConnection` + `EnterpriseWemeetAppConfig` |
| 连接器 UI 组件 | `apps/web/src/components/super-lobster/FeishuConnectorDialog.tsx` 等 | 飞书/企微/钉钉各一套 | 新增 `WemeetConnectorDialog`（复用同一套交互） |
| 凭证加密 | `apps/api/src/common/secret-crypto.service.ts` | AES-256-GCM | 直接复用，零改动 |
| Skill 下发通道 | `feishu-connector-sync.service.ts` → OpenClaw 沙箱 | 凭证写 `connectors/feishu.json` | 平行实现 `connectors/wemeet.json` |

---

## 3. 腾讯会议开放平台能力与授权模型

### 3.1 接入身份与路径对比（决策依据）

#### 3.1.1 关键认知：用"谁的应用身份"接入，决定要不要认证

> 依据：WorkBuddy tmeet 连接器接入指南（`C:\Users\44112\WorkBuddy\2026-08-18-12-41-07\腾讯会议连接器接入指南.md`）+ `@tencentcloud/tmeet` v1.0.15 源码核实（GitHub TencentCloud/tencentmeeting-cli，MIT）。

| 维度 | X. 复用 WorkBuddy 官方 tmeet | Y. 自建腾讯会议应用 ✅ 本项目 |
|---|---|---|
| 应用身份 | tmeet CLI **内置 WorkBuddy 官方应用固定凭证**（无 config 命令、**不支持自定义 client**） | insightweaver 自己在开放平台注册应用 |
| 用户侧体验 | 纯 OAuth 设备码授权，**零认证零回调** | 同为设备码授权（扫码即连），**认证仅在开发期发生一次** |
| 门槛 | 无（WorkBuddy 已注册） | **开发者实名认证**（个人可做）+ OAuth 应用申请（内测预约制） |
| 身份/数据归属 | **归属 WorkBuddy 平台**——insightweaver 复用等于借用他人应用身份，用户授权数据归 WorkBuddy 视角，商业/合规不可接受 | 归属 insightweaver 自己 |
| 结论 | 只适合 WorkBuddy 生态内使用，**不作为本项目方案** | ✅ 正解：一次注册，永久自有 |

> 所以"为什么 WorkBuddy 指南只要用户授权，我们的方案却要认证"——**不是流程差异，是身份差异**：WorkBuddy 是腾讯自家产品，官方应用已注册完毕；insightweaver 是独立第三方，必须自己完成应用注册（实名认证即可，个人可做）。注册完成后，**用户侧体验与指南完全一致**（设备码扫码授权）。

#### 3.1.2 自建应用后的三条鉴权路径

| 维度 | A. OAuth 2.0 用户级应用 ✅ 首选 | B. OAuth 2.0 账户级应用 | C. 企业内部开发（Secret 鉴权） |
|---|---|---|---|
| 身份粒度 | 每个用户授权自己的账号（openId） | 企业管理员安装，管理**全账户**会议/录制/用户数据 | 企业统一身份（SecretId + SecretKey + APPID + SDKID 签名） |
| 接入门槛 | **开发者实名认证**（个人即可）+ 创建应用；⚠️ **OAuth 第三方应用目前内测、预约登记审核制** | 同左（内测预约制） | **购买腾讯会议企业版/商业版**，自动开通 API 能力，管理员在【用户中心→高级】建密钥对，**无审核排队** |
| 用户体验 | 与飞书一致：用户各自设备码扫码绑定 | 无需用户逐个授权，但为账户级（管理员视角） | 无需绑定，所有调用以企业应用身份出现 |
| 能力边界 | 用户自己的会议/录制（"查看和管理您的会议"等权限范围） | 账户下所有用户的会议/录制（适合内部仪表盘/统一管理） | 企业版/商业版账号会议，个人版不可用 |
| 适用场景 | 工作台面向最终用户的连接器（**本次目标**） | 企业统一管理场景（备选） | 内部工具 / 快速落地 / OAuth 内测未通过时的降级 |
| Token | access_token 6h / refresh_token 30d | 同左 | JWT 自行签发 |

**决策**：A 为产品化正解但受内测预约约束；**若预约审核周期不可控，切 C（企业版密钥对）先行交付**——无认证/审核排队，能力差异仅是"用户级绑定"变"企业身份"（用户绑定 UI 仍保留，接入 C 后各用户共享企业身份，可按业务表做 userid 映射）。B 仅在企业需要账户级统一管理时启用。

### 3.2 OAuth 2.0 授权流程（设备码 Device Flow，RFC 8628——与飞书同款，无需回调）

> 依据：tmeet CLI 即采用 OAuth2 设备码授权（`tmeet auth login --no-browser` 输出授权 URL，用户浏览器完成，CLI 轮询结果，凭证 AES-256-GCM 加密落盘）。

```
用户点击「连接腾讯会议」
        │
        ▼
POST /api/wemeet/auth/init            ← 后端请求 device code（RFC 8628）
        │
        ▼
返回 { verification_url, user_code, device_code }
        │（前端弹出授权窗：展示 URL + 短码，或直接跳转）
        ▼
用户在浏览器打开 verification_url，登录腾讯会议并授权（300s 内）
        │
        ▼
后端轮询 token 端点（grant_type=urn:ietf:params:oauth:grant-type:device_code）
        │  └── authorization_pending → 继续轮询（间隔 5s）
        │  └── 成功 → access_token + refresh_token
        ▼
凭证 AES-256-GCM 加密入库 → 状态 connected → 可选下发沙箱
        │
        ▼
Token 自动续期：refresh_token 轮换（对齐飞书 refreshLocks 刷新锁）
```

> ✅ 设备码授权**不需要回调 URL、不需要公网 HTTPS**——与飞书连接器完全一致，Web 端复用 Device 授权对话框轮询交互（`FeishuDeviceAuthDialog` 模式），开发环境零额外配置。tmeet CLI 的 300s 阻塞/超时作废行为同样适用。

### 3.3 核心 API 清单（OAuth 模式，域名 `https://api.meeting.qq.com/v1`）

| 能力 | 方法与路径 | 说明 |
|---|---|---|
| 创建会议 | `POST /meetings` | 快速会议(type=1)/预约会议(type=0)，支持密码、静音、等候室、录制等 settings |
| 查询会议详情 | `GET /meetings/{meeting_id}` | 含 join_url、密码、状态 |
| 查询会议列表 | `GET /meetings?userid=&instanceid=` | 可按时间范围分页 |
| 修改会议 | `PUT /meetings/{meeting_id}` | 改主题/时间/配置 |
| 取消会议 | `DELETE /meetings/{meeting_id}` | |
| 参会成员列表 | `GET /meetings/{meeting_id}/participants` | 入会/离会时间、设备 |
| 录制文件列表 | `GET /records` | 云录制（需企业支持云录制） |
| 用户信息 | `GET /users/{userid}` | 绑定后校验 openId 显示名 |

公共请求头（OAuth 模式）：`Authorization: Bearer <access_token>`、`X-TC-AppId`、`X-TC-Registered: 1`（**必带**，否则 userid 被当未注册用户，会议不可见）、`Content-Type: application/json`。

常用错误码（需在 service 层统一映射）：

| 错误码 | 含义 | 处理 |
|---|---|---|
| 10001 | 参数校验失败 | 转 400，回显字段 |
| 10004 | 无权限 | 检查 scope / 转 403 |
| 20001 | 会议不存在 | 转 404 |
| 401 | token 过期/无效 | 触发自动刷新；刷新失败 → 状态置 `expired`，引导重新授权 |
| 429 | 频率限制（约 20 次/秒） | 指数退避重试 |

### 3.4 权限 Scope（以开放平台实际下发为准）

建议申请：`meeting:meeting:read`（查会议/参会者）、`meeting:meeting:write`（创建/修改/取消）、`meeting:user:read`（用户信息）、`meeting:record:read`（录制）。scope 名称以开放平台「权限管理」页实际提供为准，接入时拉取并写入 `EnterpriseWemeetAppConfig.scope`。

---

## 4. 总体架构设计

### 4.1 模块结构（对齐 feishu-connector 五件套）

```
apps/api/src/wemeet-connector/
├── wemeet-connector.module.ts          # 模块装配（imports: Database/Redis/Common/Zclaw）
├── wemeet-connector.controller.ts      # 用户侧：连接管理 + 会议业务（JwtAuthGuard）
├── wemeet-connector-admin.controller.ts# 管理侧：企业应用凭证 CRUD（AdminGuard）
├── wemeet-oauth.client.ts              # OAuth 2.0 客户端（授权URL/换token/刷新/用户信息）
├── wemeet-meeting.client.ts            # 会议业务 API 客户端（创建/查询/取消/参会者/录制）
├── wemeet-connector.service.ts         # 连接状态机（unbound→pending_auth→connected→expired→error）
├── wemeet-app-config.store.ts          # 企业应用凭证读取（AES-256-GCM 解密）
├── wemeet-session.store.ts             # 授权会话暂存（Redis TTL，防 state 重放）
├── wemeet-connector-sync.service.ts    # 凭证同步下发 OpenClaw 沙箱（connectors/wemeet.json）
├── wemeet-connector-skill.ts           # SKILL.md 生成（OpenAPI 直调模式）
└── dto/                                # 请求/响应 DTO + 校验
```

### 4.2 数据流

```
Web (WemeetConnectorDialog)
   │  auth/init → 跳转授权 → auth/callback
   ▼
wemeet-connector.controller ──► wemeet-oauth.client ──► 腾讯会议开放平台
   │                                                          │
   │ 会议操作（创建/查询…）                                    │ Bearer token
   ▼                                                          ▼
wemeet-meeting.client ◄────────────────────────────────  api.meeting.qq.com/v1
   │
   ├─► UserWemeetConnection（凭证密文，AES-256-GCM）
   ├─► wemeet-session.store（Redis）
   └─► wemeet-connector-sync.service ──► OpenClaw 沙箱 connectors/wemeet.json
                                          └──► 会议助手 agent 通过 wemeet-connection skill 操作
```

---

## 5. 数据模型设计（Prisma）

在 `packages/db/prisma/schema.prisma` 新增两个模型，字段对齐飞书命名风格：

```prisma
/// 企业级腾讯会议 OAuth 应用配置（管理员在平台配置一次）
model EnterpriseWemeetAppConfig {
  id                 String   @id @default(uuid())
  enterpriseId       String   @unique
  /// 腾讯会议 OAuth 应用 client_id（明文）
  clientId           String
  /// client_secret（AES-256-GCM 密文）
  clientSecretEncrypted String
  /// 授权回调地址（与开放平台登记一致）
  redirectUri        String
  /// 已申请 scope
  scope              String?
  createdBy          String?
  createdAt          DateTime @default(now())
  updatedAt          DateTime @updatedAt
  isDeleted          Boolean  @default(false)
  enterprise         Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
  @@index([enterpriseId, isDeleted])
  @@map("enterprise_wemeet_app_configs")
}

/// 用户级腾讯会议连接：一人一企业一条，凭证 AES-256-GCM 加密
model UserWemeetConnection {
  id                    String    @id @default(uuid())
  userId                String
  enterpriseId          String
  status                String    @default("pending_auth") // pending_auth/connected/expired/error
  clientId              String                            // 明文
  clientSecretEncrypted String                            // 密文（冗余存，供沙箱直调）
  accessTokenEncrypted  String?
  refreshTokenEncrypted String?
  scope                 String?
  wemeetOpenId          String?   // 腾讯会议 open_id
  wemeetUserName        String?   // 显示名（前端展示）
  tokenExpiresAt        DateTime? // access_token 6h
  refreshExpiresAt      DateTime? // refresh_token 30d
  lastSyncedAt          DateTime?
  lastError             String?
  createdAt             DateTime  @default(now())
  updatedAt             DateTime  @updatedAt
  isDeleted             Boolean   @default(false)
  user                  User       @relation(fields: [userId], references: [id], onDelete: Cascade)
  enterprise            Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
  @@index([userId, enterpriseId, isDeleted])
  @@map("user_wemeet_connections")
}
```

同步在 `User` / `Enterprise` 模型上追加反向关系：`wemeetConnections UserWemeetConnection[]`、`wemeetAppConfig EnterpriseWemeetAppConfig?`。

迁移命令：`corepack pnpm --filter @insightweaver/db db:migrate --name add_wemeet_connector`

---

## 6. 后端 API 设计

### 6.1 连接管理（`/api/wemeet/`，对齐飞书语义）

| 方法 | 路径 | 说明 | 返回 |
|---|---|---|---|
| POST | `/auth/init` | 发起设备码：请求 device_code + user_code + verification_url（存 Redis，5min TTL） | `{ verificationUrl, userCode, sessionId }` |
| POST | `/auth/poll` | 轮询授权结果（authorization_pending → 继续；成功 → 换 token 加密入库 → connected） | `{ status, wemeetUserName? }` |
| GET | `/auth/status` | 连接状态查询（含脱敏 clientId、openId、token 到期时间） | `{ bound, status, ... }` |
| POST | `/refresh` | 手动刷新 token（自动续期失败时兜底） | `{ status }` |
| POST | `/sync-sandbox` | 主动下发凭证到 OpenClaw 沙箱 | `{ syncedAt }` |
| DELETE | `/connection` | 解绑：清凭证 + 通知沙箱删除 `wemeet.json` | `{ ok }` |

### 6.2 会议业务（`/api/wemeet/meetings`，JWT 登录 + 已绑定为前提）

| 方法 | 路径 | 说明 | 关键入参 |
|---|---|---|---|
| POST | `/` | 创建会议（快速/预约） | `subject, type, startTime, endTime, password?, invitees?, settings?` |
| GET | `/` | 我的会议列表（按 openId 查） | `startTime?, endTime?, page?` |
| GET | `/:meetingId` | 会议详情（含 join_url） | — |
| PUT | `/:meetingId` | 修改会议 | `subject?, startTime?, settings?` |
| DELETE | `/:meetingId` | 取消会议 | — |
| GET | `/:meetingId/participants` | 参会成员 | `page?` |
| GET | `/records` | 云录制列表 | `meetingId?` |

统一响应包裹：业务错误走 `{ code, message }` 信封（对齐现有 R(T) 风格），token 失效时返回 `WEMEET_TOKEN_EXPIRED`（前端据此引导重新授权）。

### 6.3 管理侧（`/api/admin/wemeet/app-config`，AdminGuard）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/app-config` | 查询企业应用配置（脱敏） |
| POST | `/app-config` | 保存 clientId / clientSecret / 权限 scope（secret 加密） |
| DELETE | `/app-config` | 删除配置（级联失效所有用户连接） |

---

## 7. Skill 下发与 Agent 集成

### 7.1 skill 定义（`wemeet-connector-skill.ts`）

- **skillKey**：`wemeet-connection`（对齐 `feishu-connection` 命名）。
- **能力描述**（注入 agent 系统提示）：`使用用户授权的腾讯会议账号操作会议：创建/查询/修改/取消会议、查看参会成员、获取云录制列表。用户要求会议相关操作时直接执行；回答时先说明能力，不主动提及凭证文件/授权流程，仅在实际操作失败（未连接/未授权）时引导到平台完成连接。`
- **凭证文件**：`connectors/wemeet.json`（字段：`version / provider=wemeet / clientId / clientSecret / accessToken / refreshToken / scope / openId / userName / tokenExpiresAt / refreshExpiresAt / syncedAt`）。

### 7.2 Skill 执行策略（凭证直调，双模式）

> 官方 CLI `@tencentcloud/tmeet` 内置 WorkBuddy 固定应用凭证、不支持自定义 client（源码核实），**不能直接用于 insightweaver 自建应用**。故 Skill 采用「平台凭证 + OpenAPI 直调」为主；若后续 fork 改造 CLI（MIT）支持自定义应用，再切 CLI 模式（对齐 lark-cli）。

```
1. 检查凭证：connectors/wemeet.json 存在即视为已授权（否则展示能力，操作失败再引导连接）
2. 全部能力走 curl 直调腾讯会议 OpenAPI：
   curl -s -X POST https://api.meeting.qq.com/v1/meetings \
        -H "Authorization: Bearer <accessToken>" \
        -H "X-TC-AppId: <clientId>" -H "X-TC-Registered: 1" \
        -H "Content-Type: application/json" -d '{...}'
3. 响应 code==0 表示成功；401/token 过期 → 提示用户在平台重新授权，不要重试
4. 写操作（创建/修改/取消）先向用户复述影响再执行
```

（可选演进：fork `TencentCloud/tencentmeeting-cli`（MIT）注入自有 client 凭证，Skill 内 `tmeet meeting +create` 等命令化调用，与 lark-cli 完全对齐。）

### 7.3 激活会议助手

- `builtin-agent-catalog.ts` 中 `builtin-meeting-assistant.skillKeys` 由 `"Tencent Meeting"`（占位）替换为 `"wemeet-connection"`（真实 skillKey）。
- agent 模板 `workplace-assistant` 保持不动，skill 装载即能力生效。
- 沙箱侧同步：`wemeet-connector-sync.service.ts` 与飞书共用同一套 putManagedSkill / 凭证下发通道，仅文件名与内容不同。

---

## 8. Web UI 设计

| 组件 | 位置 | 说明 |
|---|---|---|
| `WemeetConnectorCard.tsx` | `apps/web/src/components/super-lobster/` | 连接状态卡（未绑定/已绑定/过期），对齐 FeishuConnectorCard |
| `WemeetConnectorDialog.tsx` | 同上 | 弹窗：连接入口 + 状态 + 解绑；已绑定后内嵌「快捷建会」表单 |
| `WemeetDeviceAuthDialog.tsx` | 同上 | **设备码授权对话框**（展示授权 URL + 短码 + 轮询），直接复用 `FeishuDeviceAuthDialog` 交互，**无需回调路由** |
| 管理页 | 复用 `admin/feishu-app-config/page.tsx` 模式 | 新增 `admin/wemeet-app-config` 页，配置 clientId/Secret/权限 scope |

UI 文案全部走 i18n（`apps/web/messages/zh.json` + `en.json`，见 `docs/web-i18n.md`），不硬编码。

---

## 9. 落地步骤（分阶段 + 验收标准）

### M0 前置：接入路径确认 + 凭证准备（阻塞项，先行启动）

> 无"企业开发者认证"要求；按 3.1 三条路径并行确认，**拿到凭证即可开工，代码开发可与审核并行**。

| 步骤 | 动作 | 负责 | 预计耗时 |
|---|---|---|---|
| 1 | 开放平台完成**开发者实名认证**（个人可实名，非企业资质） | 对接人 | 即时~1 天 |
| 2 | **路径 A**：提交 OAuth 第三方应用**内测预约登记**（当前为预约审核制） | 对接人 | 审核周期不可控，先提交 |
| 3 | **路径 C（兜底）**：确认企业是否已有/可购买**企业版或商业版**账号，管理员在【用户中心→高级】建密钥对（SecretId/SecretKey + APPID + SDKID） | 企业管理员 | 购买后即时可用 |
| 4 | **联调先行**：用免费组织账号 + 调试模式（手机号加入调试列表）先跑通 API（创建会议等 4 个调用门槛 API，限频 10 次/天/账号、200 次/月/应用） | 开发 | 即时 |
| 5 | 依据 A/C 结果确定最终鉴权模式，拿到 `clientId/clientSecret/权限scope` 或密钥对，填入管理页 | 开发 | — |

**验收**：至少一条路径可用——A 审核通过后完成一次 OAuth 授权换 token；或 C 密钥对调通 `POST /meetings` 创建会议成功。

### M1 连接能力（后端）

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | Prisma 新增两模型 + 迁移 | `pnpm db:migrate` 成功，Studio 可见新表 |
| 2 | `wemeet-oauth.client.ts` + `wemeet-session.store.ts` | 单测覆盖设备码发起/轮询/换token/刷新（mock HTTP） |
| 3 | `wemeet-connector.service.ts` 状态机 + controller | 绑定→connected→刷新→解绑全链路接口通过（curl 验证） |
| 4 | `wemeet-connector-admin.controller.ts` 配置 CRUD | 管理页可保存/读取（secret 脱敏） |
| 5 | `wemeet-meeting.client.ts` 会议 API 客户端 | 单测 + 真联调：创建→查询→取消闭环 |

### M2 会议业务 API + Web

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | meetings 业务接口（§6.2 全部） | 真实账号创建会议成功，返回 join_url 可入会 |
| 2 | `WemeetConnectorCard/Dialog` + 回调页 | UI 走查：绑定、建会、解绑三流程无报错 |
| 3 | 管理页 + i18n 文案 | zh/en 双语齐备 |

### M3 技能化 + 激活会议助手

| 步骤 | 动作 | 验收 |
|---|---|---|
| 1 | `wemeet-connector-skill.ts` + sync 下发 | 沙箱内出现 `connectors/wemeet.json`，agent 可按 skill 调会议 API |
| 2 | 更新 `builtin-agent-catalog.ts` skillKeys | 会议助手对话中可执行「帮我建一个 2 点的大纲评审会」并返回 join_url |
| 3 | 全链路回归 | `pnpm lint` + `pnpm build`（含 `@insightweaver/api` TS 编译）通过；测试套件补充 `wemeet-connector.service.test.ts` |

---

## 10. 风险与注意事项

| 风险 | 等级 | 说明与对策 |
|---|---|---|
| **OAuth 2.0 内测预约审核周期不可控** | **高** | M0 同时提交预约登记 + 确认企业版/商业版密钥对（路径 C 无审核排队）；哪条先通走哪条，代码层把鉴权封装成可切换接口，不阻塞开发 |
| 会议 API 依赖商业版/企业版 | 高 | 用户级 OAuth 用免费账号仅能调 4 个门槛 API 且限频（10 次/天/账号、200 次/月/应用）；**开发期用调试模式够用，生产建议企业版/商业版** |
| 回调需公网 HTTPS | 中 | 生产走正式域名；本地开发用内网穿透或「授权后粘贴 code」降级交互 |
| access_token 6h / refresh_token 30d | 中 | 对齐飞书：刷新锁 + 提前 60s 刷新 + 失败置 `expired` 引导重授权 |
| X-TC-Registered 漏带 | 中 | client 层统一注入，单测断言头存在 |
| 频率限制 20 次/秒 | 低 | 会议 API 客户端统一指数退避重试（429） |
| 凭证泄露 | 低 | 复用 SecretCryptoService 加密；skill 明令禁止输出 token 原文 |

---

## 11. 工作量与资源

| 阶段 | 后端(人日) | Web(人日) | 测试(人日) | 依赖 |
|---|---|---|---|---|
| M0 路径确认 + 凭证准备 | 0.5 | — | — | 实名认证 / 企业版账号管理员 |
| M1 连接能力 | 3 | — | 1 | M0 |
| M2 会议 API + Web | 2.5 | 2.5 | 1 | M1 |
| M3 技能化 + 激活 | 1.5 | 0.5 | 0.5 | M2 |
| **合计** | **7.5** | **3** | **2.5** | — |

**建议并行项**：M0 启动后，M1 的 Prisma/状态机/单测可与凭证申请并行推进（mock 数据先行）；M2 会议 API 联调依赖真实凭证，注意排期串行。

---

## 附：与飞书连接器的对照表（实现时可逐文件对齐）

| 飞书文件 | 腾讯会议对应 | 主要改动 |
|---|---|---|
| `feishu-oauth.client.ts` | `wemeet-oauth.client.ts` | 授权流程/令牌端点换为腾讯会议设备码；refresh 端点换；**其余几乎同构** |
| `feishu-app-registration.store.ts` | `wemeet-session.store.ts` | 存 device_code + 轮询状态（pending/authorized/expired），TTL 5min |
| `feishu-connector.service.ts` | `wemeet-connector.service.ts` | 状态机复用；refresh 端点换 |
| `feishu-connector-sync.service.ts` | `wemeet-connector-sync.service.ts` | 凭证文件名/字段换 |
| `feishu-connector-skill.ts` | `wemeet-connector-skill.ts` | lark-cli 分支保留（若 fork tmeet CLI）或凭证直调；无 CLI 时 OpenAPI 直调 |
| `feishu-connector-admin.controller.ts` | `wemeet-connector-admin.controller.ts` | 字段换 clientId/clientSecret/scope |
| `FeishuDeviceAuthDialog.tsx` | `WemeetDeviceAuthDialog.tsx` | **设备码轮询交互几乎原样复用**；加建会表单 |

---

## 附 2：鉴权模式切换（A→C）对实现的影响

> 若 OAuth 内测预约（路径 A）迟迟不通过，切路径 C（企业内部开发，密钥对）时仅以下部分变化，**Prisma 模型、会议 API、Skill 下发、Web 组件全部复用**：

| 模块 | 路径 A（OAuth 设备码） | 路径 C（Secret 密钥对） |
|---|---|---|
| `wemeet-oauth.client.ts` | 设备码换取 token（RFC 8628） | 简化为 JWT 签名客户端（SecretId/SecretKey + APPID/SDKID 生成签名头），无 token 续期 |
| 授权流程 | 用户浏览器授权（设备码，无需回调） | **无需用户授权**，服务端直签；`UserWemeetConnection` 仍保留（存企业身份 + 业务 userid 映射） |
| `auth/init` + 轮询 | 保留（设备码轮询） | 删除，改为「企业密钥对校验后直接 connected」 |
| token 续期 | refresh_token 轮换 | 无（每次请求重新签名） |
| 沙箱凭证 `wemeet.json` | accessToken/refreshToken | clientId + 签名参数模板（agent 侧签名密钥不下发，改由平台代理调用，见备注） |

> 备注：路径 C 下**不建议**把 SecretId/SecretKey 下发沙箱（签名密钥不应出服务端）；此时 agent Skill 改为「平台代理调用」——agent 把会议操作意图发回平台 API（§6.2），由服务端签名后调腾讯会议，沙箱凭证文件仅存只读的 userid 映射与说明。这是与路径 A 的 Skill 设计差异点，实现时按最终选定路径收敛。
