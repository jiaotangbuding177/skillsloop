# Web Frontend Layer - Overview

## Scope

`apps/web/` is a Next.js 16 (App Router) application serving as the primary user-facing frontend for InsightWeaver. It covers the main chat shell, admin console, landing pages, billing, and dashboard.

## Source Layout

```
apps/web/
├── lib/                    # Shared API client and types (non-src, root-level)
│   ├── api.ts              # ApiClient singleton, http helpers, parseResponse
│   ├── api-client.ts       # Core fetch wrapper with TimeoutController
│   ├── api-types.ts        # ApiEnvelope<T>, ApiError, TimeoutError
│   └── ...
├── messages/               # i18n message catalogs
│   ├── zh.json
│   └── en.json
├── src/
│   ├── api/                # API module definitions
│   │   ├── index.ts        # Barrel export of all modules
│   │   └── moudles/        # Per-domain API functions (note: typo in dirname)
│   │       ├── auth.ts
│   │       ├── billing.ts
│   │       ├── credits.ts
│   │       ├── enterprise.ts
│   │       ├── skills.ts
│   │       ├── agents.ts
│   │       ├── zclaw.ts
│   │       └── ...
│   ├── app/                # Next.js App Router
│   │   ├── layout.tsx      # Root <html> layout
│   │   └── [locale]/       # Locale-prefixed routes
│   │       ├── layout.tsx  # Provider composition
│   │       ├── (zclaw-shell)/   # Main app shell (~40 pages)
│   │       ├── (product-landing)/ # Marketing pages
│   │       └── (home)/     # Home/dashboard pages
│   ├── i18n/
│   │   └── routing.ts      # next-intl defineRouting config
│   ├── lib/                # Client-side utilities
│   │   ├── enterprise-context.ts
│   │   ├── error-codes.ts
│   │   ├── error-handler.ts
│   │   ├── api.ts          # Re-export from ../../lib/api
│   │   └── ...
│   ├── middleware.ts        # Auth redirect + intl middleware
│   └── components/         # Shared UI components
├── next.config.mjs         # createNextIntlPlugin + next config
└── tailwind.config.*       # Tailwind CSS v4 config
```

## Key Architectural Decisions

1. **All pages are client components** - Every page uses `'use client'`, including admin list pages. This is intentional: pages need `useState`, `useEffect`, `useTranslations`, and direct API calls.

2. **No global state library** - State is managed via React Context (for cross-cutting concerns like theme, locale, error handling), `CustomEvent` dispatch on `window` (for enterprise context), and `useState`/`useReducer` at the page level.

3. **Native fetch, no axios** - The API client wraps the browser's native `fetch` with a custom `TimeoutController` built on `AbortController`.

4. **Custom component library** - Built on Radix UI primitives, not shadcn/ui. Icons from `lucide-react`, animations via `motion` (Framer Motion successor) and `gsap`.

5. **Enterprise multi-tenancy** - `x-enterprise-id` header injected into all `/api/zclaw/*` requests from `localStorage`. Enterprise switching uses `CustomEvent` for loose coupling.

## Spec Files

| File | Covers |
|------|--------|
| [routing-and-pages.md](./routing-and-pages.md) | App Router structure, route groups, layouts, page component patterns |
| [api-integration.md](./api-integration.md) | ApiClient, api modules, response envelope, error chain, enterprise headers, 登录态就绪等待 |
| [i18n.md](./i18n.md) | next-intl v4, locale routing, message files, `useTranslations` |
| [state-management.md](./state-management.md) | Enterprise context events, React Context providers, page-level state, conversationDraft 最小集, 生成轮询超时, 请求去重登出竞态, 停滞计数器 ref 持久化 |
| [error-handling.md](./error-handling.md) | Four-tier severity, toast dedup, bilingual translation, silent rules |
| [component-patterns.md](./component-patterns.md) | Radix UI, Tailwind v4, icons, animations, page component template, TipTap 粘贴处理, Dialog a11y |
| [quota-display-patterns.md](./quota-display-patterns.md) | Quota mode display logic, context derivation, unlimited sentinel handling |
| [build-and-deployment.md](./build-and-deployment.md) | Standalone build, pnpm NFT trace 陷阱, 显式依赖声明, Dockerfile 关键点, Next.js 升级检查清单 |
| [message-render-grouping.md](./message-render-grouping.md) | 消息渲染分组管线：turn 切分、工具块 computed 字段、入口排序契约、!278/!279/!280 修复沉淀、排查入口（fiber dump / 翻页并集 diff） |
| [intersection-observer-sentinel.md](./intersection-observer-sentinel.md) | 哨兵分批加载契约：观察器绑节点生命周期（callback ref）、触发后自重臂、IO mock 语义保真测试要求、既有 5 处用法处置（bugfix-20260908-history-sentinel-observer 沉淀） |

## Dependencies Summary

| Category | Library |
|----------|---------|
| Framework | Next.js 16 (App Router) |
| i18n | next-intl v4 |
| Icons | lucide-react |
| Animations | motion, gsap |
| Charts | ECharts 6, ECharts GL |
| Rich text | TipTap |
| Toasts | sonner |
| Styling | Tailwind CSS v4 + @tailwindcss/postcss |
| UI primitives | Radix UI |
| HTTP | Native fetch (no axios) |
