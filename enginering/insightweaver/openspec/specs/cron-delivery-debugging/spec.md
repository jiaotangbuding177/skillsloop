# 定时任务结果投递失败排查经验

## 故障现象

- 用户创建定时任务，任务到时间后 km-agent 日志显示执行成功
- 但前端运行结果页显示 `status: "error"`，无摘要内容
- 错误信息：`Channel is required (no configured channels detected). Set delivery.channel explicitly or use a main session with a previous channel.`

## 排查链路

### 1. 定位错误来源

```
浏览器 console → insightweaver 前端 → insightweaver API → km-agent
```

错误信息 "Channel is required" 不是 insightweaver 前端或 API 产生的，需要追到 km-agent 代码。

### 2. 搜索错误消息

```bash
grep -r "Channel is required" km-agent/src/
```

命中 `km-agent/src/infra/outbound/channel-selection.ts:201`：

```typescript
if (configured.length === 0) {
  throw new Error("Channel is required (no configured channels detected).");
}
```

### 3. 追踪调用链（从终端往上游追）

```
channel-selection.ts:201
  ↑ resolveMessageChannelSelection({ cfg })
  ↑ delivery-target.ts:80       resolveDeliveryTarget()
  ↑ run.ts:201                  resolveCronDeliveryContext()
  ↑ run.ts:462                  定时任务执行入口
  ↑ delivery.ts:50              resolveCronDeliveryPlan()
  ↑ initial-delivery.ts:27      resolveInitialCronDelivery()
  ↑ jobs.ts:557                 createJob()
  ↑ cron-routes.ts:106          insightweaver API → km-agent
```

### 4. 找到根因

**两个关键位置的组合导致**：

① **km-agent `initial-delivery.ts:27-35`**：isolated cron 任务默认 delivery mode 为 `"announce"`，但不设置 channel：
```typescript
export function resolveInitialCronDelivery(input: CronJobCreate): CronDelivery | undefined {
  if (input.sessionTarget === "isolated" && input.payload.kind === "agentTurn") {
    return { mode: "announce" };  // ← 无 channel 字段
  }
}
```

② **km-agent `delivery-dispatch.ts:63-71`**：`bestEffort` 默认为 `false`，导致 delivery 失败时整条 run 标 `error`：
```typescript
export function resolveCronDeliveryBestEffort(job: CronJob): boolean {
  // ...
  return false;  // ← 默认不 bestEffort
}
```

**完整因果链**：
```
insightweaver 创建 cron 任务 → 未传 delivery.channel
  → initial-delivery 返回 { mode: "announce" }，无 channel
  → 定时触发时 → resolveCronDeliveryPlan 回退到 "last"
  → resolveDeliveryTarget → resolveMessageChannelSelection 失败
  → bestEffort=false → failDeliveryTarget() → run status="error"
```

### 5. 修复

`delivery-dispatch.ts:63-71` — 当 `delivery.mode === "announce"` 且未显式配置 `channel` 时，默认 `bestEffort = true`：

```typescript
if (job.delivery?.mode === "announce" && !job.delivery.channel) {
  return true;
}
```

**零 impact 修改**：
- 已显式配置 `delivery.channel` 的任务不受影响
- 有 `delivery.bestEffort` 显式值的任务不受影响
- 仅影响"默认 announce 模式但无 channel"的场景

## 经验教训

### 排查经验

1. **从终端错误往上游追踪**：不要在前端代码里找根因，沿着调用链一层层回溯
2. **跨项目联合排查**：insightweaver 的前端报错，根因在 km-agent，需要同时检查两个项目
3. **API 返回值是关键证据**：直接调用 `/api/zclaw/cron/jobs` 接口查看 `lastRun.error`，比猜测有效得多

### 设计经验

4. **默认行为应覆盖最常见的场景**：定时任务最主要的功能是"执行并返回结果"，delivery channel 投递是增强功能，不应阻断核心流程
5. **fail-safe over fail-fast**：对于非关键的增强功能，默认"尽力而为"比"严格要求"更合理
6. **bestEffort 模式的设计模式**：参考 `delivery-dispatch.ts:577-592` 已有的 bestEffort=true 路径，LLM 执行成功 + delivery 失败 → run status="ok"

### 团队知识

7. **多企业共用 km-agent 的 channel 隔离**：当前 km-agent 的 channel 解析不区分 enterprise，多企业场景下 delivery channel 无法自动推断。短期用 bestEffort 兜底，长期需要 enterprise-level channel 配置
8. **CronJob.delivery 字段**：`{ mode, channel?, to?, accountId?, bestEffort? }`。`channel + to + accountId` 三元组唯一标识投递目标，可区分多企业