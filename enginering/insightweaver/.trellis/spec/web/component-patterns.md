# Component Patterns

## Technology Stack

| Concern | Library | Notes |
|---------|---------|-------|
| UI primitives | Radix UI | Headless components (Dialog, DropdownMenu, Popover, Tooltip, etc.) |
| Styling | Tailwind CSS v4 | With `@tailwindcss/postcss` plugin |
| Icons | lucide-react | Exclusive icon library, no mixed icon sets |
| Animations | motion | Framer Motion successor for React animations |
| Advanced animations | gsap | For complex timeline-based animations |
| Charts | ECharts 6 + ECharts GL | Data visualization, 3D charts via GL extension |
| Rich text | TipTap | Editor for content creation pages |
| Toasts | sonner | Toast notification library |

## TipTap 输入框粘贴处理（2026-08-07 教训）

**File**: `apps/web/src/components/super-lobster/MessageInput.tsx`

聊天输入框使用 TipTap（仅 StarterKit，**未启用 Link 扩展**）。从网页/富文本编辑器粘贴时有两个坑：

### 坑 1：零宽 Unicode 字符污染消息

**Symptom**: 从飞书等富文本编辑器复制 URL 粘贴后发送，后端收到的 `message` 含不可见零宽字符（`\u200B` ZWSP、`\u200C` ZWNJ、`\u200D` ZWJ、`\uFEFF` BOM），URL 无法被识别。

**Cause**: TipTap `getText()` 完整保留剪贴板 HTML 中的零宽字符；`JSON.stringify` 原样发送。

**Fix**:
- `sanitizeInvisibleChars(text)`：**粘贴 URL 场景**剥离全部零宽字符（含 ZWJ/ZWNJ）
- `sanitizeMessageText(text)`：**发送路径**保守清理，**只剥** ZWSP/BOM/WordJoiner/MVS——**保留 ZWJ（U+200D）和 ZWNJ（U+200C）**，因为 ZWJ 是复合 emoji（👨👩👧👦）的合法组成部分，全局剥离会破坏 emoji 渲染；ZWNJ 在波斯语等文字中有语义

```typescript
// 发送前（保守版）：
export function sanitizeMessageText(text: string): string {
  return text.replace(/[\u200B\uFEFF\u2060\u180E]/g, "");
}
```

### 坑 2：粘贴链接显示锚文本而非 URL

**Symptom**: 从网页复制链接粘贴后，输入框/消息显示**页面标题**（`大麦发文打击黄牛_腾讯新闻`）而非 URL。

**Cause**: 复制链接时剪贴板为 `text/html: <a href="URL">标题</a>` + `text/plain: URL`。TipTap 无 Link 扩展 → `<a>` 标签被剥掉，但插入的是**锚文本**而非 `href`。

**Fix**: `handlePaste` 拦截——**仅当 `text/plain` 本身是 URL**（浏览器"复制链接"的标准特征）才拦截，提取 `href` 替换锚文本 + 尾随空格：

```typescript
const PASTED_URL_PROTOCOL_REGEX = /^(https?|ftp):\/\/[^\s]+$/i; // 排除 javascript:/data:

function isPastedUrl(text: string): boolean {
  return PASTED_URL_PROTOCOL_REGEX.test(sanitizeInvisibleChars(text));
}
```

**关键判别规则**：段落文字中夹杂链接的粘贴（`text/plain` 不是 URL）**不拦截**；图片套链接的粘贴（交给文件上传处理器）**不拦截**。

**测试**：`MessageInput.sanitize.test.ts`——`sanitizeInvisibleChars`（6 种零宽字符）、`sanitizeMessageText`（保留 ZWJ/ZWNJ + emoji 完整性）、`extractUrlFromPasteHtml`（多属性/单引号/多链接/飞书样式）。

## Component Library

The project uses a **custom component library** built on Radix UI primitives. This is NOT shadcn/ui -- the components are project-specific implementations.

### Radix UI Primitives Used

Common Radix components used throughout the codebase:
- `@radix-ui/react-dialog` - Modal dialogs
- `@radix-ui/react-dropdown-menu` - Dropdown menus
- `@radix-ui/react-popover` - Popover panels
- `@radix-ui/react-tooltip` - Tooltips (wrapped in `Tooltip.Provider` at locale layout)
- `@radix-ui/react-select` - Select dropdowns
- `@radix-ui/react-tabs` - Tab navigation
- `@radix-ui/react-switch` - Toggle switches
- `@radix-ui/react-scroll-area` - Custom scrollbars
- `@radix-ui/react-avatar` - User avatars

The locale layout wraps the app in `<Tooltip.Provider>`, so tooltips work everywhere without per-page config.

### Gotcha: Dialog.Content 必须含 Dialog.Title（a11y）

**Symptom**: 控制台报 `DialogContent requires a DialogTitle for the component to be accessible for screen reader users.`（Radix Dialog 的无障碍要求）。

**Cause**: 使用 `Dialog.Content` 时漏写 `Dialog.Title`。Radix 会警告（不是运行时错误），但破坏屏幕阅读器可访问性。

**Fix**: 每个 `Dialog.Content` 内必须有 `Dialog.Title`。没有可见标题的弹窗（如图片预览）用 `sr-only` 隐藏：

```tsx
<Dialog.Content className="...">
  <Dialog.Title className="sr-only">{t('clickZoom')}</Dialog.Title>
  {/* 其余内容 */}
</Dialog.Content>
```

**检查方法**（全项目扫描缺失）：

```bash
# Python 扫描：Dialog.Content 存在但 Dialog.Title 缺失的文件
python -c "
import os
for root, dirs, files in os.walk('apps/web/src'):
    if 'node_modules' in root: continue
    for f in files:
        if not f.endswith('.tsx'): continue
        path = os.path.join(root, f)
        content = open(path, encoding='utf-8').read()
        if 'Dialog.Content' in content and 'Dialog.Title' not in content:
            print('MISSING:', path)
"
```

> 注意：注释中的 `Dialog.Content` 会误报，需人工确认。别名导入（如 `DialogPrimitive.Title`）也会误报，确认时以实际渲染路径为准。

## Icons

All icons come from `lucide-react`:

```tsx
import { Settings, Users, CreditCard, ChevronDown, Plus, Trash2, Edit } from 'lucide-react';

<Settings className="h-4 w-4" />
<ChevronDown className="h-5 w-5 text-muted-foreground" />
```

No other icon libraries are used. Custom SVGs go in `public/svg/`.

## Styling with Tailwind CSS v4

Tailwind v4 with `@tailwindcss/postcss`. CSS-first configuration (no `tailwind.config.js` needed for v4). Theme tokens via CSS custom properties.

```tsx
// Card container
<div className="rounded-lg border bg-card p-6 shadow-sm">

// Responsive grid
<div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">

// Loading state
{loading && <Loader2 className="h-6 w-6 animate-spin" />}

// Empty state
<div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
  <InboxIcon className="h-12 w-12" />
  <p>{t('empty')}</p>
</div>
```

Dark mode is managed by `ThemeProvider`. The init script in root layout reads `localStorage` to prevent flash of wrong theme.

## Animations

### motion (Framer Motion)

```tsx
import { motion, AnimatePresence } from 'motion/react';

<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0 }}
  transition={{ duration: 0.2 }}
>
  {content}
</motion.div>
```

### gsap

Used for complex timeline-based animations in dashboard visualizations and landing page effects.

## Charts (ECharts)

```tsx
import * as echarts from 'echarts';
import 'echarts-gl';

useEffect(() => {
  const chart = echarts.init(chartRef.current);
  chart.setOption({ /* ECharts option */ });
  return () => chart.dispose();
}, [data]);
```

Used in dashboard pages and admin analytics views.

## Toasts (sonner)

```tsx
import { toast } from 'sonner';
toast.success(t('saved'));
toast.loading(t('processing'));
```

For API errors, always use `errorToast(error)` which handles severity, dedup, and translation.

## Page Component Template

Canonical pattern for every page:

```tsx
'use client';

import { listItemsApi, type Item } from '@/api';
import { useTranslations } from 'next-intl';
import { errorToast } from '@/lib/error-handler';
import { useState, useEffect } from 'react';

const FILTERS_KEY = 'items-page-filters';

export default function ItemsPage() {
  const t = useTranslations('items');
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem(FILTERS_KEY) || '{}'); }
    catch { return {}; }
  });

  useEffect(() => {
    (async () => {
      try { setItems(await listItemsApi(filters)); }
      catch (error) { errorToast(error); }
      finally { setLoading(false); }
    })();
  }, [filters]);

  useEffect(() => {
    sessionStorage.setItem(FILTERS_KEY, JSON.stringify(filters));
  }, [filters]);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('title')}</h1>
      {items.map(item => <div key={item.id}>{item.name}</div>)}
    </div>
  );
}
```

Key rules in this template:
1. `'use client'` directive at top
2. API functions + types from `@/api`
3. `useTranslations()` with page namespace
4. `errorToast(error)` in catch blocks
5. `useEffect` for data fetch (not React Query/SWR)
6. `sessionStorage` for filter persistence
7. Idempotency keys for create/update: `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
8. BigInt fields serialized as strings, converted in UI

## Admin Page Patterns

Admin pages at `(zclaw-shell)/admin/*` share:
- Shared components in `(zclaw-shell)/admin/_components/`
- List pages with pagination, search, and status filters
- CRUD via API module functions
- Enterprise-scoped data via active enterprise ID

## Key Import Aliases

| Alias | Resolves to |
|-------|-------------|
| `@/api` | `src/api/index.ts` (barrel of all API modules) |
| `@/lib/error-handler` | `src/lib/error-handler.ts` |
| `@/lib/enterprise-context` | `src/lib/enterprise-context.ts` |
| `@/components/*` | `src/components/*` |

## BillingPurchaseDialog: Plan Type Registration Checklist

When adding a new `BillingPlanType`, you MUST update ALL of the following in `BillingPurchaseDialog.tsx`. Missing any one causes silent filtering — the plan won't appear in the UI despite the backend returning it.

| # | Location | Purpose | Example |
|---|----------|---------|---------|
| 1 | `B2B_PLAN_TYPES` / `CONSUMER_PLAN_TYPES` array | Frontend allowlist filter | Add to the correct array |
| 2 | `getPlanCategory(planType)` | Tab grouping (monthly / storage_topup / token_topup) | Map to `'monthly'`, `'storage_topup'`, or `'token_topup'` |
| 3 | `isMonthlyPlan(planType)` | Topup prerequisite check (topups require active monthly plan) | Return `true` for monthly plans |

### Common Mistake: Missing getPlanCategory / isMonthlyPlan

**Symptom**: "当前企业暂无已上架套餐" despite backend `listPreview` returning the plan.

**Cause**: Plan passes `B2B_PLAN_TYPES` filter but `getPlanCategory` returns `null`, so `groupPlansByCategory` drops it.

**Fix**: Add the plan type to both `getPlanCategory` and `isMonthlyPlan`.

```typescript
// WRONG: added to B2B_PLAN_TYPES but not to getPlanCategory
const B2B_PLAN_TYPES = ['b2b_enterprise_plan', 'b2b_monthly_seat_plan', ...];
function getPlanCategory(planType) {
  if (planType === 'b2b_enterprise_plan' || planType === 'consumer_monthly_plan') return 'monthly';
  // b2b_monthly_seat_plan → null → silently dropped!
}

// CORRECT: all three locations updated
function getPlanCategory(planType) {
  if (planType === 'b2b_enterprise_plan' || planType === 'b2b_monthly_seat_plan' || planType === 'consumer_monthly_plan') return 'monthly';
}
function isMonthlyPlan(planType) {
  return planType === 'b2b_enterprise_plan' || planType === 'b2b_monthly_seat_plan' || planType === 'consumer_monthly_plan';
}
```

### Common Mistake: allowedPlanTypes Ignores postExpiryPurchaseMode

**Symptom**: B2B enterprise in `self_purchase` mode shows no plans in the purchase dialog, despite backend returning consumer plans.

**Cause**: `allowedPlanTypes` uses `enterpriseKind === 'b2b' ? B2B_PLAN_TYPES : CONSUMER_PLAN_TYPES` without considering `postExpiryPurchaseMode`. In `self_purchase` mode, B2B enterprises should show consumer plans, but the filter uses B2B_PLAN_TYPES and filters out all consumer plans returned by the backend.

**Fix**: Consider `postExpiryPurchaseMode` in the condition:

```typescript
// WRONG: ignores self_purchase mode
const allowedPlanTypes = enterpriseKind === 'b2b' ? B2B_PLAN_TYPES : CONSUMER_PLAN_TYPES;

// CORRECT: self_purchase mode on B2B enterprise shows consumer plans
const allowedPlanTypes =
  enterpriseKind === 'b2b' && postExpiryPurchaseMode !== 'self_purchase'
    ? B2B_PLAN_TYPES
    : CONSUMER_PLAN_TYPES;
```

**Mode Matrix**:

| enterpriseKind | postExpiryPurchaseMode | allowedPlanTypes |
|----------------|----------------------|------------------|
| b2b | contact_admin | B2B_PLAN_TYPES |
| b2b | admin_purchase | B2B_PLAN_TYPES |
| b2b | self_purchase | CONSUMER_PLAN_TYPES |
| consumer | (any) | CONSUMER_PLAN_TYPES |
| evomind_consumer | (any) | CONSUMER_PLAN_TYPES |
```

## Billing Purchase Tab Routing

### `emitOpenBillingPurchase(tab)`

Opens the billing purchase dialog with a specific tab selected.

```typescript
type BillingPurchaseTab = 'monthly' | 'storage' | 'token';

emitOpenBillingPurchase(tab: BillingPurchaseTab);
```

### Tab Selection Rules

| Scenario | Tab | Reason |
|----------|-----|--------|
| Account validity expired (monthly plan expired) | `'monthly'` | User needs to renew monthly plan to restore account validity |
| Token quota exceeded | `'token'` | User needs to buy token topup |
| Storage quota exceeded | `'storage'` | User needs to buy storage topup |

### Common Mistake: Wrong Tab for Account Validity Renewal

```tsx
// WRONG: Opens token topup tab when account validity expires
const handleRenewClick = () => emitOpenBillingPurchase("token");

// CORRECT: Opens monthly plan tab — account validity IS the monthly plan
const handleRenewClick = () => emitOpenBillingPurchase("monthly");
```

**Why**: Per PRD, `monthly_plan` anchor batch IS the account validity entitlement. When account validity expires, the user needs to buy a new monthly plan, not a token topup. Token topup requires an active monthly plan to be usable (checkpoint gate).

### Account Validity Display in ZclawShell

```tsx
// When accountValidity is null (no active monthly plan):
// - Show "账号有效期" label with "已过期" status tag (red)
// - Show guidance based on purchaseMode:
//   - self_purchase → "立即续费" button → opens monthly plan tab
//   - admin_purchase / contact_admin → "请联系管理员续费" text
```

## React Hooks Rule: No Hooks After Early Return

All React hooks must be called before any early return statement.

```tsx
// WRONG: useCallback after early return
function Component() {
  const [data, setData] = useState(null);
  if (!data) return null;
  const handleClick = useCallback(() => {}, []); //  Rules of Hooks violation
  return <button onClick={handleClick}>Click</button>;
}

// CORRECT: All hooks before early return
function Component() {
  const [data, setData] = useState(null);
  const handleClick = useCallback(() => {}, []); // ✅ Before early return
  if (!data) return null;
  return <button onClick={handleClick}>Click</button>;
}
```

**Why**: React requires hooks to be called in the same order on every render. An early return before a hook means the hook is conditionally called, violating the Rules of Hooks.

## Hydration Safety: No Client-Mutable Reads During Render

**禁止在 render 期同步读取客户端可变值**（localStorage / sessionStorage / navigator / Date.now() / Math.random() 等）。

**Why**: SSR 首帧时这些值不存在或与客户端不同（如 `typeof window === 'undefined'` 分支返回默认值），客户端 hydration 时读到真实值 → 首帧文本不一致 → `Hydration failed because the server rendered text didn't match the client`。

```tsx
// WRONG: render 期同步读 localStorage（SSR=false，客户端可能=true → mismatch）
function LanguageMenu() {
  const followSystem = getLocaleFollowSystem();  // 读 window.localStorage
  return <span>{followSystem ? "跟随系统" : "简体中文"}</span>;
}

// CORRECT: useState 默认值 + useEffect 挂载后读取
function LanguageMenu() {
  const [followSystem, setFollowSystem] = useState(false);
  useEffect(() => {
    setFollowSystem(getLocaleFollowSystem());
  }, []);
  return <span>{followSystem ? "跟随系统" : "简体中文"}</span>;
}
```

**要点**：
- SSR/客户端首帧必须一致（默认值），客户端挂载后 useEffect 更新为真实值
- 引用同一客户端状态的多组件 → 提取 `useXxx()` hook（含 useState+useEffect），一处修复全部覆盖
- 测试用 `renderToString`（不执行 effect）模拟 SSR 首帧断言默认值；用 RTL `render` + `waitFor` 断言挂载后更新——两者缺一不可

## Pattern: Pure-Fn Rule Helpers for Card/Display Logic

**Problem**: disabled/locked-mode/visibility rules embedded inline in components are untestable without heavy RTL (next-intl + API + next-navigation mocks) and drift between duplicates (the same rule reimplemented in 2-3 files).

**Solution**: extract the decision into a pure function in `src/lib/*.ts`; the component becomes a thin consumer that reads the result and renders. Test the pure fn with vitest (no RTL needed). Reserve RTL for thin contract tests (e.g. "the `disabled` prop wires to the button's disabled attribute").

**Example** (`apps/web/src/lib/quota-card-rules.ts` + `conversation-quota/QuotaLimitCard.tsx`):
```typescript
// lib/quota-card-rules.ts — pure, 12 tests in 5ms, no mocks
export function resolveLockedQuotaModes({ lockBatch, postExpiryMode }) {
  const modes: EnterpriseQuotaLimitMode[] = [];
  if (postExpiryMode === "admin_purchase" || postExpiryMode === "self_purchase") modes.push("conversation", "token");
  if (lockBatch) modes.push("batch");
  return modes.length ? modes : undefined;
}
// QuotaLimitCard.tsx — thin consumer
const lockedModes = resolveLockedQuotaModes({ lockBatch, postExpiryMode: postExpiryPurchaseMode });
```

**Why**: logic tested in isolation; component only asserts the wiring. Matches AGENTS.md "favor small, pure helpers". When a card/display rule has ≥3 branches or appears in >1 file, extract it.

**Example: Message Timestamp Formatting** (`apps/web/src/lib/format-utils.ts` + `MessageBubble.tsx`):
```typescript
// lib/format-utils.ts — pure, testable with vitest
export function isSameDay(a: Date, b: Date): boolean { /* ... */ }
export function formatMessageTime(value?: string | null, now?: Date): string {
  // today → "18:02", past days → "08-05 18:02"
  // numeric format, zh/en unified 24h, no i18n key
}
// MessageBubble.tsx — thin consumer
{formatMessageTime(message.createdAt)}
```

**Why**: Date/time display logic (isSameDay, padding, locale-independent format) is a pure decision that should be tested in isolation. The component is a thin consumer that passes `createdAt` and renders the result.

## Gotcha: Don't Gate C-End Display on `!isUnlimited`

> **Warning (historical)**: `showAccountInvalid = !isUnlimited && !hasAccountValidity && hasOrg` previously fired for conversation/token modes and surfaced a false red "账户已过期" badge.

**Symptom**: conversation/token enterprises saw a red "account expired" badge + renew prompt despite having no validity concept.
**Cause**: backend `getSummary` returned `accountValidity=null` for batchless enterprises; frontend treated `null + non-unlimited` as "invalid".
**Fix**: gate on the modes that should surface the block (`quotaMode === "batch" || quotaMode === "token"`), via `resolveAccountValidityDisplay({ quotaMode, ... })` so the rule is centralized + tested.
**Prevention**: account validity is surfaced only for batch and token modes; never surface it for conversation/unlimited. See `api/service-patterns.md` "Display Contract: Account Validity for Batch and Token Modes".

## Convention: Personal Assistant Display Name

**What**: 个人助手展示名（新会话欢迎语等场景）统一经 `getPersonalAssistantDisplayName()` 解析，禁止在组件内手写 trim/fallback 逻辑。

**Why**: 空值回退默认名「小E」是全局规则（用户未配置时欢迎语也要有名字）；散落在组件里会造成默认名漂移。

**Example** (`apps/web/src/lib/personalAssistant.ts` + `MessageList.tsx` — thin consumer):
```typescript
// lib/personalAssistant.ts — pure, testable with vitest
export const DEFAULT_PERSONAL_ASSISTANT_NAME = "小E";
export function getPersonalAssistantDisplayName(name: string | null | undefined) {
  return name?.trim() || DEFAULT_PERSONAL_ASSISTANT_NAME;
}
// MessageList.tsx — thin consumer（i18n 插值用 ICU 占位符 {name}）
t('emptyDescription', { name: getPersonalAssistantDisplayName(assistantName) })
// messages/zh.json: "我是你的专属小助手：{name}，有什么可以帮助您吗？"
```

**Related**: 新增「助手名字显示」需求时复用本 helper；`PersonalAssistantConfig.name` 原始值可能为 null 或含首尾空白。

## Pattern: Message Bubble Action Buttons (Copy / Edit)

**Problem**: 消息气泡需要操作按钮（复制、编辑），但按钮常驻会干扰阅读，且编辑涉及「重发」副作用。

**Solution**: 按钮组放气泡 footer 右侧，时间戳左侧；图标 `size-3.5`、`text-current/60 hover:bg-accent` 微样式；操作按钮通过 props 回调上抛（`onEditMessage(messageId, newContent)`），组件保持无状态（消息列表状态仍由 Context reducer 管理）。

**Example** (`apps/web/src/components/super-lobster/MessageBubble.tsx` + `MessageList.tsx`):
```tsx
// MessageBubble — footer 按钮组
<div className="mt-2 flex items-center justify-between gap-2 text-[11px]">
  <span>{time}{statusSuffix}</span>
  <span className="flex items-center gap-0.5">
    <button title={t('copyMessage')} onClick={() => handleCopy(displayContent)}>
      {copied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
    </button>
    {canEdit ? <button title={t('editMessage')} onClick={() => handleStartEdit(displayContent)}>
      <Pencil className="size-3.5" />
    </button> : null}
  </span>
</div>
```

**Why**:
- 按钮常驻（不用 `hidden group-hover:flex`）——移动端 hover 无效，`hidden` 会让移动端按钮消失（spec 审查发现）；按钮小（`size-3.5`）不影响阅读
- 复制反馈用图标切换（Copy→Check 2s）+ tooltip，不引入 toast；timer 用 `useEffect` cleanup 清理
- 编辑交互：内联 textarea（auto-focus + 全选）、Escape 取消、Ctrl+Enter 保存、空内容禁保存
- 编辑保存 = 截断该消息之后所有消息 + 重新 send（新用户消息由 `handleSend` 添加，原消息不保留，否则重复）

### Gotcha: 前端编辑重发不持久化

> **Warning**: 前端截断消息列表只是本地 state 操作，**刷新后后端会重新加载全部历史消息**（后端无删除单条消息的 API）。
>
> 因此编辑按钮只应出现在**消息数组最后一条**（`isLastMessage`，即尚未被后端持久化的最新消息）；已有后续 AI/工具回复的历史消息**不可编辑**，否则编辑结果刷新即丢失。
>
> 判断逻辑：`canEdit = isUser && isLastMessage && !isConversationStreaming && message.status !== "sending"`（`isLastMessage` 由 `MessageList` 计算：数组最后一个元素的 id）。
>
> 若要支持历史消息编辑，需后端新增删除消息 API（如 `DELETE .../messages-after?messageId=xxx`）——列为待办，需要后端联调时再实现。
