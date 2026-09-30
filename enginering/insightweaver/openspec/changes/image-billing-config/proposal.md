## Why

将生图计费中硬编码的 `TOKENS_PER_IMAGE = 100_000`（每张图 10 万 Token）改为运行时可配置，使超管能通过后台管理页面实时调整图片生成单价，无需重新部署。

## What Changes

- [ ] Redis 存储：用 Redis key `config:tokens_per_image` 存储当前图片单价，API 启动时自动初始化为默认值 100,000
- [ ] 计费逻辑改造：`zclaw.service.ts` 中图片计费从读取硬编码常量改为调用 `ImageBillingConfigService.getTokensPerImage()`，实时生效
- [ ] 后端管理 API：`GET /api/admin/config/tokens-per-image`（查看）、`PATCH /api/admin/config/tokens-per-image`（修改），仅 admin 可访问
- [ ] 前端管理页面：在 admin 后台新增"计费配置"页面，展示当前值并允许修改，仅超管可见
- [ ] Admin 首页入口：在管理后台首页添加"计费配置"卡片
- [ ] i18n 文案：zh + en 双语
- [ ] 作为超管，我希望在后台管理页面查看当前每张图片消耗的 Token 数，以便了解当前计费参数
- [ ] 作为超管，我希望修改每张图片消耗的 Token 数并立即生效，以便灵活调整计费策略

## Impact

- 非目标（明确不做什么）：
  - 不做按企业隔离配置（全局统一一个值）
  - 不做按工具/模型区分价格（所有生图工具统一单价）
  - 不做配置修改审计日志
  - 不修改 pre-freeze 逻辑
  - 不修改前端用户侧的 Token 消耗展示
- 约束：
  - 技术约束：配置存储在 Redis（不新建数据库表）；Redis 不可用时回退到硬编码默认值 100,000；读取实时生效（不做内存缓存）；后端使用 `AdminGuard`，前端使用 `usePlatformAdminAuth`
  - 业务约束：仅 `role === 'admin'` 的超管可查看和修改；值必须为非负整数；默认值 100,000
- 关联设计笔记：`_current.md` → "生图计费：日志确认后的最终方案"；`图片计费参数化实现计划.md`
- 验收标准：
  1. API 启动后 Redis 中 `config:tokens_per_image` 存在且值为 `100000`（若之前不存在）
  2. `GET /api/admin/config/tokens-per-image` 返回 `{ "value": 100000 }`（默认值）
  3. `PATCH /api/admin/config/tokens-per-image` body `{ "value": 200000 }` 成功，再次 GET 返回 `{ "value": 200000 }`
  4. 非 admin 用户调用上述 API 返回 403
  5. 前端 `/admin/billing-config` 页面能加载当前值，修改后保存成功
  6. 修改值后触发一次生图，验证扣费使用新值（如设为 200,000，生成 1 张图应多扣 200,000 Token）
  7. Redis 不可用时，计费回退到默认值 100,000，不报错
