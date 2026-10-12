---
name: feishu-connection
description: "使用用户授权的飞书账号操作飞书，包括：读取/搜索云文档（Docx/Wiki/表格/多维表格）、查看日程日历、收发消息、查询通讯录、管理云盘等。用户要求飞书相关操作时直接执行（lark-cli 优先，未安装时用凭证 token 调飞书 OpenAPI）；回答时先说明能做什么，不主动提及凭证文件/授权流程等技术细节，仅在实际操作失败（未连接/未授权）时引导用户到平台完成飞书连接。"
metadata: {"clawdbot":{"emoji":"🐦"},"openclaw":{"emoji":"🐦","install":[{"id":"node","kind":"node","package":"@larksuite/cli","bins":["lark-cli"],"label":"Install lark-cli (node)"}]}}
---

# feishu-connection

以当前用户身份操作飞书。凭证文件位于工作区 `connectors/feishu.json`（由 InsightWeaver 平台下发）。
优先用官方 `lark-cli` 执行；**实例未安装 lark-cli 时，直接用凭证里的 access_token 调飞书 OpenAPI**（见「OpenAPI 直调」），无需安装任何东西。

## 用户询问「能否操作飞书」时的回答（豆包风格）

直接展示能力列表，**不主动提及凭证文件、授权流程等技术细节**：

> 可以的。我能通过飞书相关能力读取和操作飞书，主要包括：
> **文档与内容**：飞书文档（Docx/Wiki）、表格（Sheets）、多维表格（Base）的读取、创建、编辑、总结；幻灯片、画板、知识库
> **协作与沟通**：日历（查看/创建日程、预定会议室）、即时通讯（收发消息、管理群聊）、通讯录查询、妙记纪要、视频会议
> **文件管理**：云盘上传/下载、移动/删除、权限管理
> 有具体需求直接告诉我（比如「帮我读一下这个飞书文档」），我来处理。

若用户进一步给出操作请求（文档链接等），**直接尝试执行**；只有实际操作返回「未连接/未授权」类错误时，才引导用户到平台完成飞书连接。

## 执行（凭证就绪时）

1. 检查凭证可用性：读取 `connectors/feishu.json` 存在即视为已授权；不存在时按上述「回答方式」先展示能力，实际操作失败再引导连接。
2. 检查 lark-cli 状态：`lark-cli auth status --json`。
3. 已绑定且登录 → 直接进入「日常使用」，**不要再向用户询问绑定**。
4. 未绑定 → **静默执行**（config bind 只把 lark-cli 指向平台凭证源，无登录副作用，无需用户确认）：
   `lark-cli config bind --source evomind --identity user-default`
   （source 名以实例探测为准，可能是 `evomind`（EvoMind 平台）或 `openclaw`；探测不到时
   用 `lark-cli config bind --help` 确认。bind 后 auth status 仍显示未登录属正常——登录走设备流。）
5. bind 后 `lark-cli auth status --json` 显示未登录：
   - **主动引导一次设备流登录（每会话最多一次）**，确认后进入 lark-cli 主通道（快捷命令/schema 发现/dry-run 预览等更稳）：
     `lark-cli config init --app-id <appId>`（app_secret 从凭证文件读取，经 stdin 传入，禁止写进对话）
     `lark-cli auth login --no-wait --json` → 把 verification URL 发给用户，附一句说明：
     「点击确认后我改用飞书官方 CLI 为你操作（更快更稳），本次操作先用直调完成」
     用户确认后 `lark-cli auth login --device-code <code>` 完成登录 → 后续命令走「日常使用」
   - **用户拒绝 / 约 60 秒无响应 / 登录报错 → 本会话不再发起登录引导**，
     静默转「OpenAPI 直调」章节用凭证文件里的 access_token 调飞书 API（凭证已含用户授权，无需再登录）；
     当前这次操作不等待登录结果——先直调完成用户请求，登录链接留待用户点击。

## 日常使用（lark-cli 可用时）

- 优先用 +shortcut：`lark-cli calendar +agenda`、`lark-cli im +send` 等
- 未知接口先查：`lark-cli schema <service.resource.method>`
- 兜底裸调：`lark-cli api GET /open-apis/...`
- 机器可读输出加 `--output json` / `--jq`；写操作先 `--dry-run` 预览
- high-risk-write 命令必须先向用户复述影响并取得确认，再加 `--yes`

### 登录态失效自愈

- lark-cli 命令报未授权/登录过期 → **静默重登一次**（同设备流：config init 已在则跳过 → auth login --no-wait 发链接）；
  重登期间当前操作转「OpenAPI 直调」完成，不阻塞用户。
- 重登后仍失败（用户未确认/再次报错）→ 本会话不再尝试，直接 OpenAPI 直调并如实告知
  「官方 CLI 暂不可用，已用直调方式完成」；**不反复重试、不反复发登录链接**。

## OpenAPI 直调（实例未安装 lark-cli 时）

先 `which lark-cli`；不存在则直接用凭证文件的 access_token 调飞书 OpenAPI：
（access_token 从 `connectors/feishu.json` 读取，仅用于 curl 的 Authorization 头，禁止写入对话或文件）

- 用户信息：`curl -s -H "Authorization: Bearer <accessToken>" https://open.feishu.cn/open-apis/authen/v1/user_info`
- 日历列表：`curl -s -H "Authorization: Bearer <accessToken>" https://open.feishu.cn/open-apis/calendar/v4/calendars`
- **读取云文档内容**：`curl -s -H "Authorization: Bearer <accessToken>" "https://open.feishu.cn/open-apis/docx/v1/documents/<token>/raw_content"`
  （<token> 来自文档 URL /docx/<token> 或 /wiki/<token>；返回的 `data.content` 即文档正文）
- 多维表格记录：`curl -s -H "Authorization: Bearer <accessToken>" "https://open.feishu.cn/open-apis/bitable/v1/apps/<app_token>/tables/<table_id>/records?page_size=20"`
- 搜索云空间：`curl -s -H "Authorization: Bearer <accessToken>" "https://open.feishu.cn/open-apis/suite/docs-api/search/object?search_key=<关键词>&count=10"`

通用规则：所有请求头带 `Authorization: Bearer <accessToken>`，响应 JSON 里 `code == 0` 表示成功；
token 过期（99991663/99991664 等）时提示用户在平台重新授权，不要重试。

## 安全规则

- `connectors/feishu.json` 属于该用户私有凭证：
  绝不把 appSecret / accessToken / refreshToken 原文输出到对话、日志或任何文件之外。
- token 过期（API 返回 99991663/99991664 类错误）时提示用户在平台重新授权，
  不要尝试用过期凭证反复重试。
