# Fix: 上传 OOM（diskStorage + 流式转发）

## Goal

解决 260MB 文件上传导致 NestJS OOM 崩溃（生产环境 POD 被 OOM kill，后续所有接口 502），并将大文件上传的内存占用降到最低。修复 diskStorage 切换引入的 4 个缺陷，并将 NestJS → KM Agent 的转发改为真正的流式管道。

## Background

- 生产环境 `evomind.zzz4ai.com` 上传 260MB 文件到 `/api/zclaw/shared-workspace/upload` 返回 502，浏览器响应是阿里云 ALB 错误页（`<center>alb</center>`），且失败后其他接口也全部 502 → NestJS 进程 OOM 崩溃。
- 根因：`memoryStorage()` 将 260MB 加载到 V8 堆，转发时 `new Uint8Array` + `new Blob` 再复制 2 次，峰值 ~780MB，超过容器内存限制。
- 已初步修改为 `diskStorage()`（峰值降到 ~260MB），但审查发现 4 个缺陷（见 Requirements）。
- KM Agent 端（`C:\Users\MR\workspace\evomind\km-agent`）使用 busboy 流式解析 multipart 写入临时文件，天然支持 chunked 流式上传，无需改动。生产 `KM_AGENT_MAX_UPLOAD_BYTES=524288000`（500MB），非限制因素。

## Requirements

### R1: 修复 uploadAgentAvatar 损坏（严重）
`agent-avatars/upload` 端点已改为 diskStorage，但 `zclaw.service.ts:3906` 仍用 `file.buffer` 传 OSS（diskStorage 下为 `undefined`）→ 头像上传必失败，且临时文件泄漏。
- 决策：该端点恢复 `memoryStorage()`（2MB 限制在内存中无害），avatar 服务层零改动。

### R2: 修复 lint error（未使用 import/变量）
`zclaw-km-agent.client.ts` 有 `createReadStream`/`Readable`/`resolve` 未使用 import 和未使用的 `fileStat` 局部变量，会触发 `@typescript-eslint/no-unused-vars: error`。
- 流式方案中 `createReadStream`/`statSync` 重新使用；`Readable`/`resolve` 删除。

### R3: 临时文件清理职责归 controller（第二轮 CR 修正）
multer `diskStorage` 在 controller handler **运行之前**就把文件写入 `.upload-temp`，而 service 在调用 client **之前**有多处 `await` 校验（`assertWorkspaceWriteAllowed`、`assertSharedWorkspacePermission`、`validateUploadedFile`、`resolveChatUploadTargetPath` 等）会抛异常。若清理放在 client，这些校验失败时根本到不了 client 的 finally → **临时文件永久泄漏**（攻击者/高频校验失败可耗尽磁盘）。
- 修正：3 个 diskStorage 端点（workspace/shared-workspace/chat-files）用 `try { return await service... } finally { if (file.path) await unlink(file.path).catch(()=>undefined) }` 包裹整个 service 调用（必须 `await`，否则 finally 会在 service 完成前执行而误删文件）。
- client `forwardMultipartFile` **不再 unlink**（清理单一归属 controller，避免重复职责）。

### R6: 第二轮 CR 加固（openAsBlob 错误 + 扩展名消毒）
- `openAsBlob` 用 try/catch 包裹，系统错误（ENOENT/EACCES）包装为 `InternalServerErrorException`，避免裸 SystemError 上抛成 500 并泄露 stack trace；同时确保 openAsBlob 自身失败也不会绕过清理（清理已上移 controller，与 openAsBlob 成败无关）。
- `filename` 回调对 `originalname` 扩展名消毒：`replace(/[^a-zA-Z0-9]/g, "").slice(0, 16) || "bin"`，消除攻击者可控的路径分隔符/null 字节/超长后缀注入 temp 文件名的风险。
- 硬编码路由路径（maintainability 建议）**不修**：与 client 文件其余路由的内联风格一致，改常量会破坏既有风格、制造无关 diff。

### R4: `.upload-temp` 加入 .gitignore
根 `.gitignore` 添加 `.upload-temp/`，避免 untracked 目录进入 git status。

### R5: 流式转发（openAsBlob，零新增依赖）
两个上传方法改为 Node 22 原生 `openAsBlob` 惰性 Blob（底层按 fd 流式读盘）+ 标准 Web `FormData`，V8 堆内存近 0。
- **决策变更（vs 初版设计）**：初版计划用 `form-data@4.0.5` + `createReadStream` + `knownLength`，但实施时发现该 CJS 包的 `FormData` 不是 Web 标准 `BodyInit`，配合 undici 流式 body 需要的 `duplex: 'half'` 在本仓库 `@types/node@22.19.3` 的 `RequestInit` 类型中缺失，需类型 hack。改用 `openAsBlob`：零新增依赖、标准 API、无类型 hack，且端到端实测 100MB 上传堆内存增量仅 ~0.5MB（比 form-data 方案更优）。`knownLength` 不再需要（chunked 编码，KM Agent busboy 兼容，见 design.md）。
- 两个公开上传方法折叠为共享私有 helper `forwardMultipartFile`，入参类型为共享接口 `UploadFileInput`（消除重复类型 / 重复逻辑）。
- 保留 `buffer` 分支向后兼容（`copyCrossSpaceFile` 等仍传 buffer）。
- **fd 生命周期**：`openAsBlob` 持有 fd 直到惰性 Blob 被 GC 或 undici 在传输（含 abort/失败）时消费完 `blob.stream()` 关闭 fd；磁盘 temp 文件的 unlink 由 **controller** 负责（与 openAsBlob 成败无关）。Linux 生产环境下 unlink 后 inode 存活到 fd 关闭，无泄漏；持续失败下的孤儿 fd 仅短暂存在直至 GC，风险可接受，无需显式关闭（Blob 无 dispose API）。

## Acceptance Criteria

- [ ] AC1: `pnpm --filter @insightweaver/api build` 通过（TS 严格编译无类型错误）
- [ ] AC2: `pnpm --filter @insightweaver/api lint` 无 error（无未使用 import/变量）
- [ ] AC3: `uploadAgentAvatar` 恢复 memoryStorage，avatar 上传功能正常（`file.buffer` 有值）
- [ ] AC4: 两个上传方法（workspace/shared-workspace）使用 `openAsBlob` 惰性 Blob 流式转发，不调用 `readFile` 全量读入内存；重复逻辑已折叠到共享 helper `forwardMultipartFile`，入参为共享接口 `UploadFileInput`
- [ ] AC5: 临时文件在成功/**任意失败**路径均被清理——清理在 **controller** 层 try/finally（覆盖 service 全部校验抛异常的场景），client 不 unlink
- [ ] AC6: `.upload-temp/` 已加入 .gitignore
- [ ] AC7: 260MB 文件上传不再导致 NestJS OOM（生产部署后验证）
- [ ] AC8: `openAsBlob` 系统错误被包装为 `InternalServerErrorException`（无裸 500 / stack 泄露）
- [ ] AC9: temp 文件名扩展名已消毒（仅字母数字、≤16 字符），无路径分隔符/null 字节注入

## Out of Scope

- `attachments`（20MB×6=120MB 峰值）、`skills/import-zips`（8MB×20=160MB 峰值）迁移 diskStorage → 后续任务
- 直传 OSS 架构改造
- KM Agent 端改动（无需）

## Technical Notes

- `openAsBlob(path, { type })`（Node 19.8+，生产 Node 22）返回惰性 `Blob`，undici 编码 multipart 时通过 `blob.stream()` 按块从磁盘读取，文件不进入 V8 堆；`blob.size` 已知（内部 stat），故 multipart 可带 Content-Length。
- 标准 Web `FormData` 作 `fetch` body，`Content-Type: multipart/form-data; boundary=...` 由 fetch 自动生成（满足 KM Agent 的 case-sensitive `multipart/form-data` 子串校验）；无需手动 `form.getHeaders()`，无需 `duplex`。
- `tsconfig.base.json` 已开启 `esModuleInterop`，但本方案不再依赖任何 CJS multipart 库，故无 interop 风险。
- controller 端 3 个 diskStorage 端点共享模块级 `uploadTempStorage` 实例（消除重复 `filename` 回调）；`agent-avatars/upload` 因 service 读 `file.buffer` 保留 `memoryStorage`。
- 新增代码遵循 AGENTS.md 双引号规则（import 路径跟随文件既有单引号块风格，不污染 diff）。
