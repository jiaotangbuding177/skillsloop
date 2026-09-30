## MCP 全自主接入方案

### 目标
- “全自主”生成模式走新 MCP 端口（无交互）。
- 其他模式继续使用现有 MCP 端口。
- 保留当前 SSE 流程与追问处理，确保兼容。

### 新增 MCP 端口
- 大纲：`INDUSTRY_RESEARCH_OUTLINE_MCP_URL`（需要 `/mcp` 路径）
- 正文：`INDUSTRY_RESEARCH_CONTENT_MCP_URL`（需要 `/mcp` 路径）
-
### 建议填写示例（完整路径）
```
INDUSTRY_RESEARCH_OUTLINE_MCP_URL=http://47.116.218.181:8000/mcp
INDUSTRY_RESEARCH_CONTENT_MCP_URL=http://47.116.218.181:8010/mcp
```

### 前置假设
- 工具名称与请求结构与当前 MCP 一致：
  - `generate_industry_research_outline`
  - `generate_research_content`
- 新端口不会返回追问（elicitation 事件）。
- 新端口需要 `/mcp` 路径。

### 后端改动（apps/api）
1) 环境变量
   - 在 `env/insightweaver.env` 增加：
     - `INDUSTRY_RESEARCH_OUTLINE_MCP_URL=.../mcp`
     - `INDUSTRY_RESEARCH_CONTENT_MCP_URL=.../mcp`
   - 保留 `MCP_OUTLINE_URL` / `MCP_CONTENT_URL` 作为默认。

2) MCP 端点选择
   - 文件：`apps/api/src/mcp/mcp.service.ts`
   - 新增：
     - `getOutlineEndpoint(mode?: string)`
     - `getContentEndpoint(mode?: string)`
   - 规则：
     - `mode === 'autonomous'` → 使用 `INDUSTRY_RESEARCH_*_MCP_URL`
     - 其他 → 使用 `MCP_*_URL`
     - 若 autonomous 端口缺失，回退到默认并记录 warn。

3) ToolRegistry 按端点缓存
   - 文件：`apps/api/src/mcp/tool-registry.ts`
   - 现状 cache key 仅区分 `outline|content`，需改为按 endpoint。
   - 更新：
     - `listTools({ endpointKey, mode })` 或 `listToolsForEndpoint(endpoint)`
     - cache key 使用 endpoint 字符串
     - sessionKey 包含 endpoint（如 `tools:outline:${hash(endpoint)}`）

4) ReportAgent / ToolInvoker 透传 mode
   - 文件：`apps/api/src/agent/report-agent.service.ts`
     - `generateOutline(prompt, sessionKey, handlers, mode?)`
   - 文件：`apps/api/src/agent/tool-invoker.ts`
     - `callOutlineTool(sessionKey, args, handlers, mode?)`
     - 使用 `getOutlineEndpoint(mode)` 获取端点

5) ResearchService 贯穿 mode
   - 文件：`apps/api/src/research/research.service.ts`
     - `generateOutline(..., mode?)` → 传给 `reportAgent` 与 `getOutlineEndpoint(mode)`
     - `generateContent(..., mode?)` → 使用 `getContentEndpoint(mode)`
     - sessionKey 建议包含 mode，避免不同模式复用同一 MCP 会话：`content:${outlineId}:${mode ?? 'default'}`
   - sessionStore 继续保存 endpoint + sessionId。

6) DTO 扩展
   - `apps/api/src/research/dto/generate-outline.dto.ts` 添加 `mode?: string`
   - `apps/api/src/research/dto/generate-content.dto.ts` 添加 `mode?: string`

7) Controller 透传
   - 文件：`apps/api/src/research/research.controller.ts`
   - `outline()` / `content()` 调用 service 时传入 `dto.mode`

### 前端改动（apps/web）
1) HomeDashboard 初始请求
   - 文件：`apps/web/src/components/home/HomeDashboard.tsx`
   - `/api/research/outline` body 增加 `mode: selectedMode`

2) ResearchInterface 请求
   - 文件：`apps/web/src/components/ResearchInterface.tsx`
   - `/api/research/outline` 与 `/api/research/content` body 增加 `mode: initialMode`

### 验证清单
- `mode=autonomous` 时，请求走新端口。
- 非 autonomous 仍走旧端口。
- SSE 在新端口下可直接完成，不出现追问。

### 待确认问题
- 无
