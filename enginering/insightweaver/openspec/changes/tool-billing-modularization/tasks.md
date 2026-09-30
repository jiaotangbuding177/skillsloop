# Tasks

## Phase 1: Database

- [x] T-1: 在 `packages/db/prisma/schema.prisma` 新增 `ToolCallBillingConfig` model（含 enterpriseId, toolType, toolLabel, toolNames, countingStrategy, tokensPerUnit, isEnabled 等字段）
- [x] T-2: 运行 `pnpm db:migrate` 创建数据库表
- [x] T-3: 验证表结构和种子数据（通过 `pnpm db:studio` 查看）

## Phase 2: Backend Service

- [x] T-4: 新建 `apps/api/src/billing/tool-call-billing.service.ts`，实现 `ToolCallBillingService`（含 `onModuleInit` 种子、`calculateToolBillingTokens`、`getAllConfigs`、`getUnifiedTokensPerUnit`、`updateUnifiedTokensPerUnit` 方法）
- [x] T-5: 在 `apps/api/src/billing/billing.module.ts` 注册 `ToolCallBillingService`（providers + exports）
- [x] T-6: 在 `apps/api/src/admin-config/admin-config.module.ts` 注册 `ToolCallBillingService`

## Phase 3: Backend API

- [x] T-7: 在 `apps/api/src/admin-config/admin-config.controller.ts` 新增 `GET /admin/config/tool-billing` 端点（返回所有配置 + unifiedTokensPerUnit）
- [x] T-8: 新增 `PATCH /admin/config/tool-billing/unified` 端点（更新全局 tokensPerUnit，批量更新所有行）

## Phase 4: Refactor Billing Logic

- [x] T-9: 重构 `apps/api/src/zclaw/zclaw.service.ts` Path A（billing entitlement）：替换 `countImagesFromToolActivities` + `imageBillingConfigService.getTokensPerImage()` 为 `toolCallBillingService.calculateToolBillingTokens()`
- [x] T-10: 重构 Path B（enterprise quota）：同上替换
- [x] T-11: 重构 `settleEnterpriseTokenUsageIfNeeded` 方法：参数从 `imageCount` 改为 `toolBillingTokens`，移除内部 tokensPerImage 查询

## Phase 5: Frontend API

- [x] T-12: 在 `apps/web/src/api/moudles/admin-config.ts` 新增 `ToolBillingConfigItem` 接口、`getToolBillingConfigsApi()`、`updateUnifiedTokensPerUnitApi()`

## Phase 6: Frontend UI

- [x] T-13: 在 `apps/web/src/app/[locale]/(zclaw-shell)/admin/basic-settings/page.tsx` 底部新增"工具调用计费"Section（统一配额编辑框 + 已注册工具列表展示），使用 `{isPlatformAdmin && (...)}` 包裹仅超管可见
- [x] T-14: 在 `apps/web/src/messages/catalog.json` 新增 i18n key（工具调用计费、统一配额、已注册工具等文案）
- [x] T-15: 在 `apps/web/messages/en.json` 新增英文翻译

## Phase 7: Cleanup

- [x] T-16: 删除 `apps/web/src/app/[locale]/(zclaw-shell)/admin/billing-config/page.tsx` 旧页面
- [x] T-17: 删除 `apps/web/src/app/[locale]/(zclaw-shell)/admin/page.tsx` 中的 `billingConfig` 入口卡片

## Phase 8: Verification

- [x] T-18: 验证 `pnpm db:migrate` 建表成功
- [x] T-19: 验证启动服务后种子数据 upsert 成功（2 条记录）
- [x] T-20: 验证 `GET /api/admin/config/tool-billing` 返回 2 条配置
- [x] T-21: 验证 `PATCH /api/admin/config/tool-billing/unified` 更新成功
- [x] T-22: 验证图片生成计费：1 张图 × tokensPerUnit 扣费
- [x] T-23: 验证 Tavily 搜索计费：1 次调用 × tokensPerUnit 扣费
- [x] T-24: 验证 `/admin/basic-settings` 底部显示工具计费 Section，仅超管可见
- [x] T-25: 验证旧页面 `/admin/billing-config` 已删除
