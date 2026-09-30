---
change: tool-billing-modularization
design-doc: docs/superpowers/specs/2026-07-16-tool-billing-modularization-design.md
base-ref: 35cab4305f67f0e5250e5546d619608785a34cbd
---

# 工具调用计费模块化 - 实施计划

## 目标

将图片计费从 Redis 迁移到 DB 表，新增 Tavily 搜索计费，统一配额模式，UI 集成到 basic-settings。

## 任务清单

### Phase 1: Database (T-1 ~ T-3)
- [x] T-1: 在 `packages/db/prisma/schema.prisma` 新增 `ToolCallBillingConfig` model
- [x] T-2: 运行 `pnpm db:migrate`
- [x] T-3: 验证表结构

### Phase 2: Backend Service (T-4 ~ T-6)
- [x] T-4: 新建 `apps/api/src/billing/tool-call-billing.service.ts`
- [x] T-5: 在 `billing.module.ts` 注册
- [x] T-6: 在 `admin-config.module.ts` 注册

### Phase 3: Backend API (T-7 ~ T-8)
- [x] T-7: `GET /admin/config/tool-billing`
- [x] T-8: `PATCH /admin/config/tool-billing/unified`

### Phase 4: Refactor Billing Logic (T-9 ~ T-11)
- [x] T-9: 重构 zclaw.service.ts Path A
- [x] T-10: 重构 Path B
- [x] T-11: 重构 `settleEnterpriseTokenUsageIfNeeded`

### Phase 5: Frontend API (T-12)
- [x] T-12: 新增 `admin-config.ts` API 函数

### Phase 6: Frontend UI (T-13 ~ T-15)
- [x] T-13: basic-settings 页面新增 Section
- [x] T-14: catalog.json i18n
- [x] T-15: en.json 翻译

### Phase 7: Cleanup (T-16 ~ T-17)
- [x] T-16: 删除 billing-config 页面
- [x] T-17: 删除 admin 入口卡片

### Phase 8: Verification (T-18 ~ T-25)
- [x] T-18~T-25: 端到端验证

## 执行策略

- 按 Phase 顺序执行
- 每个 Phase 完成后提交一次
- Phase 8 为集成测试，需启动服务验证
