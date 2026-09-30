# RagFlow Phase 0 API Spike 记录

## 目标

验证当前 RagFlow 部署版本是否支持 EvoMind v2 方案所需的基础 API 能力。Phase 0 只做接口能力 spike，不接入 EvoMind 正式业务链路，不新增数据库表，不修改 Nest 模块。

参考文档：[RagFlow HTTP API Reference](https://ragflow.com.cn/docs/http_api_reference)。

## 运行前置条件

需要在运行环境中设置：

```text
RAGFLOW_BASE_URL=https://your-ragflow-host
RAGFLOW_API_KEY=your-api-key
```

可选：

```text
RAGFLOW_DEFAULT_EMBEDDING_MODEL=your-embedding-model
RAGFLOW_DEFAULT_CHUNK_METHOD=naive
RAGFLOW_DEFAULT_PARSER_CONFIG_JSON={"chunk_token_num":512}
RAGFLOW_DEFAULT_PERMISSION=me
RAGFLOW_SPIKE_RUN_GRAPH=true
RAGFLOW_SPIKE_GRAPH_TRACE_ATTEMPTS=90
RAGFLOW_SPIKE_GRAPH_TRACE_INTERVAL_MS=5000
```

说明：

- `RAGFLOW_SPIKE_RUN_GRAPH` 默认不启用，避免 GraphRAG 构建耗时过长。
- `RAGFLOW_SPIKE_GRAPH_TRACE_ATTEMPTS` 仅在启用 GraphRAG 时生效，控制 trace 轮询次数。
- `RAGFLOW_SPIKE_GRAPH_TRACE_INTERVAL_MS` 仅在启用 GraphRAG 时生效，控制 trace 轮询间隔。
- 脚本会创建临时 dataset 和临时文档，并在结束时尝试清理。
- 如果清理失败，脚本会输出需要手动删除的 dataset/document id。
- 日志不会输出完整 API key。

## 运行命令

```bash
pnpm --filter @insightweaver/api ragflow:spike
```

无 RagFlow 环境变量时，脚本应清晰提示缺少 `RAGFLOW_BASE_URL` 或 `RAGFLOW_API_KEY`，并以非 0 状态退出。

## 真实运行环境

| Field | Value |
| --- | --- |
| Run time | 2026-06-08T03:42:43.635Z |
| Base host | `http://47.116.171.63` |
| Run ID | `2026-06-08T03-42-43-634Z-674izo` |
| GraphRAG requested | `true` |
| GraphRAG trace attempts | `6` in script rerun; manual completed-graph verification reached `progress=1.0` |
| GraphRAG trace interval ms | `5000` |
| Cleanup | dataset `1af256b462ec11f1979cc9ff57f9fcdc` cleaned up |

注意：API key 不记录到文档中。

## 验证项

| Item | Expected | Result | Notes |
| --- | --- | --- | --- |
| dataset | `supported` | `supported` | created dataset `1af256b462ec11f1979cc9ff57f9fcdc` |
| create dataset language | `supported` 或 `unsupported` | `unsupported` | `POST /api/v1/datasets` 返回 code 101：`language` 是额外字段，不允许传入 |
| upload meta_fields | `supported` 或 `unsupported` | `supported` | multipart `meta_fields` accepted |
| upload | `supported` | `supported` | uploaded document `1b2cb77862ec11f1979cc9ff57f9fcdc` |
| parse | `supported` | `supported` | parse triggered for document `1b2cb77862ec11f1979cc9ff57f9fcdc` |
| status polling | `supported` | `supported` | document parsed with `progress=1` |
| retrieve document_ids | `supported` | `supported` | retrieved 1 chunk |
| metadata update | `supported` 或 `unsupported` | `supported` | document `meta_fields` update accepted |
| metadata filter | `supported` 或 `unsupported` | `supported` | request accepted; returned 1 chunk |
| delete document | `supported` | `supported` | deleted temporary document |
| GraphRAG | `supported`、`unsupported` 或 `not-tested` | `supported` | run、trace、graph、delete 均有可用路径 |
| GraphRAG run | `supported`、`unsupported` 或 `not-tested` | `supported` | `POST /api/v1/datasets/:datasetId/run_graphrag` accepted in 56ms，返回 `task_id` |
| GraphRAG trace | `supported`、`unsupported` 或 `not-tested` | `supported` | 6 次轮询可读到 `task_type=graphrag`、`progress`、`progress_msg` |
| GraphRAG graph | `supported`、`unsupported` 或 `not-tested` | `supported` | `GET /api/v1/datasets/:datasetId/knowledge_graph` 返回 `graph.nodes` 和 `graph.edges` |
| GraphRAG nodes | `supported`、`unsupported` 或 `not-tested` | `supported` | 手动验证完成图谱返回节点字段：`id/entity_name/entity_type/description/source_id/pagerank` |
| GraphRAG edges | `supported`、`unsupported` 或 `not-tested` | `supported` | 手动验证完成图谱返回边字段：`source/target/src_id/tgt_id/description/keywords/source_id/weight` |
| GraphRAG display fields | `supported`、`unsupported` 或 `not-tested` | `supported` | 可按后端白名单展示节点和边详情 |
| GraphRAG node chat | `supported`、`unsupported` 或 `not-tested` | `not-tested` | 未发现节点级问答 API，MVP 采用节点描述 + documentIds 受限 retrieve 降级 |
| GraphRAG delete | `supported`、`unsupported` 或 `not-tested` | `supported` | 当前部署实际可用路径为 `DELETE /api/v1/datasets/:datasetId/graph`；官方文档的 `DELETE /knowledge_graph` 不适用 |

## GraphRAG 专项记录

| Area | Result | Notes |
| --- | --- | --- |
| run request | `supported` | `POST /run_graphrag` accepted in 56ms，返回 `task_id=1f1bd9ae62ec11f1979cc9ff57f9fcdc` |
| trace polling | `supported` | 6 次轮询均可读；最新 `task_type=graphrag`、`progress=0.0196693`、`progress_msg` 包含构建子图日志 |
| graph request | `supported` | `GET /knowledge_graph` 可读取完成图谱；构建未完成时可能暂时返回空节点/空边 |
| nodes returned | `supported` | 完成图谱返回 `description`、`entity_name`、`entity_type`、`id`、`pagerank`、`source_id` |
| edges returned | `supported` | 完成图谱返回 `description`、`keywords`、`source`、`source_id`、`src_id`、`target`、`tgt_id`、`weight` |
| safe display fields | `supported` | 节点 hover 可展示 `entity_name`、`entity_type`、`description`、`pagerank`；边 hover 可展示 `source`、`target`、`description`、`keywords`、`weight` |
| unsafe/internal fields | `supported` | `source_id` 只能经权限过滤后转成可访问 documentIds；不展示原始 RagFlow JSON、未过滤 source_id、chunk ids、score、embedding、prompt/raw/text/content |
| node chat capability | `not-tested` | 未发现可验证的节点级问答 API；后续采用节点描述 + documentIds 受限 retrieve 的降级方案 |
| delete request | `supported` | 当前部署可用路径为 `DELETE /graph`，返回 `{"code":0,"data":{}}`；`DELETE /knowledge_graph` 返回后端缺少 `delete_knowledge_graph` |

结论：

- 当前 RagFlow 部署版本支持 GraphRAG 构建、状态和图谱读取接口：`POST /run_graphrag`、`GET /trace_graphrag`、`GET /knowledge_graph`。
- GraphRAG 构建耗时可能达到 5 分钟以上。短轮询时 `knowledge_graph` 可能返回空图，不能据此判断无节点/边。
- 当前部署删除图谱的真实可用路径为 `DELETE /graph`，不是官方文档中的 `DELETE /knowledge_graph`。
- 脚本已补充分层分类，RagFlow 业务错误包中的 405、extra input、缺失方法等场景会标记为 `unsupported`。
- `runGraphRag` / `traceGraphRag` / `getKnowledgeGraph` 可按官方路径进入 Phase 1；`deleteKnowledgeGraph` 按当前部署路径 `DELETE /graph` 封装，并保留路径兼容配置。
- 图谱构建必须作为后台长任务处理，前端只展示状态，不同步等待完成。

初始实现决策：

- 如果 trace 不返回节点/边，Phase 5/6 先按“节点能力不可用”降级，不阻塞图谱构建状态能力。
- 如果没有明确节点级问答 API，节点对话默认使用“图谱节点描述 + 可访问 documentIds 二次 retrieve + 现有会话链路”。
- 前端 hover 字段必须使用后端筛选后的安全字段，不能透出 RagFlow 原始 JSON。

## 脚本输出摘要

```markdown
## RagFlow Phase 0 Spike Summary

- Run ID: `2026-06-08T03-42-43-634Z-674izo`
- Base host: `http://47.116.171.63`
- Dataset name: `evomind-phase0-2026-06-08T03-42-43-634Z-674izo`
- Dataset ID: `cleaned-up`
- Document ID: `cleaned-up`
- GraphRAG requested: `true`
- GraphRAG trace attempts: `6`
- GraphRAG trace interval ms: `5000`

| Item | Status | Detail |
| --- | --- | --- |
| dataset | `supported` | created dataset 1af256b462ec11f1979cc9ff57f9fcdc |
| create dataset language | `unsupported` | POST /api/v1/datasets returned RagFlow code 101: language extra input is not permitted |
| upload meta_fields | `supported` | multipart meta_fields accepted |
| upload | `supported` | uploaded document 1b2cb77862ec11f1979cc9ff57f9fcdc |
| parse | `supported` | parse triggered for document 1b2cb77862ec11f1979cc9ff57f9fcdc |
| status polling | `supported` | document parsed with progress=1 |
| retrieve document_ids | `supported` | retrieved 1 chunks |
| metadata update | `supported` | document meta_fields update accepted |
| metadata filter | `supported` | request accepted; returned 1 chunks |
| delete document | `supported` | deleted document 6ce8d45062e911f193e77bdc3fb8acce |
| GraphRAG | `supported` | run, trace, graph, delete supported; completed graph verified manually |
| GraphRAG run | `supported` | POST accepted in 56ms; response={"task_id":"1f1bd9ae62ec11f1979cc9ff57f9fcdc"} |
| GraphRAG trace | `supported` | 6 trace response(s); latest progress=0.0196693 task=graphrag |
| GraphRAG graph | `supported` | completed graph returns nodes and edges from `data.graph` |
| GraphRAG nodes | `supported` | fields: id, entity_name, entity_type, description, source_id, pagerank |
| GraphRAG edges | `supported` | fields: source, target, src_id, tgt_id, description, keywords, source_id, weight |
| GraphRAG display fields | `supported` | backend whitelist can support node/edge hover details |
| GraphRAG node chat | `not-tested` | no documented node-level chat endpoint exercised; plan fallback is node description + authorized document_ids retrieval |
| GraphRAG delete | `supported` | DELETE /graph returned {"code":0,"data":{}} in manual verification |
```

## 接口差异记录

| Area | Expected | Actual | Impact on Phase 1 |
| --- | --- | --- | --- |
| dataset | 创建临时 dataset | supported | 可以封装正式 dataset create 能力 |
| create dataset language | 可能支持 `language=Chinese` | unsupported，字段不允许 | 正式实现不要传 `language`；如需语言能力，需寻找 RagFlow 支持字段 |
| upload meta_fields | 上传时携带 metadata | supported | 可以优先使用 multipart `meta_fields` 写入 document metadata |
| upload | 上传文档 | supported | 可以接入正式文档同步 |
| parse | 触发文档解析 | supported | 可以接入正式 parse job |
| status polling | 轮询 `run/progress/progress_msg` | supported | 可以映射本地解析状态 |
| retrieve document_ids | 支持指定 documentIds 召回 | supported | 节点对话的 documentIds 受限 retrieve 可行 |
| metadata update | 可能支持更新 document metadata | supported | 可以封装 metadata update；不同部署版本可能存在差异，仍需保留 405 降级 |
| metadata filter | 支持 metadata 条件 | supported | 后续可作为辅助过滤条件，但还需要更多复杂条件验证 |
| delete document | 删除临时 document | supported | 可以接入删除同步和清理 |
| GraphRAG | 支持 run/trace/get/delete | supported | run、trace、get、delete 均有可用路径；delete 路径与官方文档不同 |
| GraphRAG run | `POST /datasets/:id/run_graphrag` | supported | 返回 `task_id` |
| GraphRAG trace | `GET /datasets/:id/trace_graphrag` | supported | trace 只用于任务状态，不作为节点/边来源；`progress=1` 或 `Knowledge Graph done` 表示完成 |
| GraphRAG graph | `GET /datasets/:id/knowledge_graph` | supported | 节点/边应从该接口读取；构建未完成时可能为空 |
| GraphRAG nodes | `knowledge_graph.graph.nodes` 返回节点 | supported | 字段：`id/entity_name/entity_type/description/source_id/pagerank` |
| GraphRAG edges | `knowledge_graph.graph.edges` 返回边 | supported | 字段：`source/target/src_id/tgt_id/description/keywords/source_id/weight` |
| GraphRAG display fields | 可从 `knowledge_graph` 判断字段 | supported | hover 字段可按白名单实现 |
| GraphRAG node chat | 存在节点级问答 API 或可降级 | not-tested | 默认使用节点描述 + documentIds 受限 retrieve 的降级方案 |
| GraphRAG delete | `DELETE /datasets/:id/graph` | supported | 当前部署实际删除路径为 `/graph`；官方文档 `/knowledge_graph` 删除路径不可用 |

## Phase 1 决策

根据本次 spike 结论确认：

- 正式 `RagflowClient` 可先封装 dataset create、document upload、parse、status polling、retrieve、document delete。
- create dataset 不传 `language=Chinese`。
- upload document 支持 `meta_fields`，正式同步应优先在上传阶段写入 metadata。
- 可以封装 document `PUT` metadata update；同时保留 405/unsupported 降级，以兼容不同 RagFlow 部署版本。
- parse 状态可通过 document `run/progress/progress_msg` 轮询。
- retrieve 稳定支持 `document_ids` 限定，可支撑节点对话的二次受限召回。
- metadata filter 当前请求可接受，但需要更多条件组合验证后再作为正式权限边界。
- GraphRAG 构建、trace、读取图谱可按官方路径封装。
- GraphRAG 删除按当前部署实测路径 `DELETE /graph` 封装，并保留配置项兼容其他版本。
- 图谱构建可能超过默认 30 秒，需要后台 job 继续轮询，不应依赖前端请求同步等待。
- 节点问答第一版不依赖 RagFlow 节点级 API，先采用节点描述和 documentIds 受限召回方案。
