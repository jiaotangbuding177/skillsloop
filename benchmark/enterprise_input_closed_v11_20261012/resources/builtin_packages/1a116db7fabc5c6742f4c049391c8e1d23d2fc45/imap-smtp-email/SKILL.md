---
name: imap-smtp-email
description: Read and send email via IMAP/SMTP (163.com, QQ Mail, 126.com, 188.com, yeah.net, exmail.qq.com, NetEase Enterprise and custom servers). Check, fetch, search, mark read/unread, send with attachments. NOT for Feishu/Lark email. 触发词 发邮件 发送邮件 发email 查邮件 检查邮件 收邮件 收信 发信 查看邮件 看邮件 新邮件 邮件附件 发附件 带附件 163邮箱 QQ邮箱 126邮箱 网易邮箱 send email compose reply forward check email read email fetch email search email download attachment
---

# IMAP/SMTP Email Tool

Read, search, and manage email via IMAP protocol. Send email via SMTP. Supports 网易 (163/vip.163/126/vip.126/188/vip.188/yeah), QQ Mail, exmail.qq.com, NetEase Enterprise, and custom IMAP/SMTP servers.

### 与 lark-mail（飞书邮件）的区别

| 场景     | 用本技能 (imap-smtp-email)                                                                   | 用 lark-mail                   |
| ------ | ---------------------------------------------------------------------------------------- | ----------------------------- |
| 邮箱提供商  | 163.com / QQ Mail / 126.com / 188.com / yeah.net / exmail.qq.com / 网易企业邮 / 自定义 IMAP/SMTP | 飞书邮箱（Feishu/Lark）             |
| 协议     | IMAP 收信 + SMTP 发信                                                                        | 飞书 Open API                   |
| 凭证     | 授权码/密码，存本地 `.env`                                                                        | 飞书应用凭证，走 lark-cli             |
| 典型用户话术 | "用 163 邮箱发" / "QQ 邮箱查一下" / "发到 xxx@163.com"                                              | "用飞书发" / "飞书邮箱" / "Lark mail" |

> 🛑 **排他规则**：用户提示词中出现"飞书"、"Feishu"、"Lark"、"飞书邮箱" → **不使用本技能**，引导用户改用 lark-mail。

## Configuration

### Agent 会话持久化工作流

| 标记            | 位置            | 何时触发                    | agent 行为                           |
| ------------- | ------------- | ----------------------- | ---------------------------------- |
| 🔴 CHECKPOINT | Step 3 (无配置)  | `.env` 不存在              | 收集凭证 → **展示确认** → 写入               |
| 🔴 CHECKPOINT | Step 4 (认证失败) | IMAP/SMTP 返回 auth error | 告知失效 → 收集新授权码 → **再次确认** → 更新      |
| 🛑 STOP       | 发送邮件          | `smtp.js send` 执行前      | 验证 --to / --subject / --body 三要素完整 |
| 🛑 STOP       | 下载附件          | `imap.js download` 执行前  | 验证 --dir 在 ALLOWED_WRITE_DIRS 白名单内 |
| 🛑 STOP       | 用户提示词模糊       | 缺文件路径/收件人/主题任一          | 追问补全，不猜测                           |

skill 的 `.env` 文件持久存在于 skill 目录中，跨会话生效。agent 按以下流程处理用户凭证：

skill 的 `.env` 文件持久存在于 skill 目录中，跨会话生效。agent 按以下流程处理用户凭证：

0. ⚡ **自动初始化**：先运行 `NODE_PATH=/usr/local/lib/node_modules node -e "try { require('imap'); require('mailparser'); require('nodemailer') } catch(e) { process.exit(1) }"` 验证核心依赖是否可用。若通过，确保 `node_modules/.package-lock.json` 存在（不存在则 `mkdir -p node_modules && touch node_modules/.package-lock.json`）然后跳过安装。若探测失败，检查 `node_modules` 目录是否存在，不存在则自动执行 `npm install --production`。**若 `npm install` 失败**：打印错误输出，引导用户检查 Node.js 版本（需 ≥14）并重试；**仍失败**：退出，提示用户手动执行 `cd <skill-dir> && npm install`

1. **启动时（按优先级检查）**：首先检查 `~/.config/imap-smtp-email/.env` 是否存在；若无，再检查 skill 目录 `.env`。找到后验证是否包含有效的 `PROVIDER` + `USERNAME` + `PASSWORD`

2. ✅ **已有配置**：直接使用，**不询问用户**。打印一句确认（如"使用已配置的账号 xxx@163.com"）即可

3. 🔴 **CHECKPOINT · 无配置**：向用户一次性收集邮箱地址、授权码/密码、提供商（默认 163）。**收集完展示确认后**，以简化格式写入 `~/.config/imap-smtp-email/.env`：
   ```bash
   PROVIDER=163
   USERNAME=you@163.com
   PASSWORD=your_auth_code
   ```
   脚本自动补全 IMAP/SMTP 服务器地址。**若写入失败**：回退到 skill 目录 `.env`；**若仍失败**：告知用户路径，请用户手动创建
   **写入后验证**：执行 `node scripts/imap.js list-accounts` 确认配置可读。若验证失败，检查格式是否匹配并重试

4. 🔴 **CHECKPOINT · 认证失败**：仅当 IMAP/SMTP 返回认证错误时，告知用户"授权码可能已失效，请提供新的授权码"。用户提供后更新 `~/.config/imap-smtp-email/.env` 中 `PASSWORD` 字段，**再次确认后**重试

5. 🚫 **禁止反复询问**：不要在没有失败信号的情况下反复问用户要已保存的凭证

### 手动配置（备用）

以上自动流程失败时，可回退到手动运行 setup 脚本（在 skill 目录下执行）：

```bash
cd <skill-dir>
bash setup.sh   # 自动安装 node_modules + 交互式配置邮箱
```

或直接手动完成等效操作：

```bash
npm install --production                                    # Step A: 安装依赖
echo -e "PROVIDER=163\nUSERNAME=you@163.com\nPASSWORD=xxx" > .env  # Step B: 写入凭证
```

# File access whitelist (security)

ALLOWED_READ_DIRS=~/Downloads,~/Documents
ALLOWED_WRITE_DIRS=~/Downloads

```
The `PROVIDER` preset auto-fills IMAP/SMTP server settings. For custom servers:

```bash
PROVIDER=custom
USERNAME=your@163.com
PASSWORD=your_password

SMTP_HOST=smtp.163.com
```

## Multi-Account

You can configure additional email accounts in the same config file. Each account uses a name prefix (uppercase) on all variables.

### Adding an account

Run the setup script and choose "Add a new account":

```bash
bash setup.sh
```

Or manually add prefixed variables to the skill's `.env` file:

```bash
# Work account (WORK_ prefix)
WORK_PROVIDER=163
WORK_USERNAME=me@company.com
WORK_PASSWORD=app_password
```

### Using a named account

Add `--account <name>` before the command:

```bash
node scripts/imap.js --account work check
node scripts/smtp.js --account work send --to foo@bar.com --subject Hi --body Hello
```

Without `--account`, the default (unprefixed) account is used.

### Account name rules

- Letters and digits only (e.g., `work`, `163`, `personal2`)
- Case-insensitive: `work` and `WORK` refer to the same account
- The prefix in `.env` is always uppercase (e.g., `WORK_PROVIDER`)
- `ALLOWED_READ_DIRS` and `ALLOWED_WRITE_DIRS` are shared across all accounts (always unprefixed)

## Common Email Servers

| Provider      | IMAP Host          | IMAP Port | SMTP Host          | SMTP Port |
| ------------- | ------------------ | --------- | ------------------ | --------- |
| 163.com       | imap.163.com       | 993       | smtp.163.com       | 465       |
| vip.163.com   | imap.vip.163.com   | 993       | smtp.vip.163.com   | 465       |
| 126.com       | imap.126.com       | 993       | smtp.126.com       | 465       |
| vip.126.com   | imap.vip.126.com   | 993       | smtp.vip.126.com   | 465       |
| 188.com       | imap.188.com       | 993       | smtp.188.com       | 465       |
| vip.188.com   | imap.vip.188.com   | 993       | smtp.vip.188.com   | 465       |
| yeah.net      | imap.yeah.net      | 993       | smtp.yeah.net      | 465       |
| QQ Mail       | imap.qq.com        | 993       | smtp.qq.com        | 587       |
| exmail.qq.com | imap.exmail.qq.com | 993       | smtp.exmail.qq.com | 465       |

**Important for 163.com:**

- Use **authorization code** (授权码), not account password
- Enable IMAP/SMTP in web settings first

## IMAP Commands (Receiving Email)

### check

Check for new/unread emails.

```bash
node scripts/imap.js [--account <name>] check [--limit 10] [--mailbox INBOX] [--recent 2h]
```

Options:

- `--limit <n>`: Max results (default: 10)
- `--mailbox <name>`: Mailbox to check (default: INBOX)
- `--recent <time>`: Only show emails from last X time (e.g., 30m, 2h, 7d)
- `--unseen`: Only show unread messages

### fetch

Fetch full email content by UID.

```bash
node scripts/imap.js [--account <name>] fetch <uid> [--mailbox INBOX]
```

### 🛑 download

Download all attachments from an email, or a specific attachment.

```bash
node scripts/imap.js [--account <name>] download <uid> [--mailbox INBOX] [--dir <path>] [--file <filename>]
```

Options:

- `--mailbox <name>`: Mailbox (default: INBOX)
- `--dir <path>`: Output directory (default: current directory)
- `--file <filename>`: Download only the specified attachment (default: download all)

### search

Search emails with filters.

```bash
node scripts/imap.js [--account <name>] search [options]

Options:
  --unseen           Only unread messages
  --seen             Only read messages
  --from <email>     From address contains
  --subject <text>   Subject contains
  --recent <time>    From last X time (e.g., 30m, 2h, 7d)
  --since <date>     After date (YYYY-MM-DD)
  --before <date>    Before date (YYYY-MM-DD)
  --limit <n>        Max results (default: 20)
  --mailbox <name>   Mailbox to search (default: INBOX)
  --sort <mode>      uid (default, fast) or date (strict INTERNALDATE sort;
                     fetches all matches, use when mailbox has COPY'd/backdated mail)
```

### mark-read / mark-unread

Mark message(s) as read or unread.

```bash
node scripts/imap.js [--account <name>] mark-read <uid> [uid2 uid3...]
node scripts/imap.js [--account <name>] mark-unread <uid> [uid2 uid3...]
```

### list-mailboxes

List all available mailboxes/folders.

```bash
node scripts/imap.js [--account <name>] list-mailboxes
```

### list-accounts

List all configured email accounts.

```bash
node scripts/imap.js list-accounts
node scripts/smtp.js list-accounts
```

Shows account name, email address, server addresses, and configuration status.

## SMTP Commands (Sending Email)

### 🛑 send

Send email via SMTP.

```bash
node scripts/smtp.js [--account <name>] send --to <email> --subject <text> [options]
```

**Required:**

- `--to <email>`: Recipient (comma-separated for multiple)
- `--subject <text>`: Email subject, or `--subject-file <file>`

**Optional:**

- `--body <text>`: Plain text body
- `--html`: Send body as HTML
- `--body-file <file>`: Read body from file
- `--html-file <file>`: Read HTML from file
- `--cc <email>`: CC recipients
- `--bcc <email>`: BCC recipients
- `--attach <file>`: Attachments (comma-separated)
- `--from <email>`: Override default sender

**Examples:**

```bash
# Simple text email
node scripts/smtp.js send --to recipient@example.com --subject "Hello" --body "World"

# HTML email
node scripts/smtp.js send --to recipient@example.com --subject "Newsletter" --html --body "<h1>Welcome</h1>"

# Email with attachment
node scripts/smtp.js send --to recipient@example.com --subject "Report" --body "Please find attached" --attach report.pdf

# Multiple recipients
node scripts/smtp.js send --to "a@example.com,b@example.com" --cc "c@example.com" --subject "Update" --body "Team update"
```

### 提示词模板

用户在聊天界面可以用自然语言触发发邮件，把下面 `<>` 部分替换为实际值：

```
使用 imap-smtp-email 技能，发送 <文件路径> 到 <收件人>，主题为 "<主题>"，正文为 "<正文>"
```

示例：

```
使用 imap-smtp-email 技能，发送 ~/Downloads/日报.png 到 manager@163.com，主题为 "6月22日日报"，正文为 "请查收附件"
```

### 🛑 用户提示词模糊时的处理

用户提示词常缺参数或用模糊指代（如"发送这个图片""把附件发过去"）。遇到以下情况，agent 必须追问而非猜测：

| 🛑 模糊写法             | 缺失信息            | 追问方式                   |
| ------------------- | --------------- | ---------------------- |
| 发送这个图片到 xxx@163.com | 文件路径            | "请提供要发送的图片文件路径"        |
| 把附件发过去              | 收件人 + 文件路径      | "请指定收件人邮箱和附件文件路径"      |
| 发个邮件给张三             | 收件人邮箱 + 主题 + 正文 | "请提供收件人邮箱、邮件主题和正文内容"   |
| 主题写了"日报"，发一下        | 收件人 + 正文或附件     | "请提供收件人邮箱，以及正文内容或附件路径" |

> 🛑 **原则：三个必填项（收件人、主题、正文或附件）缺一不可。缺任何一项，先追问再执行。**

### test

Test SMTP connection by sending a test email to yourself.

```bash
node scripts/smtp.js [--account <name>] test
```

## 反例与黑名单（不要做的事）

| 🚫 禁止行为 | 原因 | 正确做法 |
|---|---|---|
| 不检查依赖直接运行脚本 | `MODULE_NOT_FOUND` 崩溃 | 先执行 Step 0 自动初始化（优先全局包，避免重复 npm install） |
| 认证失败后无脑重试 | 多次错误密码触发临时锁定 | 失败 1 次即停，确认新授权码后再试 |
| 用户说"发邮件给张三"时不追问 | 必缺收件人/主题/正文 | 🛑 对照模糊处理表逐项追问 |
| 将凭证输出到对话或日志 | 授权码泄露不可逆 | `.env` 权限 600，永不回显 `PASSWORD` |
| config.js 报错后猜测配置 | 假配置导致连接挂起 | 回到 Step 1，引导用户重新配置 |
| `.env` 已存在时重复询问凭证 | 破坏持久化原则 | Step 2：有配置直接确认使用 |

## Security Notes

- Configuration is stored in the skill's `.env` file (primary), or in `~/.config/mail-skills/.env` / `~/.config/imap-smtp-email/.env` (legacy) with `600` permissions (owner read/write only)
- For 163.com: use authorization code (授权码), not account password

## Troubleshooting

以下三段式 fallback 表覆盖常见失败场景。每行遵循"触发条件 → 一线修复 → 仍失败兜底"结构。

| 触发条件                               | 一线修复                                             | 仍失败兜底                                                                                                                 |
| ---------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `npm install --production` 报错      | 检查 Node.js 版本 ≥ 14，`npm cache clean --force` 后重试 | 退出，引导用户手动执行 `cd <skill-dir> && npm install` 并检查报错                                                                     |
| `.env` 写入失败（权限不足）                  | `chmod 700` 确保 skill 目录可写                        | 退出，告知用户路径并请用户手动创建 `.env` 文件                                                                                           |
| IMAP 连接超时                          | 等待 5s 后重试 1 次                                    | 退出，打印 `IMAP connection failed: <错误信息>`，检查网络/防火墙                                                                       |
| IMAP 认证失败（首次）                      | 回退到 Step 4：告知用户确认授权码是否正确                         | 用户提供新授权码后更新 `.env` 并重试 1 次                                                                                            |
| IMAP 认证失败（已有配置）                    | 打印"授权码可能已失效"，按 Step 4 收集新授权码                     | 连续失败 2 次：退出，引导用户登录 Web 邮箱检查 IMAP/SMTP 开关是否开启                                                                          |
| IMAP 返回 `Unsafe Login` / `IDLE` 错误 | 网易系邮箱强制要求 IMAP ID 握手，标准库默认不发                     | 检查 `scripts/imap.js` 的 `imap.id(IMAP_ID, ...)` 调用是否存在于 `ready` 事件后；若缺失，按 RFC 2971 补充 ID 命令（name/vendor/support-email） |
| SMTP `send` 返回错误                   | 检查 `--to`/`--subject` 参数完整性，检查附件路径可达性            | 退出，打印完整 SMTP error JSON，不猜测原因                                                                                         |
| `bash setup.sh` 执行失败               | agent 自动回退到手动 `npm install` + 提示词模板配置流程          | 退出，打印 setup.sh 错误输出                                                                                                   |

## Related Skills

- **[caldav-sync](https://clawhub.ai/gzlicanyi/caldav-sync)** - Calendar and task management via CalDAV protocol. Manage events, todos, and free/busy queries with Google Calendar, iCloud, NetEase, and more. Install with:
  
  ```bash
  npx skills add https://github.com/gzlicanyi/mail-skills -s caldav-sync
  ```

## Feedback