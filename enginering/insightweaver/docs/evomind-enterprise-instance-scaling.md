# EvoMind 企业级实例池与共享知识库方案说明

## 1. 结论先行

EvoMind 接入 zclaw-edu 的“实例池 + 用户绑定 + 后续固定路由”逻辑，但不能照搬 zclaw-edu 的单企业模型。zclaw-edu 可以近似看作一个固定企业；EvoMind 是多企业产品，因此实例池必须以企业为隔离边界。

本方案的核心结论：

```text
每个企业维护自己的 EvoMind / ZClaw KM Gateway 实例池。
新成员首次真正使用企业空间 Agent 时，只能从该企业实例池中分配实例。
分配成功后，用户在该企业空间固定绑定到同一实例。
共享知识库必须保持企业级一致，不能随着用户绑定实例漂移。
```

这不是自动购买云服务器的弹性伸缩。Phase 2 只做“手动实例池 MVP”：运维先部署实例，平台超管在后台登记实例，后端按健康状态和容量为新用户分配实例。自动创建机器、自动释放机器、平滑缩容和跨实例迁移都不在 Phase 2 范围内。

## 2. 当前实现口径

### 2.1 数据模型

`enterprise_openclaw_instances` 从“每企业一条配置”升级为“每企业多实例池”：

| 字段 | 说明 |
| --- | --- |
| `enterpriseId` | 所属企业，不再单字段唯一 |
| `instanceKey` | 企业内唯一实例标识，例如 `default`、`prod-01` |
| `name` | 后台展示名 |
| `status` | Phase 2 只使用 `active` / `disabled` |
| `kmAgentBaseUrl` | EvoMind / KM Agent 基础地址 |
| `gatewayBaseUrl` | ZClaw KM Gateway 地址，可为空 |
| `gatewayTokenEncrypted` | 加密保存的 Gateway token |
| `gatewayTokenMask` | 脱敏字段，仅兼容 API，不在实例池列表展示 |
| `healthStatus` | 健康检查状态，调度兼容 `ok` / `healthy` |
| `lastHealthCheckAt` | 最近健康检查时间 |
| `weight` | 调度权重 |
| `maxAgents` | 建议绑定上限，不等于真实并发上限 |
| `activeAgents` | 当前有效企业 Agent 绑定数 |
| `sharedWorkspacePrimary` | 是否为该企业共享知识库主实例 |
| `region` / `env` | 运维标记 |
| `lastError` | 最近健康检查错误 |
| `metadata` | 扩展备注 |

关键约束：

```text
@@unique([enterpriseId, instanceKey])
```

`zclaw_agent_instances` 增加 `enterpriseId`，用于表达“同一用户在同一企业只有一个有效企业 Agent 绑定”。实际路由仍以 `enterpriseOpenClawInstanceId` 为准。

历史迁移策略：

1. 旧企业单实例迁移为 `instanceKey = "default"`。
2. 旧用户绑定继续保留原 `enterpriseOpenClawInstanceId`。
3. 从旧绑定回填 `zclaw_agent_instances.enterpriseId`。
4. 根据有效绑定数回填 `activeAgents`。
5. 每个企业选择一台旧实例设为 `sharedWorkspacePrimary = true`，优先 `instanceKey = "default"`，否则选择最早创建的未删除实例。

### 2.2 状态语义

Phase 2 只保留两个可配置状态：

| 状态 | 是否参与新用户分配 | 已绑定用户是否继续访问 | 说明 |
| --- | --- | --- | --- |
| `active` | 是 | 是 | 健康检查通过后可承接新绑定 |
| `disabled` | 否 | 是 | 停止新分配，但老绑定用户仍固定路由到该实例 |

`draining`、平滑缩容、绑定迁移和自动化扩缩容不在当前阶段实现，也不在后台页面暴露入口。

### 2.3 后台入口

管理入口仍是管理员后台的“组织实例”页面，仅平台超管可见可用。普通组织管理员不配置实例池。

页面展示口径：

| 区域 | 内容 |
| --- | --- |
| 筛选区 | 企业、状态、关键词、刷新、新增实例 |
| 主列表 | 企业/实例、状态/健康、容量、地址、权重、区域/环境、操作 |
| 常用操作 | 编辑、测试、统计、详情 |
| 详情展开 | 完整 URL、最近错误、绑定用户、启用/停用、删除 |

列表不展示 token 或 token mask。token 只在新增/编辑表单中作为配置输入；编辑时留空表示不修改当前 token。

### 2.4 API 口径

基础路径：

```text
/api/zclaw/admin/enterprise-instances
```

Phase 2 接口：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/api/zclaw/admin/enterprise-instances?enterpriseId=&status=&healthStatus=&keyword=` | 查询实例池 |
| `POST` | `/api/zclaw/admin/enterprise-instances` | 新增实例 |
| `PUT` | `/api/zclaw/admin/enterprise-instances/{instanceId}` | 编辑实例 |
| `POST` | `/api/zclaw/admin/enterprise-instances/{instanceId}/enable` | 启用实例 |
| `POST` | `/api/zclaw/admin/enterprise-instances/{instanceId}/disable` | 停用实例 |
| `POST` | `/api/zclaw/admin/enterprise-instances/{instanceId}/test` | 连接测试并写入健康状态 |
| `POST` | `/api/zclaw/admin/enterprise-instances/{instanceId}/refresh-active-agents` | 重新统计绑定数 |
| `GET` | `/api/zclaw/admin/enterprise-instances/{instanceId}/agents` | 查看绑定用户 |
| `DELETE` | `/api/zclaw/admin/enterprise-instances/{instanceId}` | 软删除实例 |

不暴露 `drain` 接口。删除实例时，如果仍有有效绑定，后端返回错误：

```text
该实例仍有绑定用户，请先迁移或清空绑定后再删除
```

新增实例请求体示例：

```json
{
  "enterpriseId": "enterprise-id",
  "instanceKey": "prod-01",
  "name": "生产实例 01",
  "kmAgentBaseUrl": "http://10.0.0.12:18789",
  "gatewayBaseUrl": "http://10.0.0.12:18789",
  "gatewayToken": "only-submit-in-admin-form",
  "status": "disabled",
  "weight": 100,
  "maxAgents": 50,
  "region": "cn-shanghai",
  "env": "prod"
}
```

编辑实例时：

1. 不允许修改 `enterpriseId`。
2. `gatewayToken` 为空表示保留旧 token。
3. `status` 只接受 `active` / `disabled`。

## 3. 调度与固定绑定

企业空间请求解析 target 的流程：

```text
请求携带 enterpriseId
  -> 校验用户是该企业有效成员
  -> 查询用户在该企业是否已有有效 ZclawAgentInstance 绑定
    -> 有绑定：读取绑定的 enterpriseOpenClawInstanceId，固定路由到原实例
    -> 无绑定：从该企业实例池选择一台可用实例
      -> 远端 bootstrap
      -> 创建企业 Agent 绑定
      -> 刷新实例 activeAgents
      -> 后续请求固定路由到这台实例
```

候选实例必须满足：

1. `enterpriseId = 当前企业 id`
2. `isDeleted = false`
3. `status = active`
4. `healthStatus IN ("ok", "healthy")`
5. 未达到 `maxAgents`，如果设置了 `maxAgents`

排序策略：

1. `activeAgents / maxAgents` 使用率低者优先。
2. 使用率相同，`weight` 高者优先。
3. 仍相同，创建时间早者优先，保证稳定分配。

企业隔离规则：

| 场景 | 规则 |
| --- | --- |
| 企业 A 新用户首次使用企业 Agent | 只能从企业 A 的实例池分配 |
| 企业 A 无可用实例 | 返回明确错误，不 fallback 到企业 B |
| 用户同时属于企业 A 和 B | 两个企业分别绑定实例 |
| 企业实例被 `disabled` | 不接收新绑定，旧绑定继续可用 |

## 4. 共享知识库方案

### 4.1 风险判断

每企业多实例池会影响“共享知识库”的前提是：共享知识库数据是否跟随某一台实例本地存储。

如果同一企业的不同用户被分配到不同 EvoMind/KM Agent 实例，而共享知识库又存在各实例本地目录，那么用户会看到不同的共享知识库内容。这会破坏企业共享知识库的一致性。

因此本方案明确要求：

```text
共享知识库必须是企业级共享资源，不能随着用户绑定实例漂移。
```

### 4.2 Phase 2 决策

Phase 2 采用“企业共享工作区主实例”方案，不做跨实例共享知识库迁移。

规则：

1. 每个企业必须显式指定一台共享工作区主实例，即 `sharedWorkspacePrimary = true`。
2. 共享知识库查看、上传、编辑、删除、排序等共享工作区接口固定路由到该主实例。
3. 用户个人 Agent、会话、记忆等仍按用户绑定实例固定路由。
4. 同一企业所有成员看到同一份共享知识库。
5. 主实例必须保持 `active`；如果不可用，共享知识库相关功能返回“组织共享工作区不可用”。
6. 主实例不能直接停用或删除；如需调整，先把另一台实例设为主实例。

当前实现不再依赖 `instanceKey = "default"` 作为主实例判断条件。迁移时会自动把每个企业当前已有实例设为主实例；如果一个企业已有多台实例，则优先选择 `instanceKey = "default"` 的实例，否则选择最早创建的实例。

```text
共享工作区主实例 = 该企业 sharedWorkspacePrimary = true 的实例
```

后台新增/编辑实例时提供“设为共享知识库主实例”勾选项，也可以在实例详情中把非主实例切换为主实例。后端会在事务内取消同企业其他实例的主实例标记，并通过唯一索引保证每个企业最多只有一台未删除主实例。

### 4.3 后续演进

更长期的共享知识库方案有两种：

| 方案 | 说明 | 适用阶段 |
| --- | --- | --- |
| 共享存储 | 多台实例挂载同一企业共享工作区存储，如 NAS、对象存储、分布式文件系统 | Phase 3/4 |
| 主实例路由 | 共享知识库固定走企业主实例，个人 Agent 仍走用户绑定实例 | Phase 2 |

如果以后要支持平滑缩容或自动化扩缩容，推荐演进为共享存储。否则主实例会成为共享知识库的单点。

## 5. 运维落地流程

### 5.1 新增实例

1. 运维部署 EvoMind / ZClaw KM Gateway 实例。
2. 验证 `/api/km/me`、`/api/km/bootstrap`、聊天、文件、记忆、cron 等接口。
3. 平台超管在“组织实例”中新增实例。
4. 初始状态建议填 `disabled`。
5. 点击“测试”，健康状态变为 `ok` 后，再启用为 `active`。
6. 新实例开始承接该企业的新用户绑定。

### 5.2 停用实例

1. 点击“停用”，实例变为 `disabled`。
2. 新用户不再分配到该实例。
3. 已绑定用户继续访问该实例。
4. 有绑定用户时不能直接删除实例。

### 5.3 删除实例

Phase 2 只允许软删除无有效绑定的实例。

删除前必须确认：

1. `activeAgents = 0`。
2. 不是该企业共享工作区主实例。
3. 后台“绑定用户”列表为空。

如果仍有绑定用户，不能直接删除。当前阶段不提供自动迁移。

## 6. 120 并发容量规划

120 并发不能只靠 `maxAgents` 静态字段保证。`maxAgents` 是调度层绑定上限，不等价于服务器真实并发上限。

初始建议：

```text
单实例压测基线：30-50 并发
120 并发目标：至少 3-4 台 active 实例
热备：至少 1 台 disabled 实例
```

示例：

| 实例 | 状态 | 计划并发 | 用途 |
| --- | --- | --- | --- |
| `default` | active | 30-40 | 可作为迁移后的共享工作区主实例 + 正常调度 |
| `prod-02` | active | 30-40 | 正常调度 |
| `prod-03` | active | 30-40 | 正常调度 |
| `prod-04` | active | 30-40 | 高峰冗余 |
| `standby-01` | disabled | 30-40 | 热备 |

压测必须覆盖：

1. SSE 流式聊天并发。
2. 文件上传、下载、预览。
3. 共享知识库查看和上传。
4. workspace 列表和目录操作。
5. 记忆读写。
6. cron 列表和结果读取。
7. Gateway 鉴权。

压测后把真实能力回填到：

```text
maxAgents
weight
metadata.capacity
metadata.spec
```

## 7. 分阶段计划

### Phase 1：文档与现状梳理

完成本文档，明确企业实例池、固定绑定、后台管理、共享知识库一致性和 120 并发规划。

### Phase 2：手动实例池 MVP

目标：

1. 每企业多实例表结构。
2. 平台超管后台实例池 CRUD。
3. 手动健康检查。
4. 新用户按企业实例池分配并固定绑定。
5. `disabled` 停止新分配。
6. token 不在列表展示。
7. 共享知识库固定走显式配置的企业共享工作区主实例。

不做：

1. `draining`。
2. 自动买机器。
3. 自动释放机器。
4. 跨实例数据迁移。
5. 自动缩容。

### Phase 3：容量与稳定性增强

目标：

1. 定时健康检查。
2. `activeAgents` 自动校准。
3. 容量预警。
4. 共享知识库主实例健康告警。
5. 120 并发压测和容量参数回填。

### Phase 4：共享存储与迁移能力

目标：

1. 共享知识库从主实例模式演进为共享存储，或支持主实例切换。
2. 建设用户 Agent 迁移能力。
3. 迁移 workspace、memory、conversation、cron 等远端数据。
4. 迁移完成后切换 `enterpriseOpenClawInstanceId`。

### Phase 5：自动化扩缩容

目标：

1. 接入云厂商 API 或 Kubernetes。
2. 自动创建实例。
3. 自动注册到企业实例池。
4. 按负载、错误率、空闲时长做扩缩容决策。

## 8. 调度策略补充

企业实例池支持按企业切换调度策略：

1. `recent_usage_first`：默认策略，近 7 天使用率优先。
2. `smooth_weighted_round_robin`：可选策略，平滑加权轮询。

两种策略都只影响新用户首次进入企业空间时的实例选择。已绑定用户继续固定走原实例，不自动迁移。

通用候选条件：

1. 只在当前企业实例池内选择。
2. 实例必须 `active`。
3. 健康状态必须为 `ok` 或 `healthy`。
4. 实例未删除。
5. 未达到 `maxAgents`。

`recent_usage_first` 规则：

1. 统计每台候选实例近 7 天有企业会话或消息活动的去重用户数。
2. 有 `maxAgents` 时，按 `recentActiveUsers / maxAgents` 使用率低者优先。
3. 未设置 `maxAgents` 时，按 `recentActiveUsers` 低者优先。
4. 使用率相同，再按 `weight` 高者优先。
5. 仍相同，按创建时间和 ID 稳定排序。

`smooth_weighted_round_robin` 规则：

1. 每次新用户分配时，读取企业 `instanceAssignmentState`。
2. 每台候选实例的 `currentWeight += weight`。
3. 选择 `currentWeight` 最大的实例。
4. 被选中实例的 `currentWeight -= totalWeight`。
5. 保存新的 `instanceAssignmentState`。

示例：A 权重 100、B 权重 200，长期新用户分配比例约为 1:2。新增 B 实例后，B 从下一次分配开始按权重参与轮询，不会因为是新机器而承接全部新用户。

## 9. 测试用例

### 9.1 数据迁移

1. 旧企业单实例迁移后生成 `instanceKey = default`，并自动设为共享知识库主实例。
2. 旧用户绑定仍指向原实例。
3. 旧用户请求仍路由到原实例。
4. `activeAgents` 与有效绑定数一致。

### 9.2 调度隔离

1. 企业 A 新用户只分配到企业 A 的可用实例。
2. 企业 B 新用户只分配到企业 B 的可用实例。
3. 企业 A 实例全部不可用时，不 fallback 到企业 B。
4. 已绑定用户优先使用绑定实例，即使该实例已 `disabled`。

### 9.3 状态和容量

1. `disabled` 不参与新分配。
2. `error` / `unhealthy` 不参与新分配。
3. 达到 `maxAgents` 的实例不参与新分配。
4. 使用率相同时，`weight` 高者优先。

### 9.4 后台页面

1. 列表不展示 token。
2. 页面不出现排空按钮或排空状态。
3. 常用操作单行展示，详情展开显示低频操作。
4. 长企业名、长实例名、长 URL 不撑爆列表。

### 9.5 共享知识库

1. 同一企业不同用户即使绑定到不同个人实例，也看到同一份共享知识库。
2. 共享工作区读写固定走企业主实例。
3. 主实例不可用时，共享知识库返回明确错误。
4. 共享知识库权限仍按企业成员和共享工作区权限判断。

### 9.6 权限

1. 只有平台超管能访问实例池页面。
2. 普通组织管理员不能调用实例池管理 API。
3. token 明文不出现在列表或接口响应中。

## 10. 上线清单

上线前：

1. 数据迁移已在测试库验证。
2. 至少一个企业配置多台实例。
3. 每个启用实例健康检查通过。
4. 每个企业明确共享工作区主实例。
5. 后台页面只对平台超管开放。
6. token 加密密钥已配置。
7. 旧用户绑定验证通过。

上线后：

1. 观察新用户是否只分配到当前企业实例池。
2. 观察旧用户是否仍走原绑定。
3. 检查 `activeAgents` 是否准确。
4. 检查共享知识库不同用户看到的内容是否一致。
5. 检查网关日志是否有 401/403 或路由错误。
6. 分批启用新实例，不一次性切入全部流量。

## 11. 一句话解释给非技术同事

EvoMind 的实例池不是系统自动买服务器，而是平台超管把每个企业可用的 EvoMind 服务器登记到后台；企业新成员首次使用时，系统从该企业自己的服务器池里挑一台并绑定，之后这个成员在该企业空间的个人 Agent 请求都固定走这台服务器。企业共享知识库作为企业级资源保持统一入口，保证同一企业成员看到的是同一份共享内容。
