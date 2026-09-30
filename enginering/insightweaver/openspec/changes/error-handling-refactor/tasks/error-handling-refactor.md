# Tasks: 全局错误提示重构

## Task 1: 创建错误码映射表
**File:** `apps/web/src/lib/error-codes.ts`

- [ ] 从 `apps/api/src/common/constants/error-codes.ts` 导出 ErrorCode 枚举的副本
- [ ] 创建 `USER_FRIENDLY_MESSAGES` 映射：每个 ErrorCode → 中文提示
- [ ] 创建 `NETWORK_ERROR_PATTERNS`：识别网络层错误的关键词/正则列表
- [ ] 导出 `toUserFriendlyMessage(error: unknown): string` 工具函数
- [ ] 导出 `getErrorSeverity(error: ApiError): ErrorSeverity` 分级函数

**Verification:** Run `pnpm test` — 新函数通过单元测试

## Task 2: 创建错误处理核心工具
**File:** `apps/web/src/lib/error-handler.ts`

- [ ] 定义 `ErrorSeverity` 枚举（SILENT=0, LIGHT=1, NORMAL=2, CRITICAL=3）
- [ ] 实现 `DedupManager` 类：基于 `code:path` key + 30s 窗口去重
- [ ] 实现 `handleApiError(error: unknown, context?: { path?: string })` — 主入口
- [ ] 实现 `showErrorToast(message: string, severity: ErrorSeverity)` — 分级 toast
- [ ] 实现 `showCriticalDialog(severity, message, onAction)` — 关键错误弹窗（委托信用额度对话框类似模式）
- [ ] L3 关键错误的处理：code 4001 → 已有机能（credits-alert），2001/2002 → 静默退出（已有机能）

**Verification:** Run `pnpm test` — 新函数通过单元测试

## Task 3: 修改 ToastProvider 样式
**File:** `apps/web/src/components/ui/ToastProvider.tsx`

- [ ] 修改 `<Toaster>` position 从 `top-center` 改为 `bottom-right`
- [ ] 关闭 `richColors`（改用自定义低调配色）
- [ ] 设置默认样式：小字号(13px)、低调背景色、浅边框
- [ ] L1 toast 样式：灰色调，1.5s 消失
- [ ] L2 toast 样式：温和警告色，3s 消失

**Verification:** 视觉确认右下角出现、颜色低调

## Task 4: 替换高优先级文件中的 toast.error 调用
**渐进式迁移（不追求一步到位）:**

### Task 4a: useZclawChat.ts
- [ ] 替换 `toast.error()` → `handleApiError()`
- [ ] 保留 `toast.success()` 不变（成功提示不在此次重构范围）

### Task 4b: ZclawWorkspaceSidebar.tsx  
- [ ] 替换 `toast.error()` / `toast.info()` → `handleApiError()`
- [ ] 文件操作失败 → L1

### Task 4c: api-client.ts
- [ ] 在 `parseResponse()` 调用后附加 error context（request path）
- [ ] 或在 `executeRequest()` catch 中触发 error event

### Task 4d: SuperLobsterPage.tsx (高错误密度文件)
- [ ] 替换所有 `toast.error()` → `handleApiError()`

### Task 4e: HomeScreen.tsx, ResearchInterface.tsx
- [ ] 替换 `toast.error()` → `handleApiError()`

### Task 4f: 其余页面文件
- [ ] 登录页、充值页、管理页面等 — 批量替换

**Verification:** 每个文件替换后运行 `pnpm test && pnpm build`

## Task 5: 端到端验证

### Task 5a: 添加触发入口点
- [ ] 在开发模式下添加错误模拟工具（可选，通过 console 命令触发各种错误场景）
- [ ] 调用入口：浏览器 console 执行 `__insightweaver_simulateError(code, path)`

- [ ] 验证：L0 错误仅出现在控制台，无弹出
- [ ] 验证：L1 错误右下角短暂提示
- [ ] 验证：L2 错误右下角标准提示
- [ ] 验证：L3 错误触发对话/静默退出
- [ ] 验证：30s 窗口去重生效
- [ ] 验证：降级规则（高优先已提示→低优先被抑制）

## Task 6: 验证交互链完整性
- [ ] 打开应用 → 触发 API 错误 → 确认右下角 toast 出现（非居中）
- [ ] 确认 toast 自动消失不阻塞操作
- [ ] 确认短时间内重复错误不刷屏
- [ ] 确认额度不足弹窗正常工作
