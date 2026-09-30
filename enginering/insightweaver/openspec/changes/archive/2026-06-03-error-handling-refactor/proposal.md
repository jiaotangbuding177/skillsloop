# Proposal: 全局错误提示重构

## What & Why

当前系统使用 sonner toast 在所有位置统一弹出错误提示（`toast.error`），存在以下问题：
1. **无错误分级**：所有接口错误（包括底层网络故障）都以居中显眼的 toast 弹出，用户看到 "network error" 完全无法理解
2. **无频率控制**：短时间内后端多次报错，弹出多个 toast 刷屏，用户无法消化
3. **位置不佳**：当前 toast 位于 `top-center`，过于显眼，干扰用户注意力
4. **无统一抽象**：200+ 处直接调用 `toast.error()`，无法统一控制行为

### 目标
- 建立三级错误提示体系：轻量级（控制台日志）、标准级（右下角短暂 toast）、关键级（模态对话框）
- 根据接口重要性自动选择提示级别
- 实现错误去重/节流：短时间内同类型错误只提示一次
- toast 位置改为右下角，低调不抢眼
- 提供统一的错误处理工具函数，替换散落的 `toast.error` 调用
- 后端错误码自动映射为用户友好中文提示

## Scope

### In Scope
- 创建新的错误分级体系和处理工具 (`lib/error-handler.ts`)
- 创建新的 ToastProvider 和 Toaster 样式（右下角、低调风格）
- 对关键错误增加模态确认（额度不足、权限不足等）
- 错误去重/节流机制
- 后端 ErrorCode 到用户友好中文的映射表
- 逐步替换现有 `toast.error` 调用为统一错误处理

### Out of Scope
- 修改后端 API 接口签名
- 新增 React ErrorBoundary（后续可加，本次不涉及）
- 修改 SSE 流式推送的错误处理（数据流不同，暂不统一）
- 修改 Prisma/数据库错误处理

## Impact

### Files Changed
- `apps/web/src/lib/error-handler.ts` — 新增：错误处理核心工具
- `apps/web/src/lib/error-codes.ts` — 新增：错误码到中文映射
- `apps/web/src/components/ui/ToastProvider.tsx` — 修改：位置、样式、分级配置
- `apps/web/src/hooks/useZclawChat.ts` — 修改：替换 toast.error 调用
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx` — 修改：替换 toast.error 调用
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx` — 修改：替换 toast.error 调用
- `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` — 修改：替换 toast.error 调用
- 其他 20+ 文件 — 逐步替换 toast.error 调用

### Breaking Changes
- 无：`sonner` 的 `toast.error()` API 保持可用，不会立即断裂
- 渐进式迁移：旧代码与新工具共存，逐步替换
