# 数字大脑聚合：关系空间前端移植 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将新分支 `feature/relation-space-workstream-risk` 的关系空间前端移植到主工作区，作为"组织关系大脑"子模块，与现有"知识库大脑"并列于新"数字大脑"聚合页下。

**Architecture:** 聚合页 `/digital-brain` 用 Next.js 子路由（`layout.tsx` + `knowledge/page.tsx` + `relation/page.tsx`），tab 切换驱动内容；知识库大脑 tab 内嵌两个 `KnowledgeGraphStatusPanel` + `KnowledgeGraphExplorer` 复用组件；组织关系大脑 tab 直接渲染 `ZclawRelationSpacePage`。**没有顶级侧边栏导航入口**（参考现状：知识库大脑也只有输入框芯片作为入口）——组织关系大脑的唯一用户侧入口是输入框芯片选择器（Task 10）；聚合页 `/digital-brain` 仅通过芯片选择器跳转到达或用户手动输入 URL。管理端 `/admin/relation-compute` 通过管理导航进入（Task 8）。所有关系空间组件从上游分支原样复制（文件级对应），仅修改主工作区现有的 i18n 文案值（不改 key）。

**Tech Stack:** Next.js 14 (App Router) + React 18 + TypeScript 5 + next-intl + Prisma (后端前置) + ECharts（知识库大脑）+ 手写 SVG（组织关系大脑，零新依赖） + lucide-react + sonner

**Spec:** `docs/superpowers/specs/2026-08-26-digital-brain-relation-space-integration-design.md`

## Global Constraints

- 上游代码克隆于 `.tmp/insightweaver`（已就绪），所有移植文件从这里 `cp` 到主工作区 `apps/web/src/`
- **不改 i18n key，只改 zh/en 文案值**；芯片名保持"数字大脑"
- **零新增 npm 依赖**
- 所有任务结束时跑 `pnpm --filter @insightweaver/web test` 通过
- 每个任务独立可测、独立可提交
- 后端前置（Prisma 模型、relation-space 模块、relation-compute 服务）假设已就位

---

## Task 1: 移植 API 层 + 基础 i18n

**Files:**
- Create: `apps/web/src/api/moudles/relation-space.ts`（从 `.tmp/insightweaver/apps/web/src/api/moudles/relation-space.ts` 复制）
- Create: `apps/web/src/api/moudles/relation-space.test.ts`（同上）
- Modify: `apps/web/src/api/index.ts`（追加 `export * from './moudles/relation-space'`）
- Modify: `apps/web/messages/zh.json` + `en.json`（追加 `workspace.pages.relationSpace` 整块 264 key + `nav.shell.relationSpace` + `nav.shell.relationCompute`）

**Interfaces:**
- Consumes: 上游已实现的 `/relation-space/*` 后端路由（`apps/api/src/relation-space/`，前置）
- Produces: 导出 `getRelationSubgraphApi`、`askRelationSpaceApi`、`rebuildRelationWorkstreamsApi` 等 19 个函数 + 全套 TS 类型

- [ ] **Step 1: 复制 API 模块**

```bash
cp .tmp/insightweaver/apps/web/src/api/moudles/relation-space.ts \
   apps/web/src/api/moudles/relation-space.ts
cp .tmp/insightweaver/apps/web/src/api/moudles/relation-space.test.ts \
   apps/web/src/api/moudles/relation-space.test.ts
```

- [ ] **Step 2: 检查依赖**

Read `apps/web/src/api/moudles/relation-space.ts`，确认它使用的 `withActiveEnterpriseHeader` 来源。

- 若 `apps/web/src/lib/enterprise-context.ts` 已存在且导出 `withActiveEnterpriseHeader`：跳过
- 若不存在：从 `.tmp/insightweaver/apps/web/src/lib/enterprise-context.ts` 复制；若 `apps/web/src/lib/enterprise-context.ts` 已存在但缺该函数：从上游合并

主工作区已有 `getActiveEnterpriseId()`（见 `ZclawWorkspaceSidebar.tsx:137`），大概率缺 `withActiveEnterpriseHeader`。从上游复制即可。

- [ ] **Step 3: 在 api/index.ts 追加导出**

编辑 `apps/web/src/api/index.ts`，在末尾追加：

```ts
export * from './moudles/relation-space';
```

- [ ] **Step 4: 追加 i18n 块（仅新增 key，不改现有 key）**

从 `.tmp/insightweaver/apps/web/messages/zh.json` 中：

```bash
node -e "
const src = require('.tmp/insightweaver/apps/web/messages/zh.json');
const rel = src.workspace?.pages?.relationSpace;
const nav = { shell: { relationSpace: src.nav?.shell?.relationSpace, relationCompute: src.nav?.shell?.relationCompute } };
console.log(JSON.stringify({ relationSpace: rel, nav }, null, 2));
"
```

把 `relationSpace` 整块（264 key）插入主工作区 `apps/web/messages/zh.json` 的 `workspace.pages` 下；把 `nav.shell.relationSpace` 和 `nav.shell.relationCompute` 插入 `nav.shell` 下。

对 `en.json` 同样操作（从上游 en.json 提取）。

- [ ] **Step 5: 跑测试验证**

```bash
cd apps/web && pnpm test -- api/moudles/relation-space.test.ts
```

期望 PASS。

- [ ] **Step 6: 提交**

```bash
git add apps/web/src/api/moudles/relation-space.ts \
        apps/web/src/api/moudles/relation-space.test.ts \
        apps/web/src/api/index.ts \
        apps/web/messages/zh.json \
        apps/web/messages/en.json
git commit -m "feat(relation-space): port API layer + relationSpace i18n block"
```

---

## Task 2: 追加 admin compute 配置 API + 类型

**Files:**
- Modify: `apps/web/src/api/moudles/zclaw.ts`（追加 3 个 API 函数 + 2 个类型）

**Interfaces:**
- Consumes: 后端 `/relation-space/admin/compute-config` 路由（前置）
- Produces: `getAdminRelationComputeConfigApi`、`saveAdminRelationComputeConfigApi`、`testAdminRelationComputeConfigApi`；类型 `AdminRelationComputeConfig`、`SaveAdminRelationComputeConfigInput`

- [ ] **Step 1: 从上游定位要追加的代码**

Read `.tmp/insightweaver/apps/web/src/api/moudles/zclaw.ts` 行 1049-1070（类型）和 3201-3224（API 函数）。摘录：

```ts
// 类型（行 1049-1070 附近）
export interface AdminRelationComputeConfig {
  baseUrl: string;
  apiKeyMask: string;
  status: 'active' | 'disabled';
  requestTimeoutMs: number;
  healthStatus: 'ok' | 'error' | null;
  serviceVersion: string | null;
  protocolVersion: string | null;
  releaseSha: string | null;
  model: string | null;
  capabilities: string[];
  lastHealthCheckAt: string | null;
  lastHealthError: string | null;
  updatedAt: string;
}

export interface SaveAdminRelationComputeConfigInput {
  baseUrl: string;
  apiKey?: string;
  status?: 'active' | 'disabled';
  requestTimeoutMs?: number;
}

// API 函数（行 3201-3224 附近）
export async function getAdminRelationComputeConfigApi() {
  const response = await fetch('/api/relation-space/admin/compute-config', {
    credentials: 'include',
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as { config: AdminRelationComputeConfig };
}

export async function saveAdminRelationComputeConfigApi(input: SaveAdminRelationComputeConfigInput) {
  const response = await fetch('/api/relation-space/admin/compute-config', {
    method: 'POST',
    credentials: 'include',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as { config: AdminRelationComputeConfig };
}

export async function testAdminRelationComputeConfigApi() {
  const response = await fetch('/api/relation-space/admin/compute-config/test', {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as {
    config: AdminRelationComputeConfig;
    health?: unknown;
    error?: string;
  };
}
```

- [ ] **Step 2: 追加到主工作区 zclaw.ts**

在主工作区 `apps/web/src/api/moudles/zclaw.ts` 末尾追加上面三个函数；类型追加到类型块。

- [ ] **Step 3: 跑类型检查**

```bash
cd apps/web && pnpm tsc --noEmit
```

期望 PASS（无错误）。

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/api/moudles/zclaw.ts
git commit -m "feat(relation-compute): add admin compute config APIs + types"
```

---

## Task 3: 移植关系空间组件（ZclawRelationSpacePage + RelationGraphView + artifact-preview）

**Files:**
- Create: `apps/web/src/components/zclaw/ZclawRelationSpacePage.tsx`（1621 行，从上游复制）
- Create: `apps/web/src/components/relation-space/RelationGraphView.tsx`（1737 行）
- Create: `apps/web/src/components/relation-space/ArtifactPreviewDialog.tsx`
- Create: `apps/web/src/components/relation-space/artifact-preview.ts`

**Interfaces:**
- Consumes: Task 1 的 `api/moudles/relation-space.ts`；上游 `lib/enterprise-context.ts` 的 `withActiveEnterpriseHeader`；主工作区现有 `lucide-react`/`sonner`/`next-intl`
- Produces: `ZclawRelationSpacePage` 默认导出（接收无 props，内部自己管理企业上下文）；`RelationGraphView` 命名导出

- [ ] **Step 1: 复制组件文件**

```bash
mkdir -p apps/web/src/components/relation-space
cp .tmp/insightweaver/apps/web/src/components/zclaw/ZclawRelationSpacePage.tsx \
   apps/web/src/components/zclaw/ZclawRelationSpacePage.tsx
cp .tmp/insightweaver/apps/web/src/components/relation-space/RelationGraphView.tsx \
   apps/web/src/components/relation-space/RelationGraphView.tsx
cp .tmp/insightweaver/apps/web/src/components/relation-space/ArtifactPreviewDialog.tsx \
   apps/web/src/components/relation-space/ArtifactPreviewDialog.tsx
cp .tmp/insightweaver/apps/web/src/components/relation-space/artifact-preview.ts \
   apps/web/src/components/relation-space/artifact-preview.ts
```

- [ ] **Step 2: 检查导入**

对每个文件 `grep "^import" ...`，确认所有 import 路径在主工作区存在。常见问题：

- 导入 `@/api` → 已 OK（Task 1 已导出 relation-space）
- 导入 `@/lib/enterprise-context` → 确认 Task 1 已就位
- 导入 `@/hooks/useActiveEnterpriseSpace` → 若缺失，从上游复制
- 导入 `@/components/zclaw/...` 内的其他组件 → 确认已存在

逐个修复直到 `pnpm tsc --noEmit` 通过。

- [ ] **Step 3: 类型检查**

```bash
cd apps/web && pnpm tsc --noEmit
```

期望 PASS。

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/components/zclaw/ZclawRelationSpacePage.tsx \
        apps/web/src/components/relation-space/
git commit -m "feat(relation-space): port ZclawRelationSpacePage + RelationGraphView + artifact-preview"
```

---

## Task 4: 移植 /relations 与 /admin/relation-compute 页面路由

**Files:**
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/relations/page.tsx`
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/admin/relation-compute/page.tsx`

**Interfaces:**
- Consumes: Task 3 的 `ZclawRelationSpacePage`；Task 2 的 `getAdminRelationComputeConfigApi` 等
- Produces: `/relations` 路由（薄包装）+ `/admin/relation-compute` 路由（admin 配置页）

- [ ] **Step 1: 复制页面文件**

```bash
mkdir -p apps/web/src/app/\[locale\]/\(zclaw-shell\)/relations
mkdir -p apps/web/src/app/\[locale\]/\(zclaw-shell\)/admin/relation-compute
cp .tmp/insightweaver/apps/web/src/app/\[locale\]/\(zclaw-shell\)/relations/page.tsx \
   apps/web/src/app/\[locale\]/\(zclaw-shell\)/relations/page.tsx
cp .tmp/insightweaver/apps/web/src/app/\[locale\]/\(zclaw-shell\)/admin/relation-compute/page.tsx \
   apps/web/src/app/\[locale\]/\(zclaw-shell\)/admin/relation-compute/page.tsx
```

- [ ] **Step 2: 验证页面结构**

上游 `/relations/page.tsx` 应大致为：

```tsx
import ZclawRelationSpacePage from '@/components/zclaw/ZclawRelationSpacePage';
export default function RelationsPage() {
  return <ZclawRelationSpacePage />;
}
```

上游 `/admin/relation-compute/page.tsx` 含：

- `useSession()` 获取用户，`user.role !== 'admin'` → `redirect('/relations')`
- 表单 + 连接测试按钮 + 健康状态展示

Read 后确认结构。若有 `useScopedAdminAccess` 等主工作区未导入的 hook，从上游复制或适配。

- [ ] **Step 3: 类型检查 + 启动 dev 验证**

```bash
cd apps/web && pnpm tsc --noEmit
```

```bash
cd apps/web && pnpm dev  # 另一终端
curl -s http://localhost:3000/relations | head  # 应返回页面
```

注意：此阶段页面**尚未挂入导航**，只能通过直接 URL 访问。

- [ ] **Step 4: 提交**

```bash
git add apps/web/src/app/\[locale\]/\(zclaw-shell\)/relations/ \
        apps/web/src/app/\[locale\]/\(zclaw-shell\)/admin/relation-compute/
git commit -m "feat(relation-space): add /relations and /admin/relation-compute routes"
```

---

## Task 5: 移植组件测试

**Files:**
- Create: `apps/web/src/components/relation-space/RelationGraphView.test.ts`
- Create: `apps/web/src/components/relation-space/RelationGraphView.interaction.test.tsx`
- Create: `apps/web/src/components/relation-space/artifact-preview.test.ts`

**Interfaces:**
- Consumes: Task 3 组件
- Produces: 上游测试套件全部通过

- [ ] **Step 1: 复制测试文件**

```bash
cp .tmp/insightweaver/apps/web/src/components/relation-space/RelationGraphView.test.ts \
   apps/web/src/components/relation-space/RelationGraphView.test.ts
cp .tmp/insightweaver/apps/web/src/components/relation-space/RelationGraphView.interaction.test.tsx \
   apps/web/src/components/relation-space/RelationGraphView.interaction.test.tsx
cp .tmp/insightweaver/apps/web/src/components/relation-space/artifact-preview.test.ts \
   apps/web/src/components/relation-space/artifact-preview.test.ts
```

- [ ] **Step 2: 跑全部关系空间测试**

```bash
cd apps/web && pnpm test -- components/relation-space/ api/moudles/relation-space.test.ts
```

期望全部 PASS。如有 import 路径问题，按 Task 3 的"检查导入"方法修复。

- [ ] **Step 3: 提交**

```bash
git add apps/web/src/components/relation-space/*.test.*
git commit -m "test(relation-space): port component tests"
```

---

## Task 6: 抽取 useKnowledgeGraphStatuses 共享 hook

**Files:**
- Create: `apps/web/src/hooks/useKnowledgeGraphStatuses.ts`
- Create: `apps/web/src/hooks/__tests__/useKnowledgeGraphStatuses.test.ts`
- Modify: `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`（用新 hook 替换内联逻辑，**等价重构**）

**Interfaces:**
- Consumes: `getZclawRagflowGraphStatusApi`、`build/refresh/delete/cancelZclawRagflowGraphApi`、`getActiveEnterpriseId`、`ACTIVE_ENTERPRISE_CHANGED_EVENT`、`shouldPollKnowledgeGraphStatus`、`KNOWLEDGE_GRAPH_STATUS_POLL_INTERVAL_MS`、`toast`/`errorToast`、`useTranslations('workspace.toasts')`
- Produces:

```ts
export type KnowledgeGraphScope = 'workspace' | 'shared-workspace';
export type KnowledgeGraphAction = 'build' | 'refresh' | 'delete' | 'cancel';

export interface UseKnowledgeGraphStatusesInput {
  enabled: boolean;
  isBootstrapping: boolean;
}

export interface UseKnowledgeGraphStatusesResult {
  activeEnterpriseId: string | null;
  personalGraphStatus: ZclawRagflowGraphStatusResponse | null;
  enterpriseGraphStatus: ZclawRagflowGraphStatusResponse | null;
  isGraphStatusLoading: boolean;
  graphStatusMutatingKey: KnowledgeGraphScope | null;
  showEnterpriseGraphStatus: boolean;
  loadGraphStatuses: () => Promise<void>;
  runGraphStatusMutation: (source: KnowledgeGraphScope, action: KnowledgeGraphAction) => Promise<void>;
  handleBuildGraph: (source: KnowledgeGraphScope) => void;
  handleRefreshGraph: (source: KnowledgeGraphScope) => void;
  handleDeleteGraph: (source: KnowledgeGraphScope) => void;
  handleCancelGraph: (source: KnowledgeGraphScope) => void;
}

export function useKnowledgeGraphStatuses(input: UseKnowledgeGraphStatusesInput): UseKnowledgeGraphStatusesResult;
```

- [ ] **Step 1: 写 hook 测试（失败）**

创建 `apps/web/src/hooks/__tests__/useKnowledgeGraphStatuses.test.ts`：

```ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { useKnowledgeGraphStatuses } from '../useKnowledgeGraphStatuses';
import * as api from '@/api';

vi.mock('@/api', () => ({
  getZclawRagflowGraphStatusApi: vi.fn(),
  buildZclawRagflowGraphApi: vi.fn(),
  refreshZclawRagflowGraphApi: vi.fn(),
  deleteZclawRagflowGraphApi: vi.fn(),
  cancelZclawRagflowGraphApi: vi.fn(),
}));
vi.mock('@/lib/enterprise-context', () => ({
  getActiveEnterpriseId: vi.fn(() => null),
  ACTIVE_ENTERPRISE_CHANGED_EVENT: 'test-enterprise-changed',
}));
vi.mock('sonner', () => ({ toast: { success: vi.fn() }, errorToast: vi.fn() }));

describe('useKnowledgeGraphStatuses', () => {
  it('loads personal status on mount when enabled', async () => {
    const personal = { scope: 'personal', graphStatus: 'succeeded' } as any;
    vi.mocked(api.getZclawRagflowGraphStatusApi).mockResolvedValue(personal);

    const { result } = renderHook(() =>
      useKnowledgeGraphStatuses({ enabled: true, isBootstrapping: false }),
    );

    await waitFor(() => expect(result.current.isGraphStatusLoading).toBe(false));
    expect(result.current.personalGraphStatus).toEqual(personal);
    expect(result.current.enterpriseGraphStatus).toBeNull();
    expect(api.getZclawRagflowGraphStatusApi).toHaveBeenCalledWith({ source: 'workspace' });
  });

  it('skips loading when disabled', () => {
    renderHook(() => useKnowledgeGraphStatuses({ enabled: false, isBootstrapping: false }));
    expect(api.getZclawRagflowGraphStatusApi).not.toHaveBeenCalled();
  });

  it('loads both scopes when activeEnterpriseId is present', async () => {
    // 测试有 activeEnterpriseId 时的行为
    // ...
  });
});
```

- [ ] **Step 2: 创建 hook 实现**

创建 `apps/web/src/hooks/useKnowledgeGraphStatuses.ts`，**从 `ZclawWorkspaceSidebar.tsx` 行 329 / 333-341 / 434-445 / 515-522 / 553-559 / 561-718 抽出等价逻辑**：

```ts
'use client';

import { useTranslations } from 'next-intl';
import React from 'react';
import { toast } from 'sonner';
import {
  getZclawRagflowGraphStatusApi,
  buildZclawRagflowGraphApi,
  refreshZclawRagflowGraphApi,
  deleteZclawRagflowGraphApi,
  cancelZclawRagflowGraphApi,
} from '@/api';
import type { ZclawRagflowGraphStatusResponse } from '@/api';
import {
  ACTIVE_ENTERPRISE_CHANGED_EVENT,
  getActiveEnterpriseId,
} from '@/lib/enterprise-context';
import {
  KNOWLEDGE_GRAPH_STATUS_POLL_INTERVAL_MS,
  shouldPollKnowledgeGraphStatus,
} from '@/components/super-lobster/knowledge-graph-status';
import { errorToast } from '@/lib/error-toast';  // 或现有等价路径

export type KnowledgeGraphScope = 'workspace' | 'shared-workspace';
export type KnowledgeGraphAction = 'build' | 'refresh' | 'delete' | 'cancel';

export interface UseKnowledgeGraphStatusesInput {
  enabled: boolean;
  isBootstrapping: boolean;
}

export interface UseKnowledgeGraphStatusesResult {
  activeEnterpriseId: string | null;
  personalGraphStatus: ZclawRagflowGraphStatusResponse | null;
  enterpriseGraphStatus: ZclawRagflowGraphStatusResponse | null;
  isGraphStatusLoading: boolean;
  graphStatusMutatingKey: KnowledgeGraphScope | null;
  showEnterpriseGraphStatus: boolean;
  loadGraphStatuses: () => Promise<void>;
  runGraphStatusMutation: (source: KnowledgeGraphScope, action: KnowledgeGraphAction) => Promise<void>;
  handleBuildGraph: (source: KnowledgeGraphScope) => void;
  handleRefreshGraph: (source: KnowledgeGraphScope) => void;
  handleDeleteGraph: (source: KnowledgeGraphScope) => void;
  handleCancelGraph: (source: KnowledgeGraphScope) => void;
}

export function useKnowledgeGraphStatuses(
  input: UseKnowledgeGraphStatusesInput,
): UseKnowledgeGraphStatusesResult {
  const ws = useTranslations('workspace.toasts');
  const [activeEnterpriseId, setActiveEnterpriseId] = React.useState(() => getActiveEnterpriseId());
  const [personalGraphStatus, setPersonalGraphStatus] =
    React.useState<ZclawRagflowGraphStatusResponse | null>(null);
  const [enterpriseGraphStatus, setEnterpriseGraphStatus] =
    React.useState<ZclawRagflowGraphStatusResponse | null>(null);
  const [isGraphStatusLoading, setIsGraphStatusLoading] = React.useState(false);
  const [graphStatusMutatingKey, setGraphStatusMutatingKey] =
    React.useState<KnowledgeGraphScope | null>(null);
  const graphStatusPollingInFlightRef = React.useRef(false);

  // 企业变化监听
  React.useEffect(() => {
    const handle = () => setActiveEnterpriseId(getActiveEnterpriseId());
    handle();
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handle);
    window.addEventListener('storage', handle);
    return () => {
      window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handle);
      window.removeEventListener('storage', handle);
    };
  }, []);

  // 企业变化时重置
  React.useEffect(() => {
    setPersonalGraphStatus(null);
    setEnterpriseGraphStatus(null);
    graphStatusPollingInFlightRef.current = false;
  }, [activeEnterpriseId]);

  const mergeGraphStatus = React.useCallback((status: ZclawRagflowGraphStatusResponse) => {
    if (status.scope === 'enterprise') {
      setEnterpriseGraphStatus(status);
      return;
    }
    setPersonalGraphStatus(status);
  }, []);

  const loadGraphStatuses = React.useCallback(async () => {
    if (!input.enabled || input.isBootstrapping) return;
    setIsGraphStatusLoading(true);
    try {
      const requests = [getZclawRagflowGraphStatusApi({ source: 'workspace' })];
      if (activeEnterpriseId) {
        requests.push(
          getZclawRagflowGraphStatusApi({
            source: 'shared-workspace',
            enterpriseId: activeEnterpriseId,
          }),
        );
      }
      const results = await Promise.allSettled(requests);
      for (const r of results) {
        if (r.status === 'fulfilled') mergeGraphStatus(r.value);
      }
      if (!activeEnterpriseId) setEnterpriseGraphStatus(null);
    } finally {
      setIsGraphStatusLoading(false);
    }
  }, [input.enabled, input.isBootstrapping, activeEnterpriseId, mergeGraphStatus]);

  React.useEffect(() => {
    void loadGraphStatuses();
  }, [loadGraphStatuses]);

  // 1s 轮询（仅在 active 状态）
  React.useEffect(() => {
    if (!input.enabled || input.isBootstrapping ||
        !shouldPollKnowledgeGraphStatus([personalGraphStatus, enterpriseGraphStatus])) return;
    const refresh = async () => {
      if (document.visibilityState === 'hidden') return;
      if (graphStatusPollingInFlightRef.current) return;
      graphStatusPollingInFlightRef.current = true;
      try {
        const requests = [getZclawRagflowGraphStatusApi({ source: 'workspace' })];
        if (activeEnterpriseId) {
          requests.push(getZclawRagflowGraphStatusApi({
            source: 'shared-workspace',
            enterpriseId: activeEnterpriseId,
          }));
        }
        const results = await Promise.allSettled(requests);
        for (const r of results) {
          if (r.status === 'fulfilled') mergeGraphStatus(r.value);
        }
      } catch { /* best-effort */ } finally {
        graphStatusPollingInFlightRef.current = false;
      }
    };
    const interval = window.setInterval(() => void refresh(), KNOWLEDGE_GRAPH_STATUS_POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [input.enabled, input.isBootstrapping, activeEnterpriseId,
      personalGraphStatus, enterpriseGraphStatus, mergeGraphStatus]);

  const runGraphStatusMutation = React.useCallback(
    async (source: KnowledgeGraphScope, action: KnowledgeGraphAction) => {
      const request = {
        source,
        enterpriseId: source === 'shared-workspace' ? activeEnterpriseId || undefined : undefined,
      };
      setGraphStatusMutatingKey(source);
      try {
        const status =
          action === 'build' ? await buildZclawRagflowGraphApi(request) :
          action === 'refresh' ? await refreshZclawRagflowGraphApi(request) :
          action === 'delete' ? await deleteZclawRagflowGraphApi(request) :
          await cancelZclawRagflowGraphApi(request);
        mergeGraphStatus(status);
        void loadGraphStatuses();
        if (action === 'build') toast.success(ws('kgBuildQueued'));
        if (action === 'refresh') toast.success(ws('kgRefreshQueued'));
        if (action === 'delete') toast.success(ws('kgDeleteQueued'));
        if (action === 'cancel') toast.success(ws('kgCancelTask'));
      } catch (error: any) {
        errorToast(error?.message || ws('kgOperationFailed'));
      } finally {
        setGraphStatusMutatingKey(null);
      }
    },
    [activeEnterpriseId, loadGraphStatuses, mergeGraphStatus, ws],
  );

  const handleBuildGraph = React.useCallback((s: KnowledgeGraphScope) => { void runGraphStatusMutation(s, 'build'); }, [runGraphStatusMutation]);
  const handleRefreshGraph = React.useCallback((s: KnowledgeGraphScope) => { void runGraphStatusMutation(s, 'refresh'); }, [runGraphStatusMutation]);
  const handleDeleteGraph = React.useCallback((s: KnowledgeGraphScope) => {
    const label = s === 'shared-workspace' ? ws('enterpriseKnowledgeGraph') : ws('personalKnowledgeGraph');
    if (!window.confirm(ws('confirmDeleteGraph', { label }))) return;
    void runGraphStatusMutation(s, 'delete');
  }, [runGraphStatusMutation, ws]);
  const handleCancelGraph = React.useCallback((s: KnowledgeGraphScope) => {
    const label = s === 'shared-workspace' ? ws('enterpriseKnowledgeGraph') : ws('personalKnowledgeGraph');
    if (!window.confirm(ws('confirmCancelKgTask', { label }))) return;
    void runGraphStatusMutation(s, 'cancel');
  }, [runGraphStatusMutation, ws]);

  return {
    activeEnterpriseId,
    personalGraphStatus,
    enterpriseGraphStatus,
    isGraphStatusLoading,
    graphStatusMutatingKey,
    showEnterpriseGraphStatus: Boolean(activeEnterpriseId),
    loadGraphStatuses,
    runGraphStatusMutation,
    handleBuildGraph,
    handleRefreshGraph,
    handleDeleteGraph,
    handleCancelGraph,
  };
}
```

- [ ] **Step 3: 跑测试（应通过）**

```bash
cd apps/web && pnpm test -- hooks/__tests__/useKnowledgeGraphStatuses.test.ts
```

- [ ] **Step 4: 重构 ZclawWorkspaceSidebar 使用新 hook**

编辑 `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`：

1. 移除内联的状态声明（行 329、333-341、434-445、515-522、553-559、561-718）
2. 在组件顶部调用 `useKnowledgeGraphStatuses({ enabled, isBootstrapping })`，解构出所有返回值
3. 原有的 `setActiveEnterpriseIdState`、`setPersonalGraphStatus`、`setEnterpriseGraphStatus`、`setIsGraphStatusLoading`、`setGraphStatusMutatingKey` 全部删除
4. `<KnowledgeBaseSidebarSection>` 传参保持不变

```tsx
import { useKnowledgeGraphStatuses } from '@/hooks/useKnowledgeGraphStatuses';

// 在组件函数顶部：
const {
  activeEnterpriseId,
  personalGraphStatus,
  enterpriseGraphStatus,
  isGraphStatusLoading,
  graphStatusMutatingKey,
  handleBuildGraph,
  handleRefreshGraph,
  handleDeleteGraph,
  handleCancelGraph,
} = useKnowledgeGraphStatuses({ enabled, isBootstrapping });
```

- [ ] **Step 5: 跑所有知识图谱相关测试（回归）**

```bash
cd apps/web && pnpm test -- \
  super-lobster/__tests__/KnowledgeGraphExplorer.permissions.test.tsx \
  super-lobster/__tests__/KnowledgeGraphStatusPanel.test.tsx \
  super-lobster/__tests__/MessageInput.knowledge-graph.test.tsx \
  zclaw/__tests__/ZclawWorkspaceSidebar.test.tsx \
  hooks/__tests__/useKnowledgeGraphStatuses.test.ts
```

期望全部 PASS（等价重构）。

- [ ] **Step 6: 提交**

```bash
git add apps/web/src/hooks/useKnowledgeGraphStatuses.ts \
        apps/web/src/hooks/__tests__/useKnowledgeGraphStatuses.test.ts \
        apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx
git commit -m "refactor(knowledge-graph): extract useKnowledgeGraphStatuses hook (equivalent)"
```

---

## Task 7: 创建数字大脑聚合页 `/digital-brain`

**Files:**
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/page.tsx`（redirect）
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/layout.tsx`（tab 栏）
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/knowledge/page.tsx`（知识库大脑 tab）
- Create: `apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/relation/page.tsx`（组织关系大脑 tab）
- Create: `apps/web/src/components/digital-brain/KnowledgeBrainTab.tsx`（含 KnowledgeGraphExplorer 挂载）
- Modify: `apps/web/messages/zh.json` + `en.json`（追加 `workspace.digitalBrain` 块：`title`/`subtitle`/`tab.knowledge`/`tab.relation`/`openBrowser`）

**Interfaces:**
- Consumes: Task 6 的 `useKnowledgeGraphStatuses`；现有 `KnowledgeGraphStatusPanel`、`KnowledgeGraphExplorer`；Task 3 的 `ZclawRelationSpacePage`；现有 `super-lobster-events.ts` 的 `dispatchSuperLobsterGraphNodeContextSelected`
- Produces: `/digital-brain` 路由 + 两个子路由

- [ ] **Step 1: 创建重定向 page.tsx**

`apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/page.tsx`：

```tsx
import { redirect } from 'next/navigation';

export default function DigitalBrainPage() {
  redirect('/digital-brain/knowledge');
}
```

- [ ] **Step 2: 创建 layout.tsx（含 tab 栏）**

`apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/layout.tsx`：

```tsx
'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { Brain } from 'lucide-react';

export default function DigitalBrainLayout({ children }: { children: ReactNode }) {
  const t = useTranslations('workspace.digitalBrain');
  const pathname = usePathname();
  const tabs = [
    { href: '/digital-brain/knowledge', label: t('tab.knowledge') },
    { href: '/digital-brain/relation', label: t('tab.relation') },
  ];
  return (
    <div className="mx-auto max-w-7xl px-6 py-6">
      <header className="mb-6">
        <div className="flex items-center gap-3">
          <Brain className="h-7 w-7 text-primary" />
          <div>
            <h1 className="text-2xl font-semibold">{t('title')}</h1>
            <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
          </div>
        </div>
        <nav className="mt-4 flex gap-2 border-b">
          {tabs.map((tab) => {
            const active = pathname === tab.href || pathname.startsWith(tab.href + '/');
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  active
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
```

- [ ] **Step 3: 创建知识库大脑 tab 内容 + KnowledgeGraphExplorer 挂载**

创建 `apps/web/src/components/digital-brain/KnowledgeBrainTab.tsx`：

```tsx
'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import React from 'react';
import KnowledgeGraphStatusPanel from '@/components/super-lobster/KnowledgeGraphStatusPanel';
import KnowledgeGraphExplorer from '@/components/super-lobster/KnowledgeGraphExplorer';
import { canOpenKnowledgeGraph } from '@/components/super-lobster/knowledge-graph-explorer';
import { dispatchSuperLobsterGraphNodeContextSelected } from '@/lib/super-lobster-events';
import { useKnowledgeGraphStatuses } from '@/hooks/useKnowledgeGraphStatuses';
import type { KnowledgeGraphScope } from '@/hooks/useKnowledgeGraphStatuses';

export default function KnowledgeBrainTab() {
  const tToast = useTranslations('workspace.toasts');
  const tDb = useTranslations('workspace.digitalBrain');
  const router = useRouter();
  const {
    personalGraphStatus,
    enterpriseGraphStatus,
    isGraphStatusLoading,
    graphStatusMutatingKey,
    showEnterpriseGraphStatus,
    handleBuildGraph,
    handleRefreshGraph,
    handleDeleteGraph,
    handleCancelGraph,
  } = useKnowledgeGraphStatuses({ enabled: true, isBootstrapping: false });

  const [explorerSource, setExplorerSource] = React.useState<KnowledgeGraphScope | null>(null);
  const graphExplorerStatus = explorerSource === 'shared-workspace'
    ? enterpriseGraphStatus
    : personalGraphStatus;

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        <KnowledgeGraphStatusPanel
          title={tToast('personalKnowledgeGraph')}
          scope="personal"
          status={personalGraphStatus}
          isLoading={isGraphStatusLoading}
          isMutating={graphStatusMutatingKey === 'workspace'}
          canOpenGraph={canOpenKnowledgeGraph(personalGraphStatus)}
          onBuild={() => handleBuildGraph('workspace')}
          onRefresh={() => handleRefreshGraph('workspace')}
          onDelete={() => handleDeleteGraph('workspace')}
          onCancel={() => handleCancelGraph('workspace')}
          onOpenGraph={() => setExplorerSource('workspace')}
        />
        {showEnterpriseGraphStatus ? (
          <KnowledgeGraphStatusPanel
            title={tToast('enterpriseKnowledgeGraph')}
            scope="enterprise"
            status={enterpriseGraphStatus}
            isLoading={isGraphStatusLoading}
            isMutating={graphStatusMutatingKey === 'shared-workspace'}
            canOpenGraph={canOpenKnowledgeGraph(enterpriseGraphStatus)}
            onBuild={() => handleBuildGraph('shared-workspace')}
            onRefresh={() => handleRefreshGraph('shared-workspace')}
            onDelete={() => handleDeleteGraph('shared-workspace')}
            onCancel={() => handleCancelGraph('shared-workspace')}
            onOpenGraph={() => setExplorerSource('shared-workspace')}
          />
        ) : null}
      </div>

      <div className="mt-6">
        <button
          type="button"
          onClick={() => setExplorerSource('workspace')}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90"
        >
          {tDb('openBrowser')}
        </button>
      </div>

      <KnowledgeGraphExplorer
        open={Boolean(explorerSource)}
        title={explorerSource === 'shared-workspace' ? tToast('enterpriseKnowledgeGraph') : tToast('personalKnowledgeGraph')}
        source={explorerSource ?? 'workspace'}
        enterpriseId={enterpriseGraphStatus?.enterpriseId}
        status={graphExplorerStatus}
        onClose={() => setExplorerSource(null)}
        onStartNodeChat={(input) => {
          setExplorerSource(null);
          // 桥接：dispatchSuperLobsterGraphNodeContextSelected 已经写入 sessionStorage，
          // SuperLobsterPage 挂载时会读取。跳转到工作台即可。
          dispatchSuperLobsterGraphNodeContextSelected(input);
          router.push('/');
        }}
      />
    </>
  );
}
```

注：`KnowledgeGraphExplorer` 在主工作区是默认导出还是命名导出，从 `KnowledgeBaseSidebarSection.tsx` 行 18 的导入语句确认：

```bash
grep "KnowledgeGraphExplorer" apps/web/src/components/super-lobster/KnowledgeBaseSidebarSection.tsx | head -1
```

按实际导入方式调整。`canOpenKnowledgeGraph` 同理。

- [ ] **Step 4: 创建知识库 tab 页面**

`apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/knowledge/page.tsx`：

```tsx
import KnowledgeBrainTab from '@/components/digital-brain/KnowledgeBrainTab';

export default function KnowledgeBrainPage() {
  return <KnowledgeBrainTab />;
}
```

- [ ] **Step 5: 创建组织关系大脑 tab 页面**

`apps/web/src/app/[locale]/(zclaw-shell)/digital-brain/relation/page.tsx`：

```tsx
import ZclawRelationSpacePage from '@/components/zclaw/ZclawRelationSpacePage';

export default function RelationBrainPage() {
  return <ZclawRelationSpacePage />;
}
```

- [ ] **Step 6: 追加 i18n 块**

在 `apps/web/messages/zh.json` 的 `workspace` 下追加：

```json
"digitalBrain": {
  "title": "数字大脑",
  "subtitle": "个人与团队的知识沉淀、组织协作与风险洞察",
  "tab.knowledge": "知识库大脑",
  "tab.relation": "组织关系大脑",
  "openBrowser": "打开全屏图谱浏览器"
}
```

`en.json` 对称：

```json
"digitalBrain": {
  "title": "Digital Brain",
  "subtitle": "Knowledge, collaboration and risk insights for you and your team",
  "tab.knowledge": "Knowledge Base Brain",
  "tab.relation": "Organizational Relationship Brain",
  "openBrowser": "Open full-screen graph browser"
}
```

- [ ] **Step 7: 类型检查 + dev 验证**

```bash
cd apps/web && pnpm tsc --noEmit
```

dev 服务器访问：

- `http://localhost:3000/digital-brain` → 重定向到 `/digital-brain/knowledge`
- `http://localhost:3000/digital-brain/knowledge` → 显示两张状态卡 + "打开全屏图谱浏览器" 按钮
- `http://localhost:3000/digital-brain/relation` → 显示组织关系大脑（ZclawRelationSpacePage）
- 点击"打开全屏图谱浏览器" → ECharts 全屏弹出
- 在浏览器内右键节点 → "就该节点提问" → 跳转 `/`，聊天输入框自动带入节点上下文（桥接生效）

- [ ] **Step 8: 提交**

```bash
git add apps/web/src/app/\[locale\]/\(zclaw-shell\)/digital-brain/ \
        apps/web/src/components/digital-brain/ \
        apps/web/messages/zh.json \
        apps/web/messages/en.json
git commit -m "feat(digital-brain): add /digital-brain aggregation page with two tabs"
```

---

## Task 8: 接入管理端导航（无用户侧顶级入口）

**说明：** 主工作区当前**没有**顶级"数字大脑"导航项（参考现状：知识库大脑的唯一入口是输入框芯片）。本任务只追加管理端 `/admin/relation-compute` 的导航项，**不在 ZclawShell 侧边栏添加顶级"数字大脑"入口**。组织关系大脑的唯一用户侧入口是 Task 10 的输入框芯片选择器。

**Files:**
- Modify: `apps/web/src/lib/zclaw-admin-nav.ts`（追加 `RELATION_COMPUTE_NAV` + 加入 canAccessManagementBackend 分支）
- Modify: `apps/web/src/lib/__tests__/zclaw-admin-nav.test.ts`（追加 RELATION_COMPUTE_NAV 仅平台管理员可见断言）
- Modify: `apps/web/messages/zh.json` + `en.json`（追加 `nav.shell.relationSpace` + `nav.shell.relationCompute`；**不追加** `nav.shell.digitalBrain`）

**Interfaces:**
- Consumes: `useScopedAdminAccess` 的 `canAccessManagementBackend`
- Produces: `/admin/relation-compute` 对平台管理员可见（管理导航）

- [ ] **Step 1: 追加 RELATION_COMPUTE_NAV**

编辑 `apps/web/src/lib/zclaw-admin-nav.ts`，在 `ENTERPRISE_KNOWLEDGE_GRAPH_NAV` 定义后追加：

```ts
const RELATION_COMPUTE_NAV: ZclawAdminNavItem = {
  href: '/admin/relation-compute' as Route,
  labelKey: 'shell.relationCompute',
  iconKey: 'settings',
};
```

在 `getZclawAdminNavItems` 的 `canAccessManagementBackend` 分支数组中（行 212 `ENTERPRISE_KNOWLEDGE_GRAPH_NAV` 之后），追加：

```ts
RELATION_COMPUTE_NAV,
```

- [ ] **Step 2: 追加 i18n**

`apps/web/messages/zh.json` 的 `nav.shell` 下追加：

```json
"relationSpace": "关系空间",
"relationCompute": "关系计算服务"
```

**不追加** `nav.shell.digitalBrain`（没有顶级入口）。`en.json` 对称（`"relationSpace": "Relation space"`, `"relationCompute": "Relation compute service"`）。

- [ ] **Step 3: 更新 zclaw-admin-nav.test.ts**

追加测试用例：

```ts
it('includes RELATION_COMPUTE_NAV only in canAccessManagementBackend branch', () => {
  const adminItems = getZclawAdminNavItems({
    canAccessManagementBackend: true,
    canAccessDataDashboard: false,
    canAccessOrganizationManagement: false,
    canAccessEnterpriseMemberships: false,
    canAccessTopupInventories: false,
    canAccessBatchManagement: false,
    canAccessSkillManagement: false,
    canAccessAgentManagement: false,
    canAccessBasicSettings: false,
  });
  expect(adminItems.some((i) => i.href === '/admin/relation-compute')).toBe(true);

  const nonAdminItems = getZclawAdminNavItems({
    canAccessManagementBackend: false,
    canAccessDataDashboard: false,
    canAccessOrganizationManagement: true,
    canAccessEnterpriseMemberships: false,
    canAccessTopupInventories: false,
    canAccessBatchManagement: false,
    canAccessSkillManagement: false,
    canAccessAgentManagement: false,
    canAccessBasicSettings: false,
  });
  expect(nonAdminItems.some((i) => i.href === '/admin/relation-compute')).toBe(false);
});
```

- [ ] **Step 4: 跑测试 + 类型检查**

```bash
cd apps/web && pnpm test -- lib/__tests__/zclaw-admin-nav.test.ts
cd apps/web && pnpm tsc --noEmit
```

- [ ] **Step 5: dev 验证**

- 登录普通用户 → 管理导航中**无**"关系计算服务"
- 登录平台管理员 → 管理导航中出现"关系计算服务" → 点击跳转 `/admin/relation-compute`
- 用户侧侧边栏**无**"数字大脑"顶级入口（与现状一致）

- [ ] **Step 6: 提交**

```bash
git add apps/web/src/lib/zclaw-admin-nav.ts \
        apps/web/src/lib/__tests__/zclaw-admin-nav.test.ts \
        apps/web/messages/zh.json \
        apps/web/messages/en.json
git commit -m "feat(admin): add RELATION_COMPUTE_NAV to admin nav (platform-admin only)"
```

---

## Task 9: 应用术语重命名

**Files:**
- Modify: `apps/web/messages/zh.json`
- Modify: `apps/web/messages/en.json`

**Interfaces:**
- Consumes: 现有 `workspace.toasts.personalKnowledgeGraph` / `enterpriseKnowledgeGraph` 等 key（**只改值不改 key**）
- Produces: 侧边栏状态卡、Explorer 标题/标签、相关 toast、adminHome 卡片文案从"数字大脑"变为"知识库大脑"

- [ ] **Step 1: 列出要改的 key**

通过 grep 找出所有文案值为"数字大脑"的位置：

```bash
grep -n "数字大脑" apps/web/messages/zh.json
```

预期命中：

- `workspace.toasts.personalKnowledgeGraph`: "个人数字大脑" → "个人知识库大脑"
- `workspace.toasts.enterpriseKnowledgeGraph`: "团队数字大脑" → "团队知识库大脑"
- `workspace.toasts.confirmDeleteGraph`: 含"数字大脑"占位符 → 不变（占位符 `{label}` 已被调用方替换，调用方用上面两个 key 的值，自动生效）
- `workspace.toasts.confirmCancelKgTask`: 同上
- `adminHome.cards.enterpriseVectorKb.title` / `description`: 含"数字大脑" → 改为"知识库大脑"
- `auto.k_*` 哈希 key 中值含"数字大脑"的 → 同步改（按仓库 i18n 流程）

**明确不改**：`workspace.chat.knowledgeGraph` 值保持"数字大脑"（芯片名，代表容器）。

- [ ] **Step 2: 编辑 zh.json**

逐项替换。示例：

```diff
- "personalKnowledgeGraph": "个人数字大脑",
+ "personalKnowledgeGraph": "个人知识库大脑",
- "enterpriseKnowledgeGraph": "团队数字大脑",
+ "enterpriseKnowledgeGraph": "团队知识库大脑",
```

- [ ] **Step 3: 对称编辑 en.json**

- `"Personal Digital Brain"` → `"Personal Knowledge Base Brain"`
- `"Team Digital Brain"` → `"Team Knowledge Base Brain"`
- `adminHome.cards.enterpriseVectorKb` 文案对应改

- [ ] **Step 4: 跑知识图谱相关测试（回归）**

```bash
cd apps/web && pnpm test -- \
  super-lobster/__tests__/KnowledgeGraphExplorer.permissions.test.tsx \
  super-lobster/__tests__/KnowledgeGraphStatusPanel.test.tsx \
  super-lobster/__tests__/MessageInput.knowledge-graph.test.tsx
```

期望全部 PASS（文案替换不影响行为）。

- [ ] **Step 5: dev 验证**

- 工作台侧边栏两张卡标题 → 个人知识库大脑 / 团队知识库大脑
- 打开 Explorer → 标题 / tab 标签 → 知识库大脑
- Admin 首页"知识图谱服务配置"卡片 → 文案使用"知识库大脑"
- 输入框芯片 → 仍显示"数字大脑"

- [ ] **Step 6: 提交**

```bash
git add apps/web/messages/zh.json apps/web/messages/en.json
git commit -m "i18n(knowledge-graph): rename 数字大脑 → 知识库大脑 in copy (keys unchanged)"
```

---

## Task 10: 实现大脑选择器 popover + 接入 MessageInput

**Files:**
- Create: `apps/web/src/components/super-lobster/BrainSelectorPopover.tsx`
- Create: `apps/web/src/components/super-lobster/__tests__/BrainSelectorPopover.test.tsx`
- Modify: `apps/web/src/components/super-lobster/MessageInput.tsx`
- Modify: `apps/web/messages/zh.json` + `en.json`（追加 `workspace.chat.brainSelector`）

**Interfaces:**
- Consumes: `getZclawRagflowCapabilityApi` 的 capability 状态（决定知识库大脑项是否禁用）
- Produces: 替换原 `onOpenKnowledgeGraph` 触发器行为，改为打开 popover

- [ ] **Step 1: 追加 i18n**

`apps/web/messages/zh.json` 的 `workspace.chat` 下追加：

```json
"brainSelector": {
  "title": "选择大脑",
  "knowledgeBase": {
    "label": "知识库大脑",
    "description": "打开个人/团队知识图谱浏览器",
    "disabled": "知识库能力未启用"
  },
  "relationship": {
    "label": "组织关系大脑",
    "description": "工作主线 · 协同 · 风险图谱"
  }
}
```

`en.json` 对称。

- [ ] **Step 2: 写 BrainSelectorPopover 测试（失败）**

`apps/web/src/components/super-lobster/__tests__/BrainSelectorPopover.test.tsx`：

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import BrainSelectorPopover from '../BrainSelectorPopover';

describe('BrainSelectorPopover', () => {
  it('renders both items', () => {
    render(<BrainSelectorPopover open onOpenKnowledgeBase={() => {}} onClose={() => {}} ragflowCapabilityEnabled />);
    expect(screen.getByText(/知识库大脑/)).toBeInTheDocument();
    expect(screen.getByText(/组织关系大脑/)).toBeInTheDocument();
  });

  it('calls onOpenKnowledgeBase when knowledge base item clicked', () => {
    const onOpen = vi.fn();
    render(<BrainSelectorPopover open onOpenKnowledgeBase={onOpen} onClose={() => {}} ragflowCapabilityEnabled />);
    fireEvent.click(screen.getByText(/知识库大脑/));
    expect(onOpen).toHaveBeenCalled();
  });

  it('disables knowledge base item when capability is off', () => {
    render(<BrainSelectorPopover open onOpenKnowledgeBase={() => {}} onClose={() => {}} ragflowCapabilityEnabled={false} />);
    const kbItem = screen.getByText(/知识库大脑/).closest('button');
    expect(kbItem).toBeDisabled();
  });
});
```

- [ ] **Step 3: 实现 BrainSelectorPopover**

`apps/web/src/components/super-lobster/BrainSelectorPopover.tsx`：

```tsx
'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { BookOpen, Network } from 'lucide-react';
import React from 'react';

export interface BrainSelectorPopoverProps {
  open: boolean;
  onOpenKnowledgeBase: () => void;
  onClose: () => void;
  ragflowCapabilityEnabled: boolean;
}

export default function BrainSelectorPopover({
  open,
  onOpenKnowledgeBase,
  onClose,
  ragflowCapabilityEnabled,
}: BrainSelectorPopoverProps) {
  const t = useTranslations('workspace.chat.brainSelector');
  const router = useRouter();
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousedown', handleClickOutside);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={containerRef}
      className="absolute bottom-full left-0 z-50 mb-2 w-72 rounded-lg border bg-card p-2 shadow-lg"
      role="menu"
    >
      <div className="px-2 py-1 text-xs font-medium text-muted-foreground">{t('title')}</div>
      <button
        type="button"
        role="menuitem"
        disabled={!ragflowCapabilityEnabled}
        onClick={onOpenKnowledgeBase}
        className="flex w-full items-start gap-3 rounded-md px-2 py-2 text-left hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
      >
        <BookOpen className="mt-0.5 h-4 w-4 text-primary" />
        <div className="flex-1">
          <div className="text-sm font-medium">{t('knowledgeBase.label')}</div>
          <div className="text-xs text-muted-foreground">
            {ragflowCapabilityEnabled
              ? t('knowledgeBase.description')
              : t('knowledgeBase.disabled')}
          </div>
        </div>
      </button>
      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onClose();
          router.push('/digital-brain/relation');
        }}
        className="flex w-full items-start gap-3 rounded-md px-2 py-2 text-left hover:bg-accent"
      >
        <Network className="mt-0.5 h-4 w-4 text-primary" />
        <div className="flex-1">
          <div className="text-sm font-medium">{t('relationship.label')}</div>
          <div className="text-xs text-muted-foreground">{t('relationship.description')}</div>
        </div>
      </button>
    </div>
  );
}
```

- [ ] **Step 4: 跑测试**

```bash
cd apps/web && pnpm test -- super-lobster/__tests__/BrainSelectorPopover.test.tsx
```

期望 PASS。

- [ ] **Step 5: 接入 MessageInput**

编辑 `apps/web/src/components/super-lobster/MessageInput.tsx`：

1. 追加导入：

```tsx
import BrainSelectorPopover from './BrainSelectorPopover';
```

2. 追加 props（在 `MessageInputProps` 接口中）：

```tsx
ragflowCapabilityEnabled?: boolean;
```

3. 替换原芯片行为（行 992-1003 附近）：

原：

```tsx
{onOpenKnowledgeGraph ? (
  <ToolChip
    icon={Brain}
    label={t('knowledgeGraph')}
    active={false}
    disabled={isComposerLocked}
    onClick={() => {
      setActiveTool(null);
      onOpenKnowledgeGraph();
    }}
  />
) : null}
```

改为：

```tsx
{(onOpenKnowledgeGraph || ragflowCapabilityEnabled !== undefined) ? (
  <div className="relative">
    <ToolChip
      icon={Brain}
      label={t('knowledgeGraph')}
      active={brainSelectorOpen}
      disabled={isComposerLocked}
      onClick={() => {
        setActiveTool(null);
        setBrainSelectorOpen((v) => !v);
      }}
    />
    <BrainSelectorPopover
      open={brainSelectorOpen}
      onOpenKnowledgeBase={() => {
        setBrainSelectorOpen(false);
        onOpenKnowledgeGraph?.();
      }}
      onClose={() => setBrainSelectorOpen(false)}
      ragflowCapabilityEnabled={ragflowCapabilityEnabled ?? true}
    />
  </div>
) : null}
```

4. 在组件顶部追加状态：

```tsx
const [brainSelectorOpen, setBrainSelectorOpen] = React.useState(false);
```

- [ ] **Step 6: 在父组件传入 ragflowCapabilityEnabled**

在 `apps/web/src/components/super-lobster/SuperLobsterPage.tsx` 中，找到渲染 `<MessageInput>` 的位置，追加：

```tsx
ragflowCapabilityEnabled={ragflowCapability?.enabled ?? false}
```

`ragflowCapability` 来自现有的 `getZclawRagflowCapabilityApi` 调用（在 `ZclawWorkspaceSidebar` 或父组件已有）。如父组件没有，从 `ZclawWorkspaceSidebar` 中提取 capability 状态到共享 hook（或直接从父组件再次调用）。最小改动：在 SuperLobsterPage 中新增一个 `useRagflowCapability()` 调用。

- [ ] **Step 7: 跑全量回归**

```bash
cd apps/web && pnpm test
```

期望全部 PASS，特别是：

- `MessageInput.knowledge-graph.test.tsx` 仍通过（原行为由 `onOpenKnowledgeGraph` 触发，现在改为 popover，测试需按新行为调整）
- 新增的 `BrainSelectorPopover.test.tsx` 通过

若 `MessageInput.knowledge-graph.test.tsx` 因行为变化失败，按新行为更新测试：点击芯片 → 弹出 popover → 点击"知识库大脑" → 触发 `onOpenKnowledgeGraph`。

- [ ] **Step 8: 提交**

```bash
git add apps/web/src/components/super-lobster/BrainSelectorPopover.tsx \
        apps/web/src/components/super-lobster/__tests__/BrainSelectorPopover.test.tsx \
        apps/web/src/components/super-lobster/MessageInput.tsx \
        apps/web/src/components/super-lobster/SuperLobsterPage.tsx \
        apps/web/src/components/super-lobster/__tests__/MessageInput.knowledge-graph.test.tsx \
        apps/web/messages/zh.json \
        apps/web/messages/en.json
git commit -m "feat(digital-brain): brain selector popover on MessageInput chip"
```

---

## Task 11: 全量回归 + 端到端验收

**Files:** 无新文件；仅修复本任务发现的回归问题

**Interfaces:**
- Consumes: 全部已交付任务
- Produces: 验收清单 8 项全部通过

- [ ] **Step 1: 全量测试**

```bash
cd apps/web && pnpm test
```

期望全部 PASS。任何失败 → 在对应任务文件内修复。

- [ ] **Step 2: 类型检查**

```bash
cd apps/web && pnpm tsc --noEmit
```

期望 PASS。

- [ ] **Step 3: 逐项验收（后端前置就位前提下）**

按设计文档 §11 验收清单逐项手动验证：

1. **侧边栏现状保持**：侧边栏**无**"数字大脑"顶级入口（与现状一致）；工作台侧边栏内 2 张知识库状态卡（"个人知识库大脑"/"团队知识库大脑"）仍正常显示
2. **知识库大脑卡**：两张卡状态、进度、按钮（构建/取消/删除）与现状一致；活跃状态 1s 轮询正常
3. **全屏浏览器**：点击状态卡上的"打开浏览器"按钮 → ECharts 弹出 → 节点/边交互正常 → 右键节点"就该节点提问" → 跳转 `/` 且聊天输入框自动带入节点上下文
4. **组织关系大脑唯一入口**：输入框芯片点击 → 弹出选择器 → 点击"🕸 组织关系大脑" → 跳转 `/digital-brain/relation`；全功能可用（5 视角切换、筛选、节点/边详情、证据、AI 上下文、问答含历史、风险、评审、增量/全量重建、摘要共享）
5. **Deep link**：`/relations` 直接可访问（与 `/digital-brain/relation` 渲染同内容）；`/admin/relation-compute` 三层鉴权生效（非管理员无法访问）
6. **芯片选择器**：知识库大脑 / 组织关系大脑两项均正确；ragflow 能力关闭时知识库大脑项置灰
7. **i18n 层级**：zh/en 文案中"数字大脑"仅用于芯片名（代表容器）；其他处（状态卡、Explorer、toast、adminHome 卡片）已改为"知识库大脑"
8. **端到端**：发起一次会话 → 触发投影任务 → 构建完成 → 在组织关系大脑中可查看到对应节点和边

- [ ] **Step 4: 修复发现的问题**

如发现问题，定位到对应任务文件修复并提交（一个 commit 对应一个修复点）。

- [ ] **Step 5: 最终提交（如有修复）**

```bash
git commit -m "fix(digital-brain): post-integration regression fixes"
```

- [ ] **Step 6: 完成**

所有 11 个任务交付完成。设计文档验收清单全部通过。
