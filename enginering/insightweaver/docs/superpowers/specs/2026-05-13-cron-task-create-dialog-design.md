# 定时任务创建对话框重构设计

## 背景

当前 `CreateCronTaskDialog` 组件（位于 `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`）使用紧凑的 grid 布局，计划类型通过简单的 select 切换。需要重构为与产品截图一致的表单布局，支持三种计划类型：单次定时、间隔循环、定期任务。

## 变更范围

### 修改文件

- `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

### 不修改文件

- 后端 API 不变
- 提交链路不变（仍通过 `onCreateCronTask` 发送消息到对话）

### 后端约束

根据 `ZclawCronSchedule` 类型定义（[apps/web/src/api/moudles/zclaw.ts](file:///c:/Users/zhang/workspace/yunzhishi/insightweaver/apps/web/src/api/moudles/zclaw.ts#L229-L234)），后端支持以下 schedule 类型：

```typescript
export type ZclawCronSchedule =
  | { type: 'once'; at: string }
  | { type: 'interval'; everyMinutes: number }
  | { type: 'daily'; time: string; timezone: string }
  | { type: 'cron'; expr: string; timezone?: string };
```

- 支持 `once`、`interval`、`daily`、`cron` 四种类型
- **不支持** `endAt` / `endTime` / `maxRuns` 等结束条件字段
- 每周任务使用 `cron` 类型实现（如 `0 9 * * 1` 表示每周一 09:00）
- 每月暂不支持（不在本次范围）

## 表单字段

按截图从上到下顺序：

### 1. 名称（必填）

- 标签：`名称 *`
- 输入框 placeholder：`请输入定时任务名称，如定时更新看板`
- 验证：非空

### 2. 消息内容（必填）

- 标签：`消息内容 *`
- 多行文本 placeholder：`描述你的需求，例如：总结今天的新闻。`
- 验证：非空

### 3. 计划（必填）

下拉选择器，三个选项：

#### 3a. 单次定时

- 描述文字：`单次定时：在指定时间执行一次任务。`
- 字段：
  - 设置时间：日期选择器 + 时间选择器（并排）
  - 日期默认值：当前日期
  - 时间默认值：下一个整点（如当前 21:19，则默认 22:00）

#### 3b. 间隔循环

- 描述文字：`间隔循环：按照固定时间频率重复执行，直到任务结束。`
- 字段：
  - 开始时间：日期 + 时间（并排），时间默认值为下一个整点
  - 循环频率：三个输入框并排 — `天`、`小时`、`分钟`，默认 `0 天 0 小时 1 分钟`
  - 执行时间预览：显示人性化描述，如 `从 2026-05-13 22:00 开始，每 1 小时执行一次`

#### 3c. 定期任务

- 描述文字：`定期任务：按日历周期重复执行，直到任务结束。`
- 字段：
  - 开始时间：日期 + 时间（并排），时间默认值为下一个整点
  - 计划周期：下拉选择（每天 / 每周）
    - **每天**：显示时间选择器（默认下一个整点）
    - **每周**：显示星期选择器（周一~周日，单选） + 时间选择器（默认下一个整点）
  - 结束时间：灰色文字 `永不结束` + 小问号图标（hover 提示：`任务将一直执行，需手动删除或停用`）
  - 执行时间计算：显示前 3 次执行时间预览
    - 示例：
      ```
      首次执行：05/13/2026 22:00
      第 2 次执行：05/14/2026 22:00
      第 3 次执行：05/15/2026 22:00
      ...
      ```

### 4. 底部操作栏

- 右侧：取消按钮 + 创建按钮
- 创建后任务默认启用，无需开关

## 数据结构变更

### CronCreateFormState 扩展

```typescript
type CronCreateScheduleType = 'once' | 'interval' | 'recurring';
type RecurringPeriod = 'daily' | 'weekly';
type WeekDay = 1 | 2 | 3 | 4 | 5 | 6 | 0; // 1=周一, 2=周二, ..., 0=周日

type CronCreateFormState = {
  name: string;
  prompt: string;
  scheduleType: CronCreateScheduleType;
  // once
  onceAt: string; // datetime-local 格式
  // interval
  intervalStartAt: string; // datetime-local 格式
  intervalDays: string;
  intervalHours: string;
  intervalMinutes: string;
  // recurring
  recurringStartAt: string; // datetime-local 格式
  recurringPeriod: RecurringPeriod;
  recurringTime: string; // HH:mm 格式
  recurringWeekDay: WeekDay; // 仅 weekly 时使用
};
```

### buildCronCreateInstruction 适配

提交给后端的 km-cron JSON 块格式：

#### once

```json
{
  "action": "create",
  "name": "任务名称",
  "prompt": "任务内容",
  "schedule": {
    "type": "once",
    "at": "2026-05-13T22:00:00.000Z"
  }
}
```

#### interval（间隔循环）

```json
{
  "action": "create",
  "name": "任务名称",
  "prompt": "任务内容",
  "schedule": {
    "type": "interval",
    "everyMinutes": 60
  }
}
```

- `everyMinutes` = 天×1440 + 小时×60 + 分钟
- 后端不支持 `startAt`，间隔循环从创建时开始计时

#### recurring（定期任务）

**每天**：使用 `daily` 类型

```json
{
  "action": "create",
  "name": "任务名称",
  "prompt": "任务内容",
  "schedule": {
    "type": "daily",
    "time": "09:00",
    "timezone": "Asia/Shanghai"
  }
}
```

**每周**：使用 `cron` 类型

```json
{
  "action": "create",
  "name": "任务名称",
  "prompt": "任务内容",
  "schedule": {
    "type": "cron",
    "expr": "0 9 * * 1",
    "timezone": "Asia/Shanghai"
  }
}
```

- cron 表达式格式：`分 时 日 月 周`
- 例如：`0 9 * * 1` = 每周一 09:00
- 星期映射：周一=1, 周二=2, ..., 周日=0

### 人性化展示文本生成

前端需要生成人性化描述文本，用于：
1. 表单内的"执行时间计算"预览
2. 任务列表中的 schedule 显示（现有 `formatCronSchedule` 函数需要增强）

示例：
- `从 2026-05-13 22:00 开始，每 1 小时执行一次`
- `从 2026-05-13 22:00 开始，每天 09:00 执行`
- `从 2026-05-13 22:00 开始，每周一 09:00 执行`

### 执行时间预览计算逻辑

根据计划类型计算前 3 次执行时间：

- **单次定时**：仅显示首次执行时间
- **间隔循环**：从开始时间起，按间隔计算前 3 次
- **定期任务-每天**：从开始时间起，每天同一时间计算前 3 次
- **定期任务-每周**：从开始时间起，找到下一个目标星期几，计算前 3 次

## 验证规则

- 名称：必填
- 消息内容：必填
- 单次定时：时间必须有效且 >= 当前时间
- 间隔循环：总间隔时间 >= 1 分钟
- 定期任务：
  - 每周：必须选择星期几

## UI 风格

- 沿用现有 Dialog 组件的样式（圆角、边框、阴影）
- 表单字段使用垂直堆叠布局，每个字段独立区块
- 计划类型切换时，下方区域条件渲染
- 创建按钮使用主色背景，取消按钮使用边框样式

## 错误处理

- 表单验证失败时 toast 提示具体错误信息
- 提交失败时 toast 提示错误
- 创建成功后关闭对话框，刷新定时任务列表

## 注意事项

1. 后端不支持结束时间/结束次数，任务一旦创建将永久执行，直到用户手动删除或停用
2. 前端通过灰色文字"永不结束" + 小问号提示用户，hover 显示"任务将一直执行，需手动删除或停用"
3. 每月任务不在本次实现范围内
