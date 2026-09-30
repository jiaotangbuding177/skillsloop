# Proposal: 定时任务展示区域简化

## What & Why

当前定时任务展示区域（`ScheduledTasksModule`）每个任务卡片信息密度低，占用空间过大。用户需要简化展示，同时增加搜索、排序和月历视图功能。

### 当前问题
- 每个任务卡片显示：标题、计划表达式、任务内容（2行）、下次执行时间、状态标签、运行按钮、删除按钮
- 卡片高度过大，一个屏幕只能看到少量任务
- 没有搜索功能
- 没有按时间排序
- 没有宏观的时间分布视图

### 目标
- 列表行只展示核心信息（序号、标题、下次执行时间、状态）
- 悬停显示完整详情
- 前端搜索（标题+内容）
- 按下次执行时间升序排序
- 日历图标点击弹出月历浮层，展示任务在月历上的分布

## Scope

### In Scope
- `ScheduledTasksModule` 组件重构（列表展示简化）
- 前端搜索过滤（基于标题和 prompt）
- 按 `nextRunAt` 升序排序
- 悬停 Tooltip 显示完整详情
- 三点菜单（立即执行 + 删除）
- 月历浮层组件（`CronCalendarModal`）
- 月历日期格显示小圆点 + 截断标题（≤8字）
- 月历日期悬停显示当日所有任务详情

### Out of Scope
- 后端 API 变更（不需要）
- 编辑定时任务（后端不支持）
- 开关启用/停用（后端不支持）
- 定时任务创建流程（已有，不变）

## Impact

### Files Changed
- `apps/web/src/components/super-lobster/WorkbenchRailPanel.tsx` — 核心修改
  - `ScheduledTasksModule` 组件重构
  - 新增搜索状态和过滤逻辑
  - 新增排序逻辑
  - 新增月历模态框状态管理
- `apps/web/src/components/super-lobster/WorkbenchRailPanel.module.css` — 可能新增样式

### No Breaking Changes
- 后端 API 不变
- 数据模型不变
- 现有功能（创建、删除、运行）保持不变
