# 并发修复方案（多实例）

本文档汇总后端并发风险与修复方案。

## 1) MCP 会话/待处理状态仅存在内存（按方案 A 修复）
**现象**
- 跨实例请求会丢失 pending 状态，报错 `No pending MCP request found`。
- 重连、超时重试、负载均衡重分配时更易触发。

**修复方案 A（落地步骤）**
1. 引入 Redis 的 MCP 状态存储（与 `McpSessionStore` 同一 Redis 实例）。
2. 设计 key 与数据结构（示例）：  
   - `mcp:pending:{requestId}` -> `{ sessionId, endpoint, outlineId, userId, status, createdAt, ttlSeconds }`
   - `mcp:session:{outlineId}` -> `{ sessionId, endpoint, requestId, userId, status, createdAt }`
3. 在 `McpSession.callTool` 发起请求时：  
   - 写入 `pending` 记录（status=waiting）。  
   - 订阅流时若收到 `elicitation/create`，更新 `pending`（status=elicitation, elicitationId, payload 摘要）。
4. 在 `respondElicitation` 中：  
   - 优先从 Redis 读取 `pending` 或 `session`，恢复 sessionId/endpoint/requestId。  
   - 如果本地 `pendingResults` 缺失，改为从 Redis 驱动后续逻辑（例如等待新的 MCP 返回或按协议重新发起请求）。
5. 在 `waitForOutcome`/`waitForResult`：  
   - 本地没有 pending 时，查询 Redis；若存在则通过 MCP session 重新拉取结果（或根据协议重建请求等待）。  
   - 完成后删除 `pending` 记录。
6. 为 Redis 记录设置 TTL，建议 15~30 分钟，确保异常断链时自动清理。

**涉及代码**
- `apps/api/src/mcp/mcp.service.ts`
- `apps/api/src/mcp/mcp-session.ts`
- `apps/api/src/research/research.service.ts`

## 2) 短信冷却/锁与验证码校验非原子（按方案 A 修复）
**现象**
- 多实例并发下可能重复发送短信。
- 验证码校验可能被并发通过多次。

**修复方案 A（落地步骤）**
1. 使用 Redis Lua 脚本将“检查 + 写入”合并为原子操作。  
2. 发送验证码脚本：  
   - 若 `lockKey` 存在则返回锁定状态；若 `cooldownKey` 未过期则返回冷却状态。  
   - 仅在通过校验时写入 `codeKey`、`cooldownKey`，并清理 `attemptsKey`。  
3. 校验验证码脚本：  
   - 原子读取 `codeKey` 并比较；不匹配则 `INCR attemptsKey` 并设置 TTL。  
   - 若达到上限，原子写入 `lockKey`。  
   - 匹配则原子删除 `codeKey` / `attemptsKey` / `lockKey`。  
4. 在 `AuthService` 中以 `EVALSHA` 调用脚本，失败时回退 `EVAL` 并缓存脚本 SHA。  
5. Redis key TTL 仍使用现有配置（`SMS_CODE_TTL`、`SMS_SEND_COOLDOWN_SECONDS` 等）。  

**涉及代码**
- `apps/api/src/auth/auth.service.ts`

## 3) Refresh token 轮换存在并发窗口
**现象**
- 同一 refresh token 并发刷新可能产生多套新 token。

**修复方案**
- **方案 A（推荐）**：事务内条件更新（CAS）。
  - `updateMany` 条件：`revokedAt == null`、`tokenHash`、`expiresAt > now`、`isDeleted == false`。
  - 若更新行数为 0，视为并发或已撤销。
- **方案 B**：`SELECT ... FOR UPDATE` 锁行后再更新。
- **方案 C**：引入版本号（乐观锁）进行 CAS 更新。

**涉及代码**
- `apps/api/src/auth/auth.service.ts`

## 4) 研究大纲/正文写入缺少并发保护
**现象**
- 并发写入可能覆盖版本或产生重复。
- 消息去重为“先查后插”，存在竞态。

**修复方案**
- **方案 A（推荐）**：大纲/正文使用乐观锁。
  - `update` 时带 `where: { id, version }`，成功后 `version++`。
  - 失败返回 409，客户端重试/合并。
- **方案 B**：消息去重加唯一约束。
  - 例：`sessionId + role + contentHash + timeBucket`。
- **方案 C**：写入时增加 `updatedAt`/`version` 比较，只有“更高版本/更新更晚”时覆盖。

**涉及代码**
- `apps/api/src/research/research.service.ts`
- `packages/db/prisma/schema.prisma`
## 2026-07-09 月包权益并发修复记录

### 权益余额与冻结
- `freezeEntitlements`、`captureEntitlements`、`releaseEntitlements` 已改为数据库条件更新，不再读出旧余额后直接覆盖。
- capture/release 开始时锁定对应 `billing_tasks` 行，避免正常结算与 stale cleanup 同时处理同一任务。
- `entitlement_batches` 新增 CHECK 约束，数据库层保证余额、冻结和授权总量关系不被破坏。

### 订单发放
- `BillingOrderService.fulfillPaidOrder` 使用 CAS 状态机：`PENDING/FAILED -> PROCESSING -> SUCCESS/FAILED`。
- `SUCCESS` 幂等返回既有权益，`PROCESSING` 返回冲突，不允许旧并发请求覆盖成功结果。
- 订单发放相关批次新增 partial unique index，防止支付回调、对账、人工 retry 并发重复发放。

### B2B 月包成员与库存
- `ensureB2BMonthlyEntitlementsForMember` 在事务内重查并创建缺失批次，唯一冲突后读取既有批次幂等返回。
- B2B 自动补发成员权益新增 partial unique index，限制同一月包 anchor 下同一成员同一权益类型只能有一条 active/scheduled/paused 未删除批次。
- B2B topup inventory 分配使用 `remainingSeats > 0` 条件更新，避免最后一个 seat 并发超卖。

### B2B 席位审批/导入
- 成员审批、启用和导入激活时在事务内锁定企业 membership 集合，并重新计算 active/disabled 占用席位。
- 同一企业的并发审批/导入不能再基于旧 count 同时通过 `memberLimit` 检查。

### 套餐可见性与 quota 口径
- `/billing/plans` 前台接口要求 `enterpriseId` 并校验 active member 或 B 端 owner/admin，避免任意登录用户枚举所有 active plans。
- storage quota 改为授权总量减 usage snapshot；缺失 snapshot 时展示不可用，不把未知用量当成 0。
