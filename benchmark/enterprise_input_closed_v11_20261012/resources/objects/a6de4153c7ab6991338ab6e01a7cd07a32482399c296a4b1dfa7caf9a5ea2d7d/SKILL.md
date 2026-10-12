---
name: wecom-connection
description: 使用用户授权的企业微信机器人操作企业微信，包括：发送/读取消息、查询会话、日程（创建/查询/取消/忙闲/搜索）、通讯录查询、文档与表格（创建/读写/导入/搜索/权限）、智能表格、会议（创建/查询/取消）、邮件（发送/回复/列表）、微盘文件、待办等。用户要求企业微信相关操作时直接执行（优先用官方 wecom-cli）；回答时先说明能做什么，不主动提及凭证/授权流程等技术细节，仅在实际操作失败（未连接/未授权）时引导用户到平台完成企业微信连接。
metadata: {"clawdbot":{"emoji":"💼"},"openclaw":{"emoji":"💼","install":[{"id":"node","kind":"node","package":"@wecom/cli","bins":["wecom-cli"],"label":"Install wecom-cli (node)"}]}}
---

# wecom-connection

以当前企业已授权的企业微信机器人身份操作企业微信。凭证目录位于工作区 `connectors/wecom-<enterpriseId>/`
（由 InsightWeaver 平台在用户扫码授权后下发；enterpriseId 见系统提示「当前企业上下文」）。
使用官方 `wecom-cli` 执行，**每个命令前设置环境变量 `WECOM_CLI_CONFIG_DIR=connectors/wecom-<enterpriseId>`**
（相对工作区目录，用绝对路径更稳妥）。

## 用户询问「能否操作企业微信」时的回答

直接展示能力列表，**不主动提及凭证目录、授权流程等技术细节**：

> 可以的。我能通过企业微信相关能力读取和操作企业微信，主要包括：
> **沟通协作**：发送/读取消息、会话列表查询、待办管理
> **日程会议**：创建/查询/取消日程、忙闲查询、会议安排
> **文档办公**：文档与表格（创建/读写/导入/搜索/权限）、智能表格、微盘文件
> **通讯与邮件**：通讯录查询、邮件发送/回复/列表
> 有具体需求直接告诉我（比如「帮我在企业微信里发个消息」），我来处理。

若用户进一步给出操作请求，**直接尝试执行**；只有实际操作返回「未连接/未授权」类错误时，
才引导用户到平台完成企业微信连接。

## 执行（凭证就绪时）

1. 检查凭证可用性：`connectors/wecom-<enterpriseId>/` 目录存在（含 `config.json` 或 `credentials.enc`）即视为已授权；
   不存在时按上述「回答方式」先展示能力，实际操作失败再引导连接。
   **首次使用前检查 `encryption_key`（无点）文件**：平台上传时因文件系统限制去掉了点前缀，
   若目录里有 `encryption_key` 但没有 `.encryption_key`，先执行 `mv encryption_key .encryption_key` 再运行 wecom-cli。
2. 检查 CLI：`wecom-cli --version` ≥ 1.1.0；缺失时 `npm install -g @wecom/cli`。
3. 前置检查：`WECOM_CLI_CONFIG_DIR=... wecom-cli auth show --status` 输出 `authorized` 才继续；
   否则按「未连接」处理，引导用户到平台完成连接，**不要尝试自行授权**。
4. 日常使用：`WECOM_CLI_CONFIG_DIR=... wecom-cli <service> <command> ...`
   - 未知接口先查：`wecom-cli <service> --help` 或 `wecom-cli schema <service> <method>`（如有）
   - 机器可读输出加 `--json` / `--jq`；写操作（发消息/删日程/删文档）先预览再确认
   - 身份查询：`wecom-cli identity whoami`（返回当前机器人信息）
5. 错误码 853004（token 过期）时 CLI 自动静默刷新重试；连续失败提示用户在平台重新连接，
   不要反复重试。

## 平台编排模式（收到隐藏指令时）

平台（InsightWeaver）可能通过隐藏消息发起授权编排（用户在前端点「连接企业微信」）。此时：

1. **CLI 安装检查**：执行 `which wecom-cli`（Windows 用 `where wecom-cli` 或 `wecom-cli.cmd`）。
   - 已安装：跳过安装，**立即**继续下一步；并回写 CLI 标记文件
     `connectors/wecom-cli-installed.json`（格式 `{"installedAt":"<ISO时间>"}`）。
   - 未安装：执行 `npm install -g @wecom/cli`，
     完成后同样回写 CLI 标记文件。
2. **发起扫码授权（快速回传二维码，平台编排专用）**：
   设 `WECOM_CLI_CONFIG_DIR` 为工作区目录 `connectors/wecom-<enterpriseId>`
   （enterpriseId 见系统提示「当前企业上下文」；目录不存在则创建），并 `cd` 到该目录。
   **后台起 auth init 进程**（进程保持存活轮询扫码结果，扫码后凭证自动落盘）：
   ```bash
   cd connectors/wecom-<enterpriseId> && nohup wecom-cli auth init --noninteractive --no-browser --output-qrcode qr.png > /tmp/wecom-auth.log 2>&1 &
   ```
   nohup 不可用时改用 `wecom-cli auth init --noninteractive --no-browser --output-qrcode qr.png > /tmp/wecom-auth.log 2>&1 &`（保持 cd 在凭证目录内）。
   **等待二维码生成**（最多 15s，每次 sleep 0.2，检查 `connectors/wecom-<enterpriseId>/qr.png` 存在；
   若不在凭证目录，用 `find /workspace -name qr.png -mmin -2` 定位后复制到凭证目录），
   读取 qr.png 转 base64（**无 data: 前缀**），写入工作区文件
   `connectors/wecom-pending.json`，格式 `{"qrBase64":"<PNG base64>"}`（覆盖写入，不要追加）；
   并回写 CLI 标记文件。
   **起后台授权完成监控**（授权完成秒级回传平台，无需再次指令 agent）：
   ```bash
   nohup sh -c 'i=0; while [ $i -lt 150 ]; do s=$(WECOM_CLI_CONFIG_DIR="$(pwd)/connectors/wecom-<enterpriseId>" wecom-cli auth show --status 2>/dev/null); if [ "$s" = "authorized" ]; then echo "{\"status\":\"authorized\"}" > connectors/wecom-pending.json; exit 0; fi; sleep 2; i=$((i+1)); done' >/dev/null 2>&1 &
   ```
   （每 2s 本地检查一次授权状态，检测到 authorized 立即写 pending 文件；最长 300s 自退。sh 不可用时用等价 PowerShell/Node 循环。）
   ⚠️ 后台 auth init 仅用于平台编排场景；日常使用仍按「执行（凭证就绪时）」前台运行。
3. 收到状态查询指令时：执行 `WECOM_CLI_CONFIG_DIR=... wecom-cli auth show --status`，
   把结果写入同一文件：`{"status":"authorized"|"unauthorized"}`；
   若结果为 authorized，同时执行 `wecom-cli identity whoami` 提取机器人 ID 与名字
   追加写入 `"botId"` / `"botName"` 字段。
4. 收到吊销指令时：终止残留的 wecom-cli 进程，删除 `connectors/wecom-<enterpriseId>` 目录、
   `connectors/wecom-pending.json` 与 `connectors/wecom-cli-installed.json`。
5. 完成后简短回复结果；不要向用户展示二维码 base64（平台弹框会展示）。

## 隔离与安全

- 凭证目录 `connectors/wecom-<enterpriseId>/` 是该企业私有的机器人凭证
  （config.json / credentials.enc），**只属于当前会话企业**；执行写操作前校验：
  - 目录名中的 enterpriseId 与当前会话所属企业不一致 → 凭证属于另一组织，**不要使用**，
    提示用户「当前企业的企业微信凭证尚未就绪，请到平台完成企业微信连接」。
  - 只读操作可尝试执行，失败同样按「未连接」处理。
- 机密内容（credentials.enc、config.json 中的 secret 字段）绝不输出到对话、日志或写入其他文件。
- 不得外露 userid / open_vid / chat_id 等 ID 类字段到对话。
