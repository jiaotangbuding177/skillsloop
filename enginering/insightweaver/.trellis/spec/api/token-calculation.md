# Token Calculation Logic

InsightWeaver 层的 token 计算规格。覆盖数据来源、加权公式、工具调用计费、断连恢复。

---

## 1. Scope / Trigger

**Trigger**：以下改动需要 code-spec 深度：
- Token 计算公式调整（`estimateZclawWeightedTokens`）
- 工具调用计费配置变更（`tool_call_billing_configs`）
- SSE 断连恢复逻辑（`detachOnDisconnect`）
- km-agent/openclaw usage 协议字段变更

**Why**：涉及用户扣费和企业配额，错误会导致：多扣/少扣 token、对账失败、用户投诉。

---

## 2. Signatures

### 核心函数签名

```typescript
// apps/api/src/zclaw/enterprise-token-quota.constants.ts
export function estimateZclawWeightedTokens(usage: ZclawTokenUsagePayload): number

export interface ZclawTokenUsagePayload {
  input?: number;      // 总 input（含 cacheRead + 图片 token）
  output?: number;     // 输出 token
  cacheRead?: number;  // 缓存命中的 token
  cacheWrite?: number; // 缓存写入的 token
}

// apps/api/src/billing/tool-call-billing.service.ts
async calculateToolBillingTokens(
  enterpriseId: string | null,
  toolActivities: Map<string, { name: string; status: string; output?: unknown; args?: unknown }>,
  currentSkillName?: string
): Promise<number>
```

### 数据库表

| 表 | 关键字段 | 说明 |
|---|---|---|
| `tool_call_billing_configs` | `toolType`, `toolNames`, `tokensPerUnit`, `countingStrategy` | 工具计费配置 |
| `zclaw_enterprise_token_usage_settlements` | `tokens`, `messageId`, `enterpriseId`, `userId` | 企业级 token 结算记录 |
| `zclaw_enterprise_conversation_quota_usages` | `tokenUsed`, `tokenLimitSnapshot` | 用户累计用量 |
| `billing_tasks` | `billingUsageTokens`, `status`, `heldTokens` | C 端 billing 任务 |

---

## 3. Contracts

### 3.1 数据来源链路

```
provider (deepseek/openai/...)
  ↓ usage: { input, output, cache_read_input_tokens, ... }
openclaw (normalizeUsage)
  ↓ message.usage SSE event: { input, output, cacheRead, cacheWrite, total }
km-agent (透传)
  ↓ SSE: POST /api/km/conversations/{id}/messages
InsightWeaver (estimateZclawWeightedTokens)
  ↓ 加权计算 + 工具计费
  ↓ captureAiTask / settleEnterpriseTokenUsage
数据库
```

### 3.2 加权公式

```typescript
realInput = max(input - cacheRead, 0)
weighted  = realInput + cacheWrite + cacheRead × 0.2 + output × 6
totalTokens = weighted + toolBillingTokens
```

**权重语义**：
- `output × 6`：生成比读取贵，按 6 倍折算
- `cacheRead × 0.2`：缓存命中有折扣，按 0.2 倍计
- `realInput`：非缓存 input，按 1 倍计
- `cacheWrite`：缓存写入，按 1 倍计

> **Warning**: InsightWeaver **不使用** km-agent 返回的 `total` 字段。`total` 是 provider 的计费口径，InsightWeaver 用自己的加权公式。

### 3.3 工具调用计费

| toolType | 匹配工具 | tokensPerUnit | 说明 |
|---|---|---|---|
| `image_generation` | `process`, `exec` | 30,000 | 图片生成（需 `isImageGenerationFromArgs/Output` 匹配） |
| `web_search_tavily` | `tavily`, `tavily_search` | 10,000 | Tavily 搜索 |

**匹配规则**（`tool-call-billing.service.ts:172-236`）：
1. 工具名直接匹配 `toolNames`
2. 失败则尝试 `currentSkillName` fallback
3. 再失败则从 `args` 字符串中搜索工具名

**图片生成门控**：
```typescript
// process/exec 是通用工具，必须确认是图片生成调用才计费
if (config.toolType === 'image_generation' &&
    !isImageGenerationFromArgs(activity.args) &&
    !isImageGenerationFromOutput(activity.output)) {
  continue;  // 跳过，不计费
}
```

### 3.4 SSE 断连恢复（detachOnDisconnect）

**前端请求**：
```typescript
// apps/web/src/components/super-lobster/SuperLobsterPage.tsx:8372
body: JSON.stringify({
  sessionId,
  message,
  detachOnDisconnect: true,  // ← 关键
  ...
})
```

**后端处理**：
```typescript
// apps/api/src/zclaw/zclaw.controller.ts:985-988
const handleDisconnect = () => {
  if (dto.detachOnDisconnect === true) return;  // 不 abort
  abortController.abort();
};
req.on?.('close', handleDisconnect);
```

**行为**：
| 场景 | token 是否记录 | 原因 |
|---|---|---|
| 正常生成完毕 | ✅ | `captureAiTask` 正常调用 |
| 用户刷新页面 | ✅ | `detachOnDisconnect: true`，后端继续跑 |
| 用户点击"停止生成" | ❌ | abort → `releaseBillingReservation()` |
| InsightWeaver 后端重启 | ❌ | 内存 activeRun 丢失，billingTask 留 `frozen`，由 `releaseStaleFrozenTasks`（默认 1h）清理 |

---

## 4. Validation & Error Matrix

| 条件 | 处理 | 说明 |
|---|---|---|
| `input`/`output`/`cacheRead` 为负数 | `Math.max(0, ...)` 钳位 | 防止异常数据导致负扣费 |
| `cacheRead > input` | `realInput = 0` | 允许，说明 provider 的 input 字段不含 cacheRead |
| 工具调用 `status !== 'completed'` | 跳过 | 失败的工具调用不计费 |
| `process/exec` 无图片生成特征 | 跳过 | 非图片生成的 process 调用不计费 |
| billingTask 已 `captured` | 幂等返回 | 不重复扣费 |
| `billingUsageTokens` 为负数 | 抵消使用量，释放预扣 | 奖励场景 |

---

## 5. Good / Base / Bad Cases

### Good ✅

```typescript
// 正确：使用 estimateZclawWeightedTokens 计算
const llmTokens = estimateZclawWeightedTokens(usage);
const toolBillingTokens = await this.toolCallBillingService.calculateToolBillingTokens(
  enterpriseId, toolActivities, skillName
);
const totalTokens = llmTokens + toolBillingTokens;
await this.billingService.captureAiTask(userId, billingTaskId, {
  billingUsageTokens: String(totalTokens),
  ...
});
```

### Base（标准计算模板）

```typescript
// 示例：input=80256, output=3439, cacheRead=880512, cacheWrite=0
// 工具：2 次图片生成 × 30,000 = 60,000

// LLM 加权
realInput = max(80256 - 880512, 0) = 0
weighted = 0 + 0 + 880512 × 0.2 + 3439 × 6
         = 176102.4 + 20634
         = 196,736

// 总计
totalTokens = 196736 + 60000 = 256,736
```

### Bad ❌

```typescript
// ❌ 错误：直接使用 km-agent 的 total 字段
const totalTokens = usage.total;  // 这是 provider 的计费口径，不是我们的

// ❌ 错误：忽略工具调用计费
const totalTokens = estimateZclawWeightedTokens(usage);
// 缺少 + toolBillingTokens，图片生成/搜索调用未被计费

// ❌ 错误：对 cacheRead 重复计算
const weighted = input + output + cacheRead * 0.2 + output * 6;
// input 已包含 cacheRead，应先用 realInput = max(input - cacheRead, 0)
```

---

## 6. Tests Required

### 6.1 加权公式测试

| 断言点 | 用例 |
|---|---|
| `output × 6` 权重 | output=1000 → 贡献 6000 |
| `cacheRead × 0.2` 折扣 | cacheRead=10000 → 贡献 2000 |
| `realInput` 计算 | input=5000, cacheRead=3000 → realInput=2000 |
| `cacheRead > input` 钳位 | input=100, cacheRead=5000 → realInput=0 |
| 负数钳位 | input=-100 → 视为 0 |

### 6.2 工具计费测试

| 断言点 | 用例 |
|---|---|
| 图片生成匹配 | `process` + args 含 `/images/generations` → 计费 30,000 |
| 图片生成门控 | `process` + args 无图片特征 → 不计费 |
| Tavily 搜索匹配 | `tavily_search` → 计费 10,000 |
| 未完成任务跳过 | `status: 'failed'` → 不计费 |
| 多次调用累加 | 2 次图片生成 → 60,000 |

### 6.3 断连恢复测试

| 断言点 | 用例 |
|---|---|
| `detachOnDisconnect: true` | 前端断开后，后端不 abort，token 仍被记录 |
| `detachOnDisconnect: false` | 前端断开后，`releaseBillingReservation` 被调用 |
| activeRun 重连 | 前端刷新后通过 `subscribeActiveConversationRun` 接收剩余事件 |

---

## 7. Wrong vs Correct

### Wrong ❌ — 使用 provider 的 total 字段

```typescript
// 错误：total 是 provider 的计费口径，和我们的加权公式不一致
const totalTokens = usage.total;  // 可能包含 cacheWrite、图片 token 额外计费等
```

**Why**: provider 的 `total` 口径与 InsightWeaver 的加权公式不同。例如 deepseek 的 `total` 可能按 `input + output + cacheWrite` 计算，而我们的公式对 cacheRead 打 0.2 折、output 放 6 倍。

### Correct ✅ — 使用 estimateZclawWeightedTokens

```typescript
// 正确：使用我们自己的加权公式
const llmTokens = estimateZclawWeightedTokens(usage);
const totalTokens = llmTokens + toolBillingTokens;
```

---

### Wrong ❌ — 忽略 cacheRead 已包含在 input 中

```typescript
// 错误：input 和 cacheRead 重复计算
const weighted = input + cacheRead * 0.2 + output * 6;
// 如果 input=1756, cacheRead=241024，结果是 1756 + 48205 + ... = 远超实际
```

**Why**: OpenAI 协议中，`input`（prompt_tokens）通常**已包含** cached tokens。InsightWeaver 的公式用 `realInput = max(input - cacheRead, 0)` 避免重复。

### Correct ✅ — 先减后加

```typescript
// 正确：realInput 去重
const realInput = Math.max(input - cacheRead, 0);
const weighted = realInput + cacheWrite + cacheRead * 0.2 + output * 6;
```

---

### Wrong ❌ — process 调用一律计费

```typescript
// 错误：所有 process 调用都计费
if (activity.name === 'process') {
  totalTokens += 30000;  // 不管是否是图片生成
}
```

**Why**: `process`/`exec` 是通用工具，可能执行任何命令。只有确认是图片生成调用（args/output 包含 `/images/generations`、`gpt-image`、`.png` 等）才计费。

### Correct ✅ — 门控检查

```typescript
// 正确：检查是否是图片生成
if (config.toolType === 'image_generation' &&
    !isImageGenerationFromArgs(activity.args) &&
    !isImageGenerationFromOutput(activity.output)) {
  continue;  // 跳过非图片生成调用
}
```

---

## Gotcha 汇总

### Gotcha 1: input 包含 cacheRead

OpenAI 兼容协议中，`input`（prompt_tokens）通常**已包含** cached tokens。InsightWeaver 的公式用 `realInput = max(input - cacheRead, 0)` 避免重复计算。

### Gotcha 2: 不使用 provider 的 total

InsightWeaver **不使用** km-agent 返回的 `total` 字段，而是用 `estimateZclawWeightedTokens` 自己算。两边口径不同，数字可能相差 10 倍。

### Gotcha 3: 工具计费是额外的

`totalTokens = llmTokens + toolBillingTokens`。图片生成（30,000/次）、Tavily 搜索（10,000/次）是**额外**计费，不包含在 LLM 加权中。

### Gotcha 4: process/exec 需要门控

`process`/`exec` 是通用工具名，必须通过 `isImageGenerationFromArgs` 或 `isImageGenerationFromOutput` 确认是图片生成调用才计费。

### Gotcha 5: 刷新页面不丢 token

前端传 `detachOnDisconnect: true`，后端不 abort，继续持有 km-agent SSE 连接。`message.usage` 事件仍能收到，token 仍会被记录。

### Gotcha 6: 后端重启会丢 token

如果 InsightWeaver 后端重启，内存中的 `activeRun` 丢失，km-agent SSE 连接断开。`captureAiTask` 不会被调用，billingTask 停留在 `frozen` 状态，由 `releaseStaleFrozenTasks`（默认 1h 超时）定期清理。

### Gotcha 7: 图片 token 已在 input 中

用户上传的图片 token 由 provider 计入 `input` 字段，InsightWeaver 的加权公式会自动处理。不需要额外计算图片 token。
