## 1. 范围与约束确认
- [ ] 确认范围包含：Redis 存储、计费逻辑改造、后端管理 API、前端管理页面、Admin 首页入口、i18n 文案
- [ ] 遵守约束：配置存储在 Redis（不新建数据库表）；Redis 不可用时回退到默认值 100,000；读取实时生效；后端使用 `AdminGuard`，前端使用 `usePlatformAdminAuth`
- [ ] 明确非目标：不做按企业隔离配置、不做按工具/模型区分价格、不做配置修改审计日志、不修改 pre-freeze 逻辑、不修改前端用户侧的 Token 消耗展示

## 2. 实现 image-billing-config
- [ ] 新建 `ImageBillingConfigService`：从 Redis 读写 `config:tokens_per_image`，API 启动时初始化为默认值 100,000，Redis 不可用时返回默认值
- [ ] 修改 `billing.module.ts`：注册 `ImageBillingConfigService`
- [ ] 修改 `enterprise-token-quota.constants.ts`：将 `TOKENS_PER_IMAGE` 改为 `DEFAULT_TOKENS_PER_IMAGE`
- [ ] 修改 `zclaw.service.ts`：注入 `ImageBillingConfigService`，计费时调用 `getTokensPerImage()` 获取动态值
- [ ] 新建 `AdminConfigController`：实现 `GET /api/admin/config/tokens-per-image` 和 `PATCH /api/admin/config/tokens-per-image`，使用 `AdminGuard` 保护
- [ ] 新建 `AdminConfigModule`：注册 controller 和依赖
- [ ] 修改 `app.module.ts`：导入 `AdminConfigModule`
- [ ] 新建前端 API 函数 `admin-config.ts`：`getTokensPerImageApi` 和 `setTokensPerImageApi`
- [ ] 新建前端管理页面 `/admin/billing-config`：展示当前值、输入框编辑、保存按钮，使用 `usePlatformAdminAuth` 保护
- [ ] 修改 admin 首页：添加"计费配置"卡片入口
- [ ] 添加 i18n 文案：zh.json 和 en.json 中添加 `adminBillingConfig` 和 `adminHome.cards.billingConfig` 相关文案

## 3. 验收
- [ ] API 启动后 Redis 中 `config:tokens_per_image` 存在且值为 `100000`（若之前不存在）
- [ ] `GET /api/admin/config/tokens-per-image` 返回 `{ "value": 100000 }`（默认值）
- [ ] `PATCH /api/admin/config/tokens-per-image` body `{ "value": 200000 }` 成功，再次 GET 返回 `{ "value": 200000 }`
- [ ] 非 admin 用户调用上述 API 返回 403
- [ ] 前端 `/admin/billing-config` 页面能加载当前值，修改后保存成功
- [ ] 修改值后触发一次生图，验证扣费使用新值（如设为 200,000，生成 1 张图应多扣 200,000 Token）
- [ ] Redis 不可用时，计费回退到默认值 100,000，不报错
