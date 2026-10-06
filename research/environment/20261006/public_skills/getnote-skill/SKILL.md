---
name: getnote
description: >
  得到大脑（Get笔记）— 保存、搜索、管理个人笔记和知识库。
  当用户要求以下任一操作时触发此 Skill：
  (1) 保存内容到笔记：发链接、发图片、说「记一下」「存到笔记」「保存」「收藏」
  (2) 搜索或查看笔记：「搜一下」「找找笔记」「最近存了什么」「看看原文」
  (3) 管理知识库或标签：「加到知识库」「建知识库」「加标签」「删标签」
  (4) 配置 得到大脑（Get笔记）：「配置笔记」「连接得到大脑（Get笔记）」
  (5) 管理笔记：「删笔记」「改笔记」「更新笔记」「回收站」
---

# 得到大脑（Get笔记）Web API

通过 JWT Bearer Token 认证，操作 GetNotes API（`get-notes.luojilab.com`）。

> 注意：另一个域名 `notes-api.biji.com` 仅部分端点（如用户状态）可用，笔记读写请统一用 `get-notes.luojilab.com`。

## 前置条件

必须提供四项凭证，否则提示用户先获取：

- `GETNOTE_TOKEN` — JWT Bearer Token（从浏览器 Cookie 中 `token` 获取）
- `GETNOTE_CSRF` — Xi-Csrf-Token（从浏览器 Cookie 中 `csrf_token` 获取）
- `GETNOTE_DEVICE_ID` — 设备 ID（从浏览器 Cookie 中 `device_id` 获取）
- `GETNOTE_REFRESH_TOKEN` — refresh_token（从浏览器 Cookie 中 `refresh_token` 获取，用于自动续期）

**如果用户未提供凭证**，告知用户：
1. 打开 https://www.biji.com 并登录
2. F12 → Application → Cookies → www.biji.com
3. 复制 `token`、`csrf_token`、`device_id`、`refresh_token` 四个 Cookie 值

> ⚠️ `refresh_token` 通常不会自动刷新，需手动重新登录后获取。请同时提供 `GETNOTE_TOKEN` 和 `GETNOTE_REFRESH_TOKEN`。

### Token 自动刷新（Agent 自主执行，不询问用户）

**只要 `refresh_token` 未过期，Token 到期时必须自行刷新，绝不询问用户。**

刷新端点：`POST https://ddll-api.trytalks.com/account/v2/web/user/auth/refresh`
- Base URL 是 `ddll-api.trytalks.com`，**不是** `get-notes.luojilab.com`
- Body: `{"refresh_token": "<REFRESH_TOKEN>"}`
- 新 token 有效期约 30 分钟，新 refresh_token 有效期约 3 个月
- 刷新后同时更新 `/tmp/getnote_token.txt` 和 `.env` 中的字段

> ⚠️ `refresh_token` 格式：以多个 `A` 开头，以 `.` 分隔符结尾（如 `AAAAAA...xxx.yyy.zzz`），复制时务必完整勿截断。

> **微信视频号/抖音等平台链接无法解析**——这些平台需要登录 Cookie，直接 curl/wget 仅返回"视频号"占位符。如用户发来此类链接，**直接请用户提供链接里的实际内容**，不要花时间爬取。

## 直接 API 调用（推荐）

凭证有效期短，建议直接用 curl 或 urllib 调用，不依赖 SDK。

### 标准请求头（每请求必带）

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <GETNOTE_TOKEN>` |
| `Xi-Csrf-Token` | CSRF Token |
| `x-d` | 设备 ID |
| `Xi-App-Client-Source` | `getnote`（必填，否则 403）|
| `Content-Type` | `application/json` |
❌ **错误方式**（execute_code 沙箱中 token 丢失）：
```python
# Token 在 f-string 或字符串拼接中会被截断
auth = f"Bearer {token}"   # execute_code 沙箱中 token 丢失
subprocess.run(["curl", ..., "-H", f"Authorization: Bearer {token}", ...])  # 同上
```

✅ **正确方式（推荐 urllib）**：execute_code 中用 urllib 直接请求，不用 subprocess curl：
```python
import urllib.request, json
with open("/tmp/getnote_token.txt", "rb") as f:
    lines = f.read().split(b"\n")
token = lines[0].decode("utf-8")
csrf = lines[1].decode("utf-8")
did = lines[2].decode("utf-8")
req = urllib.request.Request(url, headers={
    "Authorization": "Bearer " + token,
    "Xi-Csrf-Token": csrf,
    "x-d": did,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.biji.com",
    "Referer": "https://www.biji.com/",
    "Xi-App-Client-Source": "getnote",
})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
```

> ⚠️ **subprocess+curl 在 execute_code 中不稳定**：shell 字符串拼接会截断 token。urllib 绕过 shell 直接请求，最稳定。terminal 工具中 curl 正常。

❌ **错误方式**（execute_code 会静默截断 Token）：
```python
# Token 在 f-string 或字符串拼接中会被截断
auth = f"Bearer {token}"   # execute_code 沙箱中 token 丢失
subprocess.run(["curl", ..., "-H", f"Authorization: Bearer {token}", ...])  # 同上
```

### Python urllib 参考

```python
import urllib.request, json, os

def getnote(path, token=None, csrf=None, device_id=None):
    token = token or os.environ.get("GETNOTE_TOKEN") or open("/tmp/getnote_token.txt").read().strip()
    csrf  = csrf  or os.environ.get("GETNOTE_CSRF", "")
    did   = did   or os.environ.get("GETNOTE_DEVICE_ID", "")
    req = urllib.request.Request(
        f"https://get-notes.luojilab.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Xi-Csrf-Token": csrf,
            "x-d": did,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.biji.com",
            "Referer": "https://www.biji.com/",
            "Xi-App-Client-Source": "getnote",
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["c"]
```

> ⚠️ **urllib ParseTokenFailed 通常是 Token 已过期的信号**，不是 urllib 本身的问题。遇到此错误请先检查 Token 有效期（exp），确认过期后请用户重新登录获取新 Token。

### Token 过期排查流程
### Token 过期处理流程（自动刷新，无需询问用户）

当 API 返回 `LoginRequired` 或 403 Forbidden 时，执行以下自动刷新流程：

1. **从 .env 读取 refresh_token**，调用刷新端点：
   ```bash
   curl -s -X POST 'https://ddll-api.trytalks.com/account/v2/web/user/auth/refresh' \
     -H 'Content-Type: application/json' \
     -H 'Xi-App-Client-Source: getnote' \
     -H 'Xi-Csrf-Token: <CSRF>' \
     -H 'x-d: <DEVICE_ID>' \
     -d '{"refresh_token":"<REFRESH_TOKEN>"}'
   ```
   响应：`{ h: { c: 0 }, c: { success: true, token: { token, token_expire_at, refresh_token, refresh_token_expire_at } } }`

2. **将新 token + refresh_token 写入 `/tmp/getnote_token.txt`**（覆盖第1行和第4行），同时更新 `.env` 中的对应字段。

3. **重试原 API 请求**，使用新 token。

> ⚠️ refresh_token 有效期约 3 个月（`refresh_token_expire_at`），以 `.env` 中记录为准。若刷新返回失败，检查 refresh_token 是否已过期，过期则需用户提供新凭证。
>
> ⚠️ 刷新端点是 `ddll-api.trytalks.com`，**不是** `get-notes.luojilab.com`——搞混会导致 404。
>
> ⚠️ **永远不要让用户重新提供 token**——只要 refresh_token 未过期，就应当自动刷新，不打扰用户。
> ⚠️ Token 在飞书/消息平台对话中会被自动截断（显示 `eyJhbG...rfBk`），用户必须粘贴完整字符串，不能省略中间部分。

### 快速开始（curl）

```bash
# 列出笔记
curl -s 'https://get-notes.luojilab.com/voicenotes/web/notes?limit=20&sort=create_desc' \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Xi-Csrf-Token: <CSRF>' \
  -H 'x-d: <DEVICE_ID>' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  ## 更新笔记（PUT）

  **⚠️ 必须同时传 title，否则标题被清空。**
  **⚠️ json_content 必须从详情 API 获取**（`GET /voicenotes/web/notes/<id>`），因为只有详情 API 返回的 json_content 包含完整的 paragraph 节点（包括章节标题如"一、主食"的文字）。列表 API 的 json_content 中 section header 段落是空的！

  ```bash
  curl -s -X PUT "https://get-notes.luojilab.com/voicenotes/web/notes/<note_id>" \
    -H "Authorization: Bearer $GETNOTE_TOKEN" \
    -H "Xi-Csrf-Token: $GETNOTE_CSRF" \
    -H "x-d: $GETNOTE_DEVICE_ID" \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -H 'Origin: https://www.biji.com' \
    -H 'Referer: https://www.biji.com/' \
    -H 'Xi-App-Client-Source: getnote' \
    -d '{"title": "笔记标题", "json_content": "<新json_content>", "content": "<纯文本>", "body_text": "<纯文本>"}'
  ```

  > 详情 API (`GET /voicenotes/web/notes/<id>`) 的 `json_content` 字段始终为空字符串。本 session 实测：即使 Token 未过期，详情 API 也返回 `"json_content": ""`。正确做法：用列表 API 按 `note_id` 找到目标笔记，从列表返回对象的 `json_content` 字段读取原始 ProseMirror JSON 字符串，PUT 时直接回填该字符串（不要做 `json.loads()` 再 `json.dumps()`——保持原始字符串格式）。

  > **`content` 和 `body_text` 是预览渲染的关键**：只有 json_content 时预览页面空白。本 session 实测：content=纯文本换行分隔，body_text=同内容但换行用`<br>`。
## SDK（TypeScript Node.js 包）

SDK 位于 `scripts/` 目录下。使用 `npx tsx` 直接执行脚本。

### SDK 执行已知问题

**`basic.ts` 第 40 行有语法错误**（esbuild 无法解析模板字符串中的中文），且 `require()` 在 tsx -e 模式下不 work——直接用 Python subprocess + curl 模式最可靠。

> **本会话验证的可靠工作流**：写入 token 到 `/tmp/getnote_token.txt`（每行 token/csrf/device_id），用 `subprocess.run` + curl 调用 API，从文件读 token 避免截断。列表 API 含完整 json_content，永远优先用列表 API 而非详情 API。

### Token 刷新

Token 有效期约 30 分钟，过期后所有 API 返回 `LoginRequired`。刷新端点：

```
POST https://ddll-api.trytalks.com/account/v2/web/user/auth/refresh
Body: { "refresh_token": "..." }
```

> ⚠️ **Base URL 不是 `get-notes.luojilab.com`**，而是 `ddll-api.trytalks.com`——混淆后会导致 404。

响应：`{ h: { c: 0 }, c: { success: true, token: { token, token_expire_at, refresh_token, refresh_token_expire_at } }`

> **注意**：每次刷新成功后，服务端会返回**新的 refresh_token**（值与旧的不同），必须用新值更新存储位置（.env 和 /tmp/getnote_token.txt）。下一次刷新必须用最新那次返回的 refresh_token，用旧值会导致"刷新Token已过期"错误（本 session 实测：第二次刷新时用旧值报过期，换用用户新提供的后成功）。
>
> **Token 过期判断**：JWT `exp` 字段仅供参考（客户端时间可被篡改），以 API 返回 `LoginRequired` 为准。若收到 `LoginRequired` 且 `exp` 未过，说明服务端已主动吊销，需立即刷新。
>
> **refresh_token 格式**：以多个 `A` 开头，以 `.` 分隔符结尾（如 `AAAAAA...xxx.yyy.zzzFMDiKGGD...`），复制时务必完整勿截断。

### .env 文件

写入 `.env` 时推荐逐字段用 `hermes config set`，避免 heredoc 多行拼接导致 Token 中间字符被截断。格式：

```
GETNOTE_TOKEN=eyJhbG...n
GETNOTE_CSRF=...
GETNOTE_DEVICE_ID=...
GETNOTE_REFRESH_TOKEN=...
GETNOTE_TOKEN_EXPIRE_AT=...
GETNOTE_REFRESH_TOKEN_EXPIRE_AT=...
```

如需使用 SDK，改用 subprocess 方式并从文件读取 token：

```python
import subprocess, os
with open("/tmp/getnote_token.txt") as f:
    token = f.read().strip()
env = {**os.environ, "GETNOTE_TOKEN": token, ...}
result = subprocess.run(["npx", "tsx", "examples/basic.ts"],
    cwd="/Users/wansong/.hermes/skills/getnote/scripts", env=env)
```

> ⚠️ **SDK 默认读取 .env 中的凭证**。若 .env 中 token 已过期，SDK 所有调用均返回 `LoginRequired`，urllib 模式也会失败。务必先确认 .env 中 token 未过期。

### 初始化客户端

```typescript
import { GetNoteClient } from "./scripts/src/index";

const client = new GetNoteClient({
  token: process.env.GETNOTE_TOKEN,
  csrfToken: process.env.GETNOTE_CSRF,
  deviceId: process.env.GETNOTE_DEVICE_ID,
});
```

### 环境变量设置

在终端中设置（或写入 `.env` 文件）：

```bash
export GETNOTE_TOKEN="eyJ..."        # JWT Bearer Token
export GETNOTE_CSRF="abc123..."      # Xi-Csrf-Token
export GETNOTE_DEVICE_ID="e152..."    # x-d 设备ID
```

## API 速查

### 笔记操作

```typescript
// 获取笔记列表
const list = await client.notes.list({ limit: 10, sort: "create_desc" });
// list.total_items: 总数
// list.list: NoteListItem[]

// 获取所有笔记（自动翻页）
const all = await client.notes.listAll(50);

// 获取笔记详情
const detail = await client.notes.detail("note_id");

// 创建文本笔记
const created = await client.notes.createText("标题", "内容");

// 更新笔记
const updated = await client.notes.updateContent("note_id", "新标题", "新内容");

// 删除笔记（移入回收站）
await client.notes.delete("note_id");

// 获取笔记总数
const count = await client.notes.count();
```

### 搜索 API

```typescript
// 搜索笔记
const result = await client.notes.search("关键词", 1, 10);
// result.total: 匹配数
// result.list: SearchNoteResult[]
```

**搜索 API 是 GET 而非 POST**：查询参数直接拼接在 URL 中（`?keyword=<URL编码>&page=1&size=50`），无需 request body。

**⚠️ 搜索 API 关键词过滤不生效**：实测（2026-06）搜索"减肥/瘦身/减脂/体重"均返回相同结果（按更新时间倒序的前10条笔记），关键词参数可能未被服务端处理。搜索结果与直接翻列表 API 的前10条高度重合。如需精准搜索笔记，建议通过列表 API 遍历全部笔记后在本地用关键词过滤（见下方代码）。

**搜索响应格式（本 session 实测）**：
- 请求：`GET https://get-notes.luojilab.com/voicenotes/web/notes/search?keyword=<URL编码>&page=1&size=50`
- 响应结构：`c.items[]`（不是 `c.list`），每条含 `note_id`（不是 `id`）
- `content` 字段含 `<hl>关键词</hl>` 高亮标签，需用 `re.sub(r'<[^>]+>', '', content)` 去除
- `ref_content` 字段为空字符串，不要使用
- `body_text` 含全部章节标题（用 `<br>` 分隔），可用于判断笔记类型
- 翻页：响应含 `c.has_more: true/false`，逐页拉取直到 `has_more` 为 false
- Token 过期后搜索 API 返回 `LoginRequired`，需先刷新 token

**搜索结果字段对照**：

| 字段 | 说明 |
|------|------|
| `note_id` | 笔记 ID（搜索返回用此字段，**不是 `id`**） |
| `content` | 含高亮标签的正文，需 strip HTML |
| `ref_content` | 始终为空，不要使用 |
| `body_text` | 章节结构概览（如"一、主食<br>二、凉菜..."） |
| `title` | 标题也含 `<hl>` 标签，需 strip |
| `created_at` | 创建时间，格式 `YYYY-MM-DD HH:MM:SS` |

**列表 API vs 详情 API 内容差异**：

| 字段 | 列表/搜索 API | 详情 API |
|------|-------------|---------|
| `content` | ✅ 含表格正文（`\|` 分隔） | ❌ 始终为空 |
| `body_text` | ✅ 含全部章节结构 | ❌ 始终为空 |
| `json_content` | ⚠️ 缺少 section header 段落文字 | ✅ 完整 ProseMirror JSON（含章节标题）|

> ⚠️ **永远优先用列表/搜索 API 的 `content` 字段**，详情 API 的 content/body_text 为空。

### 标签

```typescript
// 获取标签列表
const tags = await client.tags.list(200);
// tags.items: TagInfo[]

// 为笔记添加标签
await client.tags.add("note_id", ["标签1", "标签2"]);

// 删除笔记标签（需要 tag_id）
await client.tags.remove("note_id", ["tag_id"]);
```

### 回收站

```typescript
// 回收站列表
const trash = await client.notes.recycleBin(1, 20);

// 回收站搜索
const found = await client.notes.searchRecycleBin("关键词");

// 批量恢复
await client.notes.recycleBinBatchOp(["note_id"], "restore");

// 批量彻底删除
await client.notes.recycleBinBatchOp(["note_id"], "delete");

// 清空回收站
await client.notes.clearRecycleBin();
```

### 知识库（话题）

```typescript
// 添加笔记到话题
await client.knowledge.addNotesToTopic(topicId, ["note_id"]);

// 从话题移除笔记
await client.knowledge.removeNoteFromTopic(topicId, "note_id");

// 在话题中创建笔记
await client.knowledge.createNoteInTopic({
  topic_id: 123,
  title: "标题",
  json_content: "...",
});

// 获取博主列表
const bloggers = await client.knowledge.getBloggerList();

// 获取博主内容
const posts = await client.knowledge.getBloggerPosts("follow_id");

// 取消关注博主
await client.knowledge.unfollowBlogger(["follow_id"]);
```

## 执行脚本模式

对于一次性操作，使用内联脚本模式（`npx tsx -e`）：

```bash
cd scripts && \
GETNOTE_TOKEN="..." GETNOTE_CSRF="..." GETNOTE_DEVICE_ID="..." \
npx tsx -e '
const { GetNoteClient } = require("./src/index");
const client = new GetNoteClient({
  token: process.env.GETNOTE_TOKEN,
  csrfToken: process.env.GETNOTE_CSRF,
  deviceId: process.env.GETNOTE_DEVICE_ID,
});
(async () => {
  const list = await client.notes.list({ limit: 5 });
  console.log(JSON.stringify(list, null, 2));
})().catch(e => console.error(e.message));
'
```

## 注意事项

1. **Token 有效期**：Token 有过期时间（exp 字段），过期后所有 API 返回 `ParseTokenFailed`。列表 API 通常比详情 API 窗口更宽。提供 `refresh_token` 可实现自动续期；否则需用户重新从浏览器获取。检查方式：`python3 -c "import jwt; print(jwt.decode(token, options={'verify_signature':False})['exp'])"`
2. **int64 ID**：`note_id` 是 64 位整数，SDK 已自动以字符串处理，避免 JS 精度丢失。
3. **响应格式**：Web API 格式为 `{ h: { c: 0, e: "", ... }, c: <data> }`，`h.c === 0` 表示成功。
4. **列表含全内容**：列表端点返回的每条记录中已包含完整 `json_content`，**永远优先用列表 API 而非详情 API**。若必须查详情：
   - 详情 API 的 `content` 字段**永远为空**，不要使用
   - `body_text` 也为空
   - **真实内容在 `json_content` 字段**（ProseMirror JSON），需 `json.loads()` 后自行解析节点树
   - 详情 API 在 Token 快要过期时返回 `LoginRequired`，而列表 API 仍可用
5. **创建笔记**：使用 ProseMirror JSON 格式（SDK 的 `createText` 方法自动处理）。
6. **ProseMirror 节点命名**：得到笔记使用 **camelCase** 节点名（`tableRow`/`tableCell`，不是 snake_case）。
7. **paragraph attrs**：必须带完整 attrs `{"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}`，缺少任一字段会导致预览渲染异常。
8. **tableCell attrs**：必须带 `"attrs":{"colspan":1,"rowspan":1,"colwidth":null}`。
9. **速率限制**：SDK 内置 429 自动重试。
10. **知识库**：biji.com 中知识库称为"话题"（Topic），通过 `topic_id` 标识。
11. **搜索需重新认证**：搜索端点（`/voicenotes/web/notes/search`）在 Token 过期后返回 `LoginRequired`，此时需用户刷新 Cookie 后重试。
12. **urllib 偶发 ParseTokenFailed**：列表 API urllib/curl 均稳定；详情 API urllib 偶发此错误，curl 稳定。遇到详情报错时换用 curl 即可。
13. **刷新偶发失败可重试**：刷新请求有时返回"刷新Token已过期"但实际上 refresh_token 仍有效（exp 在未来），重试一次通常成功。遇到刷新失败不要立即判定 token 已失效，先重试一次。
14. **PUT 更新笔记必须同时传 title、json_content、content 三个字段**：
   - **必须同时传 `title`**：否则标题被清空（本 session 实测：只传 json_content 导致标题丢失）。
   - **json_content 必须是原始 JSON 字符串**，不能是解析后的对象。API 返回 `h.c=10000 json: cannot unmarshal object into Go struct field UpdateNoteReq.json_content of type string`。
   - 正确模式：先 GET 拿到 `json_content`（原始字符串），PUT 时直接回传该字符串，不要 `json.loads()` 再 `json.dumps()`。
   - **必须同时传 `content`（纯文本）和 `body_text`（HTML）**：这两个字段驱动笔记预览渲染。如果只有 `json_content`，预览页面会显示空白。本 session 实测：回退到旧版后预览仍空白，加上 `content` 后才恢复正常。
   - **`content` 生成方法**：列表 API 返回的 `note["content"]` 已包含完整章节标题和表格内容，**直接使用不做重建**。如需在特定 section 追加条目，在正确位置做字符串插入操作。
   - **`body_text` 生成方法**：同 `content` 但段落/行之间用 `<br>` 连接（非表格内容也用 `<br>` 而非 `\n`）。致良知笔记的 `body_text` 格式为纯文本含 `<br>` 换行，可直接作为 HTML 渲染。
   - ⚠️ **`body_text` 会被服务器清理/截断**：实测 `<br>` 标签在 PUT 后被移除，服务器只保留纯文本部分。因此 `body_text` 实际上与 `content` 完全相同（纯文本，无 HTML 标签）。预览渲染以 `content` 字段为准。

   ## Token 文件格式（当前实际格式）

   **`/tmp/getnote_token.txt` 当前格式**：第一行是 Python dict（单引号，非 JSON），第四行是 refresh_token 纯字符串：

   ```
   # 行1：Python dict（单引号）
   {'jti': '...', 'token': 'eyJhbG...', 'token_expire_at': 1781432136, 'refresh_token': 'AAAAAA...', 'refresh_token_expire_at': 1788794800}
   # 行2：空
   # 行3：空
   # 行4：refresh_token 纯字符串（以多个 A 开头）
   AAAAAAAbi-EZTPlkATfE5mhc9XOQSLj1AAAAAGqe17CBELmuNicK3NgHNCAEa9bh.FMDiKGGDGEUqSllF3lgNmJ2u83TiQ1vISg5-fmsnxBw
   ```

   **读取方式**：
   ```python
   with open("/tmp/getnote_token.txt", "rb") as f:
   lines = f.read().split(b"\n")
   data = ast.literal_eval(lines[0].decode("utf-8"))  # 行1是Python dict
   token = data["token"]
   refresh = data["refresh_token"]
   ```

   > ⚠️ 不要用 `json.loads()` 解析行1——文件是 Python dict 格式（单引号），不是 JSON。必须用 `ast.literal_eval()`。

   > ⚠️ 文档旧版说"4行分别是 token/csrf/did/refresh_token"——那是旧格式，当前格式已变更，以本节为准。

   ## Token 刷新（自动执行）

   **刷新端点**：`POST https://ddll-api.trytalks.com/account/v2/web/user/auth/refresh`
   - Base URL 是 `ddll-api.trytalks.com`，**不是** `get-notes.luojilab.com`
   - Body: `{"refresh_token": "<REFRESH_TOKEN>"}`

   **刷新响应结构（2026-06 实测）**：
   ```json
   {
   "h": { "c": 0 },
   "c": {
   "success": true,
   "status": 1,
   "uid": "...",
   "token": {
     "token": "eyJhbG...",          // 新 token（嵌套在 c.token.token）
     "token_expire_at": 1781432136,
     "refresh_token": "AAAAAA...",  // 新 refresh_token
     "refresh_token_expire_at": 1788794800
   }
   }
   }
   ```

   > ⚠️ **Token 嵌套在 `c.token.token`**（不是直接在 `c.token`）。CSRF 和 DID 字段**不再从刷新接口返回**，刷新后会丢失。需重新从浏览器 Cookie 获取。

   刷新后保存方式：
   ```python
   with open("/tmp/getnote_token.txt", "w") as f:
   f.write(str({
       "token": new_token,
       "refresh_token": new_refresh,
       "token_expire_at": new_exp,
       "refresh_token_expire_at": new_refresh_exp
   }))
   ```

   ## SDK（TypeScript Node.js 包）

   表格要在笔记预览中正常渲染，必须满足以下全部条件：

   | 节点 | 必须的 attrs | 说明 |
   |------|-------------|------|
   | `table` | `{"commentIds": [], "class": null}` | **关键！** 无此 attrs 表格预览不渲染 |
   | `tableHeader`（表头格） | `{"colspan": 1, "rowspan": 1, "colwidth": null}` | 表头行用此 type，**不是** `tableCell` |
   | `tableCell`（数据格） | `{"colspan": 1, "rowspan": 1, "colwidth": null}` | 数据单元格 |
   | `paragraph`（表格内外均需） | `{"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}` | 段落节点缺少此 attrs 会导致预览异常 |

   **表格节点结构示例**：
   ```json
   {
     "type": "table",
     "attrs": {"commentIds": [], "class": null},
     "content": [
       {
         "type": "tableRow",
         "content": [
           {
             "type": "tableHeader",
             "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
             "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "名称"}]}]
           },
           {
             "type": "tableHeader",
             "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
             "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "做法"}]}]
           }
         ]
       },
       {
         "type": "tableRow",
         "content": [
           {
             "type": "tableCell",
             "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
             "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "米饭"}]}]
           },
           {
             "type": "tableCell",
             "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
             "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "米水比1:1.2"}]}]
           }
         ]
       }
     ]
   }
   ```

   **重建含表格的 json_content 时的辅助函数**：
   ```python
   para_attrs = {"lineHeight": "100%", "textAlign": None, "class": None, "indent": 0}
   def make_para(text):
       return {"type": "paragraph", "attrs": dict(para_attrs),
               "content": [{"type": "text", "text": text}]}
   def make_header_cell(text):
       return {"type": "tableHeader", "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None},
               "content": [make_para(text)]}
   def make_data_cell(text):
       return {"type": "tableCell", "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None},
               "content": [make_para(text)]}
   def make_header_row(cols):
       return {"type": "tableRow", "content": [make_header_cell(c) for c in cols]}
   def make_data_row(cols):
       return {"type": "tableRow", "content": [make_data_cell(c) for c in cols]}
   def make_table(cols, rows_data):
       content = [make_header_row(cols)]
       for rd in rows_data:
           content.append(make_data_row(rd))
       return {"type": "table", "attrs": {"commentIds": [], "class": None}, "content": content}
   ```

   **添加新表格行**（在已有 table 节点末尾追加）：
   ```python
   new_row = {"type": "tableRow", "content": [
       {"type": "tableCell", "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None},
        "content": [make_para("新菜名")]},
       {"type": "tableCell", "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None},
        "content": [make_para("做法说明")]}
   ]}
   for block in jc['content']:
       if block.get('type') == 'table':
           block['content'].append(new_row)
   ```

   ### ⚠️ `content` 字段决定预览是否渲染表格

   **GetNotes 预览渲染读的是 `content` 字段，不是 `json_content`**。即使 `json_content` 的 ProseMirror table 节点完全正确，如果 `content` 字段格式不对，预览也不显示表格。

   实测结论：
   - ❌ `content = "名称 | 做法\n米饭 | 米水比..."`（管道符纯文本）→ 不渲染表格
   - ✅ `content = "| 名称 | 做法 |\n| --- | --- |\n| 米饭 | 米水比..."`（**Markdown 表格格式**）→ 正常渲染

   修复含表格笔记时，`content` 字段必须从 `json_content` 重建为 Markdown 表格格式（`|` 分隔 + `| --- |` 分隔行），参考 `references/recipe-note-table-fix.md`。

## 图片/多媒体笔记

### 读取图片

笔记中的图片在 `attachments` 字段中：

```python
d = getnote(f"/voicenotes/web/notes/{note_id}")
for att in d.get("attachments", []):
    if att["type"] == "image":
        print("图片URL:", att["url"])         # 缩略图 OSS 签名链接
        print("原始图片:", att["original_url"])  # 原始尺寸 OSS 签名链接
        print("大小:", att["size"], "bytes")
```

音频在 `attachments` 中 `type: "audio"`，或直接读 `audio_url` 字段。

OSS 签名链接有过期时间，过期后需重新调用 API 获取新链接。

### 保存图片

**无公开上传 API**。图片走 App→OSS 直传路径，服务端只记录 URL。如需新建含图片的笔记，需要：
1. App 端上传图片到 OSS，获取 URL
2. 调用 `POST /voicenotes/web/notes` 创建 `img_text` 类型笔记，传入 `attachments`（需自行构造签名 URL）

本 SDK 不包含 OSS 上传能力。

## 参考资料

- 快速开始（curl/Python 模式）：`references/quickstart.md`
- API 端点完整列表：`references/api-reference.md`
- ProseMirror 表格格式模板（含预览渲染完整 attrs）：`references/table-format-template.md`
- 搜索 API 实测记录（响应格式、字段说明、翻页）：`references/search-api-notes.md`
- 详细类型定义：`scripts/src/types.ts`
- 使用示例：`scripts/examples/basic.ts`
- **更新含表格笔记的完整工作流（含代码模板）**：`references/update-recipe-notes.md`
- **菜谱笔记表格不渲染诊断案例**：`references/recipe-note-table-fix.md`（`content` 字段损坏的修复方法）
