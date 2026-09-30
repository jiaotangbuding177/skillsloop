# 数字大脑聚合：关系空间前端移植设计

> 日期：2026-08-26
> 状态：设计完成，待实施
> 范围：**仅前端**
> 上游：`feature/relation-space-workstream-risk` 分支（克隆于 `.tmp/insightweaver`）

## 1. 背景

主工作区已有基于 ragflow 的知识图谱功能，代码/文案中称为**"数字大脑"**（个人数字大脑 = 个人知识图谱，团队数字大脑 = 企业知识图谱）。入口分布在工作台侧边栏状态卡、全屏 `KnowledgeGraphExplorer` 弹窗、`MessageInput` 芯片等处，没有独立页面容器。

新分支新增了**关系空间**（relation-space）前端：独立路由 `/relations`，包含 5 视角图谱（工作主线全景 / 跨组协同 / 工作重叠 / 部门图谱 / 个人局部图）、工作主线人工评审、企业图谱构建、会话摘要、风险分析、图谱问答（含历史）、证据查看、AI 上下文导出、产物预览等完整功能；管理端有 `/admin/relation-compute` 配置页。

本设计将关系空间移植为主工作区的**"组织关系大脑"**子模块，与现有**"知识库大脑"**（现有数字大脑功能的重新命名）并列于新的**"数字大脑"聚合页**下，建立清晰的层级：

```
数字大脑（容器，聚合页）
├── 知识库大脑 = 现有 ragflow 知识图谱（功能不变，仅重命名与入口收拢）
└── 组织关系大脑 = 新移植的关系空间（完整功能）
```

## 2. 关键决策（已通过）

| 决策点 | 结论 |
|---|---|
| 容器形态 | **聚合页**：顶级导航"数字大脑"，页内 tab 切换 |
| 输入框芯片 | **单芯片 + 选择器**：芯片名"数字大脑"，点击弹 popover 选知识库/组织关系 |
| 代码组织 | **方案 A：原样移植 + 硬编码双 tab**（保持文件级对应，便于上游同步） |

## 3. 信息架构与路由

### 3.1 路由（`[locale]/(zclaw-shell)/` 下）

| 路由 | 状态 | 内容 |
|---|---|---|
| `/digital-brain` | 新增 | 重定向到 `/digital-brain/knowledge` |
| `/digital-brain/knowledge` | 新增 | 聚合页 layout（头部 + tab 栏）+ 知识库大脑内容 |
| `/digital-brain/relation` | 新增 | 聚合页 layout + 组织关系大脑内容 |
| `/relations` | 新增（不入导航） | 薄包装页，渲染 `ZclawRelationSpacePage`，兼容上游分支深链接 |
| `/admin/relation-compute` | 新增 | 关系计算服务配置页（admin-only） |

Tab 切换使用子路由（非 in-page 状态），支持深链接与组件状态保持。

### 3.2 导航

**用户侧：没有顶级导航入口**（参考现状：知识库大脑也没有顶级导航入口，唯一入口是输入框芯片）。

- `ZclawShell.tsx` **不新增**"数字大脑"顶级按钮
- 侧边栏工作台区的 2 张知识库状态卡保留（作为工作台内的上下文操作区，不算"入口"）
- 组织关系大脑的**唯一用户侧入口** = 输入框芯片选择器（第 5 节）

**管理端 (`zclaw-admin-nav.ts`)**

```
企业知识图谱（现有，不动）
  ├─ 图谱配置 /admin/ragflow
  └─ 图谱任务 /admin/ragflow/jobs
关系计算服务 ▸ 新增 (/admin/relation-compute)
```

`RELATION_COMPUTE_NAV` 仅 `canAccessManagementBackend` 分支可见。

### 3.3 术语重命名

**仅改 i18n 值，不改 key / 代码标识符**（最小化代码差异）：

- 侧边栏状态卡标题："个人数字大脑" → "个人知识库大脑"、"团队数字大脑" → "团队知识库大脑"
- `KnowledgeGraphExplorer` 弹窗标题、个人/团队 tab 标签、相关 toast、`adminHome.cards.enterpriseVectorKb` 文案
- 输入框芯片名 **保持"数字大脑"不变**（现在代表容器）

## 4. 聚合页内部结构

### 4.1 知识库大脑 Tab（`/digital-brain/knowledge`）

```
┌─────────────────────────┬─────────────────────────┐
│ 📗 个人知识库大脑           │ 📘 团队知识库大脑          │
│ [状态徽章] 进度 68%        │ [状态徽章] 已完成          │
│ 详情文案…                 │ 详情文案…                │
│ [构建/更新] [取消] [删除]   │ [查看] [更新] [删除]      │
└─────────────────────────┴─────────────────────────┘
        [ 📖 打开全屏图谱浏览器 ]  ← 主按钮
```

- 两张卡**复用现有 `KnowledgeGraphStatusPanel`** 组件，行为与侧边栏卡片一致（活跃状态 1s 轮询、构建/取消/删除）；团队卡仍仅在有活跃企业时显示
- **关键重构**：把 `ZclawWorkspaceSidebar` 的 `loadGraphStatuses` / `runGraphStatusMutation` 状态逻辑抽出为共享 hook `useKnowledgeGraphStatuses`，侧边栏与聚合页共用
- 能力开关：`getZclawRagflowCapabilityApi` 关闭时显示与现有逻辑一致的禁用态

**跨页桥接**（节点提问场景）：
当 Explorer 从聚合页打开，点击"就该节点提问"时：

1. 上下文写入 `sessionStorage`（key：`pendingGraphNodeContext`）
2. `router.push('/')` 跳工作台
3. `SuperLobsterPage` 挂载时读取并恢复 `pendingGraphNodeContext`
4. 聊天照常继续

`SuperLobsterPage` 需增加挂载时的读取逻辑（约几十行）。

### 4.2 组织关系大脑 Tab（`/digital-brain/relation`）

完整渲染 `ZclawRelationSpacePage`，**不做任何删减或改版**：

- 5 视角：工作主线全景 / 跨组协同 / 工作重叠 / 部门图谱 / 个人局部图
- 筛选工具栏（跳数 / 密度 / 类型 / 来源 / 搜索）
- 节点 / 边详情抽屉、证据查看、AI 上下文导出、产物预览
- 图谱问答弹窗（含历史）、风险分析弹窗
- 工作主线人工评审（确认 / 否决 / 改名 / 合并 / 拆分）
- 企业图谱构建覆盖率 + 增量 / 全量重建
- 会话摘要生成与共享到组织
- 企业上下文：`x-enterprise-id` 头透传；无企业时回退个人视角

### 4.3 侧边栏现状保持

工作台左侧知识库区两张卡片不动（与聚合页共享同一状态逻辑）。

## 5. 输入框芯片选择器

- **触发器**：`MessageInput` 工具条芯片，名称"数字大脑"（Brain 图标）
- **始终显示**（组织关系大脑无需能力开关）
- **Popover 内容**：
  - 📚 **知识库大脑** → 调现有 `onOpenKnowledgeGraph()`，行为零变化
  - 🕸 **组织关系大脑** → `router.push('/digital-brain/relation')`
- 知识库大脑条目在 ragflow 能力关闭时**置灰**并附说明文案
- Esc / 点击外部关闭
- i18n：新增 `workspace.chat.brainSelector`（标题、两项名称与描述、禁用说明）

## 6. 管理端配置页

`/admin/relation-compute` 完整移植上游：

- **表单**：服务 URL、API Key（掩码）、请求超时（ms）、启用 / 停用
- **操作**：保存、测试连接
- **健康状态展示**：协议版本、Release SHA、模型、capabilities、上次检查时间、最近错误
- **权限三层守卫**：页内 `user.role !== 'admin'` 重定向 + `ZclawShell` admin 路由守卫 + 后端 `AdminGuard`

## 7. 移植清单

### 7.1 原样复制（上游 → 主工作区，文件级对应）

| 文件 | 说明 |
|---|---|
| `app/[locale]/(zclaw-shell)/relations/page.tsx` | 薄包装页 |
| `app/[locale]/(zclaw-shell)/admin/relation-compute/page.tsx` | 配置页（含三层权限守卫） |
| `components/zclaw/ZclawRelationSpacePage.tsx` | 主容器（1621 行） |
| `components/relation-space/RelationGraphView.tsx` | 手写 SVG 图谱（1737 行，零第三方依赖） |
| `components/relation-space/ArtifactPreviewDialog.tsx` + `artifact-preview.ts` | 产物预览 |
| `api/moudles/relation-space.ts` | API 层（443 行，19 个函数 + 全部类型） |
| `RelationGraphView.test.ts` | 图谱单元测试 |
| `RelationGraphView.interaction.test.tsx` | 图谱交互测试 |
| `artifact-preview.test.ts` | 产物匹配测试 |
| `relation-space.test.ts` | API 层测试 |
| `zclaw-admin-nav.test.ts`（新增用例） | 管理导航测试 |

### 7.2 修改主工作区现有文件

| 文件 | 修改内容 |
|---|---|
| `api/moudles/zclaw.ts` | 追加 compute 配置 API 三件套（`get/save/testAdminRelationComputeConfigApi`）+ 类型 |
| `api/index.ts` | `export *` 新增 relation-space 模块 |
| `lib/zclaw-admin-nav.ts` | 新增 `RELATION_COMPUTE_NAV`（仅平台管理员分支） |
| `components/zclaw/ZclawShell.tsx` | `secondaryNavItems` 增加"数字大脑"项 + `/admin/relation-compute` 纳入 admin 路由守卫 |
| `messages/zh.json` + `en.json` | 新增 `workspace.pages.relationSpace` 整块（264 key）+ `workspace.digitalBrain` + `workspace.chat.brainSelector` + `nav.shell.digitalBrain/relationSpace/relationCompute`；知识图谱相关文案值"数字大脑"→"知识库大脑" |
| `ZclawWorkspaceSidebar.tsx` | 图谱状态逻辑抽出为 `useKnowledgeGraphStatuses` hook（**等价重构**，现有测试兜底） |
| `SuperLobsterPage.tsx` | 挂载时读取 sessionStorage 恢复 `pendingGraphNodeContext` |
| `MessageInput.tsx` | 芯片行为改为打开大脑选择器 |

### 7.3 新增文件

- `app/[locale]/(zclaw-shell)/digital-brain/layout.tsx`
- `app/[locale]/(zclaw-shell)/digital-brain/knowledge/page.tsx`
- `app/[locale]/(zclaw-shell)/digital-brain/relation/page.tsx`
- `app/[locale]/(zclaw-shell)/digital-brain/page.tsx`（redirect）
- `hooks/useKnowledgeGraphStatuses.ts`
- 大脑选择器组件（popover）

### 7.4 条件移植（实施时验证）

- `lib/enterprise-context.ts`（`withActiveEnterpriseHeader`）
- `hooks/useActiveEnterpriseSpace.ts`

主工作区已有活跃企业概念（团队大脑依赖 `activeEnterpriseId`），但文件组织可能不同；缺失则连同移植，已有则适配。

### 7.5 npm 依赖

**零新增**。图谱为手写 SVG；`lucide-react`/`sonner`/`next-intl` 均为现有依赖。

## 8. 边界（明确不做）

- 不新增后端已有但上游前端未用接口的 UI：`/relation-space/path`、`/timeline`、投影任务管理 admin API（与上游保持一致）
- 不做组织关系大脑的聊天侧集成（问答保持上游页内弹窗形态）
- 不新增权益 / 计费开关，沿用上游"登录即可用 + 企业维度隔离"

## 9. 前置条件（非本次前端范围）

前端功能全量可用依赖以下后端 / 数据就位（本设计文档列为验收前置）：

1. `apps/api` 移植 `relation-space` 模块（4 组 controller + 投影管道 + 调度器）
2. `packages/relation-contract` + `apps/relation-compute` 服务
3. Prisma 迁移：11 个 `Relation*` 模型（`RelationNode` / `RelationEdge` / `RelationEvidence` / `RelationSessionDigest` / `RelationAnalysisSnapshot` / `RelationQuestionHistory` / `RelationWorkstreamReview` / `RelationProjectionJob` / `RelationProjectionCheckpoint` / `RelationMemorySnapshot` / `RelationComputeConfig`）
4. compute 服务部署 + 环境变量（或管理页在线配置）
5. 数据源已具备：evomind 会话（`zclawSession`）与 ragflow 图谱（知识库大脑自身）在主工作区均已存在，投影管道可工作

## 10. 测试策略

### 10.1 移植测试

`RelationGraphView.test.ts`、`RelationGraphView.interaction.test.tsx`、`artifact-preview.test.ts`、`relation-space.test.ts`、admin-nav 用例原样运行。

### 10.2 新测试

- 聚合页：默认重定向、tab 子路由切换与高亮
- `useKnowledgeGraphStatuses` hook：等价迁移现有侧边栏状态逻辑的断言
- 大脑选择器：渲染 / 跳转 / 能力关闭时禁用态
- 跨页桥接：`sessionStorage` 写入 → `SuperLobsterPage` 挂载恢复
- `zclaw-admin-nav.test.ts` 更新：`RELATION_COMPUTE_NAV` 仅平台管理员可见

### 10.3 回归

现有知识图谱全部测试（`KnowledgeGraphExplorer.permissions`、`KnowledgeGraphStatusPanel`、`MessageInput.knowledge-graph` 等）零失败。

## 11. 验收清单

1. 侧边栏**无**"数字大脑"顶级入口（与现状一致）；工作台侧边栏内 2 张知识库状态卡（"个人知识库大脑"/"团队知识库大脑"）仍正常显示
2. 知识库大脑卡片行为与现状一致（构建 / 取消 / 删除 / 1s 轮询）
3. 全屏浏览器交互不变；"就该节点提问" → 跳工作台并恢复上下文继续聊天（桥接）
4. **组织关系大脑唯一用户侧入口**：输入框芯片选择器 → "🕸 组织关系大脑" → `/digital-brain/relation`；全功能可用：5 视角、筛选、节点 / 边详情、证据、AI 上下文、问答（含历史）、风险、评审、增量 / 全量重建、摘要共享
5. `/relations` 深链接可用；`/admin/relation-compute` 三层鉴权生效（仅平台管理员）
6. 芯片选择器两入口正确；无企业上下文时组织关系大脑回退个人视角；ragflow 能力关闭时知识库大脑项置灰
7. zh / en 文案命名体系符合"数字大脑 → 知识库大脑 / 组织关系大脑"层级（芯片保持"数字大脑"代表容器）
8. 第 9 节后端前置就位后，端到端走通一次"会话 → 投影 → 构建 → 视图"链路

## 12. 实施顺序（供 plan 阶段参考）

① API 层 + i18n 块移植（无 UI 变化）
→ ② 关系空间组件 + `/relations` + `/admin/relation-compute` 页（功能可用但未入导航）
→ ③ hook 抽取 + 聚合页 + 导航 + 重命名
→ ④ 跨页桥接 + 芯片选择器
→ ⑤ 全量回归

## 附录 A：数据流回顾

- **存储**：全部在主平台 PostgreSQL（`relation_*` 表），compute 服务无状态
- **增量**：变更扫描器 + 投影任务队列 + 检查点游标幂等 upsert 三张事实表（`RelationNode` / `RelationEdge` / `RelationEvidence`）
- **视图**：5 个前端视角共享同一个 `GET /relation-space/subgraph` 查询结果，客户端过滤渲染；**视图无独立存储**
- **compute 服务**：仅两个端点 `/health` 与 `/complete`，本质是带鉴权与版本校验的 LLM 调用代理

## 附录 B：上游相关代码清单

**上游（`.tmp/insightweaver`）核心路径：**

- `apps/web/src/app/[locale]/(zclaw-shell)/relations/`
- `apps/web/src/app/[locale]/(zclaw-shell)/admin/relation-compute/`
- `apps/web/src/components/zclaw/ZclawRelationSpacePage.tsx`
- `apps/web/src/components/relation-space/`（RelationGraphView、ArtifactPreviewDialog、artifact-preview）
- `apps/web/src/api/moudles/relation-space.ts`
- `apps/web/src/lib/zclaw-admin-nav.ts`（RELATION_COMPUTE_NAV）
- `apps/web/src/components/zclaw/ZclawShell.tsx`（secondaryNavItems 与 admin 入口）
- `apps/web/messages/zh.json` + `en.json`（`workspace.pages.relationSpace` 整块）
- `apps/api/src/relation-space/`（后端模块，前端移植的依赖对象）
- `apps/relation-compute/` + `packages/relation-contract/` + `deploy/relation-compute/`
