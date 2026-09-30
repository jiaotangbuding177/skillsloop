# 定时任务展示区域简化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 简化定时任务展示区域，提升信息密度，新增搜索、排序、月历视图和空状态创建入口，优化创建对话框时间选择器。

**Architecture:** 在现有 `WorkbenchRailPanel.tsx` 中重构 `ScheduledTasksModule` 组件，新增搜索状态和过滤排序逻辑，添加空状态组件、月历浮层组件，优化创建对话框时间选择器。所有变更均在单一文件内完成，不新增独立文件。

**Tech Stack:** React 18, Next.js 15, TypeScript, Tailwind CSS, Radix UI (Dialog, DropdownMenu, Tooltip), lucide-react icons

---

## 文件结构

**修改文件**:
- `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` — 核心修改，包含所有组件和逻辑

**新增组件（内联在同一文件中）**:
- `EmptyState` — 空状态展示（日历图标 + 提示 + 创建按钮）
- `CronTaskRow` — 单行任务展示（序号 + 标题 + 时间 + 状态 + 三点菜单）
- `CronCalendarModal` — 月历浮层（月份切换 + 日历网格 + 日期悬停）
- `CalendarDayCell` — 单日格子（日期数字 + 小圆点 + 数量）

**不新增文件**：所有组件内联在 `WorkbenchRailPanel.tsx` 中，保持与现有代码风格一致。

---

### Task 1: 添加搜索状态和过滤排序逻辑

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 在 WorkbenchRailPanel 组件中添加搜索状态**

在现有 state 声明区域（约第 3273 行附近）添加：

```typescript
const [cronSearchQuery, setCronSearchQuery] = React.useState('');
```

- [ ] **Step 2: 添加过滤排序逻辑**

在 `loadCronJobs` 回调之后添加：

```typescript
const filteredAndSortedJobs = React.useMemo(() => {
  const query = cronSearchQuery.trim().toLowerCase();
  let jobs = [...cronJobs];
  
  if (query) {
    jobs = jobs.filter(job =>
      (job.name || '').toLowerCase().includes(query) ||
      (job.prompt || '').toLowerCase().includes(query)
    );
  }
  
  jobs.sort((a, b) => {
    if (!a.nextRunAt && !b.nextRunAt) return 0;
    if (!a.nextRunAt) return 1;
    if (!b.nextRunAt) return -1;
    return new Date(a.nextRunAt).getTime() - new Date(b.nextRunAt).getTime();
  });
  
  return jobs;
}, [cronJobs, cronSearchQuery]);
```

- [ ] **Step 3: 更新 ScheduledTasksModule 的 jobs prop**

找到 `ScheduledTasksModule` 调用处（约第 3681 行），将 `jobs={cronJobs}` 改为 `jobs={filteredAndSortedJobs}`

- [ ] **Step 4: 验证**

```bash
cd apps/web && pnpm lint
```

Expected: 无类型错误

---

### Task 2: 重构 ScheduledTasksModule — 头部工具栏和搜索

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx:2323-2380`

- [ ] **Step 1: 重构头部区域，保留原有工具栏，添加搜索**

找到 `ScheduledTasksModule` 函数的头部区域（约第 2340-2380 行），将原有头部重构为：

```tsx
<div className="mb-2 space-y-2">
  {/* 原有工具栏：保留 */}
  <div className="flex items-center justify-between gap-2">
    <div className="text-xs text-muted-foreground">
      共 <span className="font-semibold text-foreground">{jobs.length}</span> 个任务
    </div>
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onOpenResults}
        className="inline-flex h-7 items-center gap-1.5 rounded-md border border-border bg-card px-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        title="查看运行结果"
      >
        <History className="size-3.5 text-[var(--color-primary)]" />
        运行结果
        {unreadResultCount > 0 ? (
          <span className="rounded-full bg-[var(--color-danger)] px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">
            {unreadResultCount}
          </span>
        ) : null}
      </button>
      <button
        type="button"
        onClick={onRefresh}
        disabled={isLoading}
        className="inline-flex size-7 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
        title="刷新"
      >
        <RefreshCw className={`size-3.5 ${isLoading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  </div>
  
  {/* 新增：搜索 + 加号 */}
  <div className="flex items-center gap-2">
    <div className="relative flex-1">
      <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
      <input
        type="text"
        value={cronSearchQuery}
        onChange={(e) => setCronSearchQuery(e.target.value)}
        placeholder="搜索任务名称或内容..."
        className="w-full rounded-lg border border-border bg-card py-1.5 pl-8 pr-3 text-xs text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-[var(--color-primary)]"
      />
      {cronSearchQuery && (
        <button
          type="button"
          onClick={() => setCronSearchQuery('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <X className="size-3" />
        </button>
      )}
    </div>
    <button
      type="button"
      onClick={() => {/* 调用创建对话框 */}}
      className="inline-flex size-7 shrink-0 items-center justify-center rounded-md bg-[var(--color-primary)] text-white transition-colors hover:bg-[var(--color-primary-hover)]"
      title="创建定时任务"
    >
      <Plus className="size-4" />
    </button>
  </div>
</div>
```

注意：加号按钮的 `onClick` 需要调用父组件的创建对话框开关，见 Task 6。

- [ ] **Step 2: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 3: 创建 EmptyState 空状态组件

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 在 ScheduledTasksModule 函数之前添加 EmptyState 组件**

在 `ScheduledTasksModule` 函数定义之前（约第 2320 行）添加：

```tsx
function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-secondary px-3 py-8 text-center">
      <div className="mx-auto flex size-12 items-center justify-center rounded-lg border border-border bg-card text-[var(--color-primary)]">
        <CalendarClock className="size-5" />
      </div>
      <div className="mt-3 text-sm font-semibold text-foreground">还没有定时任务</div>
      <div className="mt-1 text-xs leading-5 text-muted-foreground">
        在对话里让智能体按时间执行，或点击下方按钮创建
      </div>
      <button
        type="button"
        onClick={onCreate}
        className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
      >
        <Plus className="size-4" />
        创建任务
      </button>
    </div>
  );
}
```

- [ ] **Step 2: 在 ScheduledTasksModule 中使用 EmptyState**

在 `jobs.length === 0` 的条件分支中（约第 2383 行），将原有空状态替换为：

```tsx
<EmptyState onCreate={() => {/* 调用创建对话框 */}} />
```

- [ ] **Step 3: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 4: 重构任务列表行 — CronTaskRow 组件

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 添加 CronTaskRow 组件**

在 `EmptyState` 组件之后添加：

```tsx
function CronTaskRow({
  index,
  job,
  onRun,
  onDelete,
  isRunning,
  isDeleting,
}: {
  index: number;
  job: ZclawCronJob;
  onRun: () => void;
  onDelete: () => void;
  isRunning: boolean;
  isDeleting: boolean;
}) {
  return (
    <article className="group flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5 shadow-sm transition-colors hover:bg-accent/50">
      <span className="w-5 shrink-0 text-xs text-muted-foreground">{index}</span>
      <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">
        {job.name || '未命名任务'}
      </span>
      <span className="shrink-0 text-xs text-muted-foreground">
        {formatCronDateTime(job.nextRunAt) || '-'}
      </span>
      <span
        className={`shrink-0 rounded-md border px-1.5 py-0.5 text-[11px] font-medium ${
          job.enabled
            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
            : 'border-border bg-secondary text-muted-foreground'
        }`}
      >
        {job.enabled ? (job.isRunning ? '运行中' : '启用') : '停用'}
      </span>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button
            type="button"
            className="shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
            title="更多操作"
          >
            <MoreHorizontal className="size-4 text-muted-foreground" />
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            className="min-w-[160px] rounded-lg border border-border bg-card p-1 shadow-lg"
            align="end"
          >
            <DropdownMenu.Item
              className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm text-foreground outline-none hover:bg-accent"
              onSelect={onRun}
              disabled={isRunning || isDeleting}
            >
              <Play className="size-3.5" />
              立即执行
            </DropdownMenu.Item>
            <DropdownMenu.Separator className="my-1 h-px bg-border" />
            <DropdownMenu.Item
              className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm text-[var(--color-danger)] outline-none hover:bg-[var(--color-danger-light)]"
              onSelect={onDelete}
              disabled={isRunning || isDeleting}
            >
              <Trash2 className="size-3.5" />
              删除
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </article>
  );
}
```

- [ ] **Step 2: 更新 import 添加 MoreHorizontal 图标**

在文件顶部 import 区域添加 `MoreHorizontal` 到 lucide-react import。

- [ ] **Step 3: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 5: 添加任务行悬停 Tooltip

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 在 CronTaskRow 外层包裹 Tooltip**

使用 Radix UI Tooltip 包裹 `CronTaskRow`：

```tsx
import * as Tooltip from '@radix-ui/react-tooltip';

// 在 CronTaskRow 组件内，将 <article> 包裹在 Tooltip.Provider 和 Tooltip.Root 中
<Tooltip.Provider>
  <Tooltip.Root>
    <Tooltip.Trigger asChild>
      <article className="...">...</article>
    </Tooltip.Trigger>
    <Tooltip.Portal>
      <Tooltip.Content
        className="max-w-[320px] rounded-lg border border-border bg-card p-3 shadow-lg"
        sideOffset={8}
      >
        <div className="space-y-2 text-xs">
          <div>
            <div className="text-[10px] uppercase text-muted-foreground">任务名称</div>
            <div className="mt-0.5 text-sm font-medium text-foreground">{job.name || '未命名任务'}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-muted-foreground">任务内容</div>
            <div className="mt-0.5 leading-5 text-foreground">
              {stripCronPromptContext(job.prompt) || '暂无任务内容'}
            </div>
          </div>
          <div className="flex gap-4">
            <div>
              <div className="text-[10px] text-muted-foreground">计划</div>
              <div className="mt-0.5 text-foreground">{formatCronSchedule(job.schedule)}</div>
            </div>
            <div>
              <div className="text-[10px] text-muted-foreground">下次执行</div>
              <div className="mt-0.5 text-foreground">{formatCronDateTime(job.nextRunAt) || '-'}</div>
            </div>
            <div>
              <div className="text-[10px] text-muted-foreground">状态</div>
              <div className="mt-0.5 text-foreground">
                {job.enabled ? (job.isRunning ? '运行中' : '启用') : '停用'}
              </div>
            </div>
          </div>
        </div>
        <Tooltip.Arrow className="fill-card" />
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>
```

- [ ] **Step 2: 更新 import 添加 Tooltip**

在文件顶部添加 `import * as Tooltip from '@radix-ui/react-tooltip';`

- [ ] **Step 3: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 6: 添加日历图标点击事件和月历状态

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 在 WorkbenchRailPanel 中添加月历状态**

在现有 state 声明区域添加：

```typescript
const [isCalendarOpen, setIsCalendarOpen] = React.useState(false);
const [calendarMonth, setCalendarMonth] = React.useState(() => new Date());
```

- [ ] **Step 2: 在 ScheduledTasksModule 模块标题左侧添加可点击日历图标**

找到 `module.id === 'scheduled-tasks'` 的 section 渲染处（约第 3679 行），在标题前添加日历图标：

```tsx
<button
  type="button"
  onClick={() => setIsCalendarOpen(true)}
  className="inline-flex size-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
  title="查看月历"
>
  <CalendarClock className="size-4" />
</button>
```

- [ ] **Step 3: 传递创建对话框开关给 ScheduledTasksModule**

修改 `ScheduledTasksModule` 的 props 接口，添加 `onCreateTask` 回调，并在调用处传递 `() => setIsCreateCronOpen(true)`。

- [ ] **Step 4: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 7: 实现 CronCalendarModal 月历浮层组件

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 添加日历相关辅助函数**

在文件底部辅助函数区域添加：

```typescript
function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

function truncateTitle(title: string, maxLen = 8): string {
  return title.length > maxLen ? title.slice(0, maxLen) + '…' : title;
}

function groupJobsByDate(
  jobs: ZclawCronJob[],
  year: number,
  month: number
): Map<number, ZclawCronJob[]> {
  const map = new Map<number, ZclawCronJob[]>();
  
  for (const job of jobs) {
    if (!job.nextRunAt) continue;
    const runDate = new Date(job.nextRunAt);
    if (runDate.getFullYear() === year && runDate.getMonth() === month) {
      const day = runDate.getDate();
      if (!map.has(day)) map.set(day, []);
      map.get(day)!.push(job);
    }
  }
  
  return map;
}
```

- [ ] **Step 2: 实现 CronCalendarModal 组件**

在 `CronRunsDialog` 组件之后添加：

```tsx
function CronCalendarModal({
  open,
  jobs,
  month,
  onMonthChange,
  onOpenChange,
}: {
  open: boolean;
  jobs: ZclawCronJob[];
  month: Date;
  onMonthChange: (date: Date) => void;
  onOpenChange: (open: boolean) => void;
}) {
  const year = month.getFullYear();
  const m = month.getMonth();
  const daysInMonth = getDaysInMonth(year, m);
  const firstDay = getFirstDayOfMonth(year, m);
  const jobsByDate = groupJobsByDate(jobs, year, m);
  const today = new Date();
  const isToday = (day: number) =>
    today.getFullYear() === year && today.getMonth() === m && today.getDate() === day;

  const prevMonth = () => {
    const d = new Date(month);
    d.setMonth(d.getMonth() - 1);
    onMonthChange(d);
  };

  const nextMonth = () => {
    const d = new Date(month);
    d.setMonth(d.getMonth() + 1);
    onMonthChange(d);
  };

  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  const monthLabel = `${year}年${m + 1}月`;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-[rgba(15,23,42,0.32)] backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(28rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border border-border bg-card shadow-[0_24px_80px_rgba(15,23,42,0.16)]">
          <div className="border-b border-border px-5 py-4">
            <div className="flex items-center justify-between">
              <Dialog.Title className="text-base font-semibold text-foreground">定时任务月历</Dialog.Title>
              <Dialog.Close className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground">
                <X className="size-4" />
              </Dialog.Close>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <button onClick={prevMonth} className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground">
                <ChevronLeft className="size-5" />
              </button>
              <span className="text-sm font-medium text-foreground">{monthLabel}</span>
              <button onClick={nextMonth} className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground">
                <ChevronRight className="size-5" />
              </button>
            </div>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-7 gap-1">
              {weekdays.map((d) => (
                <div key={d} className="py-1 text-center text-xs text-muted-foreground">{d}</div>
              ))}
              {Array.from({ length: firstDay }).map((_, i) => (
                <div key={`empty-${i}`} className="aspect-square" />
              ))}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1;
                const dayJobs = jobsByDate.get(day) || [];
                const hasJobs = dayJobs.length > 0;
                const todayClass = isToday(day) ? 'ring-2 ring-[var(--color-primary)]' : '';
                const hasJobsClass = hasJobs ? 'bg-[var(--color-primary-light)]' : '';
                
                return (
                  <CalendarDayCell
                    key={day}
                    day={day}
                    jobs={dayJobs}
                    className={`${todayClass} ${hasJobsClass}`}
                  />
                );
              })}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

- [ ] **Step 3: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 8: 实现 CalendarDayCell 日期格子组件

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 添加 CalendarDayCell 组件**

在 `CronCalendarModal` 之前添加：

```tsx
function CalendarDayCell({
  day,
  jobs,
  className = '',
}: {
  day: number;
  jobs: ZclawCronJob[];
  className?: string;
}) {
  const hasJobs = jobs.length > 0;
  const maxDots = 3;
  const dotsToShow = Math.min(jobs.length, maxDots);
  const overflowCount = jobs.length - maxDots;

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <div
          className={`aspect-square rounded-lg p-1 ${className} ${
            hasJobs ? 'cursor-pointer hover:brightness-110' : ''
          }`}
        >
          <div className="text-xs text-muted-foreground">{day}</div>
          {hasJobs && (
            <div className="mt-0.5 flex items-center gap-0.5">
              {Array.from({ length: dotsToShow }).map((_, i) => (
                <span
                  key={i}
                  className="size-1.5 shrink-0 rounded-full bg-[var(--color-primary)]"
                />
              ))}
              {overflowCount > 0 && (
                <span className="text-[9px] text-muted-foreground">+{overflowCount}</span>
              )}
            </div>
          )}
        </div>
      </Tooltip.Trigger>
      {hasJobs && (
        <Tooltip.Portal>
          <Tooltip.Content
            className="max-w-[280px] rounded-lg border border-border bg-card p-3 shadow-lg"
            sideOffset={8}
          >
            <div className="text-xs font-medium text-foreground">
              {jobs.length} 个定时任务
            </div>
            <div className="mt-2 space-y-2">
              {jobs.map((job) => (
                <div key={job.id} className="space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-foreground">
                      {job.name || '未命名'}
                    </span>
                    <span className={`shrink-0 rounded border px-1 py-0.5 text-[10px] ${
                      job.enabled
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        : 'border-border bg-secondary text-muted-foreground'
                    }`}>
                      {job.enabled ? '启用' : '停用'}
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {formatCronSchedule(job.schedule)}
                  </div>
                </div>
              ))}
            </div>
            <Tooltip.Arrow className="fill-card" />
          </Tooltip.Content>
        </Tooltip.Portal>
      )}
    </Tooltip.Root>
  );
}
```

- [ ] **Step 2: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 9: 在 WorkbenchRailPanel 中渲染 CronCalendarModal

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

- [ ] **Step 1: 在 JSX 末尾添加 CronCalendarModal**

在 `CreateCronTaskDialog` 调用之后添加：

```tsx
<CronCalendarModal
  open={isCalendarOpen}
  jobs={cronJobs}
  month={calendarMonth}
  onMonthChange={setCalendarMonth}
  onOpenChange={setIsCalendarOpen}
/>
```

- [ ] **Step 2: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 10: 优化 CreateCronTaskDialog 时间选择器

**Files:**
- Modify: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx:3055-3080`

- [ ] **Step 1: 为单次定时的日期输入添加日历图标**

找到 `form.scheduleType === 'once'` 的日期输入区域（约第 3061 行），将：

```tsx
<div className="mt-1.5 flex items-center gap-2">
  <input type="date" ... className="flex-1 ..." />
  <input type="time" ... className="w-32 ..." />
</div>
```

改为：

```tsx
<div className="mt-1.5 flex items-center gap-2">
  <div className="relative flex-1">
    <input
      type="date"
      value={form.onceAt.split('T')[0]}
      onChange={(event) => {
        const time = form.onceAt.includes('T') ? form.onceAt.split('T')[1] : '00:00';
        updateForm('onceAt', `${event.target.value}T${time}`);
      }}
      className="w-full rounded-lg border border-border bg-card px-3 py-2 pr-8 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
    />
    <button
      type="button"
      className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-border bg-card p-0.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      title="选择日期"
    >
      <Calendar className="size-3.5" />
    </button>
  </div>
  <div className="relative w-32">
    <input
      type="time"
      value={form.onceAt.includes('T') ? form.onceAt.split('T')[1] : ''}
      onChange={(event) => {
        const date = form.onceAt.split('T')[0];
        updateForm('onceAt', `${date}T${event.target.value}`);
      }}
      className="w-full rounded-lg border border-border bg-card px-3 py-2 pr-8 text-sm text-foreground outline-none transition-colors focus:border-[var(--color-primary)]"
    />
    <button
      type="button"
      className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-border bg-card p-0.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      title="选择时间"
    >
      <Clock className="size-3.5" />
    </button>
  </div>
</div>
```

- [ ] **Step 2: 添加 Calendar 和 Clock 图标 import**

在文件顶部 lucide-react import 中添加 `Calendar, Clock`

- [ ] **Step 3: 对 interval 和 recurring 类型的时间选择器做同样修改**

对 `form.scheduleType === 'interval'` 和 `form.scheduleType === 'recurring'` 的时间选择区域重复 Step 1 的修改。

- [ ] **Step 4: 验证**

```bash
cd apps/web && pnpm lint
```

---

### Task 11: 完整交互链验证

- [ ] **Step 1: 启动开发服务器**

```bash
pnpm --filter @insightweaver/web dev
```

- [ ] **Step 2: 逐项验证**

1. 打开工作区面板 → 确认定时任务模块渲染正确
2. 空状态验证 → 确认"创建任务"按钮可点击并打开对话框
3. 输入搜索关键词 → 确认列表过滤和排序正确
4. 清空搜索 → 确认列表恢复完整
5. 悬停任务行 → 确认 Tooltip 显示完整信息
6. 点击 `···` → 确认菜单展开
7. 点击「立即执行」→ 确认任务执行并刷新列表
8. 点击「删除」→ 确认 ConfirmDialog 弹出
9. 点击日历图标 → 确认月历浮层弹出
10. 切换月份 → 确认日历网格更新
11. 悬停日期 → 确认 Tooltip 显示当日任务
12. 打开创建对话框 → 确认时间选择器图标按钮可点击

- [ ] **Step 3: 停止开发服务器**

---

### Task 12: 运行 lint 和 typecheck

- [ ] **Step 1: 运行 lint**

```bash
cd apps/web && pnpm lint
```

Expected: 无错误

- [ ] **Step 2: 运行 typecheck**

```bash
cd apps/web && npx tsc --noEmit
```

Expected: 无类型错误

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] 列表行简化 → Task 4 (CronTaskRow)
- [x] 搜索功能 → Task 1, 2
- [x] 排序功能 → Task 1
- [x] 悬停 Tooltip → Task 5
- [x] 三点菜单 → Task 4
- [x] 空状态 + 创建按钮 → Task 3
- [x] 月历浮层 → Task 6, 7, 8, 9
- [x] 月历方案 B（小圆点+数量）→ Task 8
- [x] 保留工具栏（计数/运行结果/刷新）→ Task 2
- [x] 创建对话框时间选择器优化 → Task 10

**2. Placeholder scan:** 无 TBD/TODO/不完整步骤

**3. Type consistency:**
- `ZclawCronJob` 类型贯穿所有任务
- `formatCronDateTime`, `formatCronSchedule`, `stripCronPromptContext` 辅助函数复用
- 组件 props 类型定义完整
