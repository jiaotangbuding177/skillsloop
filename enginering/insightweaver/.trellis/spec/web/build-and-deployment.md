# Web Build & Deployment

## Next.js Standalone Output

本项目使用 `output: 'standalone'` 模式构建 Next.js，生成精简的 `standalone/` 目录供容器部署。

### pnpm 严格模式下的依赖追踪陷阱

**问题**：Next.js 16.3.1 的 standalone 模式依赖 `@vercel/nft` (Node File Trace) 追踪运行时需要的文件。在 pnpm 的严格 `node_modules` 结构（`.pnpm/` 嵌套符号链接）下，某些深层依赖的文件可能被遗漏。

**典型案例**：`@swc/helpers` 是 `next` 的直接依赖（非 optional），但其 `esm/_interop_require_default.js` 文件在 pnpm 符号链接解析下未被 NFT trace 包含，导致容器启动时报 `MODULE_NOT_FOUND`。

**修复模式（2026-08-21 二版，实测有效）**：build 脚本链末尾追加 patch 脚本，把完整包合并进 standalone 的 `.pnpm/@swc+helpers@<version>/node_modules/@swc/helpers/`（与 next 包内符号链接的解析路径精确匹配）：

```
"build": "... next build && node ./scripts/patch-standalone-swc-helpers.mjs"
```

**两个无效方案的教训（均经本地构建实证）**：

1. **显式添加依赖无效**：NFT 按引用图追踪而非依赖清单，web 代码未 import 该包时不会额外 trace esm 文件。
2. **`outputFileTracingIncludes` 无效**：该配置只写 `.nft.json`（serverless 部署用），且 **Turbopack 构建模式下 `collectBuildTraces` 根本不运行**（`bundler === Turbopack` 分支跳过），对 standalone 目录复制无任何作用。

### 升级 Next.js 版本后的检查清单

升级 Next.js 版本（尤其是 minor/patch）后，standalone 构建行为可能变化。必须验证：

1. **本地构建通过**：`pnpm --filter @insightweaver/web build`
2. **容器镜像构建成功**：Docker build 无报错
3. **容器启动无 MODULE_NOT_FOUND**：启动日志无缺失模块错误
4. **首页可访问**：`curl http://localhost:3000` 返回 200

### 已知需要 build 后 patch 的依赖

以下依赖在 standalone 模式下 NFT 引用图追踪不完整，需 build 后 patch 补齐：

| 依赖 | 原因 | patch 脚本 |
|------|------|----------|
| `@swc/helpers` | NFT 只追 CJS 入口，运行时 require-hook 需要 esm 文件 | `scripts/patch-standalone-swc-helpers.mjs`（2026-08-21） |

**未来升级时**：如果容器启动报 `MODULE_NOT_FOUND`，检查缺失模块是否在 `.pnpm/@<pkg>@<version>/node_modules/` 下只有部分文件——若是，扩展 patch 脚本而非依赖显式声明或 outputFileTracingIncludes。

### Dockerfile 关键点

```dockerfile
# Stage 1: Builder
RUN pnpm --filter @insightweaver/web... install --frozen-lockfile
RUN pnpm --filter @insightweaver/web build

# Stage 2: Runner
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

CMD ["node", "apps/web/server.js"]
```

**注意**：
- `standalone/` 目录已包含精简的 `node_modules`，不需要 COPY 顶层 `node_modules`
- 静态资源 `.next/static` 和 `public/` 需要单独 COPY（standalone 不包含这些）
- 启动命令是 `node apps/web/server.js`（standalone 生成的入口）

### Turbopack 开发模式 vs 生产构建

- **开发模式**（`next dev`）默认使用 Turbopack，支持 `resolveAlias` 解决模块解析问题
- **生产构建**（`next build`）不使用 Turbopack，`resolveAlias` 配置对 standalone 输出无影响
- 如果生产构建遇到模块解析问题，需要在 `package.json` 显式声明依赖，而非依赖 Turbopack alias

### 相关提交与 PR

- `b8c60c36` (2026-08-21) — 升级 next 16.0.10→16.3.1，解决 Turbopack RangeError
- `17ba1ecd` (2026-08-21) — 显式添加 `@swc/helpers` 修复 standalone MODULE_NOT_FOUND
- PR [#242](https://gitee.com/yinzhishi/insightweaver/pulls/242) — @swc/helpers 修复
