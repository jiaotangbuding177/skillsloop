# Spec: 全局错误提示重构

## End-to-End User Path

**场景1：网络临时断连**
1. 用户操作触发 API 调用 → 网络请求失败 → 控制台静默记录 `[NetworkError] GET /api/xxx` → 用户无感知
  
**场景2：普通业务错误**
1. 用户创建文件失败（后端返回 `{code: 1001, message: "文件名已存在"}`） → 右下角短暂弹出 "文件名已存在" → 1.5秒自动消失

**场景3：后端持续报错**
1. 后端服务故障，3秒内连续 5 次接口返回 500 → 仅第一次弹出简洁提示 "服务暂时不可用" → 后续错误静默，避免刷屏 → 30秒内不再重复提示

**场景4：关键业务错误**
1. 用户操作触发额度不足（code 4001） → 弹出充值引导对话框 → 用户必须手动关闭

**场景5：登录过期**
1. 用户操作触发 token 过期（code 2001） → 静默尝试刷新 token → 刷新失败 → 静默跳转登录页

## Backend Constraints

### 后端错误码体系 (`apps/api/src/common/constants/error-codes.ts`)
```
SUCCESS = 0
INVALID_ARGUMENT = 1001       # 参数错误
VALIDATION_FAILED = 1002      # 校验失败
UNAUTHORIZED = 2001           # 未登录
TOKEN_EXPIRED = 2002          # token过期
SMS_CODE_INVALID = 2003       # 验证码错误
SMS_RATE_LIMITED = 2004       # 验证码频率限制
FORBIDDEN = 3001              # 无权限
ACCOUNT_DISABLED = 3002       # 账号已禁用
INSUFFICIENT_CREDITS = 4001   # 额度不足
IDEMPOTENCY_CONFLICT = 4002   # 幂等冲突
WORKSPACE_QUOTA_EXCEEDED = 4003 # 工作区容量超限
INTERNAL_ERROR = 5000         # 服务器内部错误
DEPENDENCY_UNAVAILABLE = 5001 # 依赖服务不可用
```

### 后端响应格式
```json
{ "code": 0, "message": "ok", "data": {...} }           // 成功
{ "code": 1001, "message": "文件名已存在", "data": null } // 业务错误
{ "code": 5000, "message": "Internal Server Error", "data": null } // 服务端错误
```

### 前端已有关键路径
- `ApiClient.parseResponse()` (api-client.ts:166): 将 HTTP 响应转为 `ApiError(code, message, status)`
- `emitInsufficientCredits()` (credits-alert.ts): code 4001 触发额度不足对话框
- `shouldClearSession()` (session-refresh.ts): 401/2001/2002 触发静默登出

## 错误分级体系

| 级别 | 名称 | 触发条件 | 展示方式 | 用户感知 |
|------|------|---------|---------|---------|
| **L0** | SILENT | NetworkError, TypeError, AbortError, TimeoutError, code 5000/5001 重复出现 | `console.warn()` | 完全无感知 |
| **L1** | LIGHT | `ApiError` 且 code 为 1001/1002/4002, HTTP 4xx(非401), 其他未知错误 | 右下角 toast, 1.5s, 小字号, 低调配色 | 可感知但不打断 |
| **L2** | NORMAL | `ApiError` 且 code 为 3001/3002, 4003 | 右下角 toast, 3s, 标准字号 | 需要关注 |
| **L3** | CRITICAL | `ApiError` 且 code 为 4001(额度), 2001/2002(登录过期) | 模态对话框 或 静默退出 | 必须处理 |

## 错误去重/节流机制

- **去重维度**: `errorCode + requestPath`
- **节流窗口**: 30秒内同一 key 只触发最高级别的提示一次
- **L0 不限流**: 控制台日志始终输出
- **降级规则**: 若同一 key 已在窗口内以高级别提示过，低级别自动降为 L0
- **缓存清理**: 窗口结束后自动过期（WeakMap + 时间戳）

## 用户友好消息映射

后端 `message` 字段可能返回英文或技术细节，前端需映射为用户可读中文：

| 后端 message | 映射后 |
|-------------|--------|
| "network error" / TypeError | "网络连接异常"（L0） |
| "Failed to fetch" | "网络请求失败，请检查连接"（L0） |
| `ERROR_MESSAGES[code]` | 中文码表映射 |
| 其他自定义 message | 透传（后端已为中文） |

## Same-Page Reference

现有 Toast 相关组件模式：
- `ToastProvider.tsx` → 唯一的 Toaster 挂载点
- `InsufficientCreditsDialog.tsx` → L3 关键错误模态对话框模式参考
- `credits-alert.ts` → EventTarget 模式的错误事件总线，可作为通用错误事件总线的参考

## Component Interaction Constraints

本需求不涉及组件间交互约束，无需此节。

## State Coordination

本需求不涉及 sibling 组件状态协调。错误处理工具为纯函数 + 事件总线，无 UI 状态。

## Framework Integration Notes

- **sonner v2**: 已在 `layout.tsx` 挂载，只需调整 `<Toaster>` 的 position 和样式 props
- **无 Portal 冲突**: toast 系统独立于任何 Dialog/DropdownMenu

## Search/Filter Scope

本需求不涉及搜索/过滤功能。

## Default Values

| 参数 | 默认值 |
|------|--------|
| Toast 位置 | `bottom-right` |
| Toast 持续时间 (L1) | 1500ms |
| Toast 持续时间 (L2) | 3000ms |
| Toast 字体大小 | 13px |
| 节流窗口 | 30000ms (30s) |
| 去重 key 组成 | `{errorCode}:{requestPath}` |
| L0 最大重复次数 | 无限制（控制台日志） |
