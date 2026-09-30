# Cross-Layer Data Flow

This guide traces the full lifecycle of a request from user interaction in `apps/web` through `apps/api` to `packages/db` and back.

---

## Request Lifecycle

```
User click
  -> Web component calls API function (from @/api)
    -> ApiClient sends HTTP request with auth + enterprise headers
      -> API controller receives request (JwtAuthGuard validates token)
        -> API service calls Prisma (via 'PrismaClient' DI token)
          -> PostgreSQL query
        <- Prisma returns rows
      <- Service returns plain object
    <- AllExceptionsFilter wraps in { code, message, data } envelope
  <- ApiClient unwraps envelope, returns data
<- Component re-renders
```

---

## The Response Envelope

Every API response — success or error — is wrapped in a standard envelope by `ResponseInterceptor` and `AllExceptionsFilter`:

```ts
// apps/api/src/common/filters/all-exceptions.filter.ts
{
  code: number,     // 0 = success, non-zero = error code enum value
  message: string,  // Human-readable message (Chinese by default)
  data: T           // Payload; null on error
}
```

**Success example:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "enterpriseId": "ent_abc123",
    "planName": "Professional"
  }
}
```

**Error example:**
```json
{
  "code": 4001,
  "message": "额度不足，请充值后重试",
  "data": null
}
```

---

## Web-Side Envelope Unwrapping

`apps/web` has a central `ApiClient` class (`lib/api-client.ts`) that:

1. Sends the HTTP request with auth and enterprise headers.
2. Receives the raw JSON envelope.
3. Checks `code === 0`. If non-zero, throws an `ApiError` with the code and message.
4. If `code === 0`, extracts and returns `data` directly — callers never see the envelope.

```ts
// apps/web/lib/api-client.ts (conceptual shape)
async get<T>(path: string): Promise<T> {
  const res = await fetch(this.baseUrl + path, { headers: this.buildHeaders() })
  const envelope = await res.json()
  if (envelope.code !== 0) {
    throw new ApiError(envelope.code, envelope.message)
  }
  return envelope.data  // Caller gets T directly
}
```

**Consequence:** Web API modules and components always receive the unwrapped `data` object. If you need the envelope `code` or `message` in a component, catch `ApiError` and expose the fields through error state.

---

## Error Code Propagation

Error codes flow through a defined pipeline:

```
API error enum (apps/api/src/common/constants/error-codes.ts)
  -> AllExceptionsFilter catches, assigns code + Chinese message
    -> HTTP response with envelope { code, message }
      -> Web ApiClient throws ApiError(code, message)
        -> Web error-codes.ts maps code -> severity + translation
          -> errorToast() renders toast with appropriate style
```

### Where Each Piece Lives

| Layer | File(s) | Responsibility |
|---|---|---|
| API enum | `apps/api/src/common/constants/error-codes.ts` | Define numeric codes + Chinese messages |
| API filter | `apps/api/src/common/filters/all-exceptions.filter.ts` | Catch exceptions, translate English framework errors to Chinese, build envelope |
| Web error map | `apps/web/src/lib/error-codes.ts` | Map codes to severity + bilingual translation rules |
| Web toast | `apps/web/src/lib/error-handler.ts` | Render toast with dedup and severity-appropriate styling |

### Adding a New Error Code

1. Add the enum value in `apps/api/src/common/constants/error-codes.ts` with a unique numeric code.
2. Add the Chinese message to `ERROR_MESSAGES` in the same file.
3. Throw it from the service using `BusinessException`.
4. The exception filter will automatically catch and envelope it.
5. Add the numeric code to `apps/web/src/lib/error-codes.ts` with severity and translation rules.
6. If the English locale needs a different message, add it to `BACKEND_PATTERN_RULES` or `BACKEND_EXACT_MESSAGES` in the same file.

---

## Enterprise Context Flow

The current enterprise is not part of the URL path — it flows as a header on every request:

```
Web: localStorage.getItem('zclaw:active-enterprise-id')
  -> ApiClient.buildHeaders() adds 'x-enterprise-id: ent_abc123'
    -> API: reads from request header in controller/service
      -> Service uses enterpriseId in Prisma where clauses
```

### Why a Header, Not a Path Param

- Enterprise context changes infrequently (user switches enterprise in the UI).
- Storing it in localStorage and injecting as a header means every API call is automatically scoped without cluttering route definitions.
- The `withActiveEnterpriseHeader()` utility in `apps/web/lib/api-client.ts` handles this automatically for `/api/zclaw/*` requests.

---

## BigInt Serialization Boundary

Prisma returns `BigInt` fields as JavaScript `bigint` values. These are not JSON-serializable by default.

**API side:** BigInt fields are serialized as strings in API responses. This happens at the Prisma/JSON serialization boundary — services return plain objects and BigInt fields become strings in the JSON response.

**Web side:** Receives these as strings. Only parse with `BigInt(value)` when you need arithmetic (e.g., comparing remaining quota against a requested amount). Display values should use formatting utilities that add locale-appropriate thousand separators.

```ts
// Common pattern in web pages
const BYTES_PER_GB = 1024n * 1024n * 1024n
const storageGb = BigInt(apiResponse.storageBytes) / BYTES_PER_GB
```

---

## Checklist for a New API Endpoint

1. Define the route in the appropriate controller under `apps/api/src/<module>/`.
2. Implement business logic in the corresponding service, using Prisma via `@Inject('PrismaClient')`.
3. Return a plain object — the exception filter and response interceptor handle enveloping.
4. Throw `BusinessException` with error codes from `apps/api/src/common/constants/error-codes.ts`.

---

## Message File Attachment Persistence

### Data Flow

```
[Send]                                [Refresh]
  │                                      │
  ├─ Web: draft (sStorage) ─────────────┼── mergeConversationMessagesWithDraft
  │   └─ files ✅                       │   └─ draftHasUserFiles → merge even if API terminal
  │                                      │
  ├─ API: createLocalMessage ───────────┼── getLocalSessionDetail
  │   └─ UUID id, rawPayload.files ✅   │   └─ UUID user (files) + trusted (no files)
  │                                      │
  └─ Agent: path-only refs ────────────┼── getRemoteSessionDetail
      └─ no inline content              │   └─ user msg (no files)
                                         │
                                    mergeMessagesWithLocalToolSnapshots
                                         │   └─ position match: UUID files → remote user
                                         │
                                    syncRemoteSessionDetail
                                         │   └─ trusted user WITH files
                                         │
                                    pruneUntrustedLocalMessages
                                         │   └─ delete UUID (files already synced)
                                         │
                                    getLocalSessionDetail
                                             └─ trusted user WITH files ✅
```

### Key Contracts

| Layer | Function | Contract |
|-------|----------|----------|
| API | `mergeMessagesWithLocalToolSnapshots` | 按位置匹配本地用户 files → 远程；返回 `ZclawSessionDetailMessage[]` |
| API | `pruneUntrustedLocalMessages` | 只删 `isDeleted=false` 的 untrusted id 消息；**merge+sync 完成后才删** |
| Web | `mergeConversationMessagesWithDraft` | 用户消息 `files: draft.files ?? api.files` |
| Web | `shouldMergeDraftOnRefresh` | API 已完成但 draft 含附件 → 仍返回 `true` |

### Common Mistake: Content Matching for File Recovery

**Symptom**: 刷新后附件仍丢失（即使后端 merge 已执行）。

**Cause**: 按内容匹配本地/远程用户消息——agent 富化用户消息（时间戳前缀 `[Wed ... GMT+8]`）→ 内容不一致 → 匹配失败。

**Fix**: 按位置匹配，不依赖内容。

### Common Mistake: Prune Before Merge+Sync

**Symptom**: 首次刷新后附件永久丢失，后续刷新也无法恢复。

**Cause**: `pruneUntrustedLocalMessages` 在 `mergeRemoteDetailWithLocalToolSnapshots` 之前执行 → UUID 快照已删 → merge 无 files 来源。

**Prevention**: prune 必须在 merge + sync 完成后执行（当前代码保证此顺序）。

### Common Mistake: sessionStorage Draft 持久化完整历史（2026-08-07 教训）

**Symptom**: 生成中刷新后历史消息重复出现、消息顺序错乱。

**Cause**: `saveConversationDraft` 在生成中轮询时把 `mergedMessages`（完整消息列表）写入 sessionStorage；刷新后三处调用点都把完整历史传入 `mergeConversationMessagesWithDraft`：

| 调用路径 | 代码位置 | 历史来源 |
|---------|---------|---------|
| hydrate（页面首次加载） | `SuperLobsterPage.tsx:3810` | `storedDraft.messages ?? cachedMessages` |
| poll（生成中轮询） | `SuperLobsterPage.tsx:2164` | `previousMessages`（内存 ref） |
| subscribe-resume（SSE 重连） | `SuperLobsterPage.tsx:2280` | `storedDraft.messages` |

merge 函数将其中已完成的 tool/toolResult 无条件 push（`role === 'tool'` 分支）、assistant 按 `findLastAssistantAfterLastUser` 错误匹配合并 → 历史重复 → 再次 `saveConversationDraft` 存回 → 恶性循环。

**Fix**: 见 `web/state-management.md → conversationDraft`——save/load 双端过滤 + merge 内部过滤 + olderLocal 内容去重。核心原则：draft 只持 in-flight（`sending`）消息 + user 消息（附件来源）+ assistant 消息（可能含比 API 更新的流式内容），**不做历史缓存**。
5. On the web side, add a typed API function in `apps/web/src/api/moudles/<module>.ts`.
6. The function calls `ApiClient.get/post/etc.` — the envelope is unwrapped automatically.
7. If the endpoint is a mutation, generate an idempotency key (see `guides/idempotency.md`).
8. If the endpoint can fail with a new condition, add the error code to the web error map (see `guides/bilingual-errors.md`).

### Common Mistake: 内容匹配过度收割（2026-08-09 教训——同内容不同附件被删）

**Symptom**: 用户重复发送同文本带不同图片（如 5 次"这是什么"带 5 张图），刷新后后续轮次的 user 消息+附件永久丢失；助手回复还在但 user 消息消失。

**Cause**: 两层叠加：
1. **OpenClaw 远端 history 对相同内容 user 消息只回显第一条**（外部行为）→ 后续轮次无 trusted 副本
2. `collectPrunableUntrustedIds` 用**纯内容匹配**收割 UUID 副本——同内容不同附件的 UUID 匹配到已有 trusted 后**无条件删除**（trusted 已有 files 时不迁移）→ 附件+消息一起丢
3. 本地去重（getLocalSessionDetail `seenUserKeys` / merge / 前端 `dedupeUserMessagesByContent`）同样纯内容匹配 → 同内容消息只剩一条

**Fix**: 统一使用 shared 包的 `isSameUserMessageSnapshot`（非对称匹配）：
```typescript
// 内容相同 && (任一方无附件 || 附件 path 集合一致) → 同一条（可合并/收割）
// 内容相同 && 双方有附件但 path 不同 → 不同消息（必须共存，禁止收割）
isSameUserMessageSnapshot({ content, files }, { content, files })
```

**Prevention**（四处必须同步用快照匹配，禁止单独用 `isSameUserMessageContent` 做 user 去重/收割判据）：
- `collectPrunableUntrustedIds`（prune 收割判据）
- `getLocalSessionDetail`（本地详情去重）
- `mergeMessagesWithLocalToolSnapshots`（remote+local 合并去重）
- 前端 `conversationMessageMerge.ts`（draft 合并去重）

> **Warning**: 去重数组索引陷阱——`seenUserSnapshots` 只收录 user 快照，但 `dedupedMessages` 含全部 role。命中副本时**必须**用快照携带的 `dedupedIndex` 定位（禁止用 seen 索引直接读 deduped 数组，会错位改写 user 前的 assistant/tool 消息）。

> **Warning**: merge 远端回显缺失的本地孤儿副本（OpenClaw 内容去重未回显的重复 user 消息）必须追加回结果（仅远端非空时），否则刷新后消息丢失；追加按 createdAt 升序插入避免乱序。

### Contract: 附件转发 hint（2026-09-03 修订：覆盖对话附件）

**背景**: OpenClaw 助手默认只检查「对话附件」目录找新附件；`AI 工作区/...` 路径引用（前端文件树/产物面板选择）即使随 files 传递也不被读取 → 助手回复"未携带图片"。实测助手可用 exec/image 工具直接读取 `/workspace/<path>`（路径可达）。2026-09-03 线上实证（会话 conv_5257d244a423）：对话附件文件即使已在目录内，extraSystemPrompt 中的附件列表仍会被部分助手忽略 → 助手回复"没带上内容"且全链路零报错——hint 范围据此扩大到对话附件。

**Contract**: 发送消息时（`streamMessage`）对**所有随消息附件**（`source: workspace|shared-workspace`，含 `对话附件/` 聊天上传文件——source 缺省视为 workspace）把路径以固定格式 `[附加文件: 名称 (/workspace/<path>)]` 追加到**消息文本**（`appendWorkspaceFileHints`，纯函数位于 `apps/api/src/zclaw/workspace-file-hints.ts`，`ZCLAW_CHAT_ATTACHMENTS_DIR` 常量同源导出）——助手处理用户消息时必然可见（extraSystemPrompt 方案会被部分助手忽略导致跑偏，消息文本方案是唯一可靠告知手段）；前端 `sanitizeUserMessageContentForDisplay` 与 shared `normalizeComparableMessageContent` 剥离提示块（trusted 带提示 / UUID 不带提示的副本对齐即依赖该剥离）。判断只能按 `source` 显式进行，禁止用 path 前缀做排除或 catch-all（两个方向的教训都发生过）。

> **Warning**: 禁止用"复制文件到对话附件目录"实现可见性——复制会污染目录，OpenClaw 助手扫描「对话附件」找新附件时会把历史复制文件误判为新附件（实测：用户发 1 个附件，助手回复"新附件：两个 docx"）。

### Contract: hint 格式转义与共享常量（2026-08-10 教训）

**问题 1 — 文件名含 `]` 时剥离正则提前闭合**：hint 格式 `[附加文件: name (path)]` 的剥离正则 `WORKSPACE_FILE_HINT_REGEX = /\[附加文件:[^\]]*\]/g` 在文件名/路径含 ASCII `]`（如 `report[final].pdf`）时会在第一个 `]` 处提前闭合，剩余部分（`b.pdf (/workspace/...)]`）泄露到用户可见内容。

**错误转义方案（无效）**：`file.name.replace(/]/g, "\u200b]")`——零宽空格 `\u200b` 不是 `]`，`[^\]]*` 会匹配它并在后面的字面 `]` 停止，正则仍提前闭合。

**正确方案**：用全角 `］`（U+FF3D）替换 ASCII `]`——`[^\]]*` 不匹配全角 `］`（不是 ASCII `]`），提示块整体正常闭合：

```typescript
// Correct: 全角 ］ 替换，正则不会提前闭合
const safeName = file.name.replace(/]/g, "］");
const safePath = file.path.replace(/]/g, "］");
return `${WORKSPACE_FILE_HINT_PREFIX} ${safeName} (${prefix}/${safePath})]`;
```

**问题 2 — 生成/剥离格式漂移**：hint 前缀在生成端（`zclaw.service.ts`）与剥离端（shared `message-content-normalize.ts`、web `sanitize-user-message-content.ts`）各自硬编码，格式变更时一端漏改 → 提示块泄露到用户可见内容。

**规则**：生成端必须引用 shared 导出的 `WORKSPACE_FILE_HINT_PREFIX = "[附加文件:"`，剥离端使用同源的 `WORKSPACE_FILE_HINT_REGEX`（已从 shared 导出并被 web sanitize 复用）。禁止两端各自硬编码格式字符串。

**问题 3 — source 显式默认**：`appendWorkspaceFileHints` 的 filter 必须显式 `file.source ?? "workspace"` 后再判断，禁止用 `!path.startsWith(对话附件/)` 作为 catch-all 条件（会误判任意非对话附件路径为 workspace 引用）。

### Contract: 附件 MIME 推断（2026-09-03 bugfix-20260903-chat-attachment-hint R6）

**背景**：`inferConversationFileMimeType`（原 SuperLobsterPage.tsx 内函数，2026-09-03 抽取为 `apps/web/src/components/super-lobster/conversation-file-mime.ts`）在树节点无 `mimeType` 时按扩展名兜底。历史上缺失 Office MIME 分支 → docx 等二进制文档误判 `text/plain` → km-agent 按文本读取二进制必然失败。

**契约**：推断顺序与 API 侧 `ZCLAW_ALLOWED_FILE_MIME_BY_EXTENSION` 白名单对齐（zclaw.service.ts:216-241）：

| 优先级 | 扩展名 | MIME |
|--------|--------|------|
| 1 | `.zip` | `application/zip` |
| 2 | 节点自带 `mimeType` | 原值（html/css/yaml → `text/plain`；zip 变体 → `application/zip`） |
| 3 | markdown | `text/markdown` |
| 4 | `.json` | `application/json` |
| 5 | `.csv` | `text/csv` |
| 6 | `.pdf` | `application/pdf` |
| 7 | `.png/.jpg/.jpeg/.gif/.webp/.svg` | `image/*`（jpg/jpeg → `image/jpeg`，svg → `image/svg+xml`） |
| 8 | **Office（新增）** | `.docx` → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`；`.doc` → `application/msword`；`.xlsx` → `spreadsheetml.sheet`；`.xls` → `application/vnd.ms-excel`；`.pptx` → `presentationml.presentation`；`.ppt` → `application/vnd.ms-powerpoint` |
| 兜底 | 其他 | `text/plain` |

**测试**：`conversation-file-mime.test.ts`（vitest）覆盖 Office 全家族（doc/docx/xls/xlsx/ppt/pptx）、大小写不敏感、既有行为回归（zip/markdown/json/csv/pdf/image/未知扩展名）——4/4 绿。
