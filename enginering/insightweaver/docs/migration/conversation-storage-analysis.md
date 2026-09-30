# Conversation Storage Analysis: km-agent & insightweaver

> Purpose: Evaluate the impact of NOT migrating the km-agent DB during a userId migration.
> Date: 2026-07-21

---

## 1. km-agent Conversation Storage

### 1.1 Workspace Files (Filesystem)

km-agent stores conversation-related data on disk in per-user workspace directories.

**Directory structure:**

- Workspace root: `{managedWorkspaceRoot}/workspace-u_{userId}/`
  - Source: `extensions/km-agent/src/storage/user-workspace-dir.ts:11,26-38`
  - The directory name is `workspace-u_` + userId (e.g. `workspace-u_abc123`)
- km-agent metadata dir: `{workspace}/.km-agent/`
  - Source: `extensions/km-agent/src/conversations/artifacts.ts:291`

**Files stored per user:**

| File | Path | Content |
|------|------|---------|
| `conversations.json` | `.km-agent/conversations.json` | Array of `ConversationMetadata` objects — the **conversation index** for this user. Each entry has: `id`, `sessionKey`, `title`, `status` (active/archived), `createdAt`, `updatedAt`, `lastMessageAt`. Source: `conversations/service.ts:23-31` |
| `session-artifacts.json` | `.km-agent/session-artifacts.json` | Array of `ConversationArtifactContext` objects — maps sessionKeys to artifact directories. Source: `conversations/artifacts.ts:14-19` |
| Artifact directories | `AI 工作区/成果文件/{title}-{id}/` | Per-conversation directories containing generated deliverables (HTML, DOCX, PDF, MD, images, etc.). Source: `conversations/artifacts.ts:43,50-65` |

**Key finding:** The conversation **metadata** (list of conversations, titles, statuses, sessionKeys) is stored as JSON files on disk, NOT in the km-agent DB. The actual **messages** are stored by the OpenClaw runtime (see 1.2 below).

### 1.2 km-agent DB (project_sessions table)

**Schema** (`extensions/km-agent/prisma/schema.prisma:92-103`):

``prisma
model ProjectSession {
  id         String   @id @default(cuid())
  projectId  String   @map("project_id")
  sessionKey String   @map("session_key")
  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt
  project    Project  @relation(...)

  @@unique([projectId])
  @@unique([sessionKey])
  @@map("project_sessions")
}
``

**What project_sessions stores:**
- A mapping from `projectId` to `sessionKey`
- The `sessionKey` format is `agent:{agentId}:km:project:{projectId}` (source: `projects/service.ts:115`)
- This is for the **old project-based chat system**, NOT the new conversations system

**The km-agent DB does NOT store conversation messages.** Messages are stored by the OpenClaw runtime's session store, accessed via `runtime.subagent.getSessionMessages()` (source: `openclaw/gateway.ts:63`). The session store is file-based, keyed by `sessionKey`.

**Other km-agent DB tables:**

| Table | Purpose | Stores messages? |
|-------|---------|-----------------|
| `projects` | Project metadata (id, userId, agentId, name, rootPath, status) | No |
| `project_sessions` | Maps projectId → sessionKey for old chat | No |
| `steps` | Project tree steps (title, order, status) | No |
| `step_files` | File metadata within steps (fileId, path, mimeType, size) | No |
| `users` | km-agent user records | No |
| `user_identities` | Provider identity mappings | No |
| `user_agent_bindings` | Maps userId → agentId (unique per user and per agent) | No |
| `refresh_tokens` | Auth refresh tokens | No |

### 1.3 How km-agent Retrieves Conversation History

**Two separate systems coexist:**

#### A. New Conversations System (`/api/km/conversations/*`)

Source: `extensions/km-agent/src/conversations/service.ts` and `http/conversation-routes.ts`

| Operation | Data Source |
|-----------|------------|
| `listConversations` | Reads `conversations.json` from disk + `gateway.listSessionEntries()` from OpenClaw runtime. Source: `service.ts:238-266` |
| `getConversation` | Reads `conversations.json` for metadata + `gateway.getSessionMessages(sessionKey)` for messages. Source: `service.ts:315-349` |
| `createConversation` | Writes to `conversations.json` + creates artifact directory + calls `gateway.resetSession()`. Source: `service.ts:268-293` |
| `streamMessage` | Calls `gateway.run(sessionKey, message)` which sends to OpenClaw runtime. Source: `service.ts:351-680` |

**Critical:** The `sessionKey` for conversations is `agent:{agentId}:km:conversation:{conversationId}` (source: `service.ts:855-857`). The `agentId` is derived from the userId (`u_{userId}`). If the userId changes, the agentId changes, and the sessionKey no longer matches.

#### B. Old Project Chat System (`/api/km/projects/:id/chat/*`)

Source: `extensions/km-agent/src/chat/service.ts`

| Operation | Data Source |
|-----------|------------|
| `listMessages` | Looks up `project_sessions` table for sessionKey, then calls `gateway.getSessionMessages(sessionKey)`. Source: `chat/service.ts:221-249` |
| `streamMessage` | Uses sessionKey from `project_sessions` table. Source: `chat/service.ts:251-483` |

### 1.4 What Happens If DB Records Are Missing But Files Exist

**For the new conversations system:**
- The conversation list (`listConversations`) reads from `conversations.json` on disk — **it does NOT query the DB**.
- Messages are retrieved via `gateway.getSessionMessages(sessionKey)` — this reads from the OpenClaw runtime's session store (file-based), **NOT from the km-agent DB**.
- **Conclusion:** The km-agent DB (project_sessions, steps, step_files) is IRRELEVANT for the new conversations system. Removing it has zero impact on conversation retrieval.

**For the old project chat system:**
- `listMessages` requires the `project_sessions` table to find the sessionKey. If the DB record is missing, it throws "project session not found" (source: `chat/service.ts:562-565`).
- **Conclusion:** Old project chats would break without the DB, but this system appears to be legacy.

---

## 2. insightweaver Conversation Storage

### 2.1 insightweaver DB Tables

**ZclawSession** (`packages/db/prisma/schema.prisma:1434-1458`):
``prisma
model ZclawSession {
  id               String    @id @default(uuid())
  userId           String
  agentInstanceId  String
  locale           String    @default("zh")
  title            String?
  status           String    @default("active")
  lastMessageAt    DateTime?
  lastUsedProvider String?
  lastUsedModel    String?
  lastUsedAt       DateTime?
  // timestamps, isDeleted...
  bindings      ZclawChatBinding[]
  messages      ZclawMessage[]
}
``

**ZclawChatBinding** (`schema.prisma:1460-1477`):
``prisma
model ZclawChatBinding {
  id                 String   @id @default(uuid())
  userId             String
  sessionId          String
  agentId            String
  openclawSessionKey String    // e.g. "agent:u_abc:km:conversation:conv_xyz"
  // timestamps, isDeleted...
}
``

**ZclawMessage** (`schema.prisma:1479-1493`):
``prisma
model ZclawMessage {
  id         String   @id @default(uuid())
  sessionId  String
  role       String
  content    String
  status     String?
  rawPayload Json?
  // timestamps, isDeleted...
}
``

**What insightweaver stores:**
- `ZclawSession`: Session metadata (title, status, timestamps) — a **local cache** of km-agent conversations
- `ZclawChatBinding`: Maps insightweaver sessionId → km-agent's `openclawSessionKey` — the **bridge** between the two systems
- `ZclawMessage`: **Local cached copy** of conversation messages, synced from km-agent

### 2.2 How insightweaver Retrieves Conversation History

Source: `apps/api/src/zclaw/zclaw.service.ts`

**listSessions** (line 3626):
1. Queries local `ZclawSession` table (`listLocalSessions`, line 7281)
2. Calls km-agent `listConversations` (`listRemoteSessions`, line 7253)
3. Syncs remote sessions into local DB (`syncRemoteSessions`, line 7682)
4. Returns local sessions

**getSessionDetail** (line 5302):
1. First checks local DB for session with messages (`getLocalSessionDetail`, line 7477)
2. If local has messages and is "trusted", returns local data directly (line 5318-5326)
3. Otherwise, calls km-agent `getConversation` (`getRemoteSessionDetail`, line 7414)
4. Syncs remote messages into local DB (`syncRemoteSessionDetail`, line 7706)
5. If km-agent fails, falls back to local data with `recover_failed` status (line 5359-5393)

**getSessionMessagesPage** (line 5397):
1. Gets the `openclawSessionKey` from `ZclawChatBinding` (line 5421)
2. Calls km-agent `getSessionHistory(userId, sessionKey)` (line 5436)
3. Falls back to local `ZclawMessage` if km-agent fails (line 5480-5496)

**createSession** (line 5500):
1. Calls km-agent `createConversation` (line 5511)
2. Creates local `ZclawSession` record (line 5526)
3. Creates `ZclawChatBinding` with the `openclawSessionKey` (line 5536)

### 2.3 The Session Key Chain

The session key is the critical link:

``
insightweaver ZclawChatBinding.openclawSessionKey
  = "agent:{agentId}:km:conversation:{conversationId}"
  = km-agent conversations.json → ConversationMetadata.sessionKey
  = OpenClaw runtime session store key
``

Source: `zclaw.service.ts:8060-8065` (`buildOpenClawConversationSessionKey`)
Source: `km-agent conversations/service.ts:855-857` (`buildConversationSessionKey`)

Both sides build the same key using the same formula: `agent:{agentId}:km:conversation:{conversationId}`.

The `agentId` is derived from userId: `u_{userId}` (seen in project knowledge context).

---

## 3. Impact Assessment: NOT Migrating km-agent DB

### 3.1 What is Lost If km-agent DB Is Not Migrated

| Data | Location | Lost? | Impact |
|------|----------|-------|--------|
| Conversation list (titles, IDs, statuses) | **Disk**: `conversations.json` | **NO** — stored on filesystem, not DB | None |
| Conversation messages | **OpenClaw runtime session store** (file-based) | **NO** — not in km-agent DB | None |
| Artifact directories (generated files) | **Disk**: `AI 工作区/成果文件/` | **NO** — stored on filesystem | None |
| Artifact index | **Disk**: `session-artifacts.json` | **NO** — stored on filesystem | None |
| Old project chat sessions | **DB**: `project_sessions` table | **YES** | Old project-based chats lose their sessionKey mapping |
| Old project tree structure | **DB**: `steps` + `step_files` tables | **YES** | Old project tree metadata lost |
| User-agent bindings | **DB**: `user_agent_bindings` table | **YES** | Binding between userId and agentId lost |

### 3.2 Can the User Still See Old Conversations?

**YES — with a critical caveat about the userId → agentId → sessionKey chain.**

The conversation data survives on disk, but access depends on the sessionKey resolution:

1. **insightweaver's local cache** (`ZclawSession` + `ZclawMessage`): If insightweaver's DB IS migrated, the local cache survives. The UI will show session titles and cached messages from `ZclawMessage`.

2. **km-agent conversation list**: `listConversations` reads `conversations.json` from the user's workspace directory. The directory is named `workspace-u_{userId}`. If the userId changes:
   - The workspace directory name changes (`workspace-u_{newUserId}` vs `workspace-u_{oldUserId}`)
   - The old `conversations.json` is in the OLD directory
   - The new userId won't find the old conversations

3. **km-agent message retrieval**: Even if the conversation list is found, `getSessionMessages(sessionKey)` uses the sessionKey which embeds the agentId (`agent:u_{userId}:km:conversation:{id}`). If the agentId changes due to userId migration, the sessionKey won't match any existing session in the OpenClaw runtime.

### 3.3 Can the User Still Access Old Workspace Files?

**Same problem as 3.2.** Workspace files are in `workspace-u_{userId}/`. If userId changes:
- Old files remain in `workspace-u_{oldUserId}/`
- New userId gets a fresh `workspace-u_{newUserId}/`
- Old workspace files become orphaned on disk

### 3.4 Data ONLY in DB, NOT on Disk

| Data | Only in DB? |
|------|------------|
| `project_sessions.sessionKey` | **YES** — the mapping from projectId to sessionKey is ONLY in the DB. Without it, old project chats cannot find their messages. |
| `steps` / `step_files` metadata | **YES** — project tree structure is only in the DB |
| `user_agent_bindings` | **YES** — the userId→agentId mapping is only in the DB |
| Conversation metadata | **NO** — duplicated in `conversations.json` on disk |
| Messages | **NO** — stored in OpenClaw runtime session store (file-based) |

### 3.5 Worst-Case User Experience

If km-agent DB is NOT migrated AND userId changes:

1. **Conversation list**: User sees an empty conversation list in km-agent (new workspace directory has no `conversations.json`). However, insightweaver's local `ZclawSession` cache may still show old session titles.

2. **Opening an old conversation from insightweaver cache**:
   - insightweaver tries to call km-agent `getConversation(conversationId)`
   - km-agent looks up `conversations.json` in the NEW workspace → not found → returns 404 "conversation not found"
   - insightweaver falls back to local `ZclawMessage` cache
   - User sees **cached messages only** (whatever was last synced into insightweaver's DB)
   - If no local cache exists: UI shows "未能从历史服务恢复该会话消息，请稍后重试" (Could not restore messages from history)

3. **Sending a new message in an old conversation**:
   - Would fail because km-agent cannot find the conversation
   - User must start a new conversation

4. **Workspace files**: Old generated files (reports, documents) in `AI 工作区/成果文件/` become inaccessible under the new userId

5. **Old project chats**: Completely broken — `project_sessions` table is the only way to resolve the sessionKey, and it's in the DB

### 3.6 Summary: What Breaks Without km-agent DB Migration

| Scenario | Breaks? | User Impact |
|----------|---------|-------------|
| New conversations (post-migration) | No | Works normally |
| Viewing old conversation titles (via insightweaver cache) | Partially | insightweaver's `ZclawSession` table preserves titles |
| Viewing old conversation messages (via insightweaver cache) | Partially | `ZclawMessage` table has cached messages; depth depends on last sync |
| Viewing old conversation messages (via km-agent) | **YES** | SessionKey mismatch → cannot retrieve from OpenClaw runtime |
| Old workspace files | **YES** | Orphaned in old `workspace-u_{oldUserId}/` directory |
| Old project-based chats | **YES** | `project_sessions` table lost |
| Continuing old conversations | **YES** | km-agent cannot find the conversation |

### 3.7 Key Insight

The km-agent DB itself is NOT the primary concern for conversation data. The real issue is the **userId → workspace directory → sessionKey chain**:

- Workspace directory: `workspace-u_{userId}/`
- agentId: `u_{userId}`
- sessionKey: `agent:u_{userId}:km:conversation:{conversationId}`

If the userId changes, ALL three change, and the link to existing on-disk data (conversations.json, messages in OpenClaw session store, workspace files, artifact directories) is broken — regardless of whether the km-agent DB is migrated or not.

**The km-agent DB migration is secondary.** The primary concern is the workspace directory and its contents. If the workspace directory is renamed/moved to match the new userId, then:
- `conversations.json` would be found
- But the sessionKeys inside still embed the OLD agentId
- OpenClaw runtime session store keys still use the OLD agentId

So even with a workspace directory rename, the sessionKey mismatch would prevent message retrieval unless the sessionKeys are also updated (in `conversations.json` AND in the OpenClaw runtime's session store files).
