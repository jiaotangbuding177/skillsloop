---
name: netease-mail-connection
description: 读取指定实验邮箱的邮件和附件，或处理本地EML；对原163账号采用已授权的个人邮箱替代时明确身份及远端资料差异。
metadata:
  provenance: context_reconstruction
---

# 邮箱连接与附件处理

原163技能正文、账户邮件及安装来源未恢复。本包是授权重建版；实验实际使用已配置的个人QQ邮箱，原文163地址保留在原会话，实际操作身份来自环境映射。QQ账号可连接不等于原163邮件已存在；指定邮件、项目资料、附件需从当前真实消息或已准备的实验材料取得。

容器已有 `/opt/real-services/mail_cli.py`，凭据默认 `/run/secrets/services.json`。本包 `scripts/mail_bridge.py` 的 `status/list/read/send` 按同一参数转发真实CLI，不保存密钥或将凭据写入回复。

```bash
python scripts/mail_bridge.py list --folder INBOX --limit 10
python scripts/mail_bridge.py read --uid 123 --output-dir /workspace/output/mail
python scripts/mail_bridge.py send --to recipient@example.com --subject 主题 --body-file body.txt --attachments report.pdf
```

用户要求最新邮件时先列当前邮箱，按 UID 读取邮件并取得实际内容和附件，再执行用户要求的项目分析。只在任务本身要求发送且收件人可确定时调用send。云附件通常只在HTML正文中包含下载链接；读取MIME看不到附件时检查 `cloud_links` 和HTML，不声称附件不存在或已经下载。通过当前浏览器/HTTP工具访问已适配链接，保存真实字节后再读取；无法访问时明示具体缺材料。

本地邮件或合成邮箱材料用独立EML模式，不接远端：

```bash
python scripts/mail_bridge.py eml --file message.eml --output-dir /workspace/output/mail
```

EML模式提取正文、MIME附件、HTML链接，并写 `message.json`；它不下载云附件，不伪造真实邮箱列表。随后读取文件验证内容和产物用途。邮件项目事实来自实际材料，不包含历史轨迹AI评估或回信答案。
