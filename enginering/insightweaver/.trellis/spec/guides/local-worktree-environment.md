# Local Worktree Environment Guide（Windows）

本指南沉淀本项目在 Windows 上使用 devflow worktree（`.devflow/worktrees/<task-id>/`）开发时的环境踩坑与解决方式。**适用前提**：Windows + pnpm monorepo（Next.js 16 + NestJS + Prisma）+ devflow worktree 隔离。

> 一句话总结：**测试/类型检查用 junction（短路径），next build 用真实安装；依赖变更后必须重生成 Prisma client；工具 cwd 必须回到 worktree 根。**

## 1. 深路径双态（核心）

worktree 路径 `.devflow/worktrees/<task-id>/` 在 Windows 上使依赖真实路径超过 MAX_PATH（260 字符），导致两类互斥故障：

| 工具 | 故障 | 解法 |
|------|------|------|
| vitest | `ERR_PACKAGE_IMPORT_NOT_DEFINED`（#module-evaluator，node_modules/.pnpm 深路径） | **junction**：worktree 的 node_modules 指向主仓库 node_modules（短路径） |
| tsc | 同上（解析 node_modules 包内类型） | 同 junction |
| next build（Turbopack） | junction 目标在 `turbopack.root` 外 → `Symlink apps/web/node_modules is invalid` | **不设 `turbopack.root`**（自动推断主仓库 → junction 目标落在 root 内）；next 16.3.1 起无 RangeError |
| next build（standalone 输出） | junction 下 `EPERM: operation not permitted, symlink`（跨 junction 创建 symlink 权限失败） | **真实安装**：`pnpm install --frozen-lockfile --ignore-scripts`（约 40s），node_modules 真实目录放 worktree 内 |
| next dev | 无 standalone 输出，junction 状态可跑 | 与测试共用 junction 态 |

**切换方式**：junction 用 Node 创建最可靠（PowerShell/cmd 在幽灵目录残留时会失败）：

```bash
node -e "
const fs=require('fs'),path=require('path');
const WT=path.resolve('<worktree 绝对路径>'), MAIN=path.resolve('<主仓库绝对路径>');
for (const p of ['node_modules','apps/web/node_modules','apps/api/node_modules','packages/db/node_modules','packages/shared/node_modules']) {
  const link=path.join(WT,p), target=path.join(MAIN,p);
  try{fs.rmSync(link,{recursive:true,force:true})}catch{}
  fs.symlinkSync(target,link,'junction');
}"
```

真实安装 ↔ junction 切换前先删净旧目录（`cmd rmdir /s /q` 对深路径报「语法不正确」但实际会删，以 `ls` 确认为准）。

## 2. pnpm install 陷阱

- ⚠️ **junction 状态下跑 `pnpm install` 会穿透 junction 删除并重建主仓库 node_modules**（输出 `Recreating C:\...\insightweaver\node_modules`）。依赖与 lockfile 对齐后不再触发；触发时主仓库 node_modules 会被重建为 worktree lockfile 的依赖集（副作用：主仓库依赖被「升级」，一般无害，但要注意主仓库代码与依赖的兼容）。
- ⚠️ **`--ignore-scripts` 跳过 postinstall → Prisma client 不生成** → API tsc 报 `@prisma/client has no exported member 'PrismaClient'`（全仓数百错）。修复：
  ```bash
  pnpm --filter @insightweaver/db exec prisma generate   # 直接 exec，turbo 缓存会跳过 db:generate
  ```
- **junction 下 Prisma client 来自主仓库（旧 schema）**：worktree 分支 schema 与主仓库不同 → 用 worktree schema 重新 generate（写穿 junction 到主仓库 node_modules，旧代码对超集字段兼容，无害）。
- `pnpm add`（依赖变更）会把 node_modules 真实化/重建 → 变更后按需切回 junction（测试）或保留真实（build）。

## 3. next@16 无 exports map

next@16 全系 package.json **无 exports map**（`next/server` 目录式导入失效，仅有 `server.js` 文件），依赖运行时内置 alias——Turbopack 只对应用代码 alias，**node_modules 包内**（如 next-intl middleware.js 的 `import 'next/server'`）不 alias → 构建报 `Can't resolve 'next-intl/middleware'`（错误归因在外层模块）。

解法（next.config.mjs，已提交为构建基线）：

```js
turbopack: {
  resolveAlias: { 'next/server': 'next/server.js' },
  // 不设 root！junction 目标必须在自动推断的 root 内
},
```

**next 16.0.10 的 Turbopack 有 `RangeError: Invalid count value: -3`（String.repeat）构建崩溃**（双 lockfile 时 root 推断错误）——升级 next 16.3.1 修复。⚠️ 网络搜索会把此错误指向 Tailwind v4.1.18——**对本项目不适用**（16.3.1 + tailwind 4.1.18 组合构建通过）。

## 4. hook 与 cwd

- devflow PreToolUse hook 按 **cwd 解析 `${ZCODE_PROJECT_DIR}/.zcode/hooks/`**：在 worktree 子目录（如 apps/api）运行工具时 hook 脚本找不到 → fail-closed 拦截（`can't open file .../.zcode/hooks/devflow-hook-guard.py`）。**worktree 需拷贝 `.zcode/hooks/` 副本；任何工具调用前先 `cd` 回 worktree 根**。
- verify 阶段源码写入被物理拦截（`verify-source-write-blocked`）→ 走官方回修路径：`set <id> verify_result fail` → `/trellis-break-loop`（break-loop-analysis.md + cp_break_loop_done）→ `transition --back <id>`。
- verify 阶段 **Bash heredoc 写文件也被拦**（analyze_bash_command 探测）→ 用 Write 工具（.trellis 白名单放行）。

## 5. 环境文件与状态真相源

- worktree 需拷贝本地环境文件：`apps/api/.env`（52 项配置，含 OSS_ACCESS_KEY_ID 等）——缺失时 API dev 报 `Configuration key "XXX" does not exist`。
- **`.trellis/tasks/<id>/` 状态真相源 = 主仓库**：`DF_MAIN` 经 `git rev-parse --git-common-dir` 解析为主仓库根——从 worktree 运行 guard/state 也读主仓库的 task.json + evidence。**evidence 文件更新后必须同步主仓库副本**（`cp` worktree → 主仓库 `.trellis/tasks/<id>/`），否则 guard 内容校验读旧文件。
- `.trellis/tasks/` 是 gitignored 的本地运行时产物；`.trellis/spec/` 是 git 跟踪的（随分支提交）。
- 主仓库 checkout 任务分支会被 worktree 占用（`fatal: already used by worktree`）——需要短路径 build 验证时用 detached HEAD（`git checkout <commit-sha>`）。

## 6. dev 环境验证

- API dev（NestJS）：worktree 内 `pnpm --filter @insightweaver/api dev` 可正常启动（需 .env）。
- web dev（next dev）：junction 态 + 无 root 配置可启动；`.next/dev/lock` 残留（进程被杀）会报锁冲突——删 `.next` 后重试。
- dev 首次编译慢（ts-node/esm 全量）属正常，耐心等待而非判定卡死。
