# 接口错误静默规则设计

## 背景

首页等关键页面中，部分接口（如工作区容量查询、技能列表）即使出错也不影响核心功能，但当前错误处理会弹出 toast，干扰用户体验。需要支持按「接口路径 + 页面路由」双维度匹配，将特定接口错误降级为控制台输出。

## 需求

1. 按「接口路径正则 + 页面路由正则」组合匹配，命中时将错误 severity 降级（如 SILENT）
2. 静态配置写在代码中，预留远程配置扩展点
3. 不影响现有 dedup、errorToast、handleError 等机制

## 数据结构

```ts
interface SilentRule {
  path: RegExp;            // 匹配接口 URL pathname
  page: RegExp;            // 匹配 Next.js 路由 pathname
  severity: ErrorSeverity; // 降级到的严重级别
}
```

示例配置：

```ts
const SILENT_RULES: SilentRule[] = [
  { path: /\/api\/zclaw\/workspace\/quota/, page: /^\/($|home)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/skills/, page: /.*/, severity: ErrorSeverity.SILENT },
];
```

远程扩展点：

```ts
let remoteRules: SilentRule[] = [];
export function setRemoteSilentRules(rules: SilentRule[]) { remoteRules = rules; }
```

匹配时合并：`[...SILENT_RULES, ...remoteRules]`，先匹配先生效。

## 匹配逻辑

扩展 `getErrorSeverity` 签名，新增 `pageContext` 参数：

```ts
export function getErrorSeverity(
  error: ErrorLike,
  requestPath?: string,
  pageContext?: string,
): ErrorSeverity
```

优先级：

1. **SILENT_RULES**（静态 + 远程）：path + page 双正则匹配，命中则返回规则指定的 severity
2. **DEFAULT_SEVERITY_MAP**：按 error code 查表
3. **兜底**：`ErrorSeverity.LIGHT`

## 页面上下文传递

### 模块级状态

```ts
// use-page-error-context.ts
let currentPage = '';
export function setCurrentPage(page: string) { currentPage = page; }
export function getCurrentPage(): string { return currentPage; }
```

### Hook

```ts
export function usePageErrorContext() {
  const pathname = usePathname();
  useEffect(() => { setCurrentPage(pathname); }, [pathname]);
}
```

在 `layout.tsx` 根布局中调用一次即可。

### 传递链

```
layout.tsx → usePageErrorContext() → setCurrentPage(pathname)
api-client.ts → emitError(err, { path, page: getCurrentPage() })
error-handler.ts → emitError() → getErrorSeverity(error, path, page)
error-codes.ts → getErrorSeverity() → 查 SILENT_RULES → 返回 severity
```

## 变更文件

| 文件 | 变更 |
|---|---|
| `error-codes.ts` | 新增 `SilentRule`、`SILENT_RULES`、`setRemoteSilentRules`、`getRemoteSilentRules`；扩展 `getErrorSeverity` 增加 `pageContext` 参数 |
| `error-handler.ts` | `emitError` 的 context 增加 `page` 字段，传递给 `getErrorSeverity` |
| `api-client.ts` | `emitError` 调用传入 `page: getCurrentPage()` |
| 新增 `use-page-error-context.ts` | `usePageErrorContext` hook + `setCurrentPage`/`getCurrentPage` |
| `layout.tsx` | 调用 `usePageErrorContext()` |

## 不变

- `DedupManager`、`errorToast`、`handleError` 逻辑不变
- `DEFAULT_SEVERITY_MAP` 不变
- `OVERRIDE_LIST` 保留但标记为 deprecated，被 `SILENT_RULES` 替代

## 首页全量接口扫描

实现完成后，扫描首页涉及的所有接口路径，全部配置为 SILENT 降级到控制台，由用户自行删减。

扫描范围：
- 首页（`/` 和 `/home` 路由）下所有 API 调用
- 包括 `useZclawChat.ts`、`HomeScreen.tsx`、`SuperLobsterPage.tsx` 中首页加载阶段的接口

## 测试

- `error-codes.test.ts`：新增 SILENT_RULES 匹配测试（path+page 命中、path 命中 page 不命中、远程规则、规则优先级）
- `use-page-error-context.ts`：单元测试验证 setCurrentPage/getCurrentPage
