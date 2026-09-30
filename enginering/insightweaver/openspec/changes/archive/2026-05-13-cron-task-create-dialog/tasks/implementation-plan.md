# 定时任务创建对话框重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 `CreateCronTaskDialog` 组件，支持单次定时、间隔循环、定期任务三种计划类型，UI 与产品截图一致。

**Architecture:** 在现有 `WorkbenchRailPanel.tsx` 中扩展 `CronCreateFormState` 类型和 `CreateCronTaskDialog` 组件，新增辅助函数处理时间计算和 cron 表达式生成。所有变更集中在单个文件内。

**Tech Stack:** React, TypeScript, Tailwind CSS, Radix UI Dialog, lucide-react icons

---

### Task 1: 扩展类型定义

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx:125-134`

- [ ] **Step 1: 替换旧的类型定义**

将现有的 `CronCreateScheduleType` 和 `CronCreateFormState` 替换为：

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

- [ ] **Step 2: 验证类型编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS (no type errors related to these types)

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "refactor: expand cron create form state types"
```

---

### Task 2: 新增辅助函数

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` (在 `buildInitialCronCreateForm` 之前插入)

- [ ] **Step 1: 添加 getNextWholeHour 函数**

在 `toDatetimeLocalValue` 函数之后添加：

```typescript
function getNextWholeHour(): Date {
  const now = new Date();
  const next = new Date(now);
  next.setHours(now.getHours() + 1, 0, 0, 0);
  return next;
}
```

- [ ] **Step 2: 添加 getWeekDayLabel 函数**

```typescript
function getWeekDayLabel(day: WeekDay): string {
  const labels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  return labels[day === 0 ? 0 : day];
}
```

- [ ] **Step 3: 添加 buildCronExpression 函数**

```typescript
function buildCronExpression(period: RecurringPeriod, time: string, weekDay?: WeekDay): string {
  const [hours, minutes] = time.split(':').map(Number);
  if (period === 'daily') {
    return `${minutes} ${hours} * * *`;
  }
  // weekly
  const cronWeekDay = weekDay === 0 ? 0 : weekDay;
  return `${minutes} ${hours} * * ${cronWeekDay}`;
}
```

- [ ] **Step 4: 添加 formatSchedulePreview 函数**

```typescript
function formatSchedulePreview(form: CronCreateFormState): string {
  if (form.scheduleType === 'once') {
    const date = new Date(form.onceAt);
    return `单次执行：${formatDateForPreview(date)}`;
  }
  if (form.scheduleType === 'interval') {
    const parts: string[] = [];
    const days = Number(form.intervalDays);
    const hours = Number(form.intervalHours);
    const minutes = Number(form.intervalMinutes);
    if (days > 0) parts.push(`${days} 天`);
    if (hours > 0) parts.push(`${hours} 小时`);
    if (minutes > 0) parts.push(`${minutes} 分钟`);
    const intervalStr = parts.length > 0 ? parts.join('') : '1 分钟';
    const startDate = new Date(form.intervalStartAt);
    return `从 ${formatDateForPreview(startDate)} 开始，每 ${intervalStr} 执行一次`;
  }
  // recurring
  const startDate = new Date(form.recurringStartAt);
  if (form.recurringPeriod === 'daily') {
    return `从 ${formatDateForPreview(startDate)} 开始，每天 ${form.recurringTime} 执行`;
  }
  // weekly
  const dayLabel = getWeekDayLabel(form.recurringWeekDay);
  return `从 ${formatDateForPreview(startDate)} 开始，${dayLabel} ${form.recurringTime} 执行`;
}

function formatDateForPreview(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
```

- [ ] **Step 5: 添加 computeNextExecutions 函数**

```typescript
function computeNextExecutions(form: CronCreateFormState, count = 3): string[] {
  const results: string[] = [];

  if (form.scheduleType === 'once') {
    const date = new Date(form.onceAt);
    results.push(formatExecutionLabel(1, date));
    return results;
  }

  if (form.scheduleType === 'interval') {
    const totalMinutes = Number(form.intervalDays) * 1440 + Number(form.intervalHours) * 60 + Number(form.intervalMinutes);
    if (totalMinutes < 1) return [];
    let current = new Date(form.intervalStartAt);
    for (let i = 1; i <= count; i++) {
      results.push(formatExecutionLabel(i, current));
      current = new Date(current.getTime() + totalMinutes * 60 * 1000);
    }
    return results;
  }

  // recurring
  let current = new Date(form.recurringStartAt);
  const [targetHours, targetMinutes] = form.recurringTime.split(':').map(Number);

  if (form.recurringPeriod === 'daily') {
    for (let i = 1; i <= count; i++) {
      const execDate = new Date(current);
      execDate.setHours(targetHours, targetMinutes, 0, 0);
      results.push(formatExecutionLabel(i, execDate));
      current = new Date(execDate);
      current.setDate(current.getDate() + 1);
    }
    return results;
  }

  // weekly
  const targetDay = form.recurringWeekDay === 0 ? 0 : form.recurringWeekDay;
  for (let i = 1; i <= count; i++) {
    const execDate = new Date(current);
    execDate.setHours(targetHours, targetMinutes, 0, 0);
    results.push(formatExecutionLabel(i, execDate));
    current = new Date(execDate);
    current.setDate(current.getDate() + 7);
  }
  return results;
}

function formatExecutionLabel(index: number, date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const year = date.getFullYear();
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  if (index === 1) {
    return `首次执行：${month}/${day}/${year} ${hours}:${minutes}`;
  }
  return `第 ${index} 次执行：${month}/${day}/${year} ${hours}:${minutes}`;
}
```

- [ ] **Step 6: 验证编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "feat: add cron helper functions for time calculation and preview"
```

---

### Task 3: 更新 buildInitialCronCreateForm

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` (找到 `buildInitialCronCreateForm` 函数)

- [ ] **Step 1: 替换函数实现**

将现有的 `buildInitialCronCreateForm` 替换为：

```typescript
function buildInitialCronCreateForm(): CronCreateFormState {
  const nextHour = getNextWholeHour();
  return {
    name: '',
    prompt: '',
    scheduleType: 'once',
    onceAt: toDatetimeLocalValue(nextHour),
    intervalStartAt: toDatetimeLocalValue(nextHour),
    intervalDays: '0',
    intervalHours: '0',
    intervalMinutes: '1',
    recurringStartAt: toDatetimeLocalValue(nextHour),
    recurringPeriod: 'daily',
    recurringTime: `${String(nextHour.getHours()).padStart(2, '0')}:${String(nextHour.getMinutes()).padStart(2, '0')}`,
    recurringWeekDay: 1,
  };
}
```

- [ ] **Step 2: 验证编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "refactor: update initial cron form state with new fields"
```

---

### Task 4: 重写 buildCronCreateInstruction

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` (找到 `buildCronCreateInstruction` 函数)

- [ ] **Step 1: 替换函数实现**

```typescript
function buildCronCreateInstruction(form: CronCreateFormState) {
  const name = form.name.trim();
  const prompt = form.prompt.trim();
  if (!name) {
    throw new Error('请输入任务名称');
  }
  if (!prompt) {
    throw new Error('请输入任务内容');
  }

  if (form.scheduleType === 'once' && Number.isNaN(Date.parse(form.onceAt))) {
    throw new Error('请选择有效的执行时间');
  }

  const totalIntervalMinutes = Number(form.intervalDays) * 1440 + Number(form.intervalHours) * 60 + Number(form.intervalMinutes);
  if (form.scheduleType === 'interval' && (!Number.isInteger(totalIntervalMinutes) || totalIntervalMinutes < 1)) {
    throw new Error('间隔时间至少为 1 分钟');
  }

  if (form.scheduleType === 'recurring' && form.recurringPeriod === 'weekly' && form.recurringWeekDay === undefined) {
    throw new Error('请选择星期几');
  }

  let schedule: Record<string, unknown>;

  if (form.scheduleType === 'once') {
    schedule = { type: 'once', at: new Date(form.onceAt).toISOString() };
  } else if (form.scheduleType === 'interval') {
    schedule = { type: 'interval', everyMinutes: totalIntervalMinutes };
  } else {
    // recurring
    if (form.recurringPeriod === 'daily') {
      schedule = {
        type: 'daily',
        time: form.recurringTime,
        timezone: 'Asia/Shanghai',
      };
    } else {
      // weekly - use cron expression
      const cronExpr = buildCronExpression('weekly', form.recurringTime, form.recurringWeekDay);
      schedule = {
        type: 'cron',
        expr: cronExpr,
        timezone: 'Asia/Shanghai',
      };
    }
  }

  const action = {
    action: 'create',
    name,
    prompt,
    schedule,
  };
  const block = `\`\`\`km-cron\n${JSON.stringify(action, null, 2)}\n\`\`\``;
  return [
    '请为我创建下面这个定时任务。',
    '请只原样输出这个 km-cron JSON 块，不要调用 cron 工具，不要改写 JSON，不要添加其他正文。',
    '',
    block,
  ].join('\n');
}
```

- [ ] **Step 2: 验证编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "feat: rewrite buildCronCreateInstruction for new schedule types"
```

---

### Task 5: 重写 CreateCronTaskDialog UI

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` (找到 `CreateCronTaskDialog` 函数，约 2014-2170 行)

- [ ] **Step 1: 替换整个 CreateCronTaskDialog 组件**

将现有的 `CreateCronTaskDialog` 函数替换为以下完整实现：

```typescript
function CreateCronTaskDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (message: string) => void;
}) {
  const [form, setForm] = React.useState<CronCreateFormState>(() => buildInitialCronCreateForm());

  React.useEffect(() => {
    if (open) {
      setForm(buildInitialCronCreateForm());
    }
  }, [open]);

  const updateForm = <K extends keyof CronCreateFormState>(key: K, value: CronCreateFormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = () => {
    try {
      onSubmit(buildCronCreateInstruction(form));
      onOpenChange(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '创建定时任务失败');
    }
  };

  const schedulePreview = formatSchedulePreview(form);
  const nextExecutions = computeNextExecutions(form);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-[rgba(15,23,42,0.32)] backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(34rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border border-border bg-card shadow-[0_24px_80px_rgba(15,23,42,0.16)]">
          <div className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
            <div>
              <Dialog.Title className="text-base font-semibold text-foreground">创建定时任务</Dialog.Title>
            </div>
            <Dialog.Close className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground">
              <X className="size-4" />
            </Dialog.Close>
          </div>

          <div className="space-y-4 px-5 py-4">
            {/* 名称 */}
            <label className="block">
              <span className="text-sm font-medium text-foreground">名称 <span className="text-[var(--color-danger)]">*</span></span>
              <input
                value={form.name}
                onChange={(event) => updateForm('name', event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                placeholder="请输入定时任务名称，如定时更新看板"
              />
            </label>

            {/* 消息内容 */}
            <label className="block">
              <span className="text-sm font-medium text-foreground">消息内容 <span className="text-[var(--color-danger)]">*</span></span>
              <textarea
                value={form.prompt}
                onChange={(event) => updateForm('prompt', event.target.value)}
                rows={3}
                className="mt-1.5 w-full resize-none rounded-lg border border-border bg-card px-3 py-2 text-sm leading-6 text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                placeholder="描述你的需求，例如：总结今天的新闻。"
              />
            </label>

            {/* 计划 */}
            <div>
              <span className="text-sm font-medium text-foreground">计划 <span className="text-[var(--color-danger)]">*</span></span>
              <select
                value={form.scheduleType}
                onChange={(event) => updateForm('scheduleType', event.target.value as CronCreateScheduleType)}
                className="mt-1.5 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
              >
                <option value="once">单次定时</option>
                <option value="interval">间隔循环</option>
                <option value="recurring">定期任务</option>
              </select>
            </div>

            {/* 单次定时 */}
            {form.scheduleType === 'once' && (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">单次定时：在指定时间执行一次任务。</div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">设置时间</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <input
                      type="date"
                      value={form.onceAt.split('T')[0]}
                      onChange={(event) => {
                        const time = form.onceAt.includes('T') ? form.onceAt.split('T')[1] : '00:00';
                        updateForm('onceAt', `${event.target.value}T${time}`);
                      }}
                      className="flex-1 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <input
                      type="time"
                      value={form.onceAt.includes('T') ? form.onceAt.split('T')[1] : ''}
                      onChange={(event) => {
                        const date = form.onceAt.split('T')[0];
                        updateForm('onceAt', `${date}T${event.target.value}`);
                      }}
                      className="w-32 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 间隔循环 */}
            {form.scheduleType === 'interval' && (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">间隔循环：按照固定时间频率重复执行，直到任务结束。</div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">开始时间</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <input
                      type="date"
                      value={form.intervalStartAt.split('T')[0]}
                      onChange={(event) => {
                        const time = form.intervalStartAt.includes('T') ? form.intervalStartAt.split('T')[1] : '00:00';
                        updateForm('intervalStartAt', `${event.target.value}T${time}`);
                      }}
                      className="flex-1 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <input
                      type="time"
                      value={form.intervalStartAt.includes('T') ? form.intervalStartAt.split('T')[1] : ''}
                      onChange={(event) => {
                        const date = form.intervalStartAt.split('T')[0];
                        updateForm('intervalStartAt', `${date}T${event.target.value}`);
                      }}
                      className="w-32 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                  </div>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">循环频率</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <input
                      type="number"
                      min={0}
                      value={form.intervalDays}
                      onChange={(event) => updateForm('intervalDays', event.target.value)}
                      className="w-16 rounded-lg border border-border bg-card px-2 py-2 text-center text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <span className="text-sm text-muted-foreground">天</span>
                    <input
                      type="number"
                      min={0}
                      value={form.intervalHours}
                      onChange={(event) => updateForm('intervalHours', event.target.value)}
                      className="w-16 rounded-lg border border-border bg-card px-2 py-2 text-center text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <span className="text-sm text-muted-foreground">小时</span>
                    <input
                      type="number"
                      min={0}
                      value={form.intervalMinutes}
                      onChange={(event) => updateForm('intervalMinutes', event.target.value)}
                      className="w-16 rounded-lg border border-border bg-card px-2 py-2 text-center text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <span className="text-sm text-muted-foreground">分钟</span>
                  </div>
                </div>
              </div>
            )}

            {/* 定期任务 */}
            {form.scheduleType === 'recurring' && (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">定期任务：按日历周期重复执行，直到任务结束。</div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">开始时间</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <input
                      type="date"
                      value={form.recurringStartAt.split('T')[0]}
                      onChange={(event) => {
                        const time = form.recurringStartAt.includes('T') ? form.recurringStartAt.split('T')[1] : '00:00';
                        updateForm('recurringStartAt', `${event.target.value}T${time}`);
                      }}
                      className="flex-1 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                    <input
                      type="time"
                      value={form.recurringStartAt.includes('T') ? form.recurringStartAt.split('T')[1] : ''}
                      onChange={(event) => {
                        const date = form.recurringStartAt.split('T')[0];
                        updateForm('recurringStartAt', `${date}T${event.target.value}`);
                      }}
                      className="w-32 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                  </div>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">计划周期</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <select
                      value={form.recurringPeriod}
                      onChange={(event) => updateForm('recurringPeriod', event.target.value as RecurringPeriod)}
                      className="flex-1 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    >
                      <option value="daily">每天</option>
                      <option value="weekly">每周</option>
                    </select>
                    {form.recurringPeriod === 'weekly' && (
                      <select
                        value={form.recurringWeekDay}
                        onChange={(event) => updateForm('recurringWeekDay', Number(event.target.value) as WeekDay)}
                        className="w-24 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                      >
                        <option value={1}>周一</option>
                        <option value={2}>周二</option>
                        <option value={3}>周三</option>
                        <option value={4}>周四</option>
                        <option value={5}>周五</option>
                        <option value={6}>周六</option>
                        <option value={0}>周日</option>
                      </select>
                    )}
                    <input
                      type="time"
                      value={form.recurringTime}
                      onChange={(event) => updateForm('recurringTime', event.target.value)}
                      className="w-32 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
                    />
                  </div>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">结束时间</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">永不结束</span>
                    <span className="group relative inline-flex cursor-help items-center justify-center rounded-full bg-muted-foreground/20 p-0.5">
                      <HelpCircle className="size-3 text-muted-foreground" />
                      <span className="absolute bottom-full left-1/2 z-50 mb-2 hidden -translate-x-1/2 whitespace-nowrap rounded-md border border-border bg-card px-2 py-1 text-xs text-muted-foreground shadow-lg group-hover:block">
                        任务将一直执行，需手动删除或停用
                      </span>
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 执行时间计算 */}
            {form.scheduleType !== 'once' && (
              <div>
                <span className="text-xs font-medium text-muted-foreground">执行时间计算</span>
                <div className="mt-1.5 space-y-0.5 text-xs text-muted-foreground">
                  {nextExecutions.map((line, index) => (
                    <div key={index}>{line}</div>
                  ))}
                  <div>...</div>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-border px-5 py-4">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              取消
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
            >
              创建
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

- [ ] **Step 2: 添加 HelpCircle import**

在文件顶部 lucide-react import 中添加 `HelpCircle`：

```typescript
import {
  AlertTriangle,
  Bot,
  CalendarClock,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  CircleSlash,
  HelpCircle,
  Layers,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
  History,
} from 'lucide-react';
```

- [ ] **Step 3: 验证编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS

- [ ] **Step 4: 验证 lint**

Run: `pnpm lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "feat: rewrite CreateCronTaskDialog with new UI layout"
```

---

### Task 6: 增强 formatCronSchedule 函数

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` (找到 `formatCronSchedule` 函数)

- [ ] **Step 1: 查找现有 formatCronSchedule 函数**

使用 Grep 搜索 `function formatCronSchedule` 定位函数位置。

- [ ] **Step 2: 增强函数以支持 cron 类型**

在现有实现基础上添加 `cron` 类型的处理：

```typescript
function formatCronSchedule(schedule: ZclawCronSchedule): string {
  if (schedule.type === 'once') {
    return `单次执行：${formatCronDateTime(schedule.at)}`;
  }
  if (schedule.type === 'interval') {
    const minutes = schedule.everyMinutes;
    if (minutes >= 1440) {
      const days = Math.floor(minutes / 1440);
      const remainingMinutes = minutes % 1440;
      if (remainingMinutes === 0) {
        return `每 ${days} 天执行一次`;
      }
      const hours = Math.floor(remainingMinutes / 60);
      const mins = remainingMinutes % 60;
      let result = `每 ${days} 天`;
      if (hours > 0) result += ` ${hours} 小时`;
      if (mins > 0) result += ` ${mins} 分钟`;
      return result + ' 执行一次';
    }
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return mins > 0 ? `每 ${hours} 小时 ${mins} 分钟执行一次` : `每 ${hours} 小时执行一次`;
    }
    return `每 ${minutes} 分钟执行一次`;
  }
  if (schedule.type === 'daily') {
    return `每天 ${schedule.time} 执行`;
  }
  if (schedule.type === 'cron') {
    return parseCronExpression(schedule.expr);
  }
  return '未知计划';
}

function parseCronExpression(expr: string): string {
  const parts = expr.trim().split(/\s+/);
  if (parts.length < 5) return expr;
  const [, hourStr, , , dayOfWeekStr] = parts;
  const hour = Number(hourStr);
  const minute = Number(parts[0]);
  const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;

  if (dayOfWeekStr === '*') {
    return `每天 ${timeStr} 执行`;
  }

  const dayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  const dayNum = Number(dayOfWeekStr);
  const dayLabel = dayLabels[dayNum] || dayOfWeekStr;
  return `${dayLabel} ${timeStr} 执行`;
}
```

- [ ] **Step 3: 验证编译**

Run: `pnpm --filter @insightweaver/web typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx
git commit -m "feat: enhance formatCronSchedule to support cron type"
```

---

### Task 7: 端到端验证

**Files:** 无修改

- [ ] **Step 1: 启动开发服务器**

Run: `pnpm --filter @insightweaver/web dev`
Expected: Server starts without errors

- [ ] **Step 2: 手动测试创建对话框**

在浏览器中：
1. 打开 AI 工作台
2. 点击定时任务区域的"+"按钮
3. 测试单次定时：填写名称、内容、选择时间，点击创建
4. 测试间隔循环：填写名称、内容、设置天/小时/分钟，点击创建
5. 测试定期任务-每天：填写名称、内容、选择每天+时间，点击创建
6. 测试定期任务-每周：填写名称、内容、选择每周+星期几+时间，点击创建
7. 验证执行时间预览正确显示
8. 验证"永不结束"提示正确显示

- [ ] **Step 3: 验证 lint 和 typecheck**

Run: `pnpm lint`
Run: `pnpm --filter @insightweaver/web typecheck`
Expected: Both PASS

- [ ] **Step 4: Commit final changes**

```bash
git add -A
git commit -m "feat: complete cron task create dialog refactor"
```
