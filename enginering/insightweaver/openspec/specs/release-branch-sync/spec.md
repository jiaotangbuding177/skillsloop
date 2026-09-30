# Release Branch Sync Specification

> origin/release 远端分支不允许直接提交代码，只能通过 PR 合并。所有 feature 分支必须在关键节点同步 release 代码。

## 核心规则

1. **origin/release 是受保护分支**：不允许 `git push origin release`，只能通过 PR 合并
2. **两个强制同步节点**：开始开发前 + 提交代码前
3. **冲突必须本地解决**：不允许在远端解决冲突

## 同步时机

### 时机 1：开发前同步

从 release 创建 feature 分支后，**开始写代码之前**：

```bash
git checkout -b feature-xxx origin/release
# 如果 feature 分支已存在：
git checkout feature-xxx
git fetch origin release
git merge origin/release --no-edit
# 解决冲突（如有）
git add -A && git commit -m "merge: sync origin/release into feature-xxx"
```

### 时机 2：提交前同步

**推送代码和创建 PR 之前**：

```bash
git fetch origin release
git merge origin/release --no-edit
# 解决冲突（如有）
# 验证构建和测试
pnpm build && pnpm test
git add -A && git commit -m "merge: sync origin/release into feature-xxx"
git push
```

## 冲突解决策略

| 文件类型 | 策略 |
|----------|------|
| 业务代码 (.ts/.tsx) | 手动解决，保留双方有效变更 |
| lockfile (pnpm-lock.yaml) | 以 release 为基础，重新 `pnpm install` 生成 |
| 配置文件 (.yaml/.json) | 合并双方新增内容 |
| 自动生成文件 (prisma client 等) | 重新生成 |

## 冲突解决后验证

冲突解决后必须执行：

```bash
pnpm install           # 确保 lockfile 一致
pnpm build             # 确保编译通过
pnpm test              # 确保测试通过
```

三条命令全部通过后才能提交 merge commit。

## 反模式（避免）

- ❌ 在 feature 分支上 `git push --force` 覆盖远端历史
- ❌ 跳过同步直接推送（可能覆盖 release 上的新变更）
- ❌ 冲突解决后不验证构建和测试
- ❌ 使用 `git rebase` 同步 release（rebase 会改写历史，PR 已创建时会导致问题）

## 与 roshan-complex-feature-workflow 的集成

本规范在以下两个 Phase 中强制执行：
- **Phase 7 前**（开发前同步）
- **Phase 13 前**（提交前同步）
