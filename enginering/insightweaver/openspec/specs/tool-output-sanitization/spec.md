# 工具输出 Sanitization 完善经验

## 背景

系统中的工具消息可能泄露敏感信息：
1. **SKILL.md 文件内容**：工具输出中的技能配置文件可能被完整展示给用户
2. **品牌名称泄露**：`openclaw`、`@mariozechner/pi-*`、`hermes` 等上游品牌名出现在用户界面

## 架构：三层防御（Defense in Depth）

```
km-agent (raw tool output)
        │
        ▼
┌─── API Layer ──────────────────────────────────────┐
│  Layer 1: SSE Stream (streamMessage)               │
│  Layer 2: REST Endpoints (getSessionDetail, etc.)  │
│  Layer 2b: DB Persistence (upsertLocalToolMessage) │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─── Frontend Layer ──────────────────────────────────┐
│  Layer 3: Message Loading                           │
│  Layer 3b: Rendering (MessageBubble, Markdown, etc) │
└─────────────────────────────────────────────────────┘
```

### 为什么需要三层？
- **API 层**保底：即使前端渲染被绕过，API 返回的数据也是干净的
- **DB 层**保底：历史数据存储在数据库中不应包含敏感内容
- **前端层**保底：即使 API 层漏过，前端渲染也会再次过滤

## 品牌替换模式

**前后端使用相同的 5 条规则**，按优先级排序：

| # | 模式 | 替换 | 匹配说明 |
|---|------|------|----------|
| 1 | `/@mariozechner\/pi-/gi` | `@evomind/evomind-` | npm 包路径（最高优先级） |
| 2 | `/@mariozechner/gi` | `@evomind` | 独立 npm scope |
| 3 | `/openclaw/gi` | `evomind` | 路径/文件名/文本 |
| 4 | `/\bpi-(agent-core\|ai\|...)\b/gi` | `evomind-$1` | 裸包名 |
| 5 | `/\bhermes\b/gi` | `evomind` | 独立单词 |

### 设计要点
- **规则 1 必须在规则 2 之前**：防止 `@mariozechner/pi-*` 被 `@mariozechner` 部分替换
- **规则 3 不包含 `-?`**：保留 `openclaw-shared` → `evomind-shared` 的连字符
- **前后端 BRAND_REPLACEMENTS 需保持同步**：两边都有注释提醒

## Skill 内容检测

检测逻辑分两层：

### 1. YAML Frontmatter 检测
```typescript
// 匹配 `---\nname: xxx\ndescription: xxx\n---` 格式
const frontmatterMatch = val.match(/---\r?\n([\s\S]*?)\r?\n---/);
if (frontmatterMatch) {
  // 检查 yaml 头部是否包含 name: 或 description:
}
```

### 2. Markdown 模式检测
```typescript
const skillPatterns = [
  /##\s*(What I do|Best.practice workflow|How to use|Usage|When to use)/i,
];
```

检测到 skill 内容后，替换为 `[已读取 ${skillName}]`。

## 性能优化：Fast-Path

**核心思想**：大部分工具输出不含 skill 内容，不需要昂贵的递归遍历。

```typescript
// 快速检查：无 skill 路径标记 + 无 frontmatter → 只做品牌替换
if (!hasSkillPath && !hasSkillContent) {
  return JSON.parse(applyBrandReplacements(text));
}
// 否则：完整递归遍历
return sanitizeRecursive(data, skillName);
```

**适用条件**：
- 不包含 `SKILL.md` 或 `skills/` 路径标记
- 不包含 `---\nname:` frontmatter

**实际效果**：95%+ 的工具消息走 fast-path，性能开销几乎可忽略。

## API 层 4 个 Sanitizer 函数

| 函数 | 作用 | 调用点 |
|------|------|--------|
| `sanitizeToolOutputForStream` | SSE 流中的工具事件 | `streamMessage` yield 前 |
| `sanitizeToolContentForResponse` | REST 响应的 tool role content | `getLocalSessionDetail`、`mapSessionDetailMessage` |
| `sanitizeToolActivityFields` | 工具活动对象（output/args/error/deltas） | `extractToolActivity` 的 2 个返回点 |
| `sanitizeRawPayloadForDb` | 入库前的 rawPayload | `upsertLocalToolMessage` |

### 关键设计：extractToolActivity 作为单一阻塞点
`extractToolActivity` 有 5 个调用方，在此处添加 sanitization 即可覆盖所有调用方，避免在每个调用点重复添加。

## 前端层覆盖

| 位置 | 函数 | 覆盖内容 |
|------|------|----------|
| `zclaw-ragflow-message.ts` | `sanitizeToolOutputForDisplay` | tool role 消息加载时 |
| `MessageBubble.tsx` | `sanitizeToolOutputRecursive` | 工具活动 output/args/error/deltas |
| `ToolActivityGroup` | `sanitizeToolOutputRecursive` | 批量工具活动的各组字段 |
| `ZclawMarkdown.tsx` | `sanitizeToolOutputForDisplay` | Markdown 渲染内容 |
| `cron-task-helpers.ts` | `sanitizeToolOutputForDisplay` | Cron 运行摘要 |

## NO_REPLY 消息过滤

**提取到共享模块** `apps/web/src/lib/message-filters.ts`：

```typescript
const SILENT_REPLY_PATTERN = /^\s*NO_REPLY\s*$/;

export function isSilentReplyMessage(message: { role?: string; content?: string }): boolean {
  return message.role === "assistant" && SILENT_REPLY_PATTERN.test(message.content ?? "");
}
```

**使用位置**：`useZclawChat.ts`（3 处）+ `SuperLobsterPage.tsx`（2 处），在 `.map()` 之前统一过滤。

## 测试覆盖

| 层 | 测试数 | 覆盖内容 |
|----|--------|----------|
| API | 11 | fast-path、品牌替换、skill 内容检测、字段级过滤、非 JSON 容错 |
| 前端 | 19 | display sanitization、recursive sanitization、tool role 路由、品牌替换 |

## 经验教训

### 设计经验

1. **防御纵深是必要的**：单一过滤层不可靠。API 和前端都需要独立 sanitization
2. **单一阻塞点模式**：`extractToolActivity` 作为 5 个调用方的统一入口，避免遗漏
3. **Fast-path 设计**：大部分数据不需要完全处理，快速路径能显著降低开销
4. **共享代码 vs 复制代码**：BRAND_REPLACEMENTS 前后端各保留一份，加同步注释。提取到 shared package 的成本高于维护两处的成本（monorepo 内文件少）
5. **`[已读取 skillName]` 标签保留 skillName**：方便调试和管理员审计，只屏蔽内容不屏蔽标识

### 实现经验

6. **类型变更（type→interface）需注意兼容性**：`HumanEfficiencySuggestionContext` 和 `SkillTemplateItemRecord` 需保持 `type` 以兼容 `Record<string, unknown>` 和 Prisma `JsonValue`
7. **`sanitizeToolActivityFields` 的 JSON 往返**：fast-path 使用 `JSON.stringify→replace→JSON.parse`，会丢失 `undefined` 值。需额外恢复
8. **技术债务**：`member-delimiter-style` 在新版 `@typescript-eslint` 中已废弃，不需要在 ESLint 配置中启用
9. **ESLint 10 兼容**：`eslint:recommended` 需要 `@eslint/js` 包，且需配置 `globals` 避免 Node.js 全局变量误报 `no-undef`

### 调试经验

10. **环境差异**：ESLint 在 Windows 上扫描 `node_modules` 会因长路径而失败，需排除
11. **Prisma client 锁定**：Windows 下 dev server 会锁住 `query_engine-windows.dll.node`，`pnpm db:generate` 前需停止 dev server
12. **前后端同步测试**：修改 BRAND_REPLACEMENTS 后需同时验证 API 和前端测试通过