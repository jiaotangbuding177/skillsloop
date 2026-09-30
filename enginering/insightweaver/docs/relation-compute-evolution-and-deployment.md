# 关系大脑：relationcompute 与 evomind 解耦评估 + 更新部署全流程文档

> 覆盖范围：insightweaver（evomind 平台：apps/web + apps/api）、relationcompute（独立仓库）、
> Unity WebGL 图谱工程（位于 relationcompute 仓库 unity-graph/）。
> 最后更新：2026-09-08

---

## 一、解耦评估结论

**结论：计算已全部下沉到 relationcompute 服务；evomind 只保留"鉴权 + 路由 + 展示 + 会话源转发"，
职责边界清晰、可独立部署。剩余耦合点为 3 处数据同步方向（单向）与 1 处契约快照同步。**

### 1.1 服务职责矩阵

| 能力 | 归属 | 说明 |
|---|---|---|
| 会话摘要 digest 生成 | **relationcompute** | 语义引擎（packages/relation-semantic） |
| 事项归一 / 产物归一 | **relationcompute** | 同上 |
| 主线（workstream）推断与审计 | **relationcompute** | workstream prompt v27，多轮 LLM |
| 业务对象（business object）归一 | **relationcompute** | 主线→上层业务对象聚合 |
| 协作 / 重叠识别与置信度 | **relationcompute** | 审计 prompt + 确定性同名事项重叠 |
| 风险分析（结构化 /risks + 长文快照） | **relationcompute** | organization_risk 快照存 compute PG |
| 全图/节点问答（graph question） | **relationcompute** | 带图上下文调模型；历史存 compute PG |
| 校对（workstream reviews）落库与重建联动 | **relationcompute** | reviews 存 compute PG |
| 图谱存取（nodes/edges/evidences） | **relationcompute** | compute PG（独立库） |
| 时间范围 / coverage / 任务进度 | **relationcompute** | 各自端点 |
| 会话叙事时间线（digest 列表） | **relationcompute** | `/digests`（本次新增，前端 0 模型调用） |
| 成员/部门/组快照来源 | **evomind 主库** | evomind 是企业成员唯一事实源 |
| 成员鉴权（JWT / 企业范围） | **evomind API** | assertMember 后转发 |
| 图谱渲染与交互 | **evomind web（/relations 独立页）** | Unity WebGL 3D + 前端投影/蒸馏 |
| Unity WebGL 产物托管 | **relationcompute** | `/unity-static/*` 静态路由 |

### 1.2 事实核查要点

1. **"计算是否全部挪到 relation-compute？" → 是。** 图算法（查询/BFS/时间窗/白名单）、
   语义引擎（digest/activity/artifact/workstream/business object/collab/overlap）、
   风险、问答、校对落库都在 relationcompute 内完成；evomind 侧没有任何模型调用。
2. **三个单向数据方向（evomind → relationcompute）**：
   - `PUT tenants/:tenantKey`（租户注册）
   - `POST sources/sync`（成员/部门/组/会话/消息/删除游标增量同步；从 evomind 主库读，写入 compute PG）
   - `POST sessions/:sessionId/digest?publishToEnterprise=true`（个人摘要发布到企业共享）
3. **反向不依赖**：relationcompute 不读 evomind 主库；全部通过 HTTP API + apiKey 鉴权。
4. **契约耦合**：`@insightweaver/relation-contract` 为 evomind 侧类型包（构建到 dist 被消费），
   relationcompute 自带同源契约副本（packages/relation-contract）。改动需两端同步（本次
   time-range/from/to 就因 evomind 侧 dist 未重建而出现类型漂移，需 `pnpm build` 同步）。
5. **图谱数据源**：compute PG 是关系图唯一数据源；evomind 主库不存图谱（仅配置与成员）。
6. **Unity 产物**：静态文件托管由 relationcompute HTTP 服务提供（无 S3/CDN 依赖），
   evomind 前端跨域加载（CORS 已放通，生产需收窄域名）。

---

## 二、部署拓扑

```
┌────────────────────────── evomind 主机 ──────────────────────────┐
│ apps/web (Next.js)      :3100/80   前端 /relations 等            │
│   └ UnityRelationGraph 跨域加载                                    │
│ apps/api (NestJS)       :8080/443  JWT、成员、转发                 │
│   主库 PG (成员/组织/配置)                                          │
└──────────────┬───────────────────────────────┬───────────────────┘
               │ HTTP /sources/sync、digests、builds、graph/query    │
               │ Bearer apiKey（AES 加密存主库 configs）              │
┌──────────────▼───────────────────────────────▼───────────────────┐
│ ┌──────────────── relationcompute 主机（独立仓库）───────────────┐ │
│ │ apps/src (Node ts)       :<port>                              │ │
│ │   · 数据面 v2 /tenants/:key/...                               │ │
│ │   · 语义引擎 packages/relation-semantic                       │ │
│ │   · /unity-static/* 静态托管（unity-build/）                  │ │
│ │ compute PG  (55432)  独立库                                   │ │
│ │ unity-graph/  Unity 2022.3 工程                              │ │
│ │ unity-build/  WebGL 产物（gitignore，构建生成）               │ │
│ └───────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## 三、环境变量与配置

### relationcompute/.env（样例）

```bash
PORT=8091
RELATION_DATABASE_URL=postgresql://relation_compute:xxx@localhost:55432/relation_compute
RELATION_COMPUTE_SERVER_API_KEY=rc_server_master_key_dev   # 主 API key
RELATION_COMPUTE_ADMIN_KEY=...                              # 管理台 key
DASHSCOPE_MODEL=qwen-plus-latest
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=...
# 可选模型并发/超时
RELATION_LLM_CONCURRENCY=3
RELATION_MODEL_REQUEST_TIMEOUT_MS=3000000
```

### evomind apps/api/.env（compute 接入）

```bash
# 首选经主库 relation_compute_configs（管理台配置，AES 加密）；环境变量为兜底：
# RELATION_COMPUTE_BASE_URL=http://<relationcompute-host>:<port>  # 仅当 DB 无配置时兜底；管理员后台配置优先
# RELATION_COMPUTE_API_KEY=rc_xxx
# 加密密钥（用于读取 configs 行）
ZCLAW_MODEL_CONFIG_SECRET=...
```

---

## 四、全流程部署/更新手册

### 4.1 数据库迁移
```bash
# relationcompute（首次或 schema 变更后自动 migrate）
cd relationcompute
pnpm db:migrate        # node dist/migrate.js 等价
pnpm dev               # 本地 watch；生产 node dist/main.js
```

### 4.2 relationcompute 代码更新
```bash
cd relationcompute
pnpm install
pnpm typecheck && pnpm test
pnpm build              # esbuild → dist/
# 重启服务（systemd/docker 按你的托管方式）
```

### 4.3 Unity WebGL 产物生成与更新（本次新增链路）

前置：本机安装 Unity **2022.3.62f3c1**（含 WebGL Build Support）；
`unity-graph/ProjectSettings/ProjectVersion.txt` 锁定 2022.3.62f3c1。

```powershell
# 一键重建（清理旧产物 → batchmode 编译/构建 → 写 manifest）
cd relationcompute
.\scripts\build-unity.ps1
```

产物输出（relationcompute 仓库根，已被 .gitignore）：
```
unity-build/
  build-manifest.json          # URL 形如 /unity-static/Build/xxx（供 evomind 前端拼 base）
  Build/…loader.js/.framework.js.br/.wasm.br/.data.br
  StreamingAssets/…
```
要点：
- 产物使用 **Brotli 压缩**；静态路由对 `.br` 返回 `content-encoding: br`（代码已处理）。
- `productVersion = 构建时间戳`，前端 Unity 缓存键自动失效（不用清浏览器缓存）。
- 构建脚本会：开 isReadable（脑网格运行时读顶点）、关引擎代码裁剪、
  添加自定义 shader（Always Included 语义按 2022.3 材质引用自动带出）、生成脑形所需资源。
- 修改 Unity C# / shader / FBX 后重新执行本脚本即可。

### 4.4 relationcompute 静态托管（生产）

relationcompute HTTP 已实现 `GET /unity-static/<file>`（鉴权豁免 + CORS + Last-Modified/HEAD 支持）。
若生产走 nginx 反代：将 `/unity-static/` location 直通 compute 服务（或指向 unity-build 目录静态服务，
并保持 brotli Content-Encoding 与 Last-Modified 语义一致——Unity 缓存再验证依赖 HEAD + Last-Modified）。

### 4.5 evomind 前端更新

```bash
cd insightweaver/apps/web
# Unity 加载地址不写死：构建时不设 NEXT_PUBLIC_UNITY_BUILD_URL（留空），
# 前端运行时从 /api/relation-space/compute-status 解析管理员后台配置的
# compute 服务地址（unityStaticBaseUrl），本地/生产/多浏览器自适应。
# 仅当需要显式覆盖时才注入：
# NEXT_PUBLIC_UNITY_BUILD_URL=https://<compute-domain>/unity-static
pnpm install
pnpm build && pnpm start
```

- 新壳页面：`/relations` → `RelationBrainPage`；主工作区/对话框保持旧 `ZclawRelationSpacePage`。
- Unity 产物更新后**无需重新部署前端**（运行时拉取新版本产物）。

### 4.6 联动验收清单（更新/新增）

1. [ ] relationcompute typecheck+test、重启
2. [ ] Unity 构建成功 → unity-build/build-manifest.json 存在，productVersion 为当日时间戳
3. [ ] `curl http://<compute-host>:<port>/unity-static/build-manifest.json` 200（.br 产物由服务端解压后明文下发，无 content-encoding 头，规避代理破坏 brotli 流）
4. [ ] evomind API 重启后 `/api/relation-space/sessions/digests?...` 返回 401（路由存在）
5. [ ] `/relations` 前端：脑图正常加载（无缓存旧版）、右栏①洞察统计与 digest 会话卡、
   风险双视图、协作/重复点亮与聚焦联动正常
6. [ ] 数据态：更新数据/全部重建/协作关系计算/重复工作计算任务正常出现在 compute jobs

### 4.7 回滚

- 前端：回滚 evomind 部署（Unity 产物不回滚也可，新前端兼容旧 manifest 字段）；
- compute：回滚服务代码即可（图数据保留在 compute PG）；
- Unity：重跑旧 tag 构建脚本即还原旧产物。

---

## 五、契约同步提醒（易踩坑）

`packages/relation-contract`（insightweaver）与 `relationcompute/packages/relation-contract` 为
**双副本**。任何接口/类型变更需：改 compute 副本 → 改 evomind 仓库同源副本 → `pnpm build`
（evomind 侧 dist 必须重建，否则 TS2305 类型漂移）。本次 time-range/from/to 曾触发此坑。
