## Context

当前图片计费通过 Redis `ImageBillingConfigService` 实现：
- Redis 键 `config:tokens_per_image` 存储单次图片消耗的 Token 数（默认 100000）
- `countImagesFromToolActivities()` 遍历 toolActivities，匹配 `process` 工具并统计图片数量
- 计费公式：`totalTokens = LLM加权token + 图片数 × tokensPerImage`
- 管理页面 `/admin/billing-config` 提供超管配置入口

**约束：**
- 需兼容两条计费路径（billing entitlement + enterprise quota）
- 超管标识：`User.role === 'admin'`
- basic-settings 页面已有 `isPlatformAdmin` 条件渲染模式
- 前端使用 `translateAutoText` 做 i18n

## Goals / Non-Goals

**Goals:**
- 将计费配置从 Redis 迁移到 DB 表 `tool_call_billing_configs`
- 支持 DB 注册可计费工具（新增工具无需改代码）
- 统一配额模式：所有工具共用 tokensPerUnit
- 新增 tavily 搜索计费（按调用次数计数）
- UI 集成到 `/admin/basic-settings` 底部，仅超管可见
- 保留旧 Redis 键和旧端点兼容

**Non-Goals:**
- 不做企业级独立配额（enterpriseId 字段预留，当前只用全局）
- 不做按工具类型独立配置（统一配额）
- 不做前端工具管理（新增/删除/禁用工具仅通过 DB 操作）

## Decisions

### D-1：数据库表 vs Redis

**选择：** DB 表 `tool_call_billing_configs`

**理由：**
- 未来需支持企业级配置，DB 天然支持 enterpriseId 维度
- 表结构可扩展（新增 toolType、countingStrategy 等字段）
- Redis 仅适合简单 KV，不适合结构化查询

**替代方案：** Redis Hash（`config:tool_billing:{enterpriseId}:{toolType}`）——查询灵活性差，无 schema 约束。

### D-2：统一配额 vs 独立配额

**选择：** 统一配额（所有工具共用 tokensPerUnit）

**理由：**
- 当前业务需求简单，超管只需调整一个值
- 减少 UI 复杂度（单输入框 vs 多行配置）
- 未来如需独立配额，表结构已支持（每行有 tokensPerUnit），只需改 UI 和 API

### D-3：计数策略硬编码 vs 可配置

**选择：** 计数策略在代码中按 `countingStrategy` 字段分支

**理由：**
- 计数逻辑涉及 output 解析，不适合存为配置
- 新增策略需改代码，但频率极低（仅新增工具类型时）
- 保持简单，避免过度设计

### D-4：UI 位置

**选择：** 集成到 `/admin/basic-settings` 底部 Section

**理由：**
- 基础设置页是系统级配置的自然归属
- 避免新增独立页面（减少导航复杂度）
- 使用 `{isPlatformAdmin && (...)}` 控制仅超管可见

### D-5：Tavily 工具名兼容

**选择：** 同时匹配 `tavily` 和 `tavily_search`

**理由：**
- 前端测试中两种名字都出现过
- 实际运行时 tool name 待确认，兼容两种降低风险
- 后续可通过日志确认并精简

## Risks / Trade-offs

**[Risk] DB 查询延迟** → 每次 `message.usage` 事件查询 DB。当前仅查 1-2 行，延迟可忽略。未来可加内存缓存。

**[Risk] Tavily 工具名不匹配** → 兼容两种名字。如都不匹配，则不计费（不影响核心功能）。上线后通过日志确认实际名字。

**[Risk] 旧 Redis 键残留** → 保留不删，不影响新逻辑。后续清理时手动删除。

**[Trade-off] 统一配额限制灵活性** → 当前够用。表结构已预留 per-tool 配额字段，未来改 UI 即可。

## Migration Plan

1. `pnpm db:migrate` 建表
2. 启动服务，`ToolCallBillingService.onModuleInit()` upsert 种子数据
3. 验证旧端点 `/admin/config/tokens-per-image` 仍可用（兼容）
4. 验证新端点 `/admin/config/tool-billing` 正常
5. 验证计费逻辑（图片 + tavily）正确扣费
6. 删除旧页面和入口卡片

**Rollback：** 新逻辑出问题可快速回退到旧 Redis 方案（代码分支保留，只需切换调用）。

## Open Questions

- Tavily 实际 tool name 是什么？（上线后日志确认）
- 未来企业级配额是否需要差异化的 UI 交互？（当前不实现）
