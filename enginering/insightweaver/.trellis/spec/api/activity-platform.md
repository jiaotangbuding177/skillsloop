# 通用活动发放平台（Activity Platform）

> 通用「认证/报名 → 审核 → 发放权益」平台。教师节认证赠送是本平台的第一条活动配置（`teacher_promo_2026`）。
> 引入任务：`tdd-20260910-activity-platform`（2026-09-10）。

## 1. 数据模型

| 表 | 说明 | 关键约束 |
|---|---|---|
| `activity_definitions` | 活动定义：`code`(唯一) / `name` / `description` / `startAt` / `endAt` / `enterpriseId` / `isActive` / `backgroundOssKey`(PC) / `backgroundMobileOssKey` / `homeUrl` / `attachmentRetentionDays` | `code` 手填且唯一；有效期存 **UTC** |
| `activity_fields` | 字段定义：`fieldKey` / `label` / `fieldType` / `required` / `isBuiltin` / `sortOrder` / `placeholder` / `helpText` | `@@unique([activityId, fieldKey])`；手机号 `fieldKey='phone'` 且 `isBuiltin=true` |
| `activity_grant_plans` | 活动 ↔ 套餐（多对多，审核通过时**全部发放**） | `@@unique([activityId, planId])` |
| `activity_applications` | 申请：`activityId` / `userId` / `phone` / `formData`(JSON 字段答案) / `status` / `rejectReason` / `reviewedBy` / `reviewedAt` / `grantedBatchIds`(JSON) | `@@unique([activityId, phone, isDeleted])`、`@@unique([activityId, userId, isDeleted])` |

**字段类型**：`text` | `textarea` | `phone` | `image` | `pdf`。

## 2. 关键契约

### 2.1 手机号由服务端解析（不接受客户端传值）
`ActivityService.resolveUserPhone(userId)` 从 `user_identities(provider='phone')` 取值；`validateAndBuildFormData` **整体跳过** `phone` 字段（含必填校验），由 `submitApplication` 注入。
- 理由：活动页强制登录，账号手机号即权威来源；`/auth/me` 仅返回脱敏号，前端本就拿不到完整号；顺带杜绝「填他人手机号代建号」。
- 账号未绑定手机号 → `BadRequestException('当前登录账号未绑定手机号…')`。

### 2.2 唯一性按活动维度
同一人可参加多个活动；同一活动内手机号与账号各唯一（靠 DB 唯一约束兜底，P2002 → 409）。

### 2.3 审核通过 = 建号/入组（可跳过）+ 多套餐逐个发放
1. 按 `application.phone` find-or-create 账号并确保为 `activity.enterpriseId` 的 **active 成员**；已是成员则跳过（不发重复成员行）。
2. 逐个 `entitlementService.grantPlan`（每套餐一次调用），**幂等键 = `activity:<applicationId>:<planId>`**（服务端派生，忽略客户端 header）。
3. 全部成功后才 `updateMany({ id, status:'pending' } → 'approved')` 并写 `grantedBatchIds`；中途失败**保持 pending**，可重试且不重发已成功套餐。
4. `sourceRefType = <活动 code>`（用于按活动统计发放量）。

> ⚠️ **幂等键必须含 `applicationId`**：若只用 `activityId + planId`，同一活动的第二个申请人会撞键、拿不到权益（已修，见 `cr-report.md`）。

### 2.4 状态派生（不落库）
`resolveState(startAt, endAt)`：`now < startAt` → `scheduled`；`now > endAt` → `ended`；否则 `running`（边界含端点）。
- 仅 `running` 可提交/重提；`ended` 可查看状态但不可提交；`isActive=false` 对外视为不存在（404）。
- **审核不受有效期限制**（活动结束后 admin 仍可审核窗口期内的申请）。

### 2.5 附件（图片/PDF）
- 存储：阿里云 OSS，`EvoMind-activity-uploads/<活动code>/<userId>/<uuid>.<ext>`；背景图 `…/backgrounds/<activityId>/<pc|mobile>-<uuid>.<ext>`。
- 读取：一律经后端代理（`sendRawFile`，`@Res()` 手写响应 + nosniff）；**禁止直接 return Buffer**（会被 ResponseInterceptor 序列化成 JSON）。
- **归属校验**：`assertActivityUploadKeyOwnedByUser(userId, key, activityCode?)` 按结构位置匹配（新活动结构 / 旧活动结构 / 教师节存量结构三选一），拒绝 `..` 与 `%?#` 控制字符；背景图校验 `…/backgrounds/<activityId>/` 前缀。
- 前端取 URL 必须走 `API_CONFIG.BASE_URL`（`apps/web/lib/api-config.ts`），**不要**自己读 `process.env.NEXT_PUBLIC_*`（web 目录无 .env，会得到空串 → 相对路径打到 web 端口 404）。

### 2.6 附件到期自动清理
`ActivityAttachmentCleanupScheduler` 每日本地零点后：扫描 `endAt < now` 且已过 `attachmentRetentionDays`（默认 30，可配 0–3650）的活动 → 删除其 image/pdf 附件的 OSS 对象 → 清空 `formData` 中对应字段（**保留申请记录与文本字段**）。OSS 删除失败则保留引用待下次重试。
- 顶层必须有 `catch`（`void runOnce().catch(...)`），否则 DB 异常会变成 unhandledRejection 终止进程。

### 2.7 背景图按端存储
PC 与移动端各一张（`backgroundOssKey` / `backgroundMobileOssKey`），上传互不影响、替换时只删同端旧对象；显示门禁为「**任一端存在即可显示**」，并按视口择优（移动端未配置回退 PC 图，反之亦然）。

### 2.8 首页链接
`homeUrl`（活动配置，留空回退 `/`）同时用于页顶「返回首页」与通过后「去首页体验」。
`normalizeHomeUrl` 仅接受站内路径（`/` 开头且非 `//`）或 `http(s)://` 绝对地址，拒绝 `javascript:` 等；前端外链用 `<a>`、站内用 `@/i18n/navigation` 的 `Link`。

## 3. 前端约定

- **活动页是独立落地页**：位于 `apps/web/src/app/[locale]/activity/[code]/page.tsx**（**不在 `(zclaw-shell)` 路由组内**）。放入外壳会连带加载会话初始化/术语表/侧边栏等无关请求。
- 匿名可读：`GET /api/activities/:code` 与 `…/background` 使用类级 `@UseGuards(OptionalJwtAuthGuard)`；**需要登录的方法（提交、查我的申请、读自己附件）显式叠加 `JwtAuthGuard`**。
  > ⚠️ NestJS 的守卫是「全局 → 类 → 方法」**顺序拼接（合并）**，方法级 `OptionalJwtAuthGuard` **无法**让类级 `JwtAuthGuard` 下的端点变公开。正确写法是「类级 Optional + 敏感方法显式 JwtAuthGuard」。
- **匿名场景的 401 不是错误**：活动页查「我的申请」与全局 `useSession` 的 `/api/auth/me` 探测，在未登录时都会 401。这类请求必须带 `suppressGlobalError: true`（必要时加 `skipAuthRefresh: true`），否则会弹全局「登录已过期」toast；页面侧按 null（未提交/未登录）处理。

## 4. 迁移清单

`20260910120000_activity_platform`（三表 + 申请表改造 + 预置教师节活动 + 历史数据回填）
`20260910130000_activity_platform_fixes`（子表软删列 + 守卫式清理旧表）
`20260910140000_activity_page_and_cleanup`（背景图 + 保留期）
`20260910150000_activity_mobile_background`（移动端背景图）
`20260910160000_activity_home_url`（首页链接）

预置活动按组织 slug 环境自适应：生产 `yzs_js`（云知师-教师版）/ dev `edu-teacher-local`。
