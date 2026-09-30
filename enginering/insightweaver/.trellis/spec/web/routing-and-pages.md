# Routing and Pages

## Root Layout

**File:** `apps/web/src/app/layout.tsx`

The root layout renders the `<html>` element with:
- Font loading (CSS variables for font families)
- Theme/dark-mode initialization script (inline `<script>` to avoid flash of wrong theme)
- Sidebar-collapse state read from `localStorage`

This layout has no providers -- those are composed in the locale layout.

## Locale Layout

**File:** `apps/web/src/app/[locale]/layout.tsx`

This is the provider composition root. It wraps all locale-scoped pages with:

```tsx
<NextIntlClientProvider>
  <ThemeProvider>
    <ErrorHandlerProvider>
      <LocaleSyncProvider>
        <Tooltip.Provider>
          <ToastProvider>
            <InsufficientCreditsDialog />
            {children}
          </ToastProvider>
        </Tooltip.Provider>
      </LocaleSyncProvider>
    </ErrorHandlerProvider>
  </ThemeProvider>
</NextIntlClientProvider>
```

The `ErrorHandlerProvider` subscribes to the `insightweaver:api-error` custom event and renders toasts via `sonner`. The `InsufficientCreditsDialog` is a global dialog triggered by the `emitInsufficientCredits` event when the API client encounters error code `4001`.

## Route Groups

### `(zclaw-shell)` - Main Application Shell

**Path:** `apps/web/src/app/[locale]/(zclaw-shell)/`

The primary authenticated application surface. Contains:
- **Sidebar navigation layout** (`layout.tsx`) with collapsible sidebar
- **~40 pages** organized by feature domain
- **Admin section** at `admin/` with 17 sub-pages

Key route segments:
```
(zclaw-shell)/
├── layout.tsx              # Shell layout with sidebar
├── page.tsx                # Chat/composer landing
├── admin/
│   ├── _components/        # Shared admin components
│   ├── billing-plans/
│   ├── entitlement-batches/
│   ├── enterprise-memberships/
│   ├── enterprise-instances/
│   ├── enterprise-departments/
│   ├── skills/
│   ├── agents/
│   ├── ragflow/
│   ├── workspace-quota/
│   ├── token-quota-batches/
│   ├── users/
│   ├── access-requests/
│   ├── basic-settings/
│   ├── conversation-quota/
│   └── topup-inventories/
├── billing/
├── dashboard/
├── employees/
├── enterprises/
├── memory/
├── my-skills/
├── skills/
└── workspace/
```

### `(product-landing)` - Marketing Pages

**Path:** `apps/web/src/app/[locale]/(product-landing)/`

Public marketing/landing pages. Has its own layout. These pages are accessible without authentication.

### `(home)` - Home/Dashboard

**Path:** `apps/web/src/app/[locale]/(home)/`

Home and dashboard pages with a separate layout from the main shell:
```
(home)/
├── layout.tsx
├── credits/
├── dl/
└── history/
```

## Middleware

**File:** `apps/web/src/middleware.ts`

Runs on every request (`matcher: ['/:path*']`):

1. **Public asset bypass** - Paths starting with `/_next`, `/favicon`, `/img/`, `/svg/`, `/agent-avatars/`, `/file/`, `/product-landing/`, and file extensions skip the intl middleware entirely. 白名单判定收敛在 `apps/web/src/lib/public-asset-paths.ts` 的 `isPublicAssetPath()`（纯函数，供 middleware 复用与单测）。
   - 精确放行条目：`/robots.txt`、`/sitemap.xml` 及第三方平台校验文件（如微信业务域名校验 `/<random>.txt`，需**精确匹配**添加，不把 `.txt` 加入扩展名正则以免扩大放行面）。
   - 根路径静态文件（`public/` 下）必须在此白名单中显式放行，否则会进入 next-intl 处理；`localePrefix: 'as-needed'` 下默认语言虽不改写 pathname，但升级 next-intl 后行为可能变化，精确白名单是既有约定（2026-08-21 沉淀）。

2. **Login redirect** - If a user with an `access_token` cookie visits `/login` or `/portal-login`, they are redirected to `/` (preserving the `/en` locale prefix if present).

3. **Public route check** - Routes identified as public by `isPublicRoute()` pass through intl middleware without auth checks.

4. **Auth enforcement** - Happens **client-side**, not in middleware. The API client's 401 handling triggers session refresh or redirect to login.

## SEO Metadata Routes（2026-08-21 新增）

- `src/app/robots.ts` + `src/app/sitemap.ts`：Next 元数据路由（非 public/ 静态文件），生成 `https://<site>/robots.txt` 与 `/sitemap.xml`。
- `SITE_URL` 单点：`src/lib/seo.ts`（`NEXT_PUBLIC_SITE_URL ?? 'https://evomind.zzz4ai.com'`），Dockerfile 构建期注入 `NEXT_PUBLIC_SITE_URL`；metadataBase/OG/robots/sitemap 统一引用。
- sitemap 只收录营销页 `/home` 树（`src/data/product-landing/placeholderRoutes.ts` 自动派生 + `/home/solutions`，zh 无前缀 / en 带 `/en` 前缀，条目带 `alternates.languages` 含 zh-CN + en），登录后私有页不入 sitemap。
- 逐页 metadata：middleware 设 `x-pathname` 响应头（`withMiddlewareHitHeader`，Next 16.0.10 实证 `headers()` 可读；注意与 next-intl 的 X-NEXT-INTL-LOCALE 请求头通道不同，升级 Next 后失效需改请求头模式）→ `(product-landing)/layout.tsx` 用 `normalizeSeoPath` + `getProductLandingSeo`（`src/lib/product-landing-seo.ts`）查 `messages` 的 `productLandingSeo` 命名空间（zh+en 各 16 条，key = 去前缀路径，与 `LANDING_PATHS` 一一对应，由完整性测试 T18/T18b 强制）；未命中回退共享文案（**禁止**用 `?? '/home'` 类默认值静默命中首页文案）。
- robots：`Allow /` + Disallow 登录后私有前缀（含 `/en` 变体——`localePrefix: 'as-needed'` 下所有路由都有 `/en` 变体，只 Disallow 无前缀版会漏收录）；`/share` 虽为公开路由但内容为用户分享数据，刻意 Disallow（公开 ≠ 可收录）。
- html lang：根布局 `app/layout.tsx` 通过 `headers()` 读 next-intl middleware 设置的 `X-NEXT-INTL-LOCALE`，用 `localeToHtmlLang()`（`src/lib/locale-path.ts`）输出 `zh-CN`/`en`。
- 约定：`[locale]/layout.tsx` 定义 `title.template`（`%s | EvoMind`）后，子布局如需完整标题须用 `title.absolute`（否则被模板包裹成双重后缀，如 product-landing layout）。

## Page Component Pattern

Every page follows this structure:

```tsx
'use client';

import { someApiFunction, type SomeType } from '@/api';
import { useTranslations } from 'next-intl';
import { errorToast } from '@/lib/error-handler';
import { useState, useEffect } from 'react';

// Local types and constants
interface PageState { ... }

// Helper functions
function formatItem(item: SomeType): string { ... }

export default function SomePage() {
  const t = useTranslations('somePage');
  const [items, setItems] = useState<SomeType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await someApiFunction();
        setItems(data);
      } catch (error) {
        errorToast(error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return ( <div>...</div> );
}
```

Key rules:
- All pages are `'use client'` -- no server components for pages
- API functions and types imported from `@/api` (barrel export)
- `useTranslations()` with a page-specific namespace
- Error handling via `errorToast(error)` in catch blocks
- `useEffect` for initial data fetch (not React Query or SWR)
- Filter state persisted in `sessionStorage` for list pages
