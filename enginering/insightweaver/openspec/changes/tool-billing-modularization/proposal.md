## Why

当前图片计费通过 Redis `ImageBillingConfigService` 硬编码，仅支持图片生成一种工具类型。现在需要新增 tavily 搜索工具计费，且未来可能扩展更多工具类型和企业级独立配置。Redis 方案无法满足"新增工具需改代码重新部署"和"企业级独立配额"的需求，需要迁移到数据库表驱动。

## What Changes

- **新增数据库表** `tool_call_billing_configs`：存储可计费工具注册信息和统一配额，支持未来企业级配置（enterpriseId 字段）
- **新建 `ToolCallBillingService`**：替代 Redis `ImageBillingConfigService`，从 DB 读取配置，遍历 toolActivities 按策略计数
- **重构 `zclaw.service.ts`**：Path A（billing entitlement）和 Path B（enterprise quota）两处计费调用改为使用新 service
- **新增管理 API**：`GET/PATCH /admin/config/tool-billing`，查询和更新统一配额
- **前端集成到 `/admin/basic-settings`**：在基础设置页底部新增"工具调用计费"Section，仅超管可见
- **删除旧页面**：`/admin/billing-config` 页面文件 + 管理后台入口卡片
- **新增 tavily 搜索计费**：匹配工具名 `tavily` / `tavily_search`，按调用次数计数

## Capabilities

### New Capabilities
- `tool-call-billing`: 工具调用计费系统——DB 注册可计费工具、统一配额模式、按策略计数（per_output_image / per_completed_call）

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **数据库**：新增 `tool_call_billing_configs` 表，需 `pnpm db:migrate`
- **后端**：`apps/api/src/billing/`（新建 service）、`apps/api/src/zclaw/zclaw.service.ts`（重构 2 处计费）、`apps/api/src/admin-config/`（新增 API 端点）
- **前端**：`apps/web/src/app/.../admin/basic-settings/page.tsx`（新增 Section）、`apps/web/src/api/moudles/admin-config.ts`（新增 API 函数）
- **删除**：`apps/web/src/app/.../admin/billing-config/page.tsx`、admin 首页 `billingConfig` 入口卡片
- **i18n**：`catalog.json` + `en.json` 新增文案
- **旧 Redis 键**：`config:tokens_per_image` 不再使用（保留不删，无影响）
