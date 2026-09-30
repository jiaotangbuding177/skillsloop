# relation-compute 独立部署 + 关系表分离 — 设计审核与可行性分析

> 审核对象：用户提出的目标架构
> 1) 走链路：evomind ──Bearer key──→ relation-compute ──DASHSCOPE_API_KEY──→ 百炼
> 2) 从 `.tmp/insightweaver` 提取 relation-compute，单独实现为独立服务 + 后台管理界面
> 3) 部署后以 url + apikey 方式调用
> 4) relation_* 11 张表也部署在 relation-compute 服务器上，与 evomind 相互独立
> 5) evomind 实时读取计算结果和图谱数据渲染，只保留必要的持久化和缓存
>
> 审核日期：2026-08-26；依据：`.tmp/insightweaver` 分支 feature/relation-space-workstream-risk 全量源码

## 一、逐项审核结论

| # | 设计点 | 判定 | 一句话理由 |
|---|--------|------|-----------|
| 1 | 链路 A（evomind→relation-compute→百炼） | ✅ 立即可行 | 上游代码原生支持，零改动 |
| 2 | 提取 relation-compute 独立部署 | ✅ 可行 | 代码完整：`apps/relation-compute/` 4 个源文件 + Dockerfile + `packages/relation-contract`，自带测试 |
| 3 | 给 relation-compute 配后台管理界面 | ⚠️ 可行但价值低 | 服务无状态、配置全部来自环境变量，没有可写配置；上游已在 evomind 侧实现管理页 `/admin/relation-compute`，重复建设还要解决独立鉴权 |
| 4 | relation_* 表移到 relation-compute 服务器 | ⚠️ 架构可行，但不是"提取"而是"重构" | 上游全部投影/授权/查询/任务代码都在 evomind，默认 11 张表与源表同库；协议 1.0.0 只有 complete/health 两个接口，没有任何图读写能力 |
| 5 | evomind 实时读取渲染、只留必要持久化 | ✅ 可行（依赖 #4 完成） | HTTP 读取 + 短 TTL 缓存即可 |

**总评：方向合理，但 #4 是整个设计的成本中心。"提取 relation-compute"只能得到计算后端；图谱智能（投影/授权/查询/问答编排）全部在 evomind 的 `apps/api/src/relation-space/`（37 个文件）里，表分离意味着这部分要重新切分。**

## 二、relation-compute 现状盘点（.tmp 中实际有什么）

```
apps/relation-compute/
├── Dockerfile
├── package.json            # 依赖：openai + @insightweaver/relation-contract
└── src/
    ├── main.ts             # 读环境变量、装配、启动（默认端口 8080）
    ├── server.ts           # 裸 node:http 服务：/health + /complete，Bearer 鉴权(timingSafeEqual)、请求体大小限制
    ├── model-client.ts     # OpenAI 兼容客户端 → 百炼（temperature 0，JSON 任务强制 json_object）
    └── server.test.ts
packages/relation-contract/src/index.ts   # 协议 1.0.0：Request/Response/Health/Capability 类型 + 校验
```

特点：
- **完全无状态**：不连数据库、不存任何东西，收到 prompt → 调模型 → 返回
- 环境变量：`RELATION_COMPUTE_SERVER_API_KEY`（必填）、`INSIGHTWEAVER_RELEASE_SHA`（必填，版本锁）、`DASHSCOPE_API_KEY`（必填，付费）、`DASHSCOPE_MODEL`（默认 qwen-plus-latest）、`DASHSCOPE_BASE_URL`、`PORT`
- 已有能力就是 url + apikey 调用（正是你要的形态），协议层还有 protocolVersion + releaseSha 双重校验

**结论：第 1、2 项你要的东西已经 100% 存在，可直接提取部署。**

## 三、设计 #4（表分离）的三个硬问题

### 问题 1：数据流向反转 —— 11 张表的原料全在 evomind

11 张 relation 表由 5 条投影管线写入（见《写入管线》报告），原料是：
组织/成员/部门/组（evomind 库）、聊天会话/消息（evomind 库）、RAGFlow 图谱（evomind 库映射 + RAGFlow API）、记忆文件（OpenClaw 工作区实时列举）、工作流推断（依赖已生成的摘要表）。

表搬走后只有三种选择：

| 方案 | 说明 | 评价 |
|------|------|------|
| a. relation-compute 直连 evomind 数据库 | 跨服务共享 DB | ❌ 与"相互独立"目标直接冲突，且把 evomind 全部业务表暴露给计算服务 |
| b. **evomind 保留投影逻辑，调服务的"写入 API"** | 服务暴露 `projectFact`（subject/relation/object/evidence 四元组）HTTP 接口，evomind 的 5 条投影管线改为远程写 | ✅ **推荐**：投影逻辑留在懂源表的一侧；服务只管存图 + 计算；单一写入方，无双写 |
| c. evomind 推原始数据，投影逻辑搬进服务 | 服务要理解 evomind 的组织模型/会话结构 | ❌ 搬运量最大，服务与业务强耦合，失去独立性意义 |

### 问题 2：授权数据必须随行 —— 这是安全边界，不是性能优化

图谱每次查询都执行**证据级授权**：调用者必须对边上至少 1 条证据有可见权，依据是
`enterprise_memberships`（谁是活跃成员）+ `ragflow_documents.permissionVersion`（文档权限版本）。

图搬到服务侧后，服务必须自己会鉴权，否则两条路都是死路：
- 不鉴权 → 用户能看到别人私有会话的推断（证据授权设计就是为了防这个）
- evomind 拉全量再本地过滤 → 每次请求跨网络拉全图，不可行

**解法：权限镜像（小表同步）**。把授权需要的最小集合同步到服务：
- 成员关系镜像：`userId + enterpriseId + status`（量级 = 人数，极小）
- 文档权限镜像：`ragflowDocumentId + permissionVersion + 归属`（量级 = 文档数）
- 同步时机：变更扫描器本来就在扫这两类源表，发现变更时顺带推一次镜像
- 安全原则：**fail-closed** —— 镜像缺失时拒绝可见，宁可少看不能多看

### 问题 3：跨服务一致性 —— 事务拆开了，靠幂等键兜底

上游"写摘要 + 投影入图"在同一个 Prisma 事务里；拆开后不存在分布式事务。
好消息：整个投影体系**本来就是幂等设计**（`idempotencyKey` / `edgeKey` / `evidenceKey` 全部确定性唯一键），失败重试安全。
需要补的：**可靠推送队列** —— 复用 `relation_projection_jobs` 表（留在 evomind），执行器从"本地投影"改成"调服务 Ingest API"，成功才标完成，失败按 `maxAttempts/nextAttemptAt` 重试。这套任务表字段（锁、重试、游标）原样可用。

## 四、推荐的目标架构（若执行 #4）

```
┌──────────────── evomind（事实源 + 渲染端）────────────────┐
│ 保留（必要持久化）:                                          │
│   users/enterprises/memberships/departments/groups         │
│   zclaw_sessions/zclaw_messages（聊天主数据，不动）          │
│   ragflow_datasets/documents/graph_jobs（RAGFlow 映射）     │
│   relation_projection_jobs/checkpoints（投影队列+游标）      │
│   relation_compute_configs（url + apikey，已有）            │
│ 搬走:                                                       │
│   relation_* 11 张表 → 服务侧                               │
│ 新增:                                                       │
│   subgraph/context 等响应的短 TTL 缓存                       │
└───────────────┬───────────────────────────────────────────┘
                │ HTTPS + Bearer apikey
┌───────────────▼──────── relation-brain 服务 ──────────────┐
│ 自有 PostgreSQL:                                            │
│   relation_* 11 张表 + 权限镜像(memberships_lite /          │
│   ragflow_documents_lite)                                   │
│ 协议 v2（url + apikey 开放接口）:                            │
│   GET  /v1/health                    （已有）               │
│   POST /v1/complete                  （已有，LLM 计算）      │
│   POST /v1/ingest/facts              （新增，projectFact）   │
│   POST /v1/ingest/retract            （新增，按 source 回收）│
│   POST /v1/permissions/mirror        （新增，权限同步）      │
│   GET  /v1/graph/subgraph|path|timeline|context|evidences  │
│        （新增，带 userId，服务侧鉴权）                        │
│   POST /v1/intelligence/digest|workstreams|ask|risks...    │
│        （新增，问答/风险/摘要编排连同 LLM 调用整体搬入）       │
│ 管理界面: 只读状态页（健康/版本/任务概览）                    │
│   写配置仍走 evomind /admin/relation-compute                │
└─────────────────────────────────────────────────────────────┘
```

管理界面建议（对设计 #3 的修正）：
- **配置类**（baseUrl/apiKey/超时/测试）继续放 evomind 的 `/admin/relation-compute`（上游已实现，含三层鉴权）
- 服务自身只加一个**只读状态页**（健康、协议版本、模型、capabilities、最近调用统计），避免给无状态服务硬造管理面，也避免第二套管理员鉴权

## 五、分阶段实施建议

| 阶段 | 内容 | 工作量 | 交付物 |
|------|------|--------|--------|
| **P1（建议立即做）** | 提取 `apps/relation-compute` + `packages/relation-contract` 独立部署；evomind 通过 url+apikey 接入（上游现成）；11 张表暂留 evomind PG（上游原设计） | 1-2 天 | 计算独立、模型密钥与主平台隔离、链路 A 跑通 |
| **P2（要做表分离再做）** | 设计 relation-contract v2（Ingest/Query/权限镜像）；服务自带 PG + 11 表；迁移投影执行器/查询/问答编排；evomind 改 HTTP 读写 + 缓存 | 周级（协议设计 + ~10 个服务迁移 + 联调） | 关系大脑完全独立部署 |
| **P3（体验优化）** | subgraph 响应短 TTL 缓存；服务侧图更新事件推送（可选，替代轮询） | 天级 | 实时渲染体验 |

**强烈建议先只做 P1**：它已经满足"计算后端独立 + url+apikey 调用 + 模型密钥隔离"，且零架构风险。P2 是否值得，取决于你是否真的需要"关系大脑与 evomind 物理隔离部署"（例如独立扩缩容、独立数据合规边界）。如果只是想让配置和密钥独立，P1 已经达成。

## 六、风险清单

| 风险 | 影响 | 缓解 |
|------|------|------|
| releaseSha 版本锁 | 两边独立部署后发版不同步 → 所有调用被拒 | 发版流程绑定：同 commit 出两个镜像；或明确关闭该锁（改代码） |
| 权限镜像同步延迟 | 成员退出后短暂仍可见 | fail-closed + 同步失败告警；镜像同步走同一投影队列保证可靠 |
| 服务从"无状态"变"有状态" | 需要备份、迁移、容量规划 | 服务自带 `prisma migrate`；11 表数据全部可从 evomind 重投影，丢了可重建（这是幂等设计的红利） |
| 网络多一跳 | 每个图视图 +1 次跨服务 RTT | evomind 侧对 (spaceKey,查询参数) 做 30-60s 短 TTL 缓存 |
| 协议 v2 是全新设计 | 上游没有任何现成代码可抄（complete/health 之外） | P2 立项前先写协议 spec，用 idempotencyKey 语义对齐现有投影契约 |
| 管理面重复建设 | 两套管理员鉴权 | 按上文分工：配置在 evomind，状态页在服务 |

## 七、回答你的三个隐含问题

1. **"目前 relation-compute 具体的代码和算法是不是已经完全给出了？"**
   计算后端（服务本体 + 协议 + 模型调用）✅ 完全给出，可直接提取。
   但"算法"的大头——摘要生成/工作流推断/风险分析/问答的 **prompt 与编排**（`relation-semantic-ai.service.ts` 1816 行、`relation-work-intelligence.service.ts` 1500+ 行）——目前在 evomind 侧。P1 阶段它们留在 evomind、把 LLM 调用委托给服务，完全可用；P2 阶段才需要把它们搬进服务。

2. **"能不能只留必要持久化和缓存？"**
   可以。evomind 最终保留：聊天主数据、组织主数据、RAGFlow 映射、投影队列/游标、url+apikey 配置、图查询缓存。11 张 relation 表 + 权限镜像全部在服务侧。

3. **"管理界面配在哪？"**
   配置管理用 evomind 现成的 `/admin/relation-compute`（上游已实现）；relation-compute 自身建议只加只读状态页。
