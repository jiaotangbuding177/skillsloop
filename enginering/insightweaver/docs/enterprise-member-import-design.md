# 组织成员 Excel 批量导入设计方案

## 实施状态（2026-06-23）

- Step 1/2 已完成：已新增 `EnterpriseMemberImportJob` 数据模型、迁移、Prisma 关系、导入 DTO、后端导入 service 骨架、Controller API、模板下载接口、基础权限校验和任务查询能力。
- Step 3/4 本轮完成：上传后会真实解析 Excel 第一张 sheet，校验表头、空数据、手机号格式、文件内重复手机号和部门；校验通过后会批量查询手机号身份，为新手机号生成 `userId` 和独立 `passwordHash`，并统计 `totalRows`、`createdUsers`。
- Step 5/6 已完成：校验和身份解析通过后会进入 `writing`，在同一个 Prisma `$transaction` 内批量创建新用户、手机号身份、钱包、成员关系，并批量初始化普通成员配额；事务成功后 job 标记为 `succeeded`，任意写入异常会回滚业务数据并把 job 标记为 `failed`。
- Step 7 已完成：前端已在现有成员管理 API 模块中新增导入上传、job 查询、模板下载方法和类型；上传使用 XHR 暴露真实上传进度，模板下载返回 `Blob` 和文件名。
- Step 8 已完成：成员管理页已新增“导入成员”按钮和导入弹窗，支持模板下载、组织选择/锁定、Excel 选择、初始密码校验、上传进度、job 轮询、成功汇总、失败错误展示与错误复制。
- Step 9 已完成：已补充后端 Controller 导入接口测试、前端导入弹窗核心交互测试，并完成导入链路定向回归与 API 全量回归。
- Step 10 已完成：按最新产品规则调整导入语义。Excel 角色列下线，新建组织成员统一为 `member`；任何已有组织绑定一律跳过，不再恢复 pending/rejected/disabled；`operator` 允许使用导入能力；文档和测试同步更新。
- Step 11 已完成：统一初始密码输入增加明文/密文切换；导入创建手机号身份时不再写入 `phoneMasked`；移除未上线角色列模板的兼容测试和文档描述；移除成员恢复统计字段，不再在 DB/API/前端展示中保留该概念。
- 当前边界：组织成员 Excel 批量导入 MVP 已完成；Web 全量测试仍存在非导入链路遗留失败，Next standalone 构建在当前 Windows 环境仍受 symlink 权限限制，详见 Step 9-11 记录。

## 1. 背景与目标

当前“组织管理 - 成员管理”页面已经支持成员申请审批、成员状态调整、角色调整和成员配额配置，但缺少面向管理员的批量导入能力。实际运营场景中，组织初始化或组织扩容可能一次性导入几千到几万名成员，如果逐个邀请或逐条写入，会造成操作成本高、接口超时、数据库压力不可控、失败后难以回滚等问题。

本方案新增“导入成员”能力：管理员上传 Excel，系统以手机号作为全局用户唯一识别来源，自动创建不存在的用户账号，并把用户与指定组织建立成员关系。整个导入必须先完整校验，再在一个数据库事务中批量写入，保证“全部成功或全部失败”。

核心目标：

- 支持平台超管、组织管理员和组织运营员批量导入组织成员。
- 手机号作为唯一识别来源。
- Excel 数据必须完整且合法，不允许空数据、重复手机号或非法部门进入写入阶段。
- 新手机号创建全局用户账号，并设置可登录的初始密码。
- 已存在手机号只在尚未绑定目标组织时建立成员关系，不修改已有账号密码。
- 只要手机号对应用户已经和目标组织存在绑定关系，无论成员状态如何都跳过，不更新姓名、部门、角色或状态。
- 数据库写入采用批量 SQL 和事务，不做逐条记录写入。
- 前端展示上传和处理进度，避免长时间无反馈。
- 文档按阶段拆分，后续可从任意步骤继续实施。

## 2. 现有系统依据

本方案基于当前代码结构和数据模型设计：

- 前端成员管理页：`apps/web/src/app/(zclaw-shell)/admin/enterprise-memberships/page.tsx`
- 后端组织控制器：`apps/api/src/enterprises/enterprise.controller.ts`
- 后端组织服务：`apps/api/src/enterprises/enterprise.service.ts`
- Prisma schema：`packages/db/prisma/schema.prisma`
- 密码能力：`apps/api/src/auth/password.service.ts`
- 手机号工具：`apps/api/src/utils/phone.ts`

现有关键模型：

- `users`
  - 全局用户账号。
  - `role = 'admin'` 表示平台超管。
  - `status = 'active'` 表示账号可登录。
  - `passwordHash` 已存在，用于手机号密码登录。

- `user_identities`
  - 账号登录身份。
  - 手机号登录使用 `provider = 'phone'`。
  - `providerUserId` 存储规范化手机号。

- `enterprises`
  - 组织主体。
  - 导入目标组织必须 `status = 'active'` 且 `isDeleted = false`。

- `enterprise_memberships`
  - 用户与组织的成员关系。
  - `role` 支持 `viewer/member/editor/operator/admin/owner`。
  - `status` 支持现有业务中的 `pending/active/rejected/disabled`。
  - 唯一约束为 `[enterpriseId, userId, isDeleted]`。

- `enterprise_departments`
  - 组织部门。
  - 导入中的部门必须匹配目标组织下未删除部门。

现有权限口径：

- 平台超管：`users.role = 'admin'`。
- 组织管理员：目标组织中的 active membership，且 `role in ('owner', 'admin')`。
- 组织运营员：目标组织中的 active membership，且 `role = 'operator'`。导入能力允许 `operator` 使用，但不把 `operator` 视为通用组织管理员。

## 3. 产品流程

### 3.1 入口

在“组织管理 - 成员管理”页面表格工具栏新增“导入成员”按钮。

可见规则：

- 平台超管可见。
- 当前激活组织的 `owner/admin/operator` 可见。
- 普通组织成员、未登录用户、无成员管理权限的用户不可见。

点击后打开“导入组织成员”弹窗。

### 3.2 弹窗字段

弹窗第一步展示表单：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| 目标组织 | 是 | 平台超管必须选择；组织管理员默认锁定当前激活组织，但仍展示组织名称 |
| Excel 文件 | 是 | 仅支持 `.xlsx`、`.xls` |
| 统一初始密码 | 是 | 只用于本次导入中新创建的用户 |

统一初始密码设计决策：

- 由执行导入的管理员填写。
- 不放入 Excel。
- 不由系统生成不可见默认值。
- 不在导入结果页明文回显。
- 只给新建用户设置密码；已存在用户密码保持不变。

选择该方案的原因：

- 管理员可提前告知新用户初始密码，保证新建用户可登录。
- 避免 Excel 中为每行携带敏感密码。
- 避免系统生成密码后无人知晓，导致用户无法登录。
- 避免修改已有用户密码，因为同一个用户可能属于多个组织，密码是全局账号属性，不属于组织成员关系。

### 3.3 Excel 模板

弹窗提供“下载模板”按钮，下载标准 Excel。

第一行固定表头：

| 手机号 | 姓名 | 部门 |
| --- | --- | --- |

字段规则：

- `手机号`
  - 必填。
  - 支持 `13800138000`、`+8613800138000`、`8613800138000`。
  - 服务端统一规范化后用于匹配 `user_identities.providerUserId`。

- `姓名`
  - 必填。
  - 写入 `enterprise_memberships.realName`。

- `部门`
  - 必填。
  - 必须等于目标组织已有部门名称。
  - 不在导入中自动创建部门。

- 角色不再作为导入列。
  - 新创建的组织成员关系统一写入 `member`。
  - 如果用户已经和组织存在绑定关系，既有角色保持不变。

### 3.4 进度与结果

导入分为两个阶段：

1. 文件上传。
2. 服务端解析、校验、写入。

前端进度条：

- 上传中：使用 XHR `upload.onprogress` 展示真实上传进度，映射到 0%-30%。
- 服务端处理中：通过 job 轮询展示估算进度。
- 完成：进度到 100%，展示汇总。
- 失败：停止进度条，展示错误。

服务端阶段建议映射：

| job status | 展示文案 | 进度范围 |
| --- | --- | --- |
| `queued` | 排队中 | 30%-35% |
| `parsing` | 解析 Excel 中 | 35%-45% |
| `validating` | 校验数据中 | 45%-65% |
| `writing` | 写入成员中 | 65%-95% |
| `succeeded` | 导入完成 | 100% |
| `failed` | 导入失败 | 停止 |

成功结果展示：

- 总行数。
- 新建用户数。
- 新增成员关系数。
- 已存在成员关系跳过数。
- 导入耗时。

失败结果展示：

- 失败阶段。
- 错误摘要。
- 前 100 条错误明细。
- 支持复制错误明细。
- 支持下载错误明细文本或 CSV。

## 4. 后端 API 设计

### 4.1 平台超管导入

`POST /api/enterprises/admin/memberships/import`

权限：

- 必须通过 `JwtAuthGuard`。
- 必须通过 `AdminGuard`。

请求类型：

`multipart/form-data`

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `enterpriseId` | string | 是 | 目标组织 ID |
| `initialPassword` | string | 是 | 统一初始密码 |
| `file` | file | 是 | Excel 文件 |

响应：

```json
{
  "jobId": "enterprise-member-import-job-id"
}
```

### 4.2 组织管理员导入

`POST /api/enterprises/enterprise-admin/memberships/import`

权限：

- 必须通过 `JwtAuthGuard`。
- 服务端校验调用人是目标组织 active `owner/admin/operator`。

请求类型：

`multipart/form-data`

字段同平台超管导入。

组织管理员额外限制：

- 不能导入到无权限组织。
- Excel 不再支持角色列，新导入成员固定为 `member`。

响应同平台超管导入。

### 4.3 查询导入任务

`GET /api/enterprises/memberships/import-jobs/:jobId`

权限：

- 任务创建者可查看。
- 平台超管可查看。
- 目标组织 active `owner/admin/operator` 可查看。

响应：

```json
{
  "job": {
    "id": "job-id",
    "enterpriseId": "enterprise-id",
    "status": "writing",
    "phase": "写入成员中",
    "progress": 82,
    "totalRows": 12000,
    "createdUsers": 3200,
    "createdMemberships": 8800,
    "skippedExistingMemberships": 2500,
    "errors": [],
    "createdAt": "2026-06-23T10:00:00.000Z",
    "updatedAt": "2026-06-23T10:01:10.000Z",
    "finishedAt": null
  }
}
```

### 4.4 下载导入模板

`GET /api/enterprises/memberships/import-template`

权限：

- 登录用户即可下载。
- 前端只在有导入入口时展示。

响应：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="enterprise-member-import-template.xlsx"`

## 5. 数据模型设计

新增 Prisma model：`EnterpriseMemberImportJob`

建议字段：

```prisma
model EnterpriseMemberImportJob {
  id                             String    @id @default(uuid())
  enterpriseId                   String
  createdBy                      String
  status                         String    @default("queued")
  phase                          String?
  progress                       Int       @default(0)
  totalRows                      Int       @default(0)
  createdUsers                   Int       @default(0)
  createdMemberships             Int       @default(0)
  skippedExistingMemberships     Int       @default(0)
  errorJson                      Json?
  createdAt                      DateTime  @default(now())
  updatedAt                      DateTime  @updatedAt
  finishedAt                     DateTime?

  enterprise Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)
  creator    User       @relation(fields: [createdBy], references: [id], onDelete: Cascade)

  @@index([enterpriseId, createdAt])
  @@index([createdBy, createdAt])
  @@index([status, createdAt])
  @@map("enterprise_member_import_jobs")
}
```

需要同步在 `User` 和 `Enterprise` 上补 relation：

- `User.enterpriseMemberImportJobs`
- `Enterprise.memberImportJobs`

状态枚举建议先使用字符串，保持当前项目模型风格一致：

- `queued`
- `parsing`
- `validating`
- `writing`
- `succeeded`
- `failed`

`errorJson` 结构：

```json
{
  "summary": "第 3 行手机号为空",
  "errors": [
    {
      "row": 3,
      "field": "手机号",
      "message": "手机号不能为空"
    }
  ]
}
```

## 6. 文件解析与校验设计

### 6.1 文件限制

- 文件字段名：`file`。
- 支持后缀：`.xlsx`、`.xls`。
- 最大文件大小：10MB。
- 最大有效数据行：50000。
- 只读取第一个 sheet。

### 6.2 表头识别

第一行必须包含：

- `手机号`
- `姓名`
- `部门`

字段名称应精确匹配。为了减少误操作，MVP 不做复杂同义词兼容。

### 6.3 空数据规则

- 完全空行忽略。
- 如果一行中任一业务字段有值，则该行必须满足所有必填字段。
- `手机号`、`姓名`、`部门` 有任意一个为空，任务失败。

### 6.4 手机号规范化

使用现有 `normalizePhone` 的语义：

- 去掉空白字符。
- `1xxxxxxxxxx` 转为 `+861xxxxxxxxxx`。
- 以 `+` 开头的号码保留。
- 其他格式保留原值后继续校验。

导入校验增加格式要求：

- 国内手机号接受：
  - `1[3-9]\d{9}`
  - `861[3-9]\d{9}`
  - `+861[3-9]\d{9}`
- 国际手机号接受：
  - `+\d{6,20}`

规范化后的手机号用于去重和匹配用户身份。

### 6.5 重复规则

同一个 Excel 文件中，规范化手机号重复则整体失败。

错误示例：

```json
{
  "row": 28,
  "field": "手机号",
  "message": "手机号与第 12 行重复"
}
```

### 6.6 部门校验

导入前查询目标组织所有未删除部门：

- `enterprise_departments.enterpriseId = targetEnterpriseId`
- `isDeleted = false`

Excel 部门必须完全匹配部门名称。

MVP 不自动创建部门，原因：

- 防止 Excel 里错别字创建脏部门。
- 部门结构属于组织管理能力，应由管理员先维护。

### 6.7 角色处理

- 导入模板不包含角色列。
- 新建的组织成员关系固定使用 `role = 'member'`。
- 导入流程不提供角色列兼容能力。
- 已有组织绑定不会被导入更新，因此既有角色保持不变。

## 7. 导入任务执行设计

### 7.1 为什么使用异步任务

上万行 Excel 解析、密码哈希、批量写入可能超过普通 HTTP 请求时长。如果在上传接口中同步等待全部处理完成，前端容易超时，用户也无法感知服务端处理阶段。

因此上传接口只创建任务并启动后台处理，立即返回 `jobId`。前端通过轮询查询任务状态。

### 7.2 任务生命周期

1. `queued`
   - 已接收文件和参数。
   - 创建任务记录。

2. `parsing`
   - 解析 Excel。
   - 提取第一个 sheet。
   - 识别表头和数据行。

3. `validating`
   - 校验组织、权限、密码、手机号、部门、重复数据。
   - 查询已有用户身份。
   - 计算导入计划。

4. `writing`
   - 进入数据库事务。
   - 批量创建用户、身份、钱包。
   - 批量插入或更新成员关系。
   - 批量初始化成员配额。

5. `succeeded`
   - 主事务提交成功。
   - 任务记录写入汇总。

6. `failed`
   - 任意阶段失败。
   - 业务写入事务如已开始则回滚。
   - 任务记录写入错误。

### 7.3 任务执行方式

MVP 可采用进程内异步执行：

```ts
void this.processEnterpriseMemberImportJob(jobId, input).catch(...)
```

注意：

- 上传接口返回前必须已经创建 job。
- 异步函数内部所有错误必须捕获并更新 job 为 `failed`。
- 如果服务进程重启，进程内任务会中断。MVP 可以接受，但需要在文档和错误处理里保留恢复策略。

后续增强：

- 可接入 Redis queue 或 BullMQ。
- 服务启动时扫描长时间 `queued/parsing/validating/writing` 的任务，将其标记为 `failed`，提示重新导入。

## 8. 批量写入与事务设计

### 8.1 总体原则

- 事务前完成全部校验和密码哈希。
- 事务内只做数据库写入。
- 事务内不做 Excel 解析、不做密码哈希、不做远程调用。
- 禁止对每一行单独执行一条 SQL。
- 使用批量 SQL、`jsonb_to_recordset` 或分块 `createMany`。
- 所有业务写入放在同一个 Prisma `$transaction` 内。

### 8.2 导入计划结构

校验完成后生成内存导入计划：

```ts
type ImportRowPlan = {
  rowNumber: number;
  phone: string;
  realName: string;
  department: string;
};
```

查询已有身份后生成：

```ts
type ResolvedImportRow = ImportRowPlan & {
  userId: string;
  isNewUser: boolean;
  passwordHash?: string;
};
```

### 8.3 查询已有用户

事务前查询：

```sql
SELECT identity."providerUserId", identity."userId"
FROM "user_identities" identity
JOIN "users" user_record ON user_record."id" = identity."userId"
WHERE identity."provider" = 'phone'
  AND identity."providerUserId" = ANY($phones)
  AND identity."isDeleted" = false
  AND user_record."isDeleted" = false
```

手机号不存在时，生成新 `userId`。

### 8.4 密码哈希

对新用户逐个生成独立 `passwordHash`。

要求：

- 使用现有 `PasswordService.hashPassword`。
- 不复用同一个 hash，因为 salt 应独立。
- 使用并发限流，例如 8 或 16 个并发，避免 CPU 瞬时打满。
- 密码哈希在事务前完成。

### 8.5 批量创建 users

只为不存在手机号创建用户。

字段：

- `id`
- `role = 'user'`
- `status = 'active'`
- `passwordHash`
- `createdAt`
- `updatedAt`
- `isDeleted = false`

建议 SQL：

```sql
INSERT INTO "users" (
  "id",
  "role",
  "status",
  "passwordHash",
  "createdAt",
  "updatedAt",
  "isDeleted"
)
SELECT
  record."id",
  'user',
  'active',
  record."passwordHash",
  NOW(),
  NOW(),
  false
FROM jsonb_to_recordset($usersJson::jsonb)
  AS record("id" text, "passwordHash" text)
```

### 8.6 批量创建 user_identities

只为新用户创建手机号身份。

字段：

- `id`
- `userId`
- `provider = 'phone'`
- `providerUserId = normalizedPhone`
- `createdAt`
- `updatedAt`
- `isDeleted = false`

说明：本导入流程不写入 `phoneMasked` 字段，数据库保持默认 `null`。

建议 SQL：

```sql
INSERT INTO "user_identities" (
  "id",
  "userId",
  "provider",
  "providerUserId",
  "createdAt",
  "updatedAt",
  "isDeleted"
)
SELECT
  record."id",
  record."userId",
  'phone',
  record."phone",
  NOW(),
  NOW(),
  false
FROM jsonb_to_recordset($identitiesJson::jsonb)
  AS record("id" text, "userId" text, "phone" text)
```

### 8.7 批量创建 wallets

只为新用户创建钱包。

字段应符合现有 `Wallet` 模型。以当前迁移为准，通常需要：

- `userId`
- `balance = 0`
- `version = 0`

建议使用 `ON CONFLICT DO NOTHING`，防止并发或历史数据已存在。

### 8.8 批量处理 enterprise_memberships

先查询目标组织中这些用户已有成员关系：

```sql
SELECT "id", "userId", "status", "role"
FROM "enterprise_memberships"
WHERE "enterpriseId" = $enterpriseId
  AND "userId" = ANY($userIds)
  AND "isDeleted" = false
```

分类：

1. 已存在 membership，任意状态
   - 跳过。
   - 不更新 `status`、`realName`、`department`、`role`、`reviewedBy`、`reviewedAt`、`joinedAt`。
   - 即使状态是 `pending/rejected/disabled`，也不恢复为 active。

2. 不存在
   - 插入新 membership。
   - `role = 'member'`。
   - `status = 'active'`。
   - `joinedAt = NOW()`。
   - `reviewedBy = 当前管理员`。
   - `reviewedAt = NOW()`。

批量插入建议：

```sql
INSERT INTO "enterprise_memberships" (
  "id",
  "enterpriseId",
  "userId",
  "role",
  "status",
  "realName",
  "department",
  "reviewedBy",
  "reviewedAt",
  "joinedAt",
  "createdAt",
  "updatedAt",
  "isDeleted"
)
SELECT
  record."id",
  $enterpriseId,
  record."userId",
  'member',
  'active',
  record."realName",
  record."department",
  $adminUserId,
  NOW(),
  NOW(),
  NOW(),
  NOW(),
  false
FROM jsonb_to_recordset($membershipsJson::jsonb)
  AS record("id" text, "userId" text, "realName" text, "department" text)
```

### 8.9 批量初始化成员配额

现有单成员审批会调用 `initializeConversationQuotaForApprovedMember`。导入时不能逐个调用，需要实现批量版本。

目标：

- 只对本次新增的 `member` 绑定初始化配额。
- 已存在 membership 的跳过用户不初始化、不刷新配额。
- 已存在配额记录时保持现有覆盖配置，使用现有逻辑的 `ON CONFLICT` 语义。

建议 SQL：

```sql
INSERT INTO "zclaw_enterprise_conversation_quota_usages" (
  "id",
  "enterpriseId",
  "userId",
  "remainingConversations",
  "limitSnapshot",
  "overrideMode",
  "tokenOverrideMode",
  "periodType",
  "tokenLimitSnapshot",
  "windowStart",
  "windowEnd",
  "resetVersion",
  "createdAt",
  "updatedAt"
)
SELECT
  'zclaw-conv-quota-' || $enterpriseId || '-' || record."userId",
  $enterpriseId,
  record."userId",
  config."conversationLimit",
  config."conversationLimit",
  'inherit',
  'inherit',
  config."periodType",
  config."tokenLimit",
  DATE_TRUNC('month', NOW()),
  DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 microsecond',
  config."resetVersion",
  NOW(),
  NOW()
FROM jsonb_to_recordset($quotaUsersJson::jsonb)
  AS record("userId" text)
CROSS JOIN "zclaw_enterprise_conversation_quota_configs" config
WHERE config."enterpriseId" = $enterpriseId
  AND (config."conversationLimit" IS NOT NULL OR config."tokenLimit" IS NOT NULL)
ON CONFLICT ("enterpriseId", "userId") DO UPDATE SET
  "remainingConversations" = CASE
    WHEN "zclaw_enterprise_conversation_quota_usages"."overrideMode" = 'limited'
     AND "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride" IS NOT NULL
    THEN "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride"
    ELSE COALESCE(EXCLUDED."remainingConversations", "zclaw_enterprise_conversation_quota_usages"."remainingConversations")
  END,
  "limitSnapshot" = CASE
    WHEN "zclaw_enterprise_conversation_quota_usages"."overrideMode" = 'limited'
     AND "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride" IS NOT NULL
    THEN "zclaw_enterprise_conversation_quota_usages"."conversationLimitOverride"
    ELSE COALESCE(EXCLUDED."limitSnapshot", "zclaw_enterprise_conversation_quota_usages"."limitSnapshot")
  END,
  "periodType" = EXCLUDED."periodType",
  "tokenLimitSnapshot" = CASE
    WHEN "zclaw_enterprise_conversation_quota_usages"."tokenOverrideMode" = 'limited'
     AND "zclaw_enterprise_conversation_quota_usages"."tokenLimitOverride" IS NOT NULL
    THEN "zclaw_enterprise_conversation_quota_usages"."tokenLimitOverride"
    ELSE COALESCE(EXCLUDED."tokenLimitSnapshot", "zclaw_enterprise_conversation_quota_usages"."tokenLimitSnapshot")
  END,
  "resetVersion" = EXCLUDED."resetVersion",
  "updatedAt" = NOW()
```

## 9. 事务与失败处理

### 9.1 事务边界

事务内包含：

- 创建新用户。
- 创建手机号身份。
- 创建钱包。
- 新增成员关系。
- 恢复非 active 成员关系。
- 初始化成员配额。

事务外包含：

- 文件上传。
- Excel 解析。
- 数据校验。
- 密码哈希。
- job 状态更新。

原因：

- 文件解析和密码哈希耗时不可控，不应占用数据库事务。
- job 状态是任务可观测性数据，不应随业务事务回滚而丢失失败原因。

### 9.2 回滚要求

如果事务内任意 SQL 失败：

- 新建用户回滚。
- 新建身份回滚。
- 新建钱包回滚。
- 新增或恢复的成员关系回滚。
- 配额初始化回滚。
- job 标记为 `failed`。
- `errorJson.summary` 记录失败原因。

### 9.3 并发与唯一约束

可能出现两个管理员同时导入相同手机号。

处理策略：

- 文件级重复在校验阶段拦截。
- 数据库唯一约束仍作为最终保护。
- 新建身份时若发生唯一冲突，整批事务失败，提示“导入期间手机号状态发生变化，请重新导入”。
- 成员关系唯一冲突同理，失败后管理员重新导入即可。

MVP 不做幂等重试，因为要求“全部成功或全部失败”，并发冲突时失败更安全。

## 10. 前端设计

### 10.1 API 封装

新增前端 API 方法：

```ts
importAdminEnterpriseMembershipsApi(input, options)
importEnterpriseAdminMembershipsApi(input, options)
getEnterpriseMembershipImportJobApi(jobId)
downloadEnterpriseMembershipImportTemplateApi()
```

上传接口应使用 XHR 而不是普通 `fetch`，以便获取上传进度。

输入类型：

```ts
type ImportEnterpriseMembershipsInput = {
  enterpriseId: string;
  initialPassword: string;
  file: File;
};
```

上传进度回调：

```ts
type ImportUploadProgress = (loaded: number, total: number) => void;
```

### 10.2 弹窗状态机

弹窗内部状态：

- `form`
  - 用户选择组织、文件、密码。

- `uploading`
  - 文件上传中。
  - 进度 0%-30%。

- `processing`
  - 已拿到 `jobId`。
  - 轮询 job。
  - 展示服务端阶段。

- `succeeded`
  - 展示汇总。
  - 提供“完成”按钮。
  - 关闭后刷新成员列表。

- `failed`
  - 展示错误。
  - 可返回表单重新选择文件。

### 10.3 组织选择

平台超管：

- 使用现有 `loadPlatformAdminManagedEnterpriseOptions` 获取组织。
- 必须选择一个组织才能提交。

组织管理员：

- 使用当前激活组织。
- 弹窗显示组织名称和 ID。
- 组织选择控件置为只读。
- 如果没有 active enterprise，按钮不可用或点击后提示先选择组织。

### 10.4 表单校验

前端提交前校验：

- 组织不能为空。
- 文件不能为空。
- 文件后缀必须为 `.xlsx` 或 `.xls`。
- 密码不能为空。
- 密码长度和字符规则尽量与后端保持一致。

注意：

- 前端校验只做体验优化。
- 服务端仍必须完整校验。

### 10.5 错误展示

错误明细表字段：

- 行号。
- 字段。
- 错误原因。

只展示前 100 条，避免弹窗过长。

提供两个操作：

- 复制错误明细。
- 下载错误明细。

### 10.6 成功后刷新

导入成功后：

- 调用当前页面已有 `loadMemberships()`。
- 如果当前筛选条件过滤掉新成员，不强制清空筛选。
- toast 提示导入成功。

## 11. 后端模块拆分建议

建议新增文件：

- `apps/api/src/enterprises/dto/import-enterprise-members.dto.ts`
  - DTO 和常量。

- `apps/api/src/enterprises/enterprise-member-import.service.ts`
  - 导入任务核心逻辑。

- `apps/api/src/enterprises/enterprise-member-import.types.ts`
  - 内部类型。

也可以先放在 `EnterpriseService` 中，但不推荐。导入逻辑较长，独立 service 更清晰。

`EnterpriseModule` 注入：

- `EnterpriseService`
- `EnterpriseMemberImportService`
- `PasswordService`

如果当前 `EnterpriseModule` 尚未注入 `PasswordService`，需要从 Auth 模块导出或直接 provider 注入，按现有模块组织调整。

## 12. 测试方案

### 12.1 后端单元测试

建议新增：

- `apps/api/src/enterprises/enterprise-member-import.service.test.ts`

必须覆盖：

1. 空文件失败。
2. 无 sheet 失败。
3. 缺少必需表头失败。
4. 空手机号失败。
5. 空姓名失败。
6. 空部门失败。
7. 非法手机号失败。
8. 同文件重复手机号失败。
9. 部门不存在失败。
10. 手机号不存在时创建 user、identity、wallet、membership、passwordHash，且 identity 不写入 `phoneMasked`。
11. 手机号存在但无组织绑定时只创建 membership，不修改已有密码。
12. 已存在 active membership 跳过，不更新姓名/部门/角色。
13. 已存在 pending membership 跳过，不恢复、不更新资料。
14. 已存在 rejected membership 跳过，不恢复、不更新资料。
15. 已存在 disabled membership 跳过，不恢复、不更新资料。
16. 组织管理员/运营员不能导入其他组织。
17. 事务中任意写入失败时，用户、身份、钱包、成员关系全部回滚。
18. 本次新增 member 的配额批量初始化。
19. 已跳过的既有成员不初始化、不刷新配额。

### 12.2 后端接口测试

可在 controller test 中覆盖：

- 超管导入接口要求 AdminGuard。
- 组织管理员导入接口要求目标组织 owner/admin/operator。
- job 查询权限。
- 模板下载返回正确文件类型。

### 12.3 前端测试

建议覆盖：

1. 非授权用户不显示导入按钮。
2. 平台超管弹窗要求选择组织。
3. 组织管理员弹窗锁定当前组织。
4. 文件为空不能提交。
5. 密码为空不能提交。
6. 非 Excel 后缀不能提交。
7. 上传进度 0%-30% 正确展示。
8. job 轮询阶段进度正确展示。
9. 成功后展示汇总并刷新列表。
10. 失败后展示错误明细。
11. 统一初始密码支持明文/密文切换，默认隐藏。

## 13. 验收标准

功能验收：

- 平台超管可导入任意 active 组织成员。
- 组织 `owner/admin/operator` 可导入自己组织成员。
- 组织管理员/运营员不能导入其他组织。
- Excel 中的角色列不再生效，新成员固定为 `member`。
- Excel 中的空数据、重复手机号、非法手机号、非法部门会阻止导入。
- 新手机号用户可使用管理员填写的初始密码登录。
- 已存在手机号用户密码不变。
- 已存在任意状态组织成员不被更新。
- 已存在非 active 成员不会被恢复为 active。
- 任意失败不会留下部分导入数据。

性能验收：

- 1000 行导入不应出现逐行 SQL。
- 10000 行导入应能在可接受时间内完成，具体时间取决于密码哈希 CPU 和数据库性能。
- 事务内耗时应主要来自批量写入，不包含 Excel 解析和密码哈希。

体验验收：

- 上传和处理期间都有进度反馈。
- 失败原因可定位到 Excel 行号和字段。
- 成功结果能让管理员知道实际新增、跳过和恢复数量。

## 14. 分步骤实施计划

后续可以按以下步骤逐步实施。每一步完成后，都应能在新会话中根据本节继续。

### Step 1：新增数据模型和迁移

目标：

- 增加 `EnterpriseMemberImportJob` Prisma model。
- 增加 migration。
- 更新 `packages/db/src/index.ts` 中 schema version 常量，如项目当前约定要求。

验收：

- `pnpm db:generate` 成功。
- 新表字段、索引和外键符合设计。

### Step 2：新增后端导入服务骨架

目标：

- 新增 `EnterpriseMemberImportService`。
- 实现 job 创建、job 查询、job 状态更新。
- Controller 暴露 4 个 API。
- 先不实现真实写入，可让任务进入 `failed` 或 mock `succeeded`。

验收：

- 上传接口能返回 `jobId`。
- 查询接口能返回 job。
- 权限规则正确。

### Step 3：实现 Excel 模板下载和解析校验

目标：

- 使用 `xlsx` 生成模板。
- 解析上传 Excel 第一张 sheet。
- 实现表头、空数据、手机号、重复、部门、权限校验。

当前实现状态（2026-06-23）：

- 已实现真实 Excel 第一张 sheet 解析，使用 `sheet_to_json(..., { header: 1, defval: '', raw: false })` 读取，避免手机号数字单元格被不可控转换。
- 已实现必需表头、空行忽略、业务字段缺失、手机号规范化与格式校验、文件内重复手机号、部门存在性和权限校验。
- 校验失败会写入 job `errorJson`，包含行号、字段和错误原因。
- 本阶段不会进入业务表写入，合法文件会继续执行 Step 4 的用户身份解析。

验收：

- 各类非法文件能返回明确错误。
- 合法文件能生成标准导入计划。

### Step 4：实现用户和身份解析

目标：

- 批量查询已有手机号 identity。
- 为不存在手机号生成 userId。
- 为新用户限流生成 passwordHash。

当前实现状态（2026-06-23）：

- 已按 `provider = 'phone'`、`providerUserId in normalizedPhones`、`isDeleted = false` 批量查询手机号身份，并排除已删除用户。
- 已为不存在手机号生成新的 `userId`，并使用 `PasswordService.hashPassword` 按固定并发 8 生成独立 `passwordHash`。
- 已存在手机号不会生成新密码 hash，也不会修改已有用户密码。
- `passwordHash` 只保留在进程内解析结果中，不写入 job，不返回前端。
- Step 5/6 已接入真实批量写入，身份解析通过后会继续进入事务写入阶段，不再以占位 `failed` 结束。

验收：

- 新旧手机号能正确分类。
- 已存在用户不会生成新密码。

### Step 5：实现事务内批量写入

目标：

- 批量创建 users。
- 批量创建 user_identities。
- 批量创建 wallets。
- 批量插入新 memberships。
- 已存在任意状态 memberships 跳过。

验收：

- 一次导入混合新用户、老用户、已存在成员、disabled 成员时结果正确，既有绑定不被更新。
- 模拟中途 SQL 失败时事务完整回滚。

当前实现状态（2026-06-23）：

- 已把解析后的 `ResolvedImportRow[]` 接入真实写入流程。
- 新用户、手机号身份、钱包、成员关系写入已放在同一个 Prisma `$transaction` 内。
- 已存在任意状态 membership 都会跳过，不恢复、不更新导入资料；不存在 membership 会以 `member` 角色批量插入。
- 事务成功后 job 标记为 `succeeded`；事务失败会回滚业务写入并标记 job 为 `failed`。

### Step 6：实现批量配额初始化

目标：

- 把现有单成员配额初始化逻辑改造成批量 SQL。
- 只处理普通成员。
- 保持已有 override 语义。

验收：

- 导入普通成员后配额记录存在。
- 已有配额 override 不被破坏。

当前实现状态（2026-06-23）：

- 已实现导入场景的批量成员配额初始化。
- 仅对本次新增的 `member` 成员初始化配额。
- 已存在任意状态 membership 的跳过用户不会重新初始化配额。

### Step 7：前端 API 封装

目标：

- 新增上传 API。
- 新增 job 查询 API。
- 新增模板下载 API。
- 上传 API 支持进度回调。

验收：

- 可在页面或测试中拿到上传进度和 jobId。

当前实现状态（2026-06-23）：

- 已新增 `importAdminEnterpriseMembershipsApi`、`importEnterpriseAdminMembershipsApi`、`getEnterpriseMembershipImportJobApi`、`downloadEnterpriseMembershipImportTemplateApi`。
- 上传使用 XHR + `FormData`，字段为 `enterpriseId`、`initialPassword`、`file`，并通过 `onProgress(loaded,total)` 暴露真实上传进度。
- 模板下载使用 `apiClient.fetchRaw`，返回 `{ blob, filename }`；文件名优先来自 `Content-Disposition`，缺失时回退为 `enterprise-member-import-template.xlsx`。

### Step 8：前端导入弹窗

目标：

- 成员管理页增加“导入成员”按钮。
- 实现表单、上传进度、轮询进度、成功结果、失败错误。

验收：

- 平台超管和组织管理员流程都可走通。
- 成功后刷新成员列表。

当前实现状态（2026-06-23）：

- 已在成员管理页表格工具栏新增“导入成员”按钮，入口位于“刷新”按钮左侧。
- 已实现 `EnterpriseMemberImportDialog`，包含表单态、上传/处理进度态、成功汇总态和失败错误态。
- 平台超管需要在弹窗内选择目标组织；组织管理员锁定当前 active enterprise。
- 上传阶段使用 Step 7 XHR 上传进度并映射到 0%-30%；拿到 `jobId` 后每 1.5 秒轮询任务状态。
- 任务成功后展示汇总并刷新成员列表；任务失败后展示前 100 条错误，并支持复制全部错误明细。

### Step 9：补测试并回归

目标：

- 补后端 service/controller 测试。
- 补前端核心交互测试。
- 跑现有相关测试。

建议命令：

```bash
pnpm --filter @insightweaver/api test
pnpm --filter @insightweaver/web test
pnpm --filter @insightweaver/api build
pnpm --filter @insightweaver/web build
```

如果 web 测试脚本当前不是完整测试，需要以实际 package script 为准。

当前实现状态（2026-06-23）：

- 已补充后端 Controller 层导入相关直测：
  - 超管导入接口会把 `userId/dto/file` 传给 `createImportJobForAdmin`。
  - 组织管理员导入接口会把 `userId/dto/file` 传给 `createImportJobForEnterpriseAdmin`。
  - job 查询接口会把调用人和 `jobId` 传给 `getImportJob`。
  - 模板下载接口会写入 xlsx `Content-Type`、`Content-Disposition`、`Cache-Control`、`Content-Length`、`X-Content-Type-Options` 和文件内容。
- 已补充前端导入弹窗测试：
  - 表单必填、Excel 后缀和密码策略校验。
  - 组织管理员锁定当前组织。
  - 平台超管选择目标组织后调用超管导入 API。
  - 成功任务展示汇总并触发成员列表刷新。
  - 失败任务展示错误并复制全部错误明细。
  - 模板下载通过 object URL 触发下载。
- 导入链路定向验证：
  - `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise-member-import.service.test.ts`：通过，17/17。
  - `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise.controller.import.test.ts`：通过，4/4。
  - `pnpm --filter @insightweaver/web test -- src/api/moudles/__tests__/enterprise-member-import-api.test.ts`：通过，7/7。
  - `pnpm --filter @insightweaver/web test -- "src/app/(zclaw-shell)/admin/enterprise-memberships"`：通过，7/7。
- 全量回归：
  - `pnpm --filter @insightweaver/api test`：通过，243/243。
  - `pnpm --filter @insightweaver/api build`：通过。
  - `pnpm --filter @insightweaver/web test`：未全量通过；失败为非导入链路既有用例，`src/lib/__tests__/error-codes.test.ts` 5 个、`src/components/super-lobster/__tests__/conversation-message-queue.test.ts` 2 个。
  - `pnpm --filter @insightweaver/web build`：编译、TypeScript、静态页生成通过；最终在 Next standalone traced files 阶段因 Windows symlink `EPERM` 失败。

Step 10 规则调整验证（2026-06-23）：

- `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise-member-import.service.test.ts`：通过，17/17。
- `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise.controller.import.test.ts`：通过，4/4。
- `pnpm --filter @insightweaver/web test -- "src/app/(zclaw-shell)/admin/enterprise-memberships"`：通过，7/7。
- `pnpm --filter @insightweaver/web test -- src/api/moudles/__tests__/enterprise-member-import-api.test.ts`：通过，7/7。
- `pnpm --filter @insightweaver/api test`：通过，243/243。
- `pnpm --filter @insightweaver/api build`：通过。
- `pnpm --filter @insightweaver/web test`：未全量通过；仍为非导入链路既有用例，`src/lib/__tests__/error-codes.test.ts` 5 个、`src/components/super-lobster/__tests__/conversation-message-queue.test.ts` 2 个。
- `pnpm --filter @insightweaver/web build`：编译、TypeScript、静态页生成通过；最终仍在 Next standalone traced files 阶段因 Windows symlink `EPERM` 失败。

Step 11 收口验证（2026-06-23）：

- `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise-member-import.service.test.ts`：通过，17/17。
- `pnpm --filter @insightweaver/api exec tsx --test src/enterprises/enterprise.controller.import.test.ts`：通过，4/4。
- `pnpm --filter @insightweaver/web test -- "src/app/(zclaw-shell)/admin/enterprise-memberships"`：通过，8/8。
- `pnpm --filter @insightweaver/web test -- src/api/moudles/__tests__/enterprise-member-import-api.test.ts`：通过，7/7。
- `pnpm --filter @insightweaver/api test`：通过，243/243。
- `pnpm --filter @insightweaver/api build`：通过。
- `pnpm --filter @insightweaver/web test`：未全量通过；仍为非导入链路既有用例，`src/lib/__tests__/error-codes.test.ts` 5 个、`src/components/super-lobster/__tests__/conversation-message-queue.test.ts` 2 个。
- `pnpm --filter @insightweaver/web build`：编译、TypeScript、静态页生成通过；最终仍在 Next standalone traced files 阶段因 Windows symlink `EPERM` 失败。

## 15. 风险与后续增强

### 15.1 进程内任务中断

MVP 使用进程内异步任务时，服务重启会导致任务停留在处理中状态。

缓解：

- 查询接口如果发现任务更新时间超过阈值，例如 30 分钟，可提示任务可能中断。
- 服务启动时扫描旧的处理中任务并标记 failed。

后续增强：

- 接入 Redis 队列。
- 支持任务重试。

### 15.2 密码通知

本方案只负责设置初始密码，不负责通知用户。

运营建议：

- 管理员线下或通过组织内部渠道通知新用户初始密码。
- 用户首次登录后可自行改密。

后续增强：

- 支持导入完成后批量发送短信通知。
- 支持强制首次登录修改密码。

### 15.3 超大规模导入

50000 行以内使用单任务、单事务。

如果未来需要几十万用户导入：

- 仍可保留“文件级全量校验”。
- 写入可拆为多个事务，但这会改变“全部成功或全部失败”的承诺。
- 若必须保持全量事务，需要评估数据库锁、事务日志和超时时间。

MVP 坚持 50000 行上限，避免设计超出当前系统承载范围。

## 16. 明确不做

MVP 不做以下能力：

- 不自动创建部门。
- 不允许导入 owner。
- 不允许每行单独密码。
- 不修改已存在用户密码。
- 不把导入做成审批流。
- 不支持 CSV。
- 不支持多 sheet 合并导入。
- 不支持导入后自动短信通知。
- 不支持部分成功。
