# 知识库看板数据说明

## 使用对象与权限

知识库看板用于企业所有者和管理员查看企业共享工作区中的文档概况、分类、存储用量与最近更新文件。接口为 `GET /api/dashboard/knowledge-base?enterpriseId=...`，沿用企业管理员鉴权和企业隔离。

知识库数据源与 EvoMind 共享工作区文件树一致，不单独维护知识库副本。

## 指标口径

| 模块 | 口径 | 数据来源 |
| --- | --- | --- |
| 分类 | 共享工作区**根目录下一级文件夹**（含空文件夹）；根目录散落文件归入「其他」 | `listEnterpriseSharedWorkspaceItems` 完整树 |
| 全部文档 | 当前筛选条件下可见文件总数 | 文件条目（排除 `对话附件`） |
| 最近文档 | 按 `updatedAt` 降序，最多 8 条（仅「全部文档」视图） | 同上 |
| 分类文档列表 | 选中某一级文件夹时，展示该目录下**全部文件**（含子文件夹内文件） | `documents` 按一级路径段归类 |
| 存储用量 | 共享区「全部文档」`sizeBytes` 之和 / `sharedWorkspaceQuotaBytes`（无配额显示 `∞`；紧凑格式如 `1.2G`） | `GET /api/dashboard/knowledge-base` 的 `storage`（内存对已枚举文件求和，无额外扫盘） |
| 部门筛选 | 下拉选项来自 `enterprise_departments`（按 `sortOrder`）；文件过滤仍按 org-share 部门前缀或 owner 部门 | `enterprise_departments` + `shared_workspace_org_shares` + `enterpriseMembership` |
| 上传者 | 最近匹配的路径 owner | `shared_workspace_path_owners` |

## 分类规则

- 一级文件夹来自共享工作区 flat tree：**有子路径的文件**、**空文件夹条目**均会出现在侧边栏。
- 文件 `categoryKey` = 路径第一段（如 `TTFA Demo 视频/子目录/a.mp4` → `TTFA Demo 视频`）。
- 根目录散落文件（无 `/` 的单文件）归入「其他」。
- 分类计数基于**全量文档**（不受部门/搜索筛选影响），避免切换筛选后文件夹消失。

## 字段可行性

| 字段 | 真实来源 | 无数据时 |
| --- | --- | --- |
| `title` / `typeLabel` | 文件名与扩展名映射 | `文件` |
| `categoryKey` | 一级文件夹名或 `uncategorized` | — |
| `updatedAt` / `relativeTime` | 文件 `updatedAt` | `—` |
| `fileSizeLabel` | 文件 `size` | `—` |
| `uploadedBy` / `lastUsedBy` | path owner + membership | 姓名 `—`，部门 `暂无` |
| `department` | org-share 部门名，否则 owner 部门 | `—` |
| `citationCount` | 暂无埋点 | `0`（API 仍返回；前端暂不展示） |
| `isStarred` | 暂无持久化 | `false` |
| `createdAt` | API 无创建时间 | `—` |
| 版本历史 / 引用记录 | 暂无埋点 | `暂无`（API/详情构造仍保留；前端暂不展示） |

## 过滤与搜索

- `department`：服务端过滤；`全部部门` 表示不过滤。筛选项列表来自企业部门主数据，不在前端写死。
- `search`：对 `title`、`path`、`typeLabel`、上传者姓名做大小写不敏感匹配。
- `categoryKey`：服务端过滤；`other` 表示根目录散落文件。
- 页面选中具体分类时，主列表展示 `documents` 全量（非 `recentDocuments` 前 8 条）。

## 同步与缓存

- 共享工作区枚举结果按 `enterpriseId` 内存缓存 5 分钟。
- km-agent / 主实例不可用时返回 `sync.status = unavailable`，文档列表为空，页面展示空态提示。
- 侧边栏「已使用」直接使用 dashboard API 的 `storage`（与「全部文档」同集合），不再额外请求个人 `workspace/usage`。

## 不在本期

- 引用次数 / 打开记录埋点（前端已隐藏「引用 N 次」「被引用次数」「版本记录」「最近引用记录」等占位 UI）
- 用户星标收藏持久化
- SOP / 产品 / 客户 / 培训 人工打标
- Ragflow 全文检索（搜索仅文件名 / 路径）

## 排障

1. 确认企业主实例与 km-agent 可用，且调用方具备企业管理员权限。
2. 对比 `GET /api/zclaw/shared-workspace/...` 与看板返回文件是否一致。
3. 空文件夹未出现时，检查 flat tree 是否包含对应 folder 条目。
4. 存储显示异常时，核对 `storage.usedLabel` 是否等于返回文档 `sizeBytes` 之和的紧凑格式，并确认未混入个人 `workspace/usage`。
