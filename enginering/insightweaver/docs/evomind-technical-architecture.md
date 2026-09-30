# EvoMind（InsightWeaver）企业级 AI 工作台 — 技术架构文档

> 面向简历/面试的完整项目技术素材。
> 覆盖：整体技术栈、Monorepo 架构、关键模块实现（重点：两大数字大脑、Skills 沉淀）、数据模型、部署拓扑。

---

## 一、项目定位（一句话）

**EvoMind 是一个面向 B 端的多租户企业级 AI 工作台**：以"数字员工（Agent）+ 会话"为核心交互，向上沉淀企业知识库与组织关系图谱（两大"数字大脑"），向下通过 14 个第三方连接器打通企业既有办公/文档/代码系统，并配套完整的订阅计费、配额权益、权限审计体系。

- **形态**：SaaS 多租户平台（消费者个人版 + 企业组织版双轨）
- **代码规模**：96 张数据表、后端 40+ NestJS 模块、前端 10+ 一级路由、单文件核心服务 `zclaw.service.ts` 近 1.4 万行
- **关键特性**：双数字大脑（知识库大脑 / 组织关系大脑）、技能沉淀与涌现、MCP 工具协议、实时流式对话

---

## 二、整体技术栈

### 2.1 工程化（Monorepo）

| 维度 | 选型 | 说明 |
|---|---|---|
| 包管理 | **pnpm 9 workspace** | `apps/*` + `packages/*` 双工作区 |
| 任务编排 | **Turborepo** | 增量构建、任务缓存、`globalPassThroughEnv` 白名单透传密钥 |
| 语言/运行时 | **TypeScript 5.6 + Node.js 22**（ESM, NodeNext） | 全仓 ESM，`engines: >=22 <23` |
| 代码规范 | ESLint 9 + Prettier | 统一风格 |

**目录结构**：
```
insightweaver/
├── apps/
│   ├── api/        # NestJS 后端（40+ 模块）
│   └── web/        # Next.js 16 前端
├── packages/
│   ├── db/                 # Prisma schema + client（96 张表）
│   ├── shared/             # 前后端共享类型/常量
│   └── relation-contract/  # 关系计算协议契约（41 个导出）
└── env/            # 环境变量模板
```

### 2.2 后端（apps/api）

| 维度 | 选型 |
|---|---|
| 框架 | **NestJS**（模块化 DI、Guard、Interceptor、Pipe） |
| ORM | **Prisma 6**（PostgreSQL，96 张表） |
| 缓存/队列 | **Redis（阿里云 Tair）** — 会话、分布式锁、限流 |
| 认证 | **JWT**（access + refresh 双 token）+ 手机号短信验证码（阿里云 SMS） |
| LLM 接入 | **OpenAI 兼容协议** → 阿里云百炼（DashScope）；模型如 `qwen-plus-latest` |
| 知识图谱引擎 | **RAGFlow**（GraphRAG，文档解析/分块/图谱构建/检索） |
| 加密 | AES-256-GCM（密钥、第三方凭证）、`timingSafeEqual` 时序安全比较 |
| 支付 | 微信支付（WechatPay） |
| 对象存储 | 阿里云 OSS（附件） |
| 文档处理 | pdf-parse、mammoth(docx)、xlsx、libreoffice-convert |

### 2.3 前端（apps/web）

| 维度 | 选型 |
|---|---|
| 框架 | **Next.js 16（App Router）+ React 19** |
| 国际化 | **next-intl**（`[locale]` 路由段，中文/英文全量双语） |
| 状态管理 | **Zustand 5** + React hooks（30+ 自定义 hooks） |
| UI 组件 | **Radix UI**（dialog/dropdown/tooltip/context-menu）+ Tailwind CSS 4 + lucide-react 图标 + sonner toast |
| 富文本 | **TipTap**（15+ 扩展：标题/列表/代码块/图片/链接/上下标…） |
| 图表/可视化 | **ECharts 6 + echarts-gl**（知识库大脑图谱）、**手写 SVG 力导向图**（组织关系大脑） |
| 3D/动效 | three.js、gsap、motion、postprocessing |
| 文档预览 | react-pdf、docx-preview、pptx-to-html、mermaid、KaTeX（数学公式） |
| 虚拟滚动 | @tanstack/react-virtual |

### 2.4 基础设施

| 维度 | 选型 |
|---|---|
| 数据库 | PostgreSQL（远程，库 `insight_weaver`） |
| 独立计算服务 | **relation-compute**（无状态 LLM 代理，独立部署，独立仓库） |
| 部署 | Docker / Docker Compose（relation-compute 自带 Dockerfile 多阶段构建） |
| 第三方连接器 | 飞书、企业微信、钉钉、腾讯会议、腾讯文档、金山文档、IMA、网易邮箱、QQ 邮箱、GetNote、企查查、Canva、Gitee 企业版（14 个） |

---

## 三、后端模块全景（apps/api，40+ 模块）

```
认证/账户     auth（JWT+SMS）、admin-users、admin-config
计费/权益     billing（订阅/充值/权益批次）、credits（积分账本）、pay（微信支付）
组织/企业     enterprises（部门/组/成员导入/品牌/到期策略）
核心工作台    zclaw（会话/消息/工作区/共享空间/配额，1.4 万行核心服务）
Agent        agent（运行时/提示词优化/工具调用）、agents（Agent 管理/内置目录/部门可见性）
技能         skills（提交/审批/版本/市场）、skill-analytics（技能涌现）
数字大脑     zclaw/ragflow（知识库大脑）、relation-space（组织关系大脑远程客户端）
MCP          mcp（会话/工具注册/待处理存储）
仪表板       dashboard（企业情报/知识库/技能工厂/安全巡检/人效）
研究         research（研究会话/大纲/内容）
附件         attachments（OSS 上传/文本抽取）
语音         speech（语音识别）
连接器 ×14   feishu / wecom / dingtalk / wemeet / tencent-docs / kdocs / ima /
             netease-mail / qq-mail / getnote / qcc / canva / gitee-ent + connector-status-aggregate
```

---

## 四、核心模块深入

### 4.1 会话与工作台引擎（zclaw 模块）

**职责**：整个平台的"心脏"——管理数字员工实例、会话、消息、个人/共享工作区、文件树、配额。

**关键实现**：
- **会话-消息模型**：`ZclawSession`（会话）→ `ZclawMessage`（消息），按 `userId + agentInstanceId` 归属，软删除 + `lastMessageAt` 索引。
- **消息去重**：位置式 ID 碰撞 + 三角色读取去重 + 同步身份匹配（`message-dedupe.ts`），解决并发流式写入的重复落库。
- **工作区配额**：`ZclawWorkspaceQuotaConfig` + 成员用量快照 + 异步刷新任务，支持个人/企业两级配额。
- **共享工作区权限**：`SharedWorkspacePermission` + 路径级 ACL（`SharedWorkspaceOwnerFileAcl`）+ 组织共享（`SharedWorkspaceOrgShare`）+ 资产分类。
- **企业 Token 配额**：批次（`ZclawEnterpriseTokenQuotaBatch`）→ 成员（`...QuotaMember`）→ 分配（`...Assignment`），支持有效期、默认批次、结算（`...TokenUsageSettlement`）。

**技术亮点**：单文件 1.4 万行的 `zclaw.service.ts` 聚合了会话、模型配置、助理人设、Agent 模板、工作区用量、访问申请等数十个领域能力，通过 Prisma 事务 + Redis 锁保证并发一致性。

---

### 4.2 数字大脑一：知识库大脑（Knowledge Graph + RAGFlow）

**定位**：把个人/企业工作区的文档沉淀为**可检索、可问答、可视化的知识图谱**。

**架构链路**：
```
工作区文件 ──同步──> RAGFlow（文档解析/分块/向量化/GraphRAG 构建）
                         │
        ┌────────────────┼─────────────────┐
   文档检索            知识图谱            图谱问答
  (retrieve)      (getKnowledgeGraph)  (基于图谱节点对话)
```

**关键实现**：
- **`RagflowClient`**（`ragflow.client.ts`）：封装 RAGFlow 全部 REST API——数据集管理、文档上传/解析/删除、检索（`retrieve`）、GraphRAG 构建/追踪（`runGraphRag`/`traceGraphRag`）、知识图谱读取（`getKnowledgeGraph`/`getKnowledgeGraphChain`）、任务取消。**鉴权错误识别**（`isRagflowAuthorizationError`）用于数据集映射失效时自动重建。
- **`RagflowService`**（`ragflow.service.ts`）：数据集生命周期（个人/企业）、**异步同步队列**（`enqueueSyncPersonalWorkspaceFile`/`enqueueSyncEnterpriseSharedWorkspaceFile`，content hash 延迟到异步处理器二次校验）、多实例配置管理（管理端配置/测试连接）、检索编排（拖拽文件检索/图谱节点检索/知识库检索三种入口）。
- **`RagflowGraphService`**（`ragflow-graph.service.ts`）：图谱构建任务状态机——`getGraphStatus` / `enqueueBuildGraphJob` / `enqueueRefreshGraphJob` / `enqueueDeleteGraphJob` / `cancelGraphJob`，任务锁（`lockGraphJob`）+ 完成/失败/取消流转（`completeGraphJob`/`failGraphJob`/`cancelGraphJob`），**授权错误自动作废旧数据集映射并重建**（code 102/109）。
- **前端可视化**：`KnowledgeGraphExplorer.tsx`（ECharts 力导向图 + 节点详情 + 基于节点对话）、`KnowledgeBaseBrowserPanel.tsx`（文件树浏览）、`KnowledgeGraphStatusPanel.tsx`（构建进度）。
- **多实例**：`EnterpriseRagflowConfig` 支持每企业独立 RAGFlow 实例，`RagflowTarget` 抽象寻址。

**技术亮点**：
- 异步同步队列 + 内容哈希去重，避免重复上传/解析。
- 图谱任务状态机 + 分布式锁，防止并发构建冲突。
- 鉴权失效自愈：检测到授权错误自动作废映射并重建数据集，无需人工介入。

---

### 4.3 数字大脑二：组织关系大脑（Relation Space + 独立 relation-compute 服务）

**定位**：从企业**会话、记忆、RAGFlow 图谱**中抽取人/事项/产物之间的**可追溯关系**，形成组织级关系图谱，支持工作主线归纳、跨组协作/工作重叠识别、风险分析、图谱问答。

**这是项目中架构最复杂、我主导重构的部分。**

#### 4.3.1 架构拓扑（实例化隔离）

```
┌────────────── EvoMind 主平台（evomind）──────────────┐
│  web (Next.js)                                        │
│   └─ 组织关系大脑弹窗 (ZclawRelationSpacePage)         │
│  api (NestJS)                                         │
│   └─ relation-space 模块【纯远程客户端，1256 行】       │
│        ├─ relation-compute-config.service  (配置/鉴权) │
│        ├─ relation-data-plane-gateway      (数据面网关) │
│        └─ 3 个 controller（query/work-intel/admin）    │
└───────────────┬───────────────────────────────────────┘
                │ HTTP + Bearer（/v2/tenants/:tenantKey/*）
┌───────────────▼───────────────────────────────────────┐
│  relation-compute【独立服务·独立仓库·独立数据库】        │
│   无状态→有状态：自带 PostgreSQL（12+ 张 relation_* 表） │
│   语义计算：OpenAI SDK → 百炼（DashScope）              │
│   管理台：/admin（配置/ApiKey/租户统计 ECharts）         │
└───────────────────────────────────────────────────────┘
```

#### 4.3.2 关键设计决策（我主导）

1. **实例化隔离（1:1:1）**：一个 evomind 实例 ↔ 一个 compute 实例 ↔ 一个组织租户。`tenantKey = enterpriseId`，组织间数据完全隔离。
2. **协议契约包 `relation-contract`**（41 个导出）：主平台与 compute 共享的类型契约——协议版本（v1 推理面 `1.0.0` / v2 数据面 `2.0.0`）、请求/响应类型、能力清单、调用日志类型。**双方靠契约对齐，零运行时耦合**。
3. **完全解耦为远程客户端**：将原 8.6k 行本地计算栈（投影/查询/任务/语义引擎）从 evomind 移除，evomind 侧只剩 1256 行纯客户端（配置服务 + 数据面网关 + 3 controller）。所有关系计算在 compute 侧完成。
4. **双级鉴权**：数据面用 master key 或 API Key 表（SHA-256 哈希，明文仅创建时返回一次）；管理台用独立 `RELATION_COMPUTE_ADMIN_KEY`。
5. **增量同步游标**：`relation_compute_tenant_states` 存每租户 `sourceCursor`，增量模式只同步 `updatedAt > cursor` 的会话，无变化则 `up_to_date` 跳过（省模型费用）。
6. **证据可追溯**：`relation_evidences` 表把每条关系边挂到源会话/消息，前端可查看"判断依据"。

#### 4.3.3 图谱数据模型（compute 侧）

- `relation_nodes`：人/部门/组/会话/事项/产物/工作主线/业务对象（`spaceKey + identityKey` 唯一）
- `relation_edges`：关系边（`relationType`/`factType`/`weight`/`confidence`/时间有效期）
- `relation_evidences`：证据（可追溯性核心，挂 node/edge）
- `relation_session_digests`：会话摘要（LLM 生成的结构化摘要）
- `relation_projection_jobs`：投影/构建任务状态机
- `relation_workstream_snapshots` / `relation_workstream_reviews`：工作主线快照与人工评审
- `relation_compute_configs` / `relation_compute_call_logs` / `relation_compute_tenant_states`：配置/调用日志/租户游标

#### 4.3.4 前端（组织关系大脑）

- **`ZclawRelationSpacePage.tsx`**（~1700 行）：5 个视角（工作主线/跨组协作/工作重叠/部门/个人局部）共用一个 `subgraph` 接口，差异仅在前端传不同 `nodeTypes`/`relationTypes` 过滤。
- **`RelationGraphView.tsx`**：**手写 SVG 力导向图**（零图表库依赖），支持缩放/平移/节点聚焦/双击展开/证据查看。
- **交互能力**：图谱问答（`ask`）、风险分析（`risk-analysis`）、工作主线人工评审（确认/否定/改名/合并/拆分）、会话摘要生成与共享、增量/全量重建。
- **入口**：输入框"大脑选择器"芯片（`BrainSelectorPopover`）+ `/digital-brain/relation` 聚合页 + 弹窗模式（`RelationSpaceDialog`）。

**技术亮点**：
- **主导完成关系计算的实例化隔离重构**：从"本地计算栈"到"纯远程客户端"，删除 ~8500 行本地代码，语义引擎去本地 LLM 化（不再 `new OpenAI`），10 张旧表从主库 schema 下线。
- **协议版本 + releaseSha 双重校验**，保证主平台与 compute 服务版本兼容。
- **异步任务状态机 + 幂等键**（`idempotencyKey`）防止重复构建。

---

### 4.4 Skills 沉淀机制（技能工厂 + 技能涌现）

**定位**：把用户在会话中反复使用的**工作流沉淀为可复用的"技能"**，并在组织内共享/审批/市场化。

**关键实现**：
- **技能提交-审批流**（`skill-submission.service.ts`）：`submit`（从个人配置打包提交）→ `resubmitVersion`（版本迭代）→ 管理员 `approveForAdmin`/`rejectForAdmin` → `removeFromOrgForAdmin`。**版本对比**（`comparePersonalAgainstLive`）+ **冲突检测**（`assertNoOtherPendingSubmission`/`isBlockedByOtherPublishedSkill`）。
- **技能市场**（`skill-market-*.ts`）：个人技能（`skill-market-personal.util`）、分类继承（`skill-market-category-inherit`）、可见性控制（`skill-market-visibility`）、Markdown 描述（`skill-market-md.util`）、重命名。
- **技能模板**（`skill-template.*`）：行业模板（`SkillTemplateIndustry`）+ 初始化模板（`SkillInitTemplate`），新用户开箱即用。
- **技能涌现**（`skill-analytics/skill-emergence-*.ts`）：`SkillEmergenceRecorder`（记录）+ `SkillEmergenceProcessor`（处理），通过 `AgentRuntime.analyzeSkillEmergenceFingerprint`/`analyzeSkillEmergenceWorkflow` 用 LLM 分析会话指纹，**自动识别可沉淀为技能的高频工作流**。
- **技能配置水合**（`skill-personal-config.service.ts`）：把技能定义"水合"为个人可用配置。
- **数据模型**：`SkillCategory`/`SkillSubmission`/`SkillSubmissionVersion`/`PersonalSkillConfig`/`GlobalSkillConfig`/`EnterpriseSkillConfig`。

**技术亮点**：技能从"人工定义"到"LLM 辅助涌现"的闭环——记录用户行为指纹 → LLM 分析 → 推荐沉淀为技能 → 提交审批 → 组织共享。

---

### 4.5 订阅计费与配额权益体系（billing + credits）

**定位**：支撑 SaaS 商业化的完整计费引擎，双轨（消费者个人 + 企业组织）。

**关键实现**：
- **积分账本**（`credits`）：`Wallet`（钱包）+ `CreditLedger`（账本）+ `CreditHold`（冻结）。**行级锁**（`lockWalletRow`）+ **幂等键**（`idempotencyKey`）保证发放/扣减不重不漏。
- **订阅计费**（`billing`）：`BillingPlan`（套餐：`planType`/`priceCents`/`periodDays`/`tokenAmount`/`storageBytes`）→ `BillingOrder`（订单）→ `EntitlementBatch`（权益批次）→ `EntitlementLedger`（权益账本，记录 `before/afterAmount` + `before/afterFreezeAmount`）。
- **权益调度**：`entitlement-auto-allocate.scheduler`（自动分配）、`entitlement-expiry.scheduler`(到期)、`billing-task-cleanup.scheduler`（任务清理）。
- **充值**：`RechargeOrder`/`RechargePackage` + 微信支付（`WechatPayModule`）。
- **到期策略**：`EnterprisePostExpiryPurchaseConfig`（企业到期后购买配置）、`EnterpriseDefaultQuotaPolicy`（默认配额策略）。
- **配额**：会话配额（`ZclawEnterpriseConversationQuotaConfig/Usage`）、Token 配额（批次→成员→分配→结算）、工作区配额。

**技术亮点**：账本式设计（每笔变动记录前后余额）+ 幂等 + 分布式锁，保证金融级一致性；多调度器协同处理权益生命周期。

---

### 4.6 MCP（Model Context Protocol）工具协议

**职责**：让 Agent 通过标准 MCP 协议调用外部工具。
- `mcp-session.ts`/`mcp-session-store.ts`：会话管理与存储
- `tool-registry.ts`：工具注册
- `mcp-pending-store.ts`：待处理调用存储
- 支持 Gitee 企业版等连接器的 MCP 自主集成

### 4.7 连接器生态（14 个）

统一模式：每个连接器一个 NestJS 模块（`*-connector`），封装第三方 OAuth/设备授权 + 数据同步。`connector-status-aggregate` 聚合所有连接器状态。覆盖：
- **办公协同**：飞书、企业微信、钉钉、腾讯会议
- **文档**：腾讯文档、金山文档、IMA、GetNote
- **邮件**：网易邮箱、QQ 邮箱
- **代码**：Gitee 企业版（MCP）
- **设计/企查**：Canva、企查查

### 4.8 仪表板（dashboard）+ 人效（human-efficiency）

- **企业情报中枢**（`company-intelligence-hub/insight`）：焦点/洞察/评分/区间聚合
- **知识库仪表板**、**技能工厂仪表板**（含 LLM 推荐理由生成）、**安全巡检仪表板**
- **人效分析**（`human-efficiency`）：`AgentRuntime.generateHumanEfficiencySuggestions` 用 LLM 生成人效建议，带 fallback 兜底

---

## 五、数据模型概览（96 张表）

| 域 | 代表表 | 说明 |
|---|---|---|
| 账户/认证 | `User`/`UserIdentity`/`RefreshToken` | 用户、身份、刷新令牌 |
| 组织 | `Enterprise`/`EnterpriseMembership`/`EnterpriseDepartment`/`EnterpriseDepartmentGroup(+Member)` | 企业、成员、部门、组 |
| 第三方绑定 | `UserFeishuConnection`/`UserWecomConnection`/`UserDingtalkConnection`/`UserWemeetConnection`/`EnterpriseFeishuAppConfig` | 各连接器授权 |
| 会话/工作台 | `ZclawSession`/`ZclawMessage`/`ZclawAgentInstance`/`ZclawChatBinding`/`ZclawFileShare` | 核心会话 |
| 助理/模板 | `UserZclawModelConfig`/`UserZclawPersonalAssistant`/`UserZclawAssistantPersona`/`UserZclawAgentTemplate` | 个性化配置 |
| 技能 | `SkillCategory`/`SkillSubmission(+Version)`/`PersonalSkillConfig`/`GlobalSkillConfig`/`EnterpriseSkillConfig`/`SkillTemplate(+Industry)` | 技能沉淀 |
| Agent | `AgentCategory`/`GlobalBuiltinAgentConfig`/`EnterpriseBuiltinAgentConfig` | Agent 管理 |
| 计费/权益 | `Wallet`/`CreditLedger`/`CreditHold`/`RechargeOrder`/`BillingPlan`/`BillingOrder`/`EntitlementBatch`/`EntitlementLedger`/`BillingTopupInventory(+Assignment)`/`BillingTask(+Event)` | 计费引擎 |
| 配额 | `ZclawWorkspaceQuotaConfig`/`ZclawEnterpriseConversationQuotaConfig(+Usage)`/`ZclawEnterpriseTokenQuotaBatch(+Member+Assignment)`/`ZclawEnterpriseTokenUsageSettlement` | 多维配额 |
| 知识库 | `EnterpriseRagflowConfig`/`RagflowDataset` | RAGFlow 集成 |
| 共享工作区 | `SharedWorkspacePermission`/`SharedWorkspaceOwnerFileAcl`/`SharedWorkspaceOrgShare`/`SharedWorkspacePathOwner`/`SharedWorkspaceAssetClassification` | 权限/分类 |
| 研究/附件 | `ResearchSession`/`ResearchMessage`/`ResearchOutline(+Version)`/`ResearchContent`/`Attachment(+Text)` | 研究/附件 |
| 审计 | `AuditLog` | 操作审计 |
| 关系计算（客户端） | `RelationComputeConfig`/`RelationComputeCallLog`/`RelationComputeTenantState` | 远程 compute 配置/日志/游标 |

> 注：原 10 张本地关系计算表（`relation_nodes/edges/evidences/...`）已在实例化隔离重构中从主库下线，迁移至独立 relation-compute 服务的自有数据库。

---

## 六、部署拓扑

```
┌───────────── 生产环境 ─────────────┐
│  web (Next.js 16, :3100)          │
│  api (NestJS, :8080)              │──> PostgreSQL (insight_weaver, 96 表)
│       │                           │──> Redis/Tair
│       │ Bearer                    │──> 阿里云百炼 (DashScope LLM)
│       ▼                           │──> 阿里云 OSS / SMS
│  relation-compute (独立, :8080)   │──> RAGFlow (GraphRAG)
│   └─ 自有 PostgreSQL (relation_*) │──> 微信支付
└───────────────────────────────────┘
```

- **relation-compute** 独立仓库（`gitee.com/yinzhishi/relationcompute`），Docker 多阶段构建，自带管理台（`/admin`）。
- evomind 通过 `url + apikey` 调用 compute，**零代码耦合，仅靠 `relation-contract` 契约对齐**。

---

## 七、可写入简历的技术亮点（提炼）

1. **主导关系计算服务实例化隔离重构**：将 8.6k 行本地关系计算栈解耦为独立 `relation-compute` 服务 + 纯远程客户端（1256 行），设计协议契约包（41 个导出）实现零运行时耦合，语义引擎去本地 LLM 化，10 张旧表下线。
2. **设计并实现组织关系大脑**：手写 SVG 力导向图谱（零图表库依赖）、5 视角统一查询接口、工作主线 LLM 归纳 + 人工评审闭环、证据可追溯、增量同步游标省费用。
3. **实现知识库大脑（RAGFlow 集成）**：异步同步队列 + 内容哈希去重、图谱任务状态机 + 分布式锁、鉴权失效自愈（自动重建数据集映射）。
4. **设计技能沉淀与涌现机制**：提交-审批-版本化工作流 + LLM 分析会话指纹自动推荐技能，打通"人工定义 → 智能涌现 → 组织共享"闭环。
5. **构建金融级计费引擎**：账本式设计（前后余额快照）+ 幂等键 + 行级锁，支撑订阅/充值/权益批次/多维配额（会话/Token/工作区）。
6. **搭建 14 个第三方连接器的统一接入层** + MCP 工具协议，打通企业办公/文档/代码生态。
7. **Monorepo 工程化**：pnpm + Turborepo 增量构建，前后端共享类型包，96 张表 Prisma 统一建模。

---

## 八、关键数字（面试可引用）

| 指标 | 数值 |
|---|---|
| 数据表 | 96 张 |
| 后端模块 | 40+ |
| 核心单文件服务 | `zclaw.service.ts` ≈ 13,895 行 |
| 第三方连接器 | 14 个 |
| 关系计算解耦 | 删除 ~8,500 行本地代码 → 1,256 行纯客户端 |
| 协议契约导出 | 41 个类型/常量 |
| 前端自定义 hooks | 30+ |
| 关系大脑视角 | 5 个（共用 1 个查询接口） |
| 计费体系 | 积分账本 + 订阅 + 权益批次 + 3 类配额 |
