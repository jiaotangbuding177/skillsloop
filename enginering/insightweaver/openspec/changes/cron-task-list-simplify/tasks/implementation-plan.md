# Tasks: 定时任务展示区域简化

## T1: 添加搜索状态和过滤排序逻辑

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

在 `WorkbenchRailPanel` 组件中添加：
1. 新增 state: `cronSearchQuery`（搜索关键词）
2. 新增 `useMemo` 计算 `filteredAndSortedJobs`：
   - 搜索过滤：同时匹配 `job.name` 和 `job.prompt`（转小写后 includes）
   - 排序：按 `nextRunAt` 升序（null 值排最后）
3. 将 `ScheduledTasksModule` 的 `jobs` prop 改为 `filteredAndSortedJobs`

**验证**：在浏览器中搜索关键词，确认列表正确过滤和排序。

---

## T2: 重构 ScheduledTasksModule — 简化列表行展示

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

重构 `ScheduledTasksModule` 组件：
1. 头部区域：
   - **保留**"共 X 个任务"计数（原有）
   - **保留**"运行结果"按钮（原有，带未读角标）
   - **保留**刷新按钮（原有）
   - 新增搜索输入框（`Search` 图标 + 输入框），放在工具栏右侧
   - 保留加号按钮（`Plus` 图标）→ 调用 `onCreateCronTask`
2. 任务列表：
   - 每行改为横向布局：`序号 | 标题 | 下次执行时间 | 状态标签 | 三点菜单`
   - 移除任务内容描述区域
   - 移除单独的"下次执行"卡片
   - 移除直接的运行/删除按钮
3. 空状态：
   - 显示日历图标 + "还没有定时任务" + 提示文案
   - 添加"创建任务"按钮 → 打开 CreateCronTaskDialog

**样式**：
- 行高约 40-48px
- 标题截断（`truncate`）
- 序号用灰色小字（`text-xs text-muted-foreground`）

---

## T3: 创建 EmptyState 空状态组件

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

新建 `EmptyState` 组件（或在 `ScheduledTasksModule` 内内联）：
1. 当 `filteredAndSortedJobs.length === 0` 时显示
2. 内容：
   - 日历时钟图标（`CalendarClock`，48x48px）
   - 标题："还没有定时任务"（14px，加粗）
   - 提示文案："在对话里让智能体按时间执行，或点击下方按钮创建"（12px，灰色）
   - "创建任务"按钮（蓝色 primary，点击调用 `setIsCreateCronOpen(true)`）

---

## T4: 添加任务行悬停 Tooltip

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

为每个任务行添加 Tooltip（可使用 `@radix-ui/react-tooltip` 或自定义）：
- 触发方式：鼠标悬停整行
- 显示内容：
  - 任务名称
  - 任务内容（`stripCronPromptContext(job.prompt)`，截断显示）
  - 计划描述（`formatCronSchedule(job.schedule)`）
  - 下次执行时间（`formatCronDateTime(job.nextRunAt)`）
  - 状态（启用/停用/运行中）

---

## T5: 添加三点菜单（立即执行 + 删除）

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

在每行右侧添加 `···` 按钮（`MoreHorizontal` 图标）：
- 点击展开下拉菜单（使用 `@radix-ui/react-dropdown-menu`）
- 菜单项：
  - `▶ 立即执行` → 调用 `onRunJob(job)`
  - ` 删除` → 调用 `onDeleteJob(job)`（已有 ConfirmDialog 确认）
- 禁用态：`runningJobId === job.id` 或 `deletingJobId === job.id` 时禁用

---

## T6: 添加日历图标点击事件和月历状态

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

1. 在模块标题「定时任务」左侧添加可点击的日历图标（`CalendarClock`）
2. 新增 state：
   - `isCalendarOpen`：月历浮层开关
   - `calendarMonth`：当前查看的月份（初始值为当前日期）
3. 点击图标 → `setIsCalendarOpen(true)`

---

## T7: 实现 CronCalendarModal 月历浮层组件

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

新建 `CronCalendarModal` 组件（或使用 Dialog 组件）：
1. 浮层布局：居中显示，尺寸约 600x500px
2. 头部：
   - 标题「定时任务月历」
   - 月份切换：`◀` 上一月 / `▶` 下一月
   - 关闭按钮
3. 日历网格：
   - 7 列表头（日 一 二 三 四 五 六）
   - 根据 `calendarMonth` 生成日期格子
   - 每个格子显示日期数字
   - 有任务的日期格子显示任务标记（**方案 B：小圆点 + 数量**，不显示标题）
4. 日期悬停 Tooltip：
   - 显示该日期所有任务的详情（名称、时间、状态、内容摘要）

**日期计算**：
- 使用 `date-fns` 或原生 `Date` 计算当月第一天是星期几、当月天数
- 对于每个任务，根据 `nextRunAt` 和 `schedule` 计算在目标月的所有执行日期

---

## T8: 实现月历日期格子和任务标记

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

新建 `CalendarDayCell` 组件：
1. 接收 props：`date`（日期）、`jobs`（该日任务列表）、`onHover`（悬停回调）
2. 渲染：
   - 日期数字
   - 任务标记区域（**方案 B：小圆点 + 数量**，不显示标题）
   - 小圆点最多显示 3 个，超过显示 `+N` 数量
3. 样式：
   - 无任务：灰色日期
   - 有任务：高亮背景或边框
   - 今天：特殊标记（蓝色边框或背景）

---

## T9: 实现月历日期悬停 Tooltip

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

为 `CalendarDayCell` 添加悬停 Tooltip：
- 触发方式：鼠标悬停日期格子
- 显示内容：
  - 日期标题（如「5月14日（周四）有 2 个定时任务」）
  - 任务列表（每个任务：名称、执行时间、状态标签、内容摘要）

---

## T10: 优化 CreateCronTaskDialog 时间选择器

**文件**: `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx`

优化现有 `CreateCronTaskDialog` 的时间输入区域：
1. 日期输入框：
   - 右侧添加日历图标按钮（`Calendar` 图标，24x24px）
   - 点击图标 → 打开日期选择器（可用浏览器原生或 `react-datepicker`）
2. 时间输入框：
   - 右侧添加时钟图标按钮（`Clock` 图标，24x24px）
   - 点击图标 → 打开时间选择器
3. 图标按钮样式：圆角边框，悬停高亮，绝对定位在输入框右侧

---

## T11: 验证交互链完整性

**验证步骤**：
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

---

## T12: 运行 lint 和 typecheck

```bash
cd apps/web && pnpm lint
```

确保无 lint 错误和类型错误。
