# Message Lifecycle: Snapshot → Trusted → Prune

Messages have three write paths, two ID formats, and a prune step. Prune was fixed (!209) to require a trusted-copy existence check before deleting — the historical data-loss bug for text-only user messages and assistant messages is closed; see the Prune section for the guard semantics.

## ID Formats

| Format | Example | Source | Trust Level |
|--------|---------|--------|-------------|
| UUID | `9dad583e-fc2e-4d1a-8c4f-cc303d92d740` | Local snapshot at send / streaming placeholder | **Untrusted** |
| `conv_x:msg_N` | `conv_d67d413d4ec9:msg_8` | `syncSessionDetailMessages` from OpenClaw history | **Trusted** |
| `conv_x:tool:${toolCallId}` | `conv_d67d413d4ec9:tool:call_00_0WYftxzaQ5t` | `upsertLocalToolMessage` from SSE stream | **Trusted** |

`isTrustedLocalSnapshotMessageId(sessionId, messageId)` = `messageId.startsWith(`${sessionId}:`)`.

## Write Paths

1. **Send** (`handleSend`): create user + assistant UUID snapshots (untrusted). Tool activity not written here.
2. **Streaming SSE**: `upsertLocalToolMessage` writes/updates `conv_x:tool:${toolCallId}` rows in real time — independent of OpenClaw history.
3. **OpenClaw history sync** (`syncSessionDetailMessages`): writes `conv_x:msg_N` trusted copies for every message the remote returns.
4. **Prune** (`pruneUntrustedLocalMessages`): soft-deletes UUID snapshots (`isDeleted=true`) after sync, with protection only for **user messages with attachments**.

## Bug: Prune Deletes When Trusted Copy Absent

`collectPrunableUntrustedIds` (`zclaw.service.ts:8614-8626`):

```typescript
// Line 8619-8621
if (message.role !== "user") {
  deletableIds.push(message.id);  // ALL assistant UUID snapshots — deleted immediately
  continue;
}
// Line 8623-8626
const files = this.extractSnapshotFiles(message.rawPayload);
if (!files.length) {
  deletableIds.push(message.id);  // ALL file-less user UUID snapshots — deleted immediately
  continue;
}
// Line 8628+ — attachment protection only; no "wait for trusted copy" guard for text-only
```

The comment on line 8572-8576 says "若 trusted 尚未出现(远端未返回),保留该 UUID 等下次" but this protection is only implemented for user messages with attachments. For text-only user messages and all assistant messages, the UUID snapshot is deleted even if the remote hasn't returned it yet.

**Trigger**: Any sync+prune that runs while OpenClaw's history doesn't yet contain the latest turn (e.g., run ended with tool error, stream hung mid-execution, sync polling race). Prune deletes the only local copies. No subsequent read path can recover them — fast path and full path both filter `isDeleted=false`, and the merge (`mergeMessagesWithLocalToolSnapshots`) is remote-driven.

**Impact**: As of 2026-08-17, ~840 sessions match "latest user UUID snapshot isDeleted=true AND no trusted user copy at or after its createdAt".

## Contracts

### Send Flow (correct sequence)

```
user/assistant UUID write (untrusted, isDeleted=false)
  → streaming tool upserts (trusted, :tool:)
  → [run completes, possibly with error/timeout]
  → OpenClaw history sync writes conv_x:msg_N (trusted)
  → prune soft-deletes UUIDs (only safe AFTER trusted copies exist)
```

### Prune Decision Matrix

| Role | Files | Trusted copy exists? | Current behavior | Correct behavior |
|------|-------|---------------------|-----------------|-----------------|
| user | yes | yes | merge files to trusted, delete UUID ✅ | Same ✅ |
| user | yes | no | keep UUID ✅ | Same ✅ |
| user | no | yes | **delete UUID** ❌ | Delete ✅ |
| user | no | **no** | **delete UUID** ❌ | **Keep UUID** (wait for trusted) |
| assistant | — | yes | **delete UUID** ❌ | Delete ✅ |
| assistant | — | **no** | **delete UUID** ❌ | **Keep UUID** (wait for trusted) |

## Fix

`collectPrunableUntrustedIds` 规则（2026-08-17 实现）:

| Role | 判定 | 行为 |
|------|------|------|
| user | `trustedUsersWithFiles.find(isSameUserMessageSnapshot)` 命中 | 附件迁移（trusted 无 files 时）→ 删除 UUID |
| user | 未命中（trusted 未出现 / 附件不一致） | 保留 UUID |
| assistant | 空占位符（NO_REPLY / "(no output)" / 空内容） | 直接删除（无可展示数据） |
| assistant | `isSameUserMessageContent` 前缀无关匹配 trusted 命中 | 删除 UUID |
| assistant | trusted 未出现 | 保留 UUID |
| tool / toolResult 等 | — | 保持原逻辑直接删除 |

**匹配语义必须是前缀无关的**（`isSameUserMessageContent` 的 `endsWith` 判定，而非严格 key 相等）：trusted 副本可能带任意新增系统注入前缀（PromptGuard、agent 设定等），严格 key 匹配会让这些 UUID 永远无法被 prune 累积成孤儿行。

## Tests Required

- Unit: `collectPrunableUntrustedIds` with (role=user, no files, no trusted) → id NOT in deletableIds.
- Unit: (role=assistant, no trusted) → id NOT in deletableIds.
- Unit: (role=assistant, empty/placeholder content, no trusted) → id IN deletableIds（占位符无可展示数据）。
- Integration: send a text-only message, simulate sync returning stale history, then prune → UUID still exists.
- Regression: existing test for user-with-attachments protection must still pass.

## Gotcha

The fast path (`getSessionMessagesPage` line 6020-6084) returns the latest N undeleted rows directly — it never triggers a remote sync. Once prune has deleted the UUIDs, even repeated refreshes can't recover the lost messages without a DB-level repair.

## Recovery

The soft-deleted UUID rows still exist in the DB (isDeleted=true, content preserved). A repair script can:
1. Identify sessions where `isDeleted=true` user/assistant UUID has no trusted copy after its createdAt.
2. Either restore them (`UPDATE SET isDeleted=false`) or write trusted `conv_x:msg_N` copies with content from the UUID.
3. Re-run prune correctly.

## 附件路径三层防御（2026-08-20 bugfix-20260820-km-attachment-path）

线上缺陷：发消息时 `files[].path` 为裸文件名/空串 → API 兜底解析失败**原样透传** → km-agent 路径守卫 400 `invalid attachment path`（错误不可诊断）。根因：path 会「过期」（树缓存陈旧，文件已被删除/移动/改名），任何缓存方案都无法 100% 正确 → 分层防御：

### 单一真相源（F3 结论）

API 的 `workspacePathExists`（zclaw.service.ts:12995）委托 `kmAgentClient.statWorkspacePath` 查询 km-agent managed workspace——**树列表与 stat 同源**（均 km-agent），无「API 根 vs km-agent 根」不一致问题。兜底解析查不到 = 发送时文件确实不在「对话附件/」或 workspace 根。

### 四层防御契约

| 层 | 位置 | 契约 |
|----|------|------|
| L1 构造 | `buildConversationAttachment`（SuperLobsterPage.tsx:1037） | path 缺失/空串 → 返回 null（**禁止** `node.path \|\| node.name` fallback）；workspace 根目录文件的裸名 path 是**合法形态**，保留 |
| L1 构造 | `buildResendAttachmentFiles`（conversation-resend-files.ts） | 编辑重发过滤 path 缺失/空串（**禁止** `f.path ?? ""`），保留 source 字段 |
| L2 入口 | `canDragFileNodeToConversation`（conversation-tree-attach.ts:105） | file 节点与 folder 分支一致要求 `Boolean(node.path?.trim())` |
| L3 API | `normalizeInputFiles`（zclaw.service.ts:12722） | 裸路径兜底解析失败 → 抛 `BadRequestException` 明确中文错误（**禁止**原样透传）；web 端 error-codes.ts `BACKEND_EXACT_MESSAGES` 注册显示文案。**兜底按 `file.source` 分流**：`shared-workspace` 源查共享根（`sharedWorkspacePathExists` → km-agent `statSharedWorkspacePath`），其余查「对话附件/」+ workspace 根（`workspacePathExists` → `statWorkspacePath`）——共享工作区根目录的裸名文件是合法形态，误查 workspace 根会误杀 |
| L4 缓存 | `fileTreeHasValidPaths`（file-tree-session-cache.ts）+ `loadFileTreeWithSessionCache`（super-lobster.ts） | 缓存树含幽灵节点（workspace/shared file 缺 path，含 source 缺失的旧结构节点；memory-* 豁免）→ `invalidateFileTreeSessionCache` + **`fetchFullFileTree(true)` 强制 fresh**（不带 true 会命中后端 45s 树缓存，循环无效）→ 重拉结果仍含幽灵节点则不写缓存 |
| L5 预览读路径（2026-09-05 bugfix-20260905-attachment-preview） | `handlePreviewConversationFile`（SuperLobsterPage.tsx） | 全量树**有意跳过展开「对话附件」目录**（zclaw-workspace-tree.util.ts `shouldSkipExpandingFolder`，性能防御，勿"修复"）→ 树中必有目录节点、必无其中文件节点。**任何**依赖文件树节点定位「对话附件/」内文件的前端功能（预览/下载等）在树内定位必然 miss——正确模式：miss 且 path 前缀为 `对话附件/`（或等于目录名）时，按需 `reloadFileTree({ mode: 'subtree', source: file.source ?? 'workspace', path: CONVERSATION_ATTACHMENTS_PATH })` 合并子树（subtree 端点不走 skip，返回完整相对路径 items）后重定位；**fetch 失败必须 catch 降级为「无法定位」toast（禁止静默失败/未处理 rejection）**。消息存储的 files[].path 是发送时 normalize 后的 `对话附件/<name>`（L3 产物），与文件类型无关——docx/pptx/png 等全部命中同一链路 |

### 常见坑

- **「改名后恢复正常」是典型幽灵附件特征**：改名 → 缓存失效 → 树刷新 → 新节点真实 path → 附加成功。排查此类问题先查树缓存来源（后端 `readZclawFileTreeSourceCache` + 前端 session 缓存，均无版本/schema 校验）。
- L3 报错消息含动态文件名后缀时，web 端转译用 `BACKEND_EXACT_MESSAGES` 的**子串 key**（`includes` 匹配），不要把完整动态消息注册为 exact 条目。
- API 侧错误与同函数既有错误保持一致用 `BadRequestException`（normalizeInputFiles 内 4 处同款），不单独引入 ErrorCode 枚举。
- L5 遗留缺口：2026-08-20 L3 上线前发送的历史消息，存储 path 可能为 `uploads/` 前缀或裸名（未 normalize），预览 L5 前缀匹配不命中仍报「无法定位」；如需覆盖可在 miss 分支追加裸名兜底尝试附件目录 subtree（~4 行），待有报障实例再做。

## 消息身份与去重（2026-08-27 bugfix-20260826-msg-dedup，C+B+A 后半）

### 根因

双 ID 体系（流式 `conv_x:tool:call_Y` / 同步 `conv_x:msg_N` 位置式下标）导致同一消息多行落库。sync 的 `msg_N` 下标随 fetch 窗口漂移，每次同步为同一消息分配不同 ID → upsert 匹配不到旧行 → 追加。

### 稳定 ID 优先级（km-agent 侧，mapHistoryMessage → resolveHistoryMessageId）

`record.id → __openclaw.id → __openclaw.seq（seq-N，绝对 transcript 行号，跨窗口稳定） → msg_${index+1}（最后兜底）`

### 读取端去重引擎（apps/api/src/zclaw/message-dedupe.ts，C 收敛）

`dedupeMessagesByKey(messages, { keyFor, prefer })` 引擎 + 三个便捷构造器：

| 角色 | 键（keyFor） | 合并（prefer） |
|------|-------------|---------------|
| user | 快照非对称匹配 `isSameUserMessageSnapshotExact`（一方无附件即同条；双方有附件需 path 一致） | trusted 优先换 id/内容，files 取有值者 |
| tool | `toolActivity.toolCallId` | trusted 优先，同信度取 createdAt 最新（整行替换） |
| assistant | content 精确 | 同上 |

约束：数组按 createdAt 升序；保留行保持首现位置（稳定顺序）；空内容/无 toolCallId 不去重（原样保留，交给 prune 占位符清理）。

### 读取管线投影（apps/api/src/zclaw/message-projection.ts，B 收敛）

`projectAndDedupeMessages(rows, sessionId, deps)`：sanitize → files → toolActivity → user/tool/assistant 去重。getLocalSessionDetail（全量）与 fast path（窗口）共用，消除手写重复。deps 由 service `buildProjectionDeps()` 注入（sanitize/extract 方法）。

**merge 位置对齐 → toolCallId 对齐**（mergeMessagesWithLocalToolSnapshots，B 修复）：本地 tool 快照按 toolCallId 索引；本地重复行不再导致快照贴错调用（原 localToolIndex 顺序消费在重复行下会漂移错位——A 快照贴到 B 调用）。

### 同步写入身份匹配（syncSessionDetailMessages，A 后半）

tool 消息同步前按 toolCallId 匹配会话内既有行（预读全会话 tool 行建索引）：

- 命中且当前 messageId 在索引中 → 保留自身，软删其余同 callId 副本
- 命中且当前 messageId 不在 → **upsert 到既有行**（流式行或其他同步副本），软删其余副本
- 未命中 → 正常插入

files 保留兜底按**实际 upsert 目标行**的 payload 计算（非 messageId）。目标：写入层不再产生重复；读取端引擎降级为存量数据遮罩（Q2=C：不做全库迁移）。

### fast path 分页（getSessionMessagesPage 无 cursor 首屏）

窗口内去重后行数 < 原始行数（存在重复）→ **放弃 fast path**，fall-through 到 getLocalSessionDetail 全量分页（下游按全量去重下标精确切片）。窗口内无重复 → 直返（`hasMore = totalCount > limit`，增量语义不变）。

## 附件快照提取契约（2026-09-03 bugfix-20260903-chat-attachment-hint R5）

**背景**：`extractSnapshotFiles`（zclaw.service.ts:10767）从 `rawPayload.files` JSON 提取结构化附件列表，供给投影管线（message-projection.ts `deps.extractSnapshotFiles`）和去重引擎（message-dedupe.ts `isSameUserMessageSnapshotExact` 依赖 path 集比较）。历史上该函数提取 `path` 但**未提取 `source`**，导致：
- 编辑重发时共享区附件丢失 source → 解析到错误根目录报 400
- API/web 两层 `files` 类型未声明 `path`/`source`，重发对 path 的依赖靠运行时偶然成立

**契约**：`extractSnapshotFiles` 必须提取以下字段（条件展开，缺省字段不输出键）：

| 字段 | 类型 | 来源 | 条件 |
|------|------|------|------|
| `name` | string | `readOptionalString(item, "name")` | **必选**，缺失整条跳过 |
| `mimeType` | string | `readOptionalString(item, "mimeType")` | **必选**，缺失整条跳过 |
| `path` | string | `readOptionalString(item, "path")` | 可选，有值时展开 |
| `source` | string | `readOptionalString(item, "source")` | 可选，有值时展开；合法值 `workspace`/`shared-workspace`（由 DTO `@IsIn(ZCLAW_FILE_SOURCES)` 锁写入域） |
| `sizeBytes` | number | `readOptionalNumber(item, "sizeBytes")` | 可选，有值时展开 |
| `previewUrl` | string | `readOptionalString(item, "previewUrl")` | 可选，有值时展开 |

**投影管线 files 类型**（ProjectedSessionMessage.files）：
```typescript
files: {
  name: string;
  mimeType: string;
  path?: string;
  source?: string;
  sizeBytes?: number;
  previewUrl?: string;
}[];
```

**web 响应类型**（ZclawSessionDetailMessage.files）：
```typescript
files?: Array<{
  name: string;
  mimeType: string;
  path?: string;
  source?: "workspace" | "shared-workspace";
  sizeBytes?: number;
  previewUrl?: string;
}>;
```

**去重影响**：`isSameUserMessageSnapshotExact` 的语义是「一方无附件即同条；双方有附件需 path 集一致」。extractSnapshotFiles 透传 path 后，本地行（rawPayload 带 path）与远端回显行（sync 写入，rawPayload 也带 path）的 path 集一致 → 正常折叠。若一侧缺 path（legacy 数据，prod 仅 25 条），按既有设计不折叠（同内容不同附件共存）。

**测试**：`zclaw.service.test.ts`「extractSnapshotFiles 透传 path/source（编辑重发保真，R5）」（65/65 绿）；`message-projection.test.ts` 投影去重回归（3/3 绿，锁定带 path 本地 vs 无 files 远端 → 折叠、path 非对称 → 不折叠）。

## Pagination Cursor Contract (!278)

### Signatures

- `getSessionMessagesPage(userId, sessionId, { limit, cursor })` → `{ sessionId, messages, nextCursor, hasMore, source, activeGeneration }`
- fast path（无 cursor + 末条 trusted + 无活跃 run + 窗口内无去重）：直接 DB 查最新 limit 条返回
- 全量路径（带 cursor 或 fast path 条件不满足）：`getLocalSessionMessagesPage` → `resolveLocalMessageCursor`

### Cursor Semantics（单一事实）

`local:N` 的 N = **全量去重 ASC 数组的 endExclusive 下标**（从最老端数）。

- 全量路径翻页：`slice(max(0, N-limit), N)`，`nextCursor = local:start`，`start === 0 → hasMore=false`
- fast path 首页：`nextCursor = local:(totalCount - limit)`（!278 修复——旧值曾发「local:limit」（错误含义=已展示最新 limit 条），被全量路径解释为「ASC 下标 limit」→ 翻页落到最老一段且 hasMore=false，>2×limit 条会话中段永久不可达）

### Validation & Error Matrix

- totalCount ≤ limit → nextCursor=null, hasMore=false
- 窗口内有去重（dedupedFinal.length < rows.length）→ 放弃 fast path，fall-through 全量路径（!259）
- cursor 非 local: 前缀 → 走 KM remote 路径
- 无效数字 → resolveLocalMessageCursor 回退 messageCount（返回尾页）

### Tests Required

- 游标值断言（totalCount=120, limit=50 → local:70）
- 链式翻页覆盖全部消息、无跳过无重复（>2×limit 会话）
- fast path fall-through 正反分支（!259 守卫）
- 锚点：`zclaw.service.test.ts`「fast path 游标语义回归」3 用例

### Common Mistake：时间戳口径

> **Warning**: orders/ledgers/users/sessions/messages/settlements 的 createdAt 统一存 UTC（Prisma 客户端写 Date）。
> db-inspect 的 ISO-Z 显示值 = 存储值 − 8h（按本机时区序列化）；TO_CHAR 直出存储原值。
> 真实北京时间 = db-inspect 显示值 + 16h。判断 UTC vs 墙钟用外部锚点（微信 notifyRaw.create_time），
> 禁止用「表间对齐」推口径——显示变换会污染对齐分析（!278 排查时曾因此误判 8 小时）。
>>>>>>> origin/release
