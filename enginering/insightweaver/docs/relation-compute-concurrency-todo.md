# 关系计算并发优化待办

> 创建时间：2026-09-10  
> 状态：待实施

## 当前并发现状

### compute 侧

| 组件 | 当前并发度 | 瓶颈等级 | 说明 |
|---|---|---|---|
| **构建任务队列** | **1**（单 worker 串行） | 🔴 高 | `drainBuildQueue` 用 `buildWorkerRunning` 标志防止并发，多租户排队等待 |
| **LLM 调用** | **3**（硬编码） | 🟡 中 | `RELATION_LLM_CONCURRENCY = 3`，digest 推断/主线审阅/证据审计等场景 |
| **DB 查询** | **无限制** | 🟢 低 | Node.js 默认连接池（pg 默认 10 连接），无显式限制 |
| **HTTP API** | **无限制** | 🟢 低 | Node.js HTTP server 无显式并发限制，受系统资源约束 |

### evomind API 侧

| 组件 | 当前并发度 | 瓶颈等级 | 说明 |
|---|---|---|---|
| **NestJS HTTP** | **无限制** | 🟢 低 | 受系统资源约束 |
| **Prisma 连接池** | **默认值** | 🟢 低 | 未显式配置，使用 Prisma 默认值 |

### 其他问题

- ❌ **无任务重试**：失败直接 `status='failed'`，无自动重试机制
- ❌ **无任务优先级**：所有任务 FIFO 排队
- ❌ **进程重启丢失 running 任务**：recover 只恢复 pending 状态

---

## 优化计划

### Phase 1：短期优化（1-2 周）

#### 1.1 构建队列并发度提升

**目标**：从单 worker 串行改为多 worker 并发

**改动位置**：`relationcompute/src/data-plane.ts` 的 `drainBuildQueue` 方法

**方案**：
```typescript
private async drainBuildQueue() {
  const concurrency = 3; // 可配置化
  const workers = Array.from({ length: concurrency }, () => this.worker());
  await Promise.all(workers);
}

private async worker() {
  while (this.buildQueue.length > 0) {
    const jobId = this.buildQueue.shift()!;
    this.queuedBuildIds.delete(jobId);
    await this.runBuild(jobId).catch(() => undefined);
  }
}
```

**工作量**：~20 行代码  
**收益**：多租户并发提升 3x

#### 1.2 LLM 并发度可配置化

**目标**：将硬编码的 `RELATION_LLM_CONCURRENCY = 3` 改为环境变量配置

**改动位置**：`relationcompute/packages/relation-semantic/src/index.ts`

**方案**：
```typescript
const RELATION_LLM_CONCURRENCY = Number(process.env.RELATION_LLM_CONCURRENCY) || 3;
```

**工作量**：~5 行代码  
**收益**：可根据 LLM API 配额动态调整

#### 1.3 任务失败自动重试

**目标**：失败任务自动重试 3 次（指数退避）

**改动位置**：`relationcompute/src/data-plane.ts` 的 `runBuild` 方法

**方案**：
```typescript
private async runBuild(jobId: string) {
  // ... 现有逻辑
  try {
    // ... 执行任务
  } catch (error) {
    const job = await this.getJob(jobId);
    if (job.attemptCount < 3) {
      // 重新入队，延迟重试
      const delay = Math.pow(2, job.attemptCount) * 1000;
      setTimeout(() => this.scheduleBuild(jobId), delay);
      return;
    }
    // 超过重试次数，标记失败
    await this.database.pool.query(
      `UPDATE relation_projection_jobs SET status = 'failed', ...`
    );
  }
}
```

**工作量**：~30 行代码  
**收益**：减少人工干预，提升可靠性

---

### Phase 2：中期优化（1-2 月）

#### 2.1 任务优先级调度

**目标**：支持任务优先级（高/中/低），高优先级任务优先执行

**改动**：
- 数据库表增加 `priority` 字段
- `scheduleBuild` 按 priority 排序
- 前端 build 按钮支持传 priority 参数

**工作量**：~100 行代码  
**收益**：关键任务（如用户主动触发）优先执行

#### 2.2 任务进度实时推送（SSE）

**目标**：前端通过 Server-Sent Events 实时接收任务进度

**改动**：
- compute 侧：`/builds/:jobId/stream` SSE 端点
- evomind API 侧：代理 SSE 流
- 前端：EventSource 替代轮询

**工作量**：~150 行代码  
**收益**：延迟从 2 秒降至 <100ms，减少轮询开销

---

### Phase 3：长期优化（3-6 月）

#### 3.1 引入 BullMQ 替代内存队列

**目标**：分布式任务调度，支持多实例部署

**技术栈**：
- BullMQ（基于 Redis）
- 支持：延迟任务、重复任务、优先级、死信队列

**改动**：
- `relationcompute` 引入 `bullmq` 依赖
- 替换 `buildQueue` 为 BullMQ Queue
- 添加 Redis 连接配置

**工作量**：~300 行代码  
**收益**：
- 多实例部署（水平扩展）
- 任务持久化（Redis）
- Dashboard UI（Bull Board）

#### 3.2 云原生队列

**目标**：大规模场景下使用云原生队列

**选项**：
- AWS SQS / 阿里云 MNS
- Google Cloud Tasks
- Azure Service Bus

**适用场景**：
- 多 region 部署
- 超高并发（>1000 QPS）
- 需要死信队列、消息过滤

---

## 实施优先级

| 优先级 | 任务 | 工作量 | 收益 | 建议时间 |
|---|---|---|---|---|
| 🔴 P0 | 构建队列并发度 | 20 行 | 3x 并发 | 本周 |
| 🔴 P0 | LLM 并发可配置 | 5 行 | 灵活调整 | 本周 |
| 🟡 P1 | 任务失败重试 | 30 行 | 可靠性提升 | 下周 |
| 🟡 P1 | 任务优先级 | 100 行 | 调度优化 | 本月 |
| 🟢 P2 | SSE 实时推送 | 150 行 | 体验提升 | 下月 |
| 🟢 P2 | BullMQ 替代 | 300 行 | 水平扩展 | 下季度 |

---

## 验收标准

### Phase 1 验收

- [ ] 同时触发 3 个 build 任务，观察是否并发执行（日志时间戳接近）
- [ ] 设置 `RELATION_LLM_CONCURRENCY=5`，观察 LLM 调用并发度
- [ ] 手动模拟 LLM 调用失败，观察是否自动重试 3 次

### Phase 2 验收

- [ ] 高优先级任务优先于低优先级任务执行
- [ ] SSE 推送进度，前端无需轮询

### Phase 3 验收

- [ ] 多实例部署，任务不重复执行
- [ ] Bull Board Dashboard 可视化任务队列

---

## 风险与注意事项

1. **LLM API 配额**：提高并发度前确认 API 配额，避免限流
2. **DB 连接池**：并发度提升后可能需要调整连接池大小
3. **Redis 依赖**：引入 BullMQ 后需部署 Redis，增加运维成本
4. **向后兼容**：任务表结构变更需考虑数据迁移

---

## 相关文档

- [关系计算代码 Review 报告](./relation-code-review.md)
- [关系大脑技术架构](./relation-brain-architecture.md)

---

**下次更新**：Phase 1 实施后
