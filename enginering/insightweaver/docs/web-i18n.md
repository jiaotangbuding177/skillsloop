# Web 前端双语（i18n）规范

> **目标**：`apps/web` 所有面向用户的 UI 文案默认中英双语；新增功能时由 AI / 开发者同步补齐，而不是事后批量迁移。

## 路由与语言

| 项 | 约定 |
|---|---|
| 框架 | [next-intl](https://next-intl.dev) |
| 语言 | `zh`（默认）、`en` |
| 路由 | `/zh/...`、`/en/...`（`localePrefix: as-needed`，默认语言可省略前缀） |
| 文案文件 | `apps/web/messages/zh.json`、`apps/web/messages/en.json` |
| 导航 | `@/i18n/navigation` 的 `Link` / `useRouter` / `redirect`（不要用 `next/link` 直接跳站内页） |

## 必须做（新增 UI 时）

1. **禁止**在 JSX/TSX 中写面向用户的中文或英文字面量（注释、`data-testid`、日志除外）。
2. **禁止**使用 `translateAutoText`（历史遗留，已淘汰）。
3. **同时**在 `zh.json` 与 `en.json` 增加相同 key；英文须为人工可读的产品文案，不要机翻占位。
4. 客户端组件用 `useTranslations('命名空间')`；服务端组件用 `getTranslations`。
5. 带变量的文案用 ICU 占位：`t('saved', { name })` ↔ `"saved": "已保存 {name}"`。
6. 预设列表（卡片、选项）在组件内 `useMemo(() => buildItems(t), [t])`，**不要**在模块顶层调用 `t()`。
7. 改完执行：`pnpm --filter @insightweaver/web build`。

### 组件示例

```tsx
'use client';

import { useTranslations } from 'next-intl';

export function ExamplePanel() {
  const t = useTranslations('workspace.example');

  return (
  <>
    <h1>{t('title')}</h1>
    <p>{t('count', { count: 3 })}</p>
  </>
  );
}
```

### 文案 key 示例（两文件结构一致）

```json
// zh.json
"workspace": {
  "example": {
    "title": "示例面板",
    "count": "共 {count} 项"
  }
}

// en.json
"workspace": {
  "example": {
    "title": "Example panel",
    "count": "{count} item(s)"
  }
}
```

## 命名空间约定

按功能域归类，优先复用已有命名空间：

| 命名空间 | 用途 |
|---|---|
| `common.*` | 全站通用按钮、状态 |
| `workspace.sidebar.*` | 侧栏、文件夹展示名 |
| `workspace.fileTree.*` | 文件树工具栏、菜单 |
| `workspace.chat.*` | 对话区 UI |
| `workspace.toasts.*` | Toast、confirm 文案 |
| `workspace.dialog.*` | 弹窗标题与表单 |
| `workspace.pages.*` | 独立页面（memory、skills、employees…） |
| `workspace.shell.*` / `nav.shell.*` | 壳层、顶栏、底栏 |
| `workspace.loading.*` | 加载态 |
| `workspace.recharge.*` | 充值中心 |
| `errors.*` | API 错误码映射（`use-error-text`） |

SuperLobster 大页可继续用 `useWorkspaceI18n()`（`workspace.toasts` / `files` / `dialog` 等）。

## 仅展示翻译、不改业务数据

- 工作区路径、API 入参、数据库存储值：**保持中文/原始值**。
- 侧栏文件夹等展示：用 `translateWorkspaceFolderName` / `translateWorkspacePathForDisplay`（`workspace-display-name.ts`）。
- Agent 指令、cron 业务配置、`buildAiEditPrompt()` 等发给模型的内容：**不要 i18n**。

## 明确不做 i18n

- 技能市场 **mock 数据**（`apps/web/src/components/zclaw/data.ts` 等演示数据）
- 浏览器 / OS 原生控件（如 `<input type="date">` 弹层）
- 后端返回的动态错误正文（走 `errorToast(error.message)` 即可）
- 用户自定义文件名、知识库名、会话标题等内容

## 批量合并脚本（可选）

大批量迁移可用 `apps/web/scripts/merge-workspace-p3-*.mjs` 模式：脚本内 `patch.zh` / `patch.en` deep-merge 进 `messages/*.json`，然后 `node apps/web/scripts/<script>.mjs`。

日常小功能：**直接编辑** `zh.json` + `en.json` 即可，不必新建脚本。

## 产品英文命名（固定译法）

| 中文 | English |
|---|---|
| EvoMind 助手 / 超级龙虾 | EvoMind Assistant |
| 新对话 | New chat |
| 个人工作区 | Personal workspace |
| 共享工作区 | Shared workspace |

## 新功能自检清单

- [ ] 所有新增/修改的用户可见字符串已进 `zh.json` + `en.json`
- [ ] 组件使用 `useTranslations` / `getTranslations`，无硬编码 UI 文案
- [ ] 链接与跳转使用 `@/i18n/navigation`
- [ ] 未改动 API 字段、权限、布局逻辑
- [ ] `pnpm --filter @insightweaver/web build` 通过

## AI 协作说明

在本仓库开发 `apps/web` 时，Agent 应：

1. 默认将双语文案视为**功能交付的一部分**，与组件代码同 PR 完成。
2. 打开本文件：[`docs/web-i18n.md`](./web-i18n.md)。
3. 遵循 Cursor 规则：`.cursor/rules/web-i18n.mdc`。
4. 需要详细工作流时可读 Skill：`.cursor/skills/web-i18n/SKILL.md`。
