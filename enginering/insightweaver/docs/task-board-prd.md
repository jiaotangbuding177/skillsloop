# 任务看板功能 PRD（InsightWeaver 适配版）

> 版本：v2.1 ｜ 日期：2026-09-08 ｜ 状态：待评审
> 参考输入：`D:\doc-w\evomind\任务看板\任务看板功能PRD.md`（multica 体系逆向结论）；multica 源码 `D:\ai-project\multica`（本版已抽查核实 7 项论断）
> 适配对象：InsightWeaver —— NestJS 11 (ESM) + Prisma 6 + Next.js 16 App Router + next-intl (zh/en) + PostgreSQL 远程 RDS
> 现状基础：feature/20260908/task-board 分支已提交 v1（`c5d713ee`），本 PRD 为 v1 的重设计，**非新增**
>
> v2.1 变更（2026-09-08 架构评审）：取消语义从 isCanceled 布尔改为**隐藏列方案**（D7/D11 重写）；冲突模型从纯 LWW 改为 **expectedRevision + 409**（D10 重写）；聚合接口含已取消卡片（B1 消解）；隐藏列可见性规则（F1）；dueDate 用 @db.Date（F2）；拖拽落点按 v1 真实算法重写（F3）；迁移补数据清理与完整流程（F4）；常量收敛 shared（F5）；工作量修正（F6）；PM 补充五条（§6.6）。

---

## 1. 背景与目标

### 1.1 背景

当前分支已落地一版任务看板（`/tasks` 页面 + `/api/tasks` 接口），但体验表现为「把 demo 嵌入了一样」：功能只覆盖「放卡片、挪卡片」，核心交互链路不完整。本 PRD 在参考 multica 任务看板能力模型之上，按 InsightWeaver 的组织架构（Enterprise → EnterpriseMembership，无 workspace/部门实体）与前后端语言（NestJS/Prisma/Next.js）重新设计，目标是交付一个**业务闭环**的任务看板，而非 demo。

### 1.2 v1 现状与 demo 感诊断

| 问题 | 现状 | 后果 |
| --- | --- | --- |
| 字段假 | `agent`/`tags`/`project`/`attachments` 为硬编码（`小智`/`小研`、固定 5 标签、固定项目、附件只有文件名） | 卡片看起来「有完整字段」，实际是假数据 |
| 拖拽弱 | 仅跨列移动，**无列内排序**；无乐观更新；无冲突保护 | 拖拽不成系统，刷新即原样 |
| 交互缺 | 无详情面板、无截止日期、无空态引导、无筛选器、删除无二次确认 | 卡片点了只能弹不够用的 modal |
| 闭环断 | 无「取消」语义、无 revision、无分页上限 | 任务生命周期不完整，「完成」后无出口 |
| 数据层 | 手动 `abortRef` + `useState` 每次全量重拉 | 与全站无数据层规范，无法复用 |

### 1.3 目标

| # | 目标 | 说明 |
| -- | -- | -- |
| G1 | **闭环** | 创建 → 指派 → 拖拽推进（列内序 + 跨列）→ 完成 / 取消 → 删除，全链路可操作、可持久化、可刷新还原 |
| G2 | 去 demo 化 | 字段全部为真实业务含义；硬编码 agent/标签/项目移除 |
| G3 | 交互完整 | 详情面板、截止日期、列表行内编辑、筛选、加载/空态、删除二次确认（六件套） |
| G4 | 架构一致 | 遵循 CLAUDE.md 分层规范；引入 React Query 作为全站数据层标准（看板模块为第一个改造者） |
| G5 | 企业边界 | 一企业一板；列配置权限收紧为管理员（`role in (admin, owner, enterprise_admin)`） |

### 1.4 非目标（本版明确不做）

- ❌ WebSocket 实时同步、操作日志、评论、标签体系、附件上传（二期候选）
- ❌ 服务端筛选/分页（保留聚合接口 + 前端筛选；数据量 >1000 时二阶段升级）
- ❌ 标题/描述全文搜索（multica 有 trgm 搜索；一期不做，显式排除防范围蔓延）
- ❌ 多板（部门/项目维度板；表结构已留 `boardId`，平滑扩展）
- ❌ agent / 智能体参与执行（agent 编排是另一条产品线）
- ❌ 自定义状态目录（二期若需要，按 multica `issue_status` 的 key/category 模式演进；本版「隐藏列取消方案」为该演进保留了单轴状态模型，见 §4.4）

---

## 2. 已确认决策记录

| # | 决策 | 结论 |
| -- | -- | -- |
| D1 | 定位 | 企业成员协作任务管理；删除硬编码 agent/标签/项目 |
| D2 | 状态列 | 保留配置化列模型；播种 **6 列**：planning/todo/doing/review/done + **canceled（默认 hidden=true）**；看板正常展示 5 列 |
| D3 | 看板粒度 | 一企业一板（TaskBoard.enterpriseId @unique 保留） |
| D4 | 交付物 | PRD + 分期实施计划（P0/P1），评审通过即排期 |
| D5 | 前端数据层 | 引入 `@tanstack/react-query`；Provider 铺全站，仅看板模块改造 |
| D6 | 闭环交互 | 详情面板 / 截止日期 / 列表行内编辑 / 筛选 / 空态与骨架屏 / 删除与清空二次确认（全部 P0） |
| D7 | 字段清理 | schema 删除 `agent`、`tags`、`project`、`attachments`；新增 `dueDate`（@db.Date）、`revision`。~~isCanceled/canceledAt~~（v2.1 取消语义改走列方案，不再新增这两个字段） |
| D8 | 列配置权限 | 列改名/隐藏/清空 = 管理员专属（`role in (admin, owner, enterprise_admin)`）；卡片 CRUD = 全体 active 成员 |
| D9 | 数据拉取 | 保留 `GET /tasks/board` 聚合（**含已取消卡片**，前端按列过滤），筛选前端做；服务端分页二阶段 |
| D10 | 冲突策略 | **expectedRevision + 409**（v2.1 重写）：PATCH 携带可选 `expectedRevision`；服务端不匹配回 409（与 multica `handler/issue.go:3366` 同模型）；前端 409 → toast「已被他人修改」+ 重拉该卡。无 WS 的一期里，滞留窗口越长并发覆盖风险越高，静默 LWW 与闭环目标冲突 |
| D11 | 取消语义 | **取消 = 流转到 canceled 列**（拖入或详情面板选择）；恢复 = 流转出该列；canceled 列默认隐藏（管理员可在列设置中开启显示）。~~isCanceled 布尔~~ |
| D12 | 工程门槛 | 新增接口/组件补测试；`pnpm lint` + `pnpm --filter @insightweaver/web build` 为门禁 |

---

## 3. 名词与约定

| 名词 | 含义 |
| --- | --- |
| 任务（task card） | 看板上最小工作单元，归属企业（enterprise） |
| 看板列 = 状态 | 播种 6 列：待规划 / 待办 / 进行中 / 审核中 / 已完成 / 已取消（canceled 默认隐藏；`columnKey` 机器句柄不变） |
| 已取消 | `columnKey === 'canceled'` 的任务；非独立状态轴 |
| 优先级 | `none / low / medium / high / urgent`（默认 none） |
| 位置 position | 列内排序键，Int，间隔 1024，`position ASC, seq ASC`；落位由服务端 `computePlacePosition` 决定（§6.3） |
| revision | 乐观锁版本号，创建 =1，每次写 +1 |

---

## 4. 数据模型

### 4.1 现状（保留）

- `TaskBoard`：一企业一板（`enterpriseId @unique`），保留
- `TaskColumnConfig`：列配置（`columnKey + name + hidden + sortOrder`），保留
- `TaskCard`：任务卡，改造（见 4.2）

### 4.2 TaskCard 迁移清单

```prisma
// 删除
agent        String?
tags         Json @default("[]")
project      String?
attachments  Json @default("[]")

// 新增
dueDate      DateTime? @db.Date   // 日期语义，免时区漂移；DTO 校验 @IsDateString()
revision     Int      @default(1) // 乐观锁，每次写 +1

// 保留（v2.1：不再新增 isCanceled / canceledAt）
id / boardId / seq / columnKey / position / title / description /
priority / assigneeUserId / createdByUserId / createdAt / updatedAt / isDeleted
```

索引不变：`[boardId, columnKey, position]` 保留；`revision` 不需索引。

### 4.3 权限模型

| 操作 | 允许者 |
| --- | --- |
| 卡片增删改（含拖拽、流转取消列） | 企业 **active** 成员（现有 `assertMembership`） |
| 列配置（改名/隐藏/清空） | 企业 active 成员且 `role in (admin, owner, enterprise_admin)` |
| 指派 | 仅限本企业 active 成员（现有 `assertAssigneeMember` 保留） |

> 实现注记：新增 `assertAdminMembership`；角色判断抽 `isAdminRole()` 工具，以三值集合为准（现有代码惯例：`zclaw.service.ts:2732` 用 `role === "admin" || role === "owner"`；`enterprise.service.ts:1666` 出现 `enterprise_admin`）。

### 4.4 取消语义的实现选择（v2.1 重写，架构评审结论）

取消走**隐藏列**而非 isCanceled 布尔，理由（与 multica 对照后的分叉决策）：

1. 本项目已有第一等状态轴（columnKey + hidden 配置），布尔是在旁边再造平行轴——状态分裂两个字段（E5 静默吞写守卫、「恢复回原列」撞位、聚合特殊过滤、筛选特殊分支，四类成本全部消失）。
2. 单轴模型与 multica `issue_status` 状态目录同构：multica 的 cancelled 本就是目录中的一列（category 7 值之一，`332_issue_status.up.sql` 已核实）；二期若上自定义状态目录，本方案零迁移成本，布尔方案要先合轴。
3. v1 已播种的 canceled 列配置行**不用迁走**，只删 discarded、其卡片软删（预发布数据量，无负担）。

视觉/产品口径不变：看板默认 5 列（D2），「已取消」通过列表视图 + 筛选可见，管理员可在列设置中临时开启 canceled 列显示。

**已知取舍**：取消时间点（原 canceledAt 语义）一期不记。若需要，二期加通用 `columnChangedAt DateTime?`（每次换列更新），比专用 canceledAt 用处更广，不阻塞本版。

### 4.5 迁移执行方案（远程 RDS，含数据清理）

CLAUDE.md 硬约束：远程库默认只启动服务、不执行迁移。完整流程：

1. 改 `schema.prisma`（§4.2）+ `packages/shared/src/task-board.ts`（TASK_COLUMN_KEYS 去掉 discarded、DEFAULT_TASK_COLUMNS 加 canceled hidden 语义）。
2. `pnpm db:generate` 生成本地客户端。
3. `prisma migrate dev --create-only`（shadow 库生成 SQL，**不落远程库**）。
4. 人工审阅生成的 SQL，追加**数据清理**（Prisma migrate 只管 schema，以下需手写在同一迁移内）：
   ```sql
   -- 数据清理 1：discarded 列的卡片软删
   UPDATE task_cards SET is_deleted = true WHERE column_key = 'discarded';
   -- 数据清理 2：discarded 列配置行软删（列配置表有 is_deleted，随 DDL 删行或软删均可，取软删）
   UPDATE task_column_configs SET is_deleted = true WHERE column_key = 'discarded';
   -- 数据清理 3：canceled 列默认隐藏
   UPDATE task_column_configs SET hidden = true WHERE column_key = 'canceled';
   -- 数据清理 4：新列回填
   UPDATE task_cards SET revision = 1, due_date = NULL;
   ```
5. 用户确认后 `prisma migrate deploy`（或 dev）执行。

### 4.6 常量收敛（防漂移）

`TASK_COLUMN_KEYS` / `TASK_PRIORITY_VALUES` / `DEFAULT_TASK_COLUMNS` 目前在 `packages/shared/src/task-board.ts` 与 `apps/web/src/components/task-board/constants.tsx` **双份维护**。P0 收敛：前端 constants 只保留 UI 专属物（列底色、图标、头像散列），枚举一律 `import { ... } from "@insightweaver/shared"`（后端 `ParseEnumPipe` 已用 shared，改完后两端同源）。改 7→6 列时只动 shared 一处。

---

## 5. 接口设计

### 5.1 接口一览（保留 v1 六端点，语义微调）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/tasks/board` | 聚合：board + columns + **cards（全部未软删，含 canceled 列卡片）** + members（含 role） |
| POST | `/api/tasks` | 创建（新增 dueDate；默认落 `todo` 列顶） |
| PATCH | `/api/tasks/:id` | 局部更新（新增 dueDate / expectedRevision 乐观锁） |
| DELETE | `/api/tasks/:id` | 删除（软删） |
| PATCH | `/api/tasks/board/columns/:columnKey` | 列改名/隐藏（管理员；取消列的隐藏可由管理员切换） |

### 5.2 语义变更

- **创建/更新 DTO 新增**：`dueDate?: string (YYYY-MM-DD) | null`（null = 清除）；`expectedRevision?: number`（仅更新）。
- **取消/恢复**：与其它跨列流转完全同一条路径——PATCH `{ columnKey: "canceled", expectedRevision }` 即取消；PATCH 回任何列即恢复，落位由服务端现算（拖到哪算哪，无「原位恢复」概念，撞位问题不存在）。
- **revision/409**：service 写入前比对 `expectedRevision !== card.revision` → 409（`{ code, message: 'task has been modified by someone else' }`）；写入 `revision + 1` 回传。前端 `onError` 判 409 → toast「任务已被他人修改，已刷新」+ invalidate 该卡。**不带 expectedRevision 的请求（如列表行内快速改优先级）仍走后写覆盖**——乐观锁是可选并发保护，不是强制门槛。
- **listMembers 返回**：增加 `role`（前端据此显示列设置入口）。
- **错误语义**：400 非法枚举/UUID/日期、403 非成员或非管理员（列配置）、404 跨企业/不存在、**409 revision 冲突**。

### 5.3 响应结构（TaskCardRecord 增量）

```json
{
  "id": "…", "seq": 12, "columnKey": "doing", "position": -1024,
  "title": "…", "description": "", "priority": "high",
  "assigneeUserId": null, "assigneeName": null,
  "dueDate": "2026-09-15", "revision": 3,
  "createdByUserId": "…", "createdAt": "…", "updatedAt": "…"
}
```

---

## 6. 前端设计

### 6.1 数据层改造（React Query 引入）

- 依赖：`@tanstack/react-query`（v5）。
- Provider：`QueryClientProvider` 置于 `apps/web/src/app/[locale]/(zclaw-shell)/layout.tsx`（后续可提至根 layout）。
- 模块化：`apps/web/src/api/queries/task-board.ts`——`taskBoardQueryKey` / `useTaskBoard`（单 query，key 含企业 id）/ `useCreateTaskCard` / `useUpdateTaskCard` / `useDeleteTaskCard` / `useUpdateColumn`。
- 乐观更新四段式（拖拽、行内编辑、删除）：`onMutate` 本地落位（**fire-and-forget `cancelQueries`，必须同步执行——借鉴 multica `mutations.ts:149`：await 会让出事件循环，dnd-kit 在乐观 patch 落地前重置视觉状态）→ `onError` 回滚 + toast（409 → 刷新该卡）→ `onSuccess` 服务端响应覆盖 → `onSettled` 兜底。数据源为单 query，以 `setQueryData` 就地 patch 为准，不整列 invalidate。
- `TaskBoardPage` 从手动 fetch + useState 迁移到上述 hooks；企业切换以 query key 维度隔离。

### 6.2 组件树

```
TaskBoardPage（客户端入口；useTaskBoard）
├── 页头：标题 ｜ 视图切换 [看板|列表] ｜ 筛选器 ｜ [+ 新建任务] ｜（管理员）[列设置]
├── BoardView（DndContext + DragOverlay；列内 SortableContext + 跨列；隐藏列不渲染、不可为拖拽目标）
│   └── BoardColumn ×5 可见（列头菜单：改名/隐藏/清空 —— 管理员可见）
│       └── BoardCard（列内可拖；点击开详情；截止日期逾期标红）
├── ListView（全部列的卡片含已取消；状态徽章/优先级行内下拉直接改；点行开详情）
├── TaskDetailPanel（右侧滑出 ~480px；全字段编辑；状态含 canceled；删除二次确认）
├── CreateTaskDialog（标题必填；Enter 提交；更多设置折叠；列头「+」预填列）
└── FilterBar（状态(可见列+已取消) × 优先级 × 负责人(含未指派)；chips + 清除全部）
```

**视图/筛选状态持久化**：视图切换（board/list）与筛选条件存 **URL searchParams**（`?view=list&status=canceled&assignee=…`），刷新/分享还原，不依赖 localStorage（v1 的 localStorage 显示偏好保留为辅助：紧凑模式等纯显示项）。

### 6.3 拖拽与落位规格（按 v1 真实算法重写）

本项目与 multica 的算法差异（均已核实源码）：

| 维度 | multica | InsightWeaver（保留 v1） |
| --- | --- | --- |
| position 类型 | float，中点 `(prev+next)/2`，端点 ±1（`drag-utils.ts:99`） | **Int，间隔 1024**，间隙耗尽整列重排（`task-board.position.ts:24`） |
| 落位决定方 | 客户端算好 position 传服务端 | 客户端传**期望落点** `requested`（邻卡中点/端点外推值），服务端 `computePlacePosition` 夹取、必要时重排 |

P0 规格不变的部分：dnd-kit PointerSensor（v1 用 4px、multica 用 5px——统一 **5px**）、DragOverlay、列内 SortableContext、跨列一次 PATCH（columnKey + 期望 position）、失败回滚 + toast。

落位契约：前端拖放结束 → 计算目标列目标槽位的 `requested`（取前后邻卡 position 中点，端点取 `first-1024`/`last+1024`）→ PATCH → 服务端夹取或整列重排（重排在事务内）→ 响应携带权威 position → 前端以响应为准校正。

### 6.4 隐藏列可见性规则（F1 补洞）

| 场景 | 行为 |
| --- | --- |
| 看板视图 | 隐藏列不渲染、不可为拖拽目标、列头计数不显示 |
| 列表视图 | 隐藏列的卡片**照常显示**（含已取消徽章），状态徽章标注列名 |
| 筛选器状态组 | 默认只列可见列 + 「已取消」快捷项；管理员开启 canceled 列显示后同普通列 |
| 拖拽 | 卡片拖到隐藏列的视觉区域 = 无效目标（droppable 未注册） |
| 新建 | 隐藏列不出现在状态选择器中（列头「+」只在可见列） |

### 6.5 i18n 键位清单（`taskBoard` 命名空间，zh.json + en.json 同步）

新增/修改键：`filters`（状态/优先级/负责人/未指派/清除全部）、`detail`（保存中/已保存/已被他人修改/删除/确认删除）、`columnSettings`（列设置/重命名/隐藏）、`dueDate`（截止日期/逾期/清除）、`emptyStates`（空列/全空引导/无匹配）、`confirm`、`permissionDenied`、`listView`（已取消徽章等）。

**列名翻译策略**：播种进 DB 的列名是中文值，英文用户会看到中文列名。前端按 `columnKey` 翻译已知列（`t(`columns.${columnKey}`)`）；仅当用户改过名（`name !== DEFAULT 之名`）时显示 DB 原值。判定「改过名」实现时用 shared 常量对照。

### 6.6 PM 补充（v2.1 评审新增）

1. **seq / 创建者 / 时间戳展示**：详情面板显示 `#seq`、创建人姓名、创建时间——协作产品起码的问责信息，零后端成本（字段已在响应里）。
2. **搜索显式排除**（已进 §1.4 非目标）。
3. **URL 持久化**（已进 §6.2）。
4. **列名 i18n**（已进 §6.5）。
5. **恢复/取消落位**：拖出 canceled 列 = 恢复，落位现算（无原位恢复），PRD §5.2 已定义。

---

## 7. 非功能需求

| 维度 | 要求 |
| --- | --- |
| 性能 | 聚合接口全量一次拉取（上限 1000 条，超限提示）；列内重排为单例更新（间隙耗尽才整列重排，重排在事务内） |
| 安全 | 所有查询带 board → enterprise 双条件；列配置管理员守卫；指派校验成员 |
| i18n | 新文案必进 zh/en；`pnpm --filter @insightweaver/web build` 为门禁（CLAUDE.md §13） |
| 工程 | 接口层无 try-catch 吞异常；Service 无 SQL 字符串；DTO 使用 class-validator |

---

## 8. 边界情况与验收标准

### 8.1 边界情况

| # | 场景 | 预期 |
| -- | -- | -- |
| E1 | 拖拽到已删任务旁 | 404 → 回滚 + toast |
| E2 | 并发拖拽同一任务（带 expectedRevision） | 409 → toast「已被他人修改」+ 刷新该卡 |
| E3 | 拖入空列（列内暂无卡片） | position 回落默认（0），正常落位 |
| E4 | dueDate 清除 | 传 `{ dueDate: null }` |
| E5 | 拖入/拖出 canceled 列 | 与普通跨列流转同路径，无特殊守卫 |
| E6 | 非管理员调列配置接口 | 403 + toast |
| E7 | 跨企业访问卡 id | 404 |
| E8 | 隐藏列卡片在列表视图 | 照常显示（§6.4） |
| E9 | 管理员清空 canceled 列 | 该列全部卡片软删（含已取消卡） |
| E10 | 间隙耗尽的列内插入 | 整列重排（事务内），相对顺序保持 |

### 8.2 验收标准（AC）

- [ ] AC1 看板展示 5 可见列，卡片按 position 正确排序，刷新后顺序保持
- [ ] AC2 列内拖拽可排序；点击与拖拽（5px 阈值）互不干扰
- [ ] AC3 跨列拖拽后状态变更，列表视图同步可见
- [ ] AC4 「新建任务」可创建，dueDate 可设可清；标题必填校验
- [ ] AC5 详情面板编辑全部字段即时生效（乐观更新 + 已保存提示）；显示 #seq/创建人/创建时间
- [ ] AC6 列表行内可改状态/优先级；已取消卡片在列表显示徽章
- [ ] AC7 筛选（状态/优先级/负责人）双视图生效；chips 可清除；URL 还原视图与筛选
- [ ] AC8 断网/接口失败时乐观变更回滚 + toast
- [ ] AC9 取消 = 流转到 canceled 列 → 看板（未开启显示时）消失、列表显示徽章；拖出即恢复
- [ ] AC10 非管理员不显示列设置入口；直调接口 403；删除/清空均有二次确认
- [ ] AC11 并发编辑同一卡片（带 expectedRevision）→ 后提交者收 409 并刷新
- [ ] AC12 `pnpm lint` 通过；`pnpm --filter @insightweaver/web build` 通过
- [ ] AC13 新增接口/核心 Hook 有测试；硬编码字段（agent/tags/project/attachments）全部移除；前端枚举只 import shared

---

## 9. 分期实施计划

### P0（约 5~7 人日，v2.1 修正——六件套 + 详情面板/筛选全为新写）

| 步骤 | 内容 | 预估 |
| --- | --- | --- |
| 1 | shared 常量收敛（7→6 列）+ schema 迁移（删 4 字段 + 加 2 字段 + 数据清理 SQL）+ `db:generate` | 0.5 日 |
| 2 | Service/Controller：dueDate、revision/409、管理员守卫、listMembers 带 role、隐藏列语义 | 1 日 |
| 3 | React Query 引入 + Provider + 模块 hooks（乐观更新四段式） | 1 日 |
| 4 | 前端闭环六件套（详情面板/截止日期/行内编辑/筛选/URL 持久化/空态/确认）+ 隐藏列规则 | 2~3 日 |
| 5 | i18n zh/en + 列名翻译策略 + lint + build + 测试 | 0.5~1 日 |

### P1（二期候选，另立 PRD）

- WebSocket 实时同步（revision 守卫直接复用 409 路径）；服务端筛选/分页（>1000 条）；评论/订阅；附件；标签体系；全文搜索；多板；agent 参与；自定义状态目录（multica issue_status 模式）；columnChangedAt。

---

## 附录 A：multica 参考核实记录（v2.1 评审）

| 论断 | 结论 | 证据 |
| --- | --- | --- |
| 状态目录 key/category 模型（cancelled 为目录列） | ✅ | `server/migrations/332_issue_status.up.sql` |
| `MIN(position)-1` 置顶 | ✅ | `server/internal/issueposition/position.go` |
| 中点算法 ±1 外推 | ✅ | `packages/views/issues/utils/drag-utils.ts:99-107` |
| 7 状态并行分页拉取 | ✅ | `packages/core/issues/queries.ts:246` |
| 乐观更新四段式 + onMutate 同步 cancelQueries | ✅（细节已抄入 §6.1） | `packages/core/issues/mutations.ts:149-156` |
| PointerSensor 阈值 8px | ⚠️ 实际 5px（本 PRD 统一 5px） | `board-view.tsx:508` |
| 「后写覆盖与参考一致」 | ❌ 参考项目实为 expectedRevision + 409（D10 已按此重写） | `handler/issue.go:3366-3376` |

## 附录 B：参考源码索引

| 主题 | 文件 |
| --- | --- |
| v1 后端 | `apps/api/src/task-board/{controller,service,dto,constants,position}.ts` |
| v1 前端 | `apps/web/src/components/task-board/*`；`apps/web/src/api/moudles/task-board.ts` |
| 数据模型 | `packages/db/prisma/schema.prisma` L2698-2753 |
| 共享常量 | `packages/shared/src/task-board.ts` |
| 组织模型 | `EnterpriseMembership`（schema L233，role L237） |
| multica 源码 | `D:\ai-project\multica` |
| multica 逆向 PRD | `D:\doc-w\evomind\任务看板\任务看板功能PRD.md` |
