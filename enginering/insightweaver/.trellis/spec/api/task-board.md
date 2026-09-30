# Task Board API Specification

> 来源：feature-20260908-task-board（2026-09-08）。契约以本文件为准，实现位于 `apps/api/src/task-board/`。

## 模块布局

- `task-board.module.ts`（注册于 app.module.ts，imports DatabaseModule）
- `task-board.controller.ts`：`@Controller('tasks')` + 类级 `JwtAuthGuard`
- `task-board.service.ts`：业务逻辑（`@Inject('PrismaClient')`）
- `task-board.constants.ts`：**re-export `@insightweaver/shared`**（列 key/优先级/position 间隔的单一事实源在 `packages/shared/src/task-board.ts`，web/api 双端共用，禁止本地复制）
- `task-board.position.ts`：列内落位纯函数（可单测）
- `dto/task-board.dto.ts`：class-validator

## 端点契约（信封 `{code,message,data}` 由全局拦截器包装）

| Method | Path | 语义 | 备注 |
|--------|------|------|------|
| GET | `/api/tasks/board` | 聚合：columns+cards+members | 首访懒初始化看板与 7 列（幂等，P2002 并发兜底） |
| POST | `/api/tasks` | 创建卡 | seq=board 内 max+1（含软删行→不复用），事务内 P2002 重试≤3；position=列最小-1024（顶部） |
| PATCH | `/api/tasks/:id` | 部分更新（含 columnKey/position 移动） | 读列→算位→写包在 `$transaction`；换列未传 position → 落目标列顶 |
| DELETE | `/api/tasks/:id` | 软删 | isDeleted=true，行保留（占住 seq 不复用） |
| PATCH | `/api/tasks/board/columns/:columnKey` | 列重命名/隐藏 | columnKey 经 ParseEnumPipe 白名单 |

## 关键不变量与陷阱

1. **租户上下文**：enterpriseId = 显式参数优先，回落 `x-enterprise-id` 头；两者皆缺 → **400 INVALID_ARGUMENT**（不是 403——403 保留给「非成员」）。每个 service 方法首行 `assertMembership`（EnterpriseMembership status=active + isDeleted=false）。
2. **seq 永不复用**：`@@unique([boardId, seq])` + aggregate max **不过滤 isDeleted**（软删行占位）。
3. **position 算法**（`computePlacePosition` 纯函数）：默认/小于首卡 → 顶部（first-1024）；大于末卡 → 底部；中间 → 前后邻卡夹取，间隙 <2 时整列重排（**移动卡之后的兄弟卡从 (i+1)*gap 起**，避免碰撞——曾在此处出过 off-by-one，见任务 evidence/cr-report.md C3）。
4. **单卡响应必须回填 `assigneeName`**：create/update 用 `resolveNameMap` 按企业成员解析；直接 `toCardRecord(card, new Map())` 会导致前端保存/拖拽后负责人显示退化为「未分配」（CR C2 教训）。
5. **assigneeUserId 必须校验为本企业 active 成员**（`assertAssigneeMember`），否则注入任意 userId 产生脏数据。
6. **成员显示名**：`enterprise_memberships.realName` → `user_identities.phoneMasked` → `"成员"` 三级兜底（users 表无 name 列，见 db spec）。

## 前端对接约定（apps/web）

- API 模块：`apps/web/src/api/moudles/task-board.ts`，全部请求带 `withActiveEnterpriseHeader()`。
- 页面：`/[locale]/(zclaw-shell)/tasks`，页面级状态（无全局 store）；显示偏好（显示空列/紧凑卡片）存 localStorage key `zclaw:task-board-display`（**不带企业维度**——纯 UI 偏好有意豁免，勿放业务数据）。
- 拖拽：@dnd-kit/core PointerSensor `distance: 4`（拖拽/点击分流，dnd-kit 在 capture 阶段抑制拖后点击）；列=useDroppable、卡=useDraggable；V1 仅跨列移动（落目标列顶），服务端已支持中点落位供后续列内排序。
- **写操作响应落地前必须校验活跃企业未变**（`getActiveEnterpriseId()` 与发起时一致），否则放弃本地写 + 重拉——防止企业切换窗口旧响应污染新企业视图。
- 浮层：`components/task-board/Popover.tsx` 为锚定浮层（首帧屏幕外 hidden 挂载测量，勿改回 `if (!pos) return null`——会造成渲染死锁，CR C1 教训）。

## 已知偏差/后续项（feature-20260908-task-board 记录）

- 列默认名/标签/智能体为中文播种（数据级文案）；列名可用户重命名自愈；i18n 化列名留后续。
- 弹窗为自绘 modal（非 Radix Dialog）：无 focus trap；可访问性增强留后续。
- 列内拖拽排序：服务端就绪，前端消费留后续。
- api 全量测试基线存在 16 个 billing/quota/skills 存量失败（时间炸弹类），与本模块无关。
