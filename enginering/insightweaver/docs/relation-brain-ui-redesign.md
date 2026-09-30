# 关系大脑 3D 界面重设计（v2）

> 目标：以"大脑 3D 图"为视觉主体，移除全部筛选栏；右侧固定功能栏承载
> AI 关键洞察与统计、组织风险速览、向全图提问、人工校对关系四大能力；
> 新增「协作关系分析 / 重复工作分析」两种图模式——脑图切换到全部
> 协作/重叠节点点亮的子图，右侧展示完整洞察面板。
> 本文件为设计稿，尚未改代码。

---

## 1. 现状盘点（改造前）

### 1.1 当前页面结构（`ZclawRelationSpacePage` standalone 变体）

```
┌──────────────────────────────────────────────────────────────┐
│ Header：标题 + [风险分析] [向图提问] [审阅主线] [刷新]        │
├──────────────────────────────────────────────────────────────┤
│ Toolbar 行：时间线下拉 + 搜索 + 关系筛选 + 来源 + hops +      │
│            密度 + 产物/协作开关（3D 变体已隐藏大部分）        │
├──────────────────────────────────────────────────────────────┤
│ <details> 数据与图谱更新（折叠）：构建/覆盖率/更新按钮 +      │
│   协作关系计算 / 重复工作计算                                 │
├──────────────────────────────────────────────────────────────┤
│ Tab 行：宏观大图 | 个人脑图                                   │
├──────────────────────────────────────────────────────────────┤
│ Unity 3D 脑图画布（hover tooltip、双击聚焦、洞察卡片叠加）    │
├──────────────────────────────────────────────────────────────┤
│ 浮动层：节点详情 / 证据 / 风险弹窗 / 提问弹窗 / 校对弹窗 /    │
│         产物预览 / 构建确认                                    │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 已有能力（全部保留，仅重排）

| 能力 | 现状入口 | 数据源 |
|---|---|---|
| 时间线选取 | Toolbar 下拉 | `timeRange` + from/to 查询 |
| 宏观大图 / 个人脑图 | Tab | `projectMacroGraph` / 个人切片 |
| 双击节点洞察子图 | 图内 | 蒸馏 + 卡片 |
| 组织风险速览 | Header 按钮 → 右侧弹层 | `getRelationRiskAnalysisApi` |
| 向全图提问 | Header 按钮 → 弹窗 | `askRelationSpaceApi` |
| 人工校对关系 | Header 按钮 → 弹窗 | review API + coverage |
| 协作/重叠计算 | 「数据与图谱更新」内按钮 | `openEnterpriseBuild('incremental','collaboration'/'overlap')` |
| 覆盖率/构建进度 | 同上折叠区 | `enterprise-builds/coverage` |

---

## 2. 设计原则

1. **图谱唯一主角**：脑图画布占满主区，除右上角最小叠加控件外不再有横向工具栏。
2. **筛选即数据模式**：不做筛选器；用「时间线」+「图模式」表达视角变化。
3. **右栏是工作台**：所有"读图之外"的动作（洞察、风险、提问、校对、分析详情）收进右栏。
4. **两套"分析模式"是图模式，不是新页面**：协作分析 / 重复分析 = 同一画布上的特殊取景，
   复用同一套渲染管线与右侧面板骨架。
5. **降噪不删功能**：构建/覆盖率的运维型控件收敛到 Header 数据状态胶囊的弹层中。

---

## 3. 新布局（全屏）

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Header（薄条）：关系大脑        企业名          数据态●      [刷新]       │
├──────────────────────────────────────────────────────────────────────────┤
│ 模式与时间线横条（同级、可拖拽滚动）：                                    │
│   [宏观大图|个人脑图|协作分析|重复分析]     时间线：今天 昨天 近7天         │
│                                           近30天 本季 今年 全部（由近→远）│
├──────────────────────────────────────────┬───────────────────────────────┤
│                                           │  右侧功能栏 (w=400)          │
│          Unity 3D 大脑画布                │  ┌────────────────────────┐  │
│   · hover/双击/聚焦/卡片叠加 沿用          │  │ ① 洞察与统计(默认)     │  │
│   · 协作分析=协作组+其1跳关联全亮，其余压暗│  │ ② 组织风险速览         │  │
│   · 重复分析=重叠组+其1跳关联全亮，同上     │  │ ③ 向全图提问           │  │
│   · 待审阅组保持半透明虚线                │  │ ④ 人工校对关系(红点)   │  │
│  底部图例：协作青绿·重叠琥珀·半透明=待审阅  │  └────────────────────────┘  │
└──────────────────────────────────────────┴───────────────────────────────┘
```

### 3.1 层次与尺寸

| 区域 | 规格 |
|---|---|
| 画布 | `flex-1`，高度 100%（脑图 canvas 620px 默认，可全屏） |
| 右侧功能栏 | 固定 `w-[400px]`，顶部 5 个 tab（图标+文字），内容区可滚动，深色与画布一致的 glass 面板 |
| Header | 48-56px：仅企业名/数据态胶囊/刷新 |
| 模式+时间线横条 | Header 下方一条 `h-10`：左侧图模式分段胶囊，右侧时间线横条（横向可拖拽滚动） |

### 3.2 时间线横条（与 tab 同级）

- 由近到远排列：`今天 | 昨天 | 近7天 | 近30天 | 本季 | 今年 | 全部`（末尾可加"自定义…"弹层）
- 拖拽式横向滚动：`overflow-x-auto` + 鼠标按住拖拽/触摸滑动；超出可视宽度时自动露出滚动提示
- 选中态：蓝底白字胶囊；默认"全部"；选中非默认档位时在图例旁显示淡蓝色时间窗徽标
- 与图模式胶囊同排（同一横条的两个分段），时间线属于"取景"而非"筛选"，因此与图模式同级

### 3.3 图模式与右栏联动规则

| 图模式 | 右侧功能栏行为 |
|---|---|
| `macro`（宏观大图） | 默认 tab ①：宏观洞察与统计 |
| `personal`（个人脑图） | 默认 tab ①：个人洞察与统计 |
| 任意模式手动切 tab ②③④ | 右栏跟随，图不变 |
| `collab-analysis`（协作分析） | **强制**右栏进入「协作关系分析」面板（见 §6.2）；用户可切回 ②③④，切回后图模式保持，右栏自由 |
| `overlap-analysis`（重复分析） | 同上，「重复工作分析」面板 |
| 图内双击节点进入聚焦子图 | 右栏 tab ① 显示该节点洞察（现状卡片能力上移并扩展） |

---

## 4. Header（薄条）

```
[关系大脑]      {企业徽标/名称}    {数据态● 更新中…}   [刷新]
```

| 控件 | 行为 |
|---|---|
| 数据态胶囊 | 状态色点 + 文案（已是最新/有新内容待更新/正在更新 N%）；点击弹出 Popover：覆盖率条、构建进度、以及四个动作按钮：更新数据（推荐）/ 全部重建 / 协作关系计算 / 重复工作计算（迁移自旧「数据与图谱更新」折叠区） |
| 刷新 | 现有 `load()` |

> 说明：旧页面中"数据与图谱更新"整块折叠区、覆盖率区块全部移除，收敛进数据态胶囊；
> 协作/重叠分析就绪提示收敛进右栏 ① 统计格与 ④ 校对 tab 红点。

---

## 5. 右栏：四大 Tab + 内容

### 5.1 ① 关键洞察与统计（默认）

**设计原则：零新增 AI 调用。** relationcompute 语义引擎在建图时已产出全部 AI 文本
（主线 AI `summary`、协作/重叠 AI `reason`、会话 digest `summary`、事项 `description`、
风险快照 answer），前端只做**组装与呈现**，不调模型。

分三段：

**A. 统计格（4 格 × 2 行）**
```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ 主线  33 │ │ 部门   5 │ │ 协作  3  │ │ 重叠  2  │
│ 事项 176 │ │ 人员  23 │ │ 产物  65 │ │ 待校对 2 │  (2×4 网格)
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```
来源：宏观投影结果 + coverage（confirmedCollaborationCount/OverlapCount）+ review 待办。
点击统计格 = 切换视角（协作格 → 协作分析模式；重叠格 → 重复分析模式；主线格 → 宏观模式）。

**B. AI 洞察卡列表（按模式组装 relationcompute 已产出的 AI 文本，不调模型）**
- **宏观模式**：
  1. 协作洞察卡：每个协作组 → 对象 + AI reason（参与人/成果链/叙事）——已有组卡能力，移至右栏常驻；
  2. 重叠洞察卡：每个重叠组 → AI reason（重复事项提示）；
  3. 主线焦点卡：top N 主线（按时间窗内边权重和）→ AI summary 摘录 + 关联人员/事项计数；
  4. 会话沉淀：时间窗内高活跃会话 digest summary（图标 + 摘要 + 归属人）。
- **个人模式**：以 viewer 为中心，组装其主线 AI summary + 参与会话 digest + 协作/重叠 reason；
- 每张卡尾部标注来源（主线/会话）与时间；点击卡 = 图内定位该节点（聚焦子图）。
- 时间窗徽标（如"近7天"）常驻卡片区顶部，标注数据截止 graphUpdatedAt。

**C. 模式快捷入口**
```
协作关系分析 →   (跳 collab-analysis，组+1跳全亮)
重复工作分析 →   (跳 overlap-analysis，组+1跳全亮)
人工校对关系 (2) → (跳 tab④)
组织风险速览  →   (跳 tab②)
```

### 5.2 ② 组织风险速览
- 内容 = 现有持久化 `riskAnalysis` 快照（relationcompute 已生成 `analysisType='organization_risk'` 存库），
  右栏仅做读取与渲染，不新调模型；
  - 顶部状态条：数据截止时间 / 图谱版本不匹配提示 + 「重新分析」（复用现有 refresh 端点）；
  - 无快照时显示空态 + 一键分析；
- 现有风险弹层/弹窗形态废弃，全部收敛于此 tab。

### 5.3 ③ 向全图提问
- 将现有提问弹窗改造为 tab 内联会话：
  - 输入框 + 发送（scope = 当前图模式对应的企业/个人/部门）；
  - 历史记录列表（复用 question-history），点击历史项在下方展开；
  - "基于节点提问"入口仍可从图内（点击节点详情按钮）带锚点跳入本 tab 并预填问题。

### 5.4 ④ 人工校对关系（内联右栏）
- 列表：待校对工作主线（collab/overlap confirmed 且 unreviewed 优先置顶，红点计数）；
- 展开项**内联渲染**现有校对工作台（摘要、协作候选、重叠候选、确认/否定/合并/拆分/改名 + 理由），
  不再使用全屏弹窗（按用户确认 #5）；
- 校对动作完成后刷新 coverage 与统计格。

---

## 6. 协作 / 重复 分析模式（图 + 右栏）

### 6.1 脑图侧取景

新增 payload 构造入口（复用 `macroProjection` 数据），发送给 Unity 的图：

| 模式 | 画布内容 | 点亮逻辑 |
|---|---|---|
| `collab-analysis` | 全部协作组节点 + **各组 1 跳关联**（关联主线/证据事项/产物/参与人/业务对象 + 关联边） | 协作组与 1 跳关联节点 `isLit=true`（发光/描边强化），**其余节点/边压暗（opacity 0.25）**；待审阅组仍半透明虚线；大脑保留 |
| `overlap-analysis` | 全部重叠组节点 + **各组 1 跳关联** | 同上，仅点亮重叠组与其 1 跳关联 |

> 确认（问题 #4）：点亮范围 = **组节点 + 其 1 跳关联**，其余压暗。
> 渲染层改动很小：payload 增加 `mode: "collab-analysis" | "overlap-analysis"`，
> Unity 根据 mode 与节点 `highlighted` 标志做明暗处理；相机自动 fit 到点亮子图；
> 不进入"钉中心/波次"聚焦语义，保留自由旋转缩放。

### 6.2 右栏「协作关系分析」面板（重复分析同构）

```
协作关系分析                           [共 3 组 · 2 组待校对] [重新计算]
─────────────────────────────────────────────────────────────
状态条：数据截止 09-07 18:00 · 语义引擎 v27 · [更新数据] (跳数据态弹层)

┌ 组卡 1 —— 协作 · TTFA科技创新管理平台      [已确认✓] ┐
│ 对象：TTFA平台                            │ 进入子图 ▸│
│ 参与人(2)：地方军阀、郑伊芳                └──────────┘
│ 成果链：提取分析 · 地方军阀 → 汇总交付 · 郑伊芳
│ 叙事：……（reason 折叠可展开）
│ [查看证据] [校对] 
├───────────────────────────────────────────────────┤
┌ 组卡 2 —— 协作 · SpaceX 投资研究（mock）   [待校对⌛] ┐
│ ……（同上骨架，待校对态有琥珀边框 + 校对按钮）        │
└───────────────────────────────────────────────────┘
```

组卡行为：
- 点击卡片 → 脑图把该协作组升为聚焦（钉中心 + 波次点亮 + 单组叙事卡片，复用聚焦管线），
  右栏停留本页（卡片高亮该组）；
- 「校对」→ 跳 tab④ 并定位到该主线；
- 「重新计算」→ 复用已暴露的 协作关系计算 / 重复工作计算按钮逻辑。

---

## 7. 状态模型

```ts
type BrainMode = 'macro' | 'personal' | 'collab-analysis' | 'overlap-analysis';
// 另有隐式 mode：聚焦子图（anchorNodeId 非空时叠加在 macro/personal/… 之上）

type RightTab = 'insight' | 'risk' | 'ask' | 'review';
// 当 BrainMode 为 collab-analysis/overlap-analysis 时，右栏主视图 = AnalysisPanel(mode)，
// 但仍可切 tab ②③④；切回 ① 时恢复"该分析模式下的洞察面板"。
```

新增/迁移 state（旧 state 复用列表见 §10 附录）。

---

## 8. 组件与文件规划

| 文件 | 职责 |
|---|---|
| `RelationBrainPage.tsx`（新，独立页壳） | BrainMode/RightTab/时间线状态、Header、模式横条、画布区 + 右栏装配；替换原 standalone 装配（`/relations` 路由） |
| `BrainHeader.tsx`（新） | 企业名、数据态胶囊（Popover 含四个计算/更新按钮与覆盖率进度）、刷新 |
| `ModeTimelineStrip.tsx`（新） | 图模式分段胶囊 + 时间线横条（由近到远、拖拽滚动），与 tab 同级一行 |
| `BrainCanvas.tsx`（新，包裹 UnityRelationGraph） | 图模式 payload 组装、聚焦事件回传、图例、底部洞察卡序列（迁移现状叠加逻辑） |
| `RightRail.tsx`（新） | 右栏 Tab 框架（①洞察 ②风险 ③提问 ④校对 + 分析面板挂载点） |
| `panels/InsightStatsPanel.tsx`（新） | §5.1 统计格 + AI 洞察卡列表（零模型调用，组装既有 AI 文本） |
| `panels/RiskPanel.tsx`（新） | §5.2（迁移现有风险 aside 渲染） |
| `panels/AskPanel.tsx`（新） | §5.3（迁移提问弹窗） |
| `panels/ReviewPanel.tsx`（新） | §5.4（迁移校对工作台渲染，内联） |
| `panels/AnalysisPanel.tsx`（新） | §6.2 协作/重叠分析面板（两模式共用，差分配色/文案） |
| `payload/collabAnalysisPayload.ts`（新） | 由 macroProjection 结果生成 collab/overlap 分析 payload（`highlighted` 标志 + 1 跳关联取景） |
| `ZclawRelationSpacePage.tsx` | 收敛为"嵌入式/对话框"专用（主工作区数字大脑路径保持旧 UI 与全部原功能），standalone 改由新壳消费其子逻辑 → 建议后续抽 hooks 共享数据逻辑 |

---

## 9. 需要新增的最小契约

1. `UnityRenderNode` 增加 `highlighted?: boolean`（或复用 `status` 枚举扩展 `'lit'`）；
2. payload `mode` 扩展 `'collab-analysis' | 'overlap-analysis'`；
3. **无新增 AI 端点**：洞察卡组装所需的 AI 文本（主线 summary、协作/重叠 reason、digest summary、
   风险快照）全部来自现有 subgraph / coverage / risk / reviews 接口，前端零模型调用。

---

## 10. 拆除清单（旧 UI 删除项）

- Toolbar 全部控件（搜索、关系类型、来源、hops、nodeLimit、产物开关、协作开关）——直接移除
- 「数据与图谱更新」折叠区 + 覆盖率区块 + 协作/重叠就绪提示区块 → 迁入数据态胶囊与右栏
- Header 原四个按钮 → 迁入右栏 tab / 数据态胶囊（风险/提问/校对进右栏，刷新留 Header）
- 独立全屏弹层形态（风险、提问、校对）→ 收敛右栏 tab；节点详情/证据仍为浮层（读图场景）

---

## 12. compute 洞察资产审计与前端升级项（2026-09-08）

### 12.1 compute 层已有资产（relationcompute PG，租户 ce904488 实测存量）

| 资产 | 存储 | 实测存量 | 关键叙事/数据字段 | 现状暴露 |
|---|---|---|---|---|
| 会话 digest | relation_session_digests | 119 | generatedTitle、AI summary、activities[](title/desc/status/evidenceMsgIds)、artifacts[](name/type/variants)、subjects[](参与人)、confidence、model、promptVersion | ❌ 仅单会话接口；无租户级 digest 列表接口 |
| 主线语义快照 | relation_workstream_snapshots | 1/租户 | 完整 workstream JSON：summary、collaborationReason、collaboratorDigestIds、overlapReason、activityRefs、promptVersion | ❌ 无接口；前端经图节点 properties 部分重建 |
| 风险分析快照 | relation_analysis_snapshots | 1（organization_risk） | question/answer/model/evidenceCount/graphUpdatedAt | ✅ risk-analysis 接口 |
| 结构化风险 | （risk-analysis 生成） | 有 | risks[]（严重度/状态/证据链）+ limitations[] | ✅ /risks 接口（**前端未消费**） |
| 提问历史 | relation_question_history | 4 | question/answer/model/scope/anchor/generatedAt | ✅ questions/history（ask 弹窗在用） |
| 人工校对记录 | relation_workstream_reviews | 0 | action/title/target/splitGroups/reason | ✅ reviews 接口（校对弹窗在用） |
| 图谱节点 AI 文本 | relation_nodes.properties | 1240 | conversation.summary(digest AI 摘要)、workstream.summary/collabReason/overlapReason、activity.description、business_object.summary/contributorUserIds/childWorkstreamCount | ✅ subgraph 返回，但**详情面板白名单基本为空 → 不展示** |
| 构建历史/进度 | relation_projection_jobs | 有 | status/phase/processed/total/attemptCount/lastError/时间戳 | ⚠️ 仅 latest 接口，无历史列表 |
| 覆盖率 | （coverage 聚合） | 有 | ready/missing/stale/pending/coveragePercent/workstreamAnalysis | ✅ coverage 接口 |

### 12.2 前端升级结论

> 结论：**需要升级，但方向是"接已有数据/接口"，不是"造新 AI"**。

**A. 纯前端（无后端改动）——打开被白名单锁死的 AI 文本**
- 节点详情面板白名单扩展（数据已在 subgraph 中）：
  `conversation: [summary]`、`workstream: [summary, collaborationReason, overlapReason, confidence]`、
  `business_object: [summary, contributorCount, childWorkstreamCount, normalizationReason]`、
  `artifact: [artifactType, variantCount, familyName]`；
- 详情面板/洞察卡里渲染 digest 摘要与 reason 的 markdown（复用 ZclawMarkdown）。

**B. 需 1 个新后端只读端点（compute + evomind 网关薄透传）——会话叙事时间线**
- `GET /sessions/digests?enterpriseId&ownerUserId?&from&to&limit` →
  返回租户级 digest 列表（generatedTitle/summary/activities/artifacts/subjects/confidence/generatedAt）；
- 用途：右侧①洞察的"会话沉淀"卡组、按人/按时间线回放团队叙事流、个人脑图的"我参与过的会话"。
  （数据全在 compute，只缺一张只读清单；不做任何新模型调用。）

**C. 可选小升级（后续迭代）**
- builds 历史列表接口 → 数据态胶囊内展示"构建/更新历史 + 覆盖趋势"；
- /risks 结构化风险前端消费 → 风险 tab 顶部改为结构化风险表格 + AI 长文双视图。

### 12.3 叙事层设计原则（防"AI 幻觉刷屏"）
- 一切卡片/长文都必须来自 compute 已落库字段（summary/reason/digest/快照/历史），前端只组装；
- 每张卡带来源戳（主线/会话/风险快照）与数据截止时间（graphUpdatedAt），可一键定位图中节点；
- 标注 model/promptVersion/confidence 元数据（compute 全都有），强化"这是引擎产物"的可信呈现。

---

## 11. 决策记录（已确认）

1. **时间线与图模式同级**：Header 下方单一横条，左=图模式胶囊，右=时间线横条，
   由近到远（今天→昨天→近7天→近30天→本季→今年→全部），横向拖拽滚动。
2. **嵌入场景本次不改**：主工作区数字大脑对话框继续旧 UI；新壳仅用于 `/relations` 独立页。
3. **AI 洞察零新增调用**：右侧洞察全部组装 relationcompute 建图时已产出的 AI 文本，
   不触发新模型请求；仅"组织风险速览"内的「重新分析」复用现有刷新端点。
4. **点亮范围**：协作/重复分析 = 组节点 + 1 跳关联全部点亮，其余压暗。
5. **校对内联右栏**：校对工作台在 tab④ 内联展开，不再全屏弹窗。

确认后进入实现。
