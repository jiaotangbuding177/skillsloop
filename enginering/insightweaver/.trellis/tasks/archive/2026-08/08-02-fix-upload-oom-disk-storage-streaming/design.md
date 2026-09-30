# Design: 上传 OOM 修复（diskStorage + 流式转发）

## Architecture

上传链路改造（本次仅改 NestJS 侧，KM Agent 不动）：

```
浏览器 → ALB → NestJS (multer diskStorage → .upload-temp 临时文件)
                    ↓ openAsBlob 惰性 Blob + Web FormData（流式，V8 堆近 0）
              KM Agent (busboy 流式 → 临时文件 → treeStore)
```

## Data Flow

0. **controller** 用 `try { return await service... } finally { if (file.path) unlink(file.path) }` 包裹整个 service 调用 → 无论 service 哪一步（含前置校验）抛异常都清理 temp 文件（multer 在 handler 前已写盘，故清理必须在此层）。
1. 浏览器 multipart 上传 → multer `diskStorage` 写入 `process.cwd()/.upload-temp/{timestamp}-{rand}.{sanitizedExt}`（V8 堆 0 占用；扩展名经消毒）
2. `ZclawService.uploadWorkspaceFile/uploadSharedWorkspaceFile/uploadChatFile` 传 `file.path` 给 client
3. `ZclawKmAgentClient` 两个公开上传方法委托给共享私有 helper `forwardMultipartFile(userId, routePath, targetPath, file, failureMessage)`：
   - `openAsBlob(filePath, { type: mimeType })` 包 try/catch → 惰性 Blob（系统错误包装为 `InternalServerErrorException`）
   - 标准 Web `FormData`：`append("path", targetPath)` + `append("file", blob, filename)`
   - `fetch(buildUrl(routePath), { method: "POST", headers: buildHeaders(userId, null), body: form })`（Content-Type 由 fetch 自动生成）
   - **不 unlink**（清理归 controller，单一职责）
4. 保留 `buffer` 分支：`new Blob([file.buffer])`（供 copyCrossSpaceFile 等内部复制路径使用）

## Key Decisions

| 决策 | 选择 | 原因 |
|------|------|------|
| avatar 端点 | 恢复 memoryStorage | `zclaw.service.ts:3906` 依赖 `file.buffer` 传 OSS；2MB 内存无害；服务层零改动 |
| 流式库 | **Node 原生 `openAsBlob`**（非 `form-data`） | 初版 form-data@4.0.5 是 CJS，其 FormData 非 Web `BodyInit`，流式 body 需 `duplex:'half'` 但本仓库 `@types/node@22.19.3` 的 `RequestInit` 缺该字段→需类型 hack。openAsBlob 零依赖、标准 API、无 hack，实测 100MB 堆增量 ~0.5MB |
| multipart 编码 | 标准 Web FormData | fetch 自动生成带 boundary 的 Content-Type，无需 `form.getHeaders()`；KM Agent 的 `multipart/form-data` 子串校验通过 |
| 清理职责 | **controller 层** try/finally（必须 `await`），client 不 unlink | multer 在 handler 前写盘，service 前置校验可抛异常绕过 client finally→client 清理会泄漏；上移 controller 覆盖全路径，单一职责 |
| openAsBlob 错误 | try/catch → `InternalServerErrorException` | 裸 ENOENT/EACCES 会上抛 500 并泄露 stack trace |
| 扩展名消毒 | `replace(/[^a-zA-Z0-9]/g,"").slice(0,16)\|\|"bin"` | originalname 客户端可控，防路径分隔符/null 字节/超长后缀注入 temp 文件名 |
| buffer 兼容 | 保留分支 | `copyCrossSpaceFile`/`copyWorkspaceFileWithinPersonalSpace` 仍传 buffer |
| 重复消除 | 共享 `forwardMultipartFile` + `UploadFileInput` 接口 + 模块级 `uploadTempStorage` | 消除两上传方法 ~30 行重复、内联类型重复、3 端点 filename 回调重复 |
| 硬编码路由 | **不改** | 与 client 文件其余路由内联风格一致，改常量制造无关 diff |
| fd 生命周期 | 不显式关闭 | 惰性 Blob 无 dispose API；undici 传输/abort 时消费 `blob.stream()` 关闭 fd；Linux unlink 后 inode 存活至 fd 关闭，持续失败下孤儿 fd 仅短暂存在至 GC |

## Compatibility

- ESM：本方案不依赖任何 CJS multipart 库（用 Node 原生 `openAsBlob` + 全局 Web `FormData`），无 interop 问题
- 传输层：惰性 Blob 的 `size` 已知（内部 stat），undici multipart 编码可带 Content-Length；Content-Type 由 fetch 自动生成（含 boundary），满足 KM Agent 的 `multipart/form-data` 子串校验
- 不破坏现有 API 契约：HTTP 路径、字段名（`path`、`file`）、响应结构均不变

## Operational Notes

- `.upload-temp` 需有 ≥2GB 可用磁盘（500MB 上限文件）
- 临时文件由 finally 清理；若 POD 被 kill，残留文件由重启/清理任务处理（记录为后续）
- 部署后验证：上传 260MB 文件观察 POD 内存曲线（应保持低位平稳）
