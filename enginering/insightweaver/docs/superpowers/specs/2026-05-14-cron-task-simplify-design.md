# Design: 定时任务展示区域简化

## 搜索范围

**最终决定**：仅按任务名称 (`job.name`) 搜索，不搜索任务内容 (`job.prompt`)。

原因：用户反馈搜索任务内容会产生过多不相关结果。

## 任务行布局

**最终实现**：
- **无序号**：用户反馈不需要序号列
- **两行布局**：
  - 第一行：任务标题（`truncate` 单行截断）
  - 第二行：🕐 时钟图标 + 下次执行时间 + 状态标签（靠右）
- 原设计为单行带序号布局，用户验收时要求调整

## Tooltip 样式

**最终实现**：
- 边框使用 `border-[var(--color-primary)]` 替代 `border-border`，提高与背景的区分度
- 任务名称使用 `line-clamp-2` 最多显示两行（原设计为无限单行）

## 三点菜单互斥

**Bug 修复**：初始实现中每个 `CronTaskRow` 各自维护 `isMenuOpen` 状态，导致多个菜单可以同时打开。
修复方式：将 `menuOpenJobId` 状态提升到 `ScheduledTasksModule`，通过共享状态实现互斥。

## 日历组件注意事项

1. **Tooltip.Provider 包裹**：`CalendarDayCell` 内部使用了 `Tooltip.Root`，必须在外层包裹 `Tooltip.Provider`，否则报错。
2. **避免 Tooltip.Portal + Dialog 冲突**：Dialog 内部的 Tooltip 不要用 `Tooltip.Portal`，会与 Dialog 的焦点陷阱冲突。改为内联渲染 `Tooltip.Content`。
3. **月份切换按钮**：必须添加 `type="button"`，防止在 form 内误触发表单提交。

## 时间选择器交互

**最终实现**：
- 日期/时间区域整体作为可点击区域，点击触发 `input.showPicker()` 弹出原生选择器
- 隐藏的真实 input 用 `pointer-events-none` + `opacity-0` + `absolute` 定位覆盖整个区域
- 选中后自动清除高亮边框（`setActivePicker(null)`）
- 默认频率：间隔循环为 1 天 0 小时 0 分钟（原为 0 天 0 小时 1 分钟）

## 后端约束

- 后端 **不支持** 编辑定时任务（无 `updateZclawCronJobApi`）
- 后端 **不支持** 开关启用/停用（无 toggle API）
- 后端 **不支持** 按时间排序（需要前端排序）
- 前端数据源：`listZclawCronJobsApi()` 返回 `ZclawCronJob[]`

```typescript
interface ZclawCronJob {
  id: string;
  name: string;
  prompt: string;
  schedule: { type: 'once' | 'interval' | 'cron'; at?: string; expr?: string; ... };
  enabled: boolean;
  isRunning: boolean;
  nextRunAt: string | null;
  createdAt: string;
}
```

## End-to-End User Path

1. **入口**：用户打开右侧工作区面板 → 点击「定时任务」模块
2. **空状态**：如果没有任务，显示空状态区域 + "创建任务"按钮 → 点击打开创建对话框
3. **浏览**：看到简化后的任务列表（序号、标题、下次执行时间、状态）
4. **搜索**：点击搜索图标 → 输入关键词 → 前端实时过滤（标题+内容匹配）
5. **查看详情**：鼠标悬停某行 → Tooltip 弹出显示完整信息
6. **操作**：点击行尾 `···` → 下拉菜单选择「立即执行」或「删除」
7. **月历视图**：点击日历图标 → 弹出月历浮层 → 查看任务在月历上的分布
8. **月历交互**：悬停日期 → 显示该日所有任务详情；点击月份切换箭头 → 切换月份

## Same-Page UI Reference

当前页面已有类似模式的组件参考：
- `InstalledAgentsModule` — 智能体列表（卡片式，带搜索和筛选）
- `CommonSkillsModule` — 技能列表（网格布局）
- 月历模式可参考：无直接参考，需新建浮层组件

## UI Layout

### 列表区域

```
┌─────────────────────────────────────────────────────────────┐
│   定时任务                                    [搜索] [+]   │
│  ┌─────────────────────────────────────────────────────────│
│  │  共 1 个任务    [运行结果 (4)] [刷新]                │ ← 保留原有计数和按钮
│  │                                                          │
│  │  1  早报               05-14 09:00  [●启用]       ···  │
│  │  2  周报               周一 10:00     [●启用]       ···  │
│  │  3  月度汇总报告       06-01 09:00    [○停用]       ···  │
│  └─────────────────────────────────────────────────────────│
└─────────────────────────────────────────────────────────────┘
```

### 空状态

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────│
│  │                    [📅]                                  │
│  │                                                          │
│  │              还没有定时任务                               │
│  │  在对话里让智能体按时间执行，或点击下方按钮创建            │
│  │                                                          │
│  │                  [+ 创建任务]                             │
│  └─────────────────────────────────────────────────────────│
─────────────────────────────────────────────────────────────
```

### Tooltip 详情

```
┌─────────────────────────────────────────────────────────────┐
│  任务名称：早报                                               │
│  任务内容：每天上午 9 点生成昨日销售日报并发送到工作群...      │
│           （最多显示 500 字，超出部分截断并换行）               │
│  计划：每天 09:00 执行                                       │
│  下次执行：2026-05-15 09:00:00                               │
│  状态：启用                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 三点菜单

```
┌──────────────────┐
│  ▶ 立即执行       │
│   删除          │
└──────────────────┘
```

### 月历浮层（方案 B：仅小圆点+数量）

```
┌─────────────────────────────────────────────────────────────┐
│                    定时任务月历                     [✕]     │
│  ┌─────────────────────────────────────────────────────────│
│  │           2026年5月  ▶                                  │
│  │                                                          │
│  │  日  一  二  三  四  五  六                              │
│  │                      1   2   3   4                       │
│  │                      ·                                   │
│  │              5   6   7   8   9  10  11                   │
│  │              ·   ·                                       │
│  │             12  13  14  15  16  17  18                   │
│  │              ·   ·  ●●2                                  │ ← 小圆点+数量
│  ─────────────────────────────────────────────────────────│
│                                                             
│  悬停日期 → Tooltip:                                        
│  ┌─────────────────────────────────────────────────────────│
│  │  5月14日（周四）有 2 个定时任务                             │
│  │  • 早报          09:00    [●启用]                       │
│  │    每天上午 9 点生成...                                   │
│  │  • 周报          10:00    [●启用]                       │
│  │    每周一上午 10 点...                                    │
│  └─────────────────────────────────────────────────────────│
─────────────────────────────────────────────────────────────
```

## Component Architecture

```
WorkbenchRailPanel
── ScheduledTasksModule (重构)
│   ├── ToolbarBar (保留原有) — 工具栏
│   │   ├── 任务计数（"共 X 个任务"）
│   │   ├── 运行结果按钮（带未读角标）
│   │   └── 刷新按钮
│   ├── 搜索输入框（新增，受控组件）
│   ├── 任务列表（过滤+排序后）
│   │   ├── CronTaskRow (新) — 单行任务展示
│   │   │   ├── 序号
│   │   │   ├── 标题（截断）
│   │   │   ├── 下次执行时间
│   │   │   ├── 状态标签
│   │   │   ├── Tooltip（悬停显示详情，内容最多 500 字）
│   │   │   └── DropdownMenu（三点菜单：立即执行 + 删除）
│   │   ── EmptyState (新) — 空状态展示
│   │       ├── 日历图标
│   │       ├── 提示文案
│   │       └── "创建任务"按钮 → 打开 CreateCronTaskDialog
│   ── CronCalendarModal (新) — 月历浮层
│       ├── 月份切换
│       ├── 日历网格
│       │   └── CalendarDayCell (新) — 单日格子
│       │       ├── 日期数字
│       │       ├── 任务标记（小圆点 + 数量，方案 B）
│       │       └── Tooltip（悬停显示当日任务）
│       ── 关闭按钮
├── CreateCronTaskDialog (优化)
│   └── 时间选择器优化
│       ├── 日期输入 + 日历图标按钮（点击打开日历组件）
│       └── 时间输入 + 时钟图标按钮（点击打开时间组件）
```

## State Management

新增状态（在 `WorkbenchRailPanel` 中）：
```typescript
const [cronSearchQuery, setCronSearchQuery] = useState('');
const [isCalendarOpen, setIsCalendarOpen] = useState(false);
const [calendarMonth, setCalendarMonth] = useState(() => new Date());
```

过滤 + 排序逻辑：
```typescript
const filteredAndSortedJobs = useMemo(() => {
  const query = cronSearchQuery.trim().toLowerCase();
  let jobs = [...cronJobs];
  
  // 搜索过滤
  if (query) {
    jobs = jobs.filter(job =>
      (job.name || '').toLowerCase().includes(query) ||
      (job.prompt || '').toLowerCase().includes(query)
    );
  }
  
  // 按 nextRunAt 升序排序（null 值排最后）
  jobs.sort((a, b) => {
    if (!a.nextRunAt && !b.nextRunAt) return 0;
    if (!a.nextRunAt) return 1;
    if (!b.nextRunAt) return -1;
    return new Date(a.nextRunAt).getTime() - new Date(b.nextRunAt).getTime();
  });
  
  return jobs;
}, [cronJobs, cronSearchQuery]);
```

## Calendar Logic

月历数据计算：
```typescript
// 将任务按日期分组
function groupJobsByDate(jobs: ZclawCronJob[], year: number, month: number): Map<number, ZclawCronJob[]> {
  const map = new Map<number, ZclawCronJob[]>();
  const targetYear = year;
  const targetMonth = month; // 0-indexed
  
  for (const job of jobs) {
    // 根据 nextRunAt 和 schedule 计算任务在目标月的所有执行日期
    const dates = computeJobDatesInMonth(job, targetYear, targetMonth);
    for (const day of dates) {
      if (!map.has(day)) map.set(day, []);
      map.get(day)!.push(job);
    }
  }
  return map;
}

// 截断标题为最多 8 个字符
function truncateTitle(title: string, maxLen = 8): string {
  return title.length > maxLen ? title.slice(0, maxLen) + '…' : title;
}
```

## Backend Constraints

- 所有数据变更通过 `onCreateCronTask`、`handleRunCronJob`、`handleDeleteJob` 回调完成
- 搜索、排序、月历视图均为前端计算，无需后端支持
- `ZclawCronJob` 类型不变

## CreateCronTaskDialog 优化

### 空状态区域

当 `cronJobs.length === 0` 时显示空状态：
- 日历图标（`CalendarClock`）
- 标题："还没有定时任务"
- 提示文案："在对话里让智能体按时间执行，或点击下方按钮创建"
- 按钮："创建任务"（蓝色 primary 按钮）→ 调用 `setIsCreateCronOpen(true)`

### 时间选择器优化

现有 `CreateCronTaskDialog` 的时间选择器需要优化：
- 日期输入框右侧添加日历图标按钮（`Calendar` 图标）
  - 点击图标 → 打开日期选择器组件（如 `react-datepicker` 或浏览器原生）
- 时间输入框右侧添加时钟图标按钮（`Clock` 图标）
  - 点击图标 → 打开时间选择器组件
- 图标按钮样式：24x24px，圆角边框，悬停高亮

### 实现方式

复用现有 `CreateCronTaskDialog` 组件，只需在时间输入区域添加图标按钮：

```tsx
// 日期输入 + 日历图标
<div className="relative flex-1">
  <input type="date" value={form.onceAt.split('T')[0]} ... />
  <button className="absolute right-2 top-1/2 -translate-y-1/2" onClick={openCalendar}>
    <Calendar className="size-4" />
  </button>
</div>

// 时间输入 + 时钟图标
<div className="relative w-32">
  <input type="time" value={form.onceAt.split('T')[1]} ... />
  <button className="absolute right-2 top-1/2 -translate-y-1/2" onClick={openTimePicker}>
    <Clock className="size-4" />
  </button>
</div>
```

## Interaction Chain

1. 用户打开面板 → `ScheduledTasksModule` 渲染列表
2. 用户输入搜索 → `cronSearchQuery` 更新 → `filteredAndSortedJobs` 重新计算 → 列表更新
3. 用户悬停行 → Tooltip 组件渲染详情
4. 用户点击 `···` → DropdownMenu 展开 → 选择操作 → 调用 `onRunJob` 或 `onDeleteJob`
5. 用户点击日历图标 → `isCalendarOpen = true` → `CronCalendarModal` 渲染
6. 用户切换月份 → `calendarMonth` 更新 → 日历网格重新渲染
7. 用户悬停日期 → Tooltip 显示当日任务

## Entry Point Location

**入口**：右侧工作区面板 → 「定时任务」模块（`module.id === 'scheduled-tasks'`）

**入口元素**：
- 搜索图标：列表头部右侧，加号按钮左侧
- 加号按钮：列表头部最右侧（已有 `onCreateCronTask` 回调）
- 日历图标：模块标题「定时任务」左侧（点击打开月历）
