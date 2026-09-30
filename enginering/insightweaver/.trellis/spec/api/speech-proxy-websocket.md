# Speech Proxy WebSocket（语音输入代理网关）

> 任务 08-19-voice-ws-proxy 沉淀，2026-08-19

## 架构契约

前端不再直连阿里云 NLS，改走后端代理网关：

```
前端 ws → POST /api/speech/start（冻结额度）→ ws /api/speech/ws → 后端 → 阿里云 NLS
```

## 关键契约

### 端点

- `POST /api/speech/start`：JwtAuthGuard，冻结 voice_input 全额（60s 单价），返回 `{ refId, billingTaskId }`；不再返回阿里云 token/appkey
- `WS /api/speech/ws`：`@WebSocketGateway`，query 传 `token`(JWT) + `enterpriseId` + `billingTaskId` + `refId`
- `POST /api/speech/stop`：**已删除**（代理侧在连接关闭时自动结算）

### 计时与结算

- 计时起点：代理收到阿里云 `TranscriptionStarted` 事件（建连等待时间不计费）
- 60s 硬切断：`hardStop` 发 `StopTranscription` → 等 `TranscriptionCompleted` → 关闭连接 + 结算全价（forceFullPrice）
- 提前关闭：按 `min(实际秒数, 60)` 结算，`tokens = floor(单价 × 秒 / 60)`
- 未开始识别关闭：0 秒，不扣费（释放冻结）
- 结算失败：立即 release 冻结，不扣费

### 认证

- ws 不支持自定义 header，token(JWT) + enterpriseId 从 query 传
- 网关用 `JWT_ACCESS_SECRET` 校验 token，查 `users` 表确认 active

### 状态机

| 状态字段 | 含义 |
|----------|------|
| `startTimeMs=0` | 未收到 TranscriptionStarted |
| `stopping=true` | 60s 定时器触发，StopTranscription 已发出 |
| `forceFullPrice=true` | 60s 切断，按全价结算 |
| `settled=true` | 已结算（幂等保护） |

### 兜底

- `SpeechSettleScheduler`：frozen voice 任务超 90s 未结算 → 按全价强制结算（ws 建立后后端崩溃场景）
- StopTranscription 后 5s 未收到 TranscriptionCompleted → 兜底关闭 + 结算

### 阿里云 NLS 协议约束

- task_id 必须无连字符（`crypto.randomUUID().replace(/-/g, "")`），否则返回 `40000002`
- StartTranscription 参数由后端构造（format pcm, sample_rate 16000, 中间结果/标点/逆文本）
- token 由 `SpeechService` 缓存持有（提前 5 分钟刷新），不外发前端

## 文件索引

- `apps/api/src/speech/speech-ws.gateway.ts` — 代理网关
- `apps/api/src/speech/speech-ws.gateway.test.ts` — 网关测试（mock 阿里云 ws）
- `apps/api/src/speech/speech.controller.ts` — start 入口
- `apps/api/src/speech/speech-billing.util.ts` — 时长换算纯函数
- `apps/api/src/speech/speech-settle.scheduler.ts` — 强制结算兜底
- `apps/web/src/hooks/useSpeechRecognition.ts` — 前端 hook（连代理、无 stop 上报）

## 配额计费契约（!228 沉淀，2026-08-20）

语音输入与企业配额体系（quotaMode）的交互，与发送消息链路语义对齐：

### 会话数模式（quotaMode=conversation）

- **扣减**：`settleFixedTokenUsage` 在 settlement create 成功后执行
  `UPDATE zclaw_enterprise_conversation_quota_usages SET remainingConversations = remainingConversations - 1 WHERE remainingConversations > 0`
  （每次语音输入 = 1 次会话；语音+发送共 2 次，独立扣减）
- **豁免**：admin/owner 不扣（`ENTERPRISE_ADMIN_ROLES`，与 `consumeEnterpriseConversationQuotaIfNeeded` 语义一致）
- **幂等**：扣减位于 settlement create（id=`voice-input-settle-<enterpriseId>-<userId>-<refId>` 唯一约束）成功之后——重复结算/重放不重复扣

### 语音 start 配额拦截

- `POST /api/speech/start` 在冻结前调用 `zclawService.assertEnterpriseTokenQuotaIfNeeded(enterpriseId, userId)`（仅 `enterpriseId` 非空时）
- 拦截矩阵：

| 场景 | 行为 |
|------|------|
| token 模式企业配额耗尽 | `ZclawTokenQuotaExceededError` 拦截，不冻结 |
| conversation 模式会话次数耗尽（≤0） | 同上拦截 |
| batch 模式配额耗尽 | 同上拦截 |
| C 端（enterpriseId=null）/ admin/owner / unlimited | 不拦截（跳过/豁免） |

- 拦截在冻结之前：配额不足不产生 billingTask 冻结，无需释放

### 明细模式标记

- 语音 settlement 记录写入 `quotaMode`（`zclawEnterpriseTokenUsageSettlement.quotaMode`，既有字段）
- 前端 `UserTokenDetailsDialog` 按 quotaMode 渲染标签：conversation → 「语音输入（会话数模式）」；token → 「月Token模式」等（`TOKEN_QUOTA_SOURCE_LABELS`）
- **前端零改动**：标签渲染为既有能力，后端写入 quotaMode 即生效

### 关键实现位置

- `apps/api/src/zclaw/enterprise-token-quota.service.ts` — `settleFixedTokenUsage`（会话扣减 + quotaMode 写入）
- `apps/api/src/zclaw/zclaw.service.ts` — `assertEnterpriseTokenQuotaIfNeeded`（public，语音 start 与发送链共用）
- `apps/api/src/speech/speech.controller.ts` — start 配额拦截

### 常见错误

> **Warning**: 语音结算时 `settleFixedTokenUsage` 的 config 查询必须 select `quotaMode`（仅 select `tokenLimit` 时 effectiveQuotaMode 恒为 null，conversation 扣减静默失效且明细无模式标记）。
>
> **Warning**: 配额拦截必须在 reserve（冻结）之前——否则配额不足时先冻结后抛错，需要额外释放逻辑。
