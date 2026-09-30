# users 四表时间戳口径契约（createdAt/updatedAt）

> 来源任务：09-08-fix-users-table-createdAt-timezone（2026-09-08 定案）

## 口径事实

| 写入路径 | createdAt/updatedAt 存储 | 适用行 |
|---------|------------------------|--------|
| Prisma（SMS `upsertUser` / OIDC `upsertYunzhishiUser` / 所有业务 CRUD） | **UTC**（Prisma 6.0.1 显式传 UTC 字面量，探针实证） | 自然注册用户及其四表行 |
| `enterprise-member-import.service.ts` 原生 SQL | **UTC**（2026-09-08 修复后；修复前为北京墙钟） | 批量导入成员（历史脏行见「存量回填」） |

其余业务表（billing_orders / entitlement_batches / zclaw_messages / zclaw_sessions / entitlement_ledgers）恒为 **UTC**（微信 `notifyRaw.create_time` 权威锚点验证）。

## 历史脏行（修复前导入的成员）

约 313 个用户（学生版 273 + Xin苗启航营 31 + 零星 B2B）的四表时间为北京墙钟（=UTC+8h）。
回填 SQL 与审计快照：`.trellis/tasks/09-08-fix-users-table-createdAt-timezone/evidence/backfill-prod-20260908.sql`。
未回填的静默成员（无锚点无法证明口径）判读规则见下。

## 判读规则（分析/排查时）

1. **判人群先看 membership 企业**：挂 B2B 真实企业 → 疑似导入行（历史脏行窗口内为北京墙钟）；挂默认企业 `00000000-0000-0000-0000-000000000001` → 自然注册（UTC）
2. **updatedAt 是 UTC 锚**：`updatedAt < createdAt`（同表存储值比较）→ createdAt 必为北京墙钟
3. **负差值指纹**：存在 UTC 锚点事件（orders/sessions/batches）早于 users.createdAt，差值 ≈ -8h±ε → 北京墙钟行；**这不是数据异常**，是导入成员先建号（导入时刻）后自发付费/使用的时序被口径差放大的伪象
4. **「订单早于用户」排查 SOP**：先按 1-3 判口径 → 口径一致仍倒挂才继续查 FK/迁移/人工操作；禁止直接推断「删库重建」

## 代码规约（防复发）

- 原生 SQL 写 timestamp 列**禁止裸 `NOW()` / `CURRENT_TIMESTAMP`**，必须 `(NOW() AT TIME ZONE 'UTC')` 与 Prisma 口径对齐
- 例外（业务有效期语义，按北京业务日理解，**不要改成 UTC**）：导入服务中 token 配额的 `validFrom/validTo`、`DATE_TRUNC('month', NOW())` 窗口边界——这些是业务时间语义，与存储口径是两个维度
- 导入服务有单测护栏：`enterprise-member-import.service.test.ts` 的「import raw SQL writes UTC timestamps」用例（断言四表 INSERT 含 UTC 表达式且无裸 NOW()）

## 已知遗留（同病不同表，独立任务处理）

- `zclaw_enterprise_conversation_quota_usages` / `zclaw_enterprise_token_quota_members` 的 createdAt/updatedAt/assignedAt 在导入路径仍用裸 NOW()（本次未动，避免触碰业务有效期语义）
- `research.service.ts:1598-1604` 的 5 秒去重比较 `Date.now() - createdAt`，若 research_messages 为北京墙钟则去重恒失效（delta ≈ -8h）
