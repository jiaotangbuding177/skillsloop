## 生成大纲附件上传 OSS + 同步解析方案

### 目标
- 通过后端接口上传附件到 OSS（不走前端直传）。
- 上传接口内完成解析，解析完成后才返回。
- 生成大纲时读取解析后的文本内容。

### 关键流程
1) 客户端调用上传接口（multipart/form-data）。
2) 后端接收文件 -> 上传到 OSS -> 同步解析文本 -> 保存附件元信息与解析结果。
3) 上传接口返回 `attachmentId`，状态已解析完成。
4) 生成大纲接口接收 `attachmentIds`，读取解析文本。

### 接口设计（后端）
1) 上传附件（同步解析）
   - `POST /attachments/upload`
   - 入参：`file`（支持多文件可用 `files`）
   - 出参：`[{ id, filename, status, textReady: true }]`

2) 生成大纲
   - `POST /research/outline`
   - 入参新增：`attachmentIds?: string[]`
   - 逻辑：加载解析文本并拼入提示词或上下文

### 后端实现要点（NestJS）
- 模块：`AttachmentModule`
  - `attachments.controller.ts`：处理上传
  - `attachments.service.ts`：上传 OSS + 同步解析
  - `attachments.parser.ts`：解析 PDF/DOCX/TXT/图片 OCR 等
- 上传接口耗时可能较长，建议配置合理超时与限流。

### 数据模型建议（Prisma）
- `Attachment`
  - `id`, `ownerId`, `filename`, `mimeType`, `size`,
    `storageKey`, `status`(PENDING/UPLOADED/PARSED/FAILED), `createdAt`
- `AttachmentText`（或直接挂在 Attachment）
  - `attachmentId`, `text`, `summary?`, `updatedAt`
- 大纲关联
  - `OutlineAttachment` 多对多 或 `outline.attachmentIds` JSON

### OSS 配置（示例键名）
- `OSS_ACCESS_KEY_ID=...`
- `OSS_ACCESS_KEY_SECRET=...`
- `OSS_BUCKET_NAME=...`
- `OSS_ENDPOINT=...`
- `OSS_DIRECTORY=`（可选，支持按业务前缀存储）

### 安全与校验
- 文件类型白名单（pdf/docx/txt/md/xls/xlsx）
- 大小限制与数量限制
- 日志避免输出密钥
- 解析失败返回错误并保留错误信息

### 前端改动方案
#### 范围与入口
- 首页上传弹窗：`apps/web/src/components/home/HomeDashboard.tsx`
- 生成页输入区（如有上传入口）：`apps/web/src/components/ResearchInterface.tsx`
- 附件展示组件：`apps/web/src/components/home/AttachedFileCard.tsx`（复用）
- 草稿缓存：`apps/web/src/lib/generationDraftStorage.ts`

#### 功能拆分
1) 文件选择与本地校验
   - `accept`: `.pdf,.docx,.txt,.md,.xls,.xlsx`
   - 客户端校验：大小 <= 20MB、数量 <= 5、类型白名单
   - 校验失败只提示，不发请求

2) 上传接口调用
   - `POST /api/attachments/upload`（后端 `POST /attachments/upload`）
   - `multipart/form-data`，字段 `files`（或 `file`）
   - 成功返回 `[{ id, filename, status, textReady }]`

3) 前端数据结构调整
   - `AttachedFile` 增加 `attachmentId`、`status`、`error`
   - 状态：`uploading` / `parsed` / `failed`

4) 生成大纲时携带附件
   - 调用 `/api/research/outline` 时追加 `attachmentIds: string[]`
   - 仅提交上传成功且已解析的附件

5) UI/交互
   - 文件卡片显示上传状态（loading/成功/失败）
   - 失败可“重试上传/移除”
   - 成功提示在接口返回后触发

### 生成大纲时的拼接策略
- 若 `AttachmentText` 存在：
  - 追加到 prompt 的 “参考资料” 部分，按文件名分段
