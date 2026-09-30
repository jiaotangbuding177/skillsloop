# Implement: 上传 OOM 修复

## Ordered Checklist

1. **声明依赖**：`apps/api/package.json` 添加 `"form-data": "^4.0.5"` → `pnpm install` 更新 lockfile
2. **R1 avatar 修复**：`zclaw.controller.ts` 的 `agent-avatars/upload` 端点恢复 `memoryStorage()`（import 恢复 `memoryStorage`）
3. **R2/R3/R5 改造 client**：`zclaw-km-agent.client.ts`
   - import：加 `import FormData from 'form-data'`；保留 `createReadStream`/`statSync`/`unlink`；删 `Readable`、`resolve`、`readFile`（不再全量读取）
   - `uploadWorkspaceFile`：流式 + try/finally
   - `uploadSharedWorkspaceFile`：流式 + try/finally
4. **R4 gitignore**：根 `.gitignore` 添加 `.upload-temp/`
5. **验证**：
   - `pnpm --filter @insightweaver/api build`
   - `pnpm --filter @insightweaver/api lint`
   - 可选：本地起 dev server + curl 上传验证

## Validation Commands

```bash
pnpm --filter @insightweaver/api build
pnpm --filter @insightweaver/api lint
```

## Risky Files

- `apps/api/src/zclaw/zclaw-km-agent.client.ts` — 核心流式改造；注意 try/finally 与 fetch body 生命周期
- `apps/api/src/zclaw/zclaw.controller.ts` — avatar 端点恢复 memoryStorage；确认 4 个端点中仅 avatar 用 memoryStorage

## Rollback Points

- 单文件粒度的 git diff 可逆；client 保留 buffer 分支，回退只需换回 `readFile` + `Blob`
