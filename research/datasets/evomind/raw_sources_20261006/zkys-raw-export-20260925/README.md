# 中科优势组织 · 原始数据导出（脱敏版）

- 导出时间：2026-09-25，生产库只读拉取
- 范围：企业 `中科优势`（B2B，37 名成员）名下全部用户的数据
- 处理原则：**内容未做任何清洗/加工，仅做 PII 脱敏**（见下）。时间戳保留 UTC 原值（北京时间 = UTC + 8 小时）。

## 文件清单（JSONL，每行一个 JSON 对象 = 一行数据库记录）

| 文件 | 行数 | 内容 |
|------|-----:|------|
| `zclaw_members.jsonl` | 37 | 成员：enterprise_memberships 全字段 + users(id/role/status/locale) + 手机号 identity（脱敏） |
| `zclaw_sessions.jsonl` | 1,524 | zclaw_sessions 全字段（title、status、createdAt、lastMessageAt 等），isDeleted=false |
| `zclaw_messages.jsonl` | 46,407 | zclaw_messages 全字段，role ∈ user/assistant/system，**UUID 副本与 conv_* trusted 副本并存**（trusted 副本 content 带平台系统前缀「请使用中文回复…」，属原始数据未剥离），isDeleted=false |
| `raw_payload_sample.jsonl` | 1,391 | tool/toolResult 行结构抽样（每会话 1 行），rawPayload 含工具调用 JSON。仅作结构参考 |

## 明确未导出

- **tool / toolResult 全量**（≈9.3 万行 / 1.1GB）：平台机器数据（exec 输出、网页抓取等），体量大且极易夹带密钥类内容，正则脱敏无法兜底。如需可单独评估后拉取。
- **软删除行**（isDeleted=true，≈4.5 万行）：用户已删除内容，默认不导出。
- 用户头像/附件二进制：不在数据库，未涉及。

## 脱敏规则（正则自动打码，用户维度仅保留尾 4 位以便交叉分析）

| 类型 | 处理 |
|------|------|
| 手机号（+86 前缀/裸号，字段或正文） | `***` + 尾 4 位 |
| 身份证（15/18 位） | `***ID***` |
| 银行卡等 13+ 位连续数字 | `***CARD***`（数字串超 43 位仅打前 43 位） |
| 32+ 位十六进制串 | `***HEX***`（超 332 位仅打前 332 位） |
| `sk-` 开头密钥 / Bearer token / password|secret|token|api_key 等赋值 | `***KEY***` / `Bearer ***` / `字段=***` |
| 邮箱（任意域名，含 .cn/.co.jp 等） | `***@***` |
| 200+ 位 base64 长串 | `***B64***` |

已知局限：长数字/hex/base64 串只打前缀部分；非规则形态（如无域名特征的微信号、地址）不识别。导出后经脚本终验：无明文 11 位手机号 / 18 位身份证 / 常见域名邮箱 / sk-key。

## 关键字段说明

- `zclaw_messages.role`：user=用户输入，assistant=AI 回复，system=系统，tool/toolResult=工具调用（未导全量）
- 消息双副本：id 为 UUID 的行 = 客户端写入副本；id 为 `conv_*:*` 的行 = trusted 副本（平台合并产物）。统计用户输入时二者取其一，避免重复计数
- `zclaw_sessions` 无 enterpriseId 列，归属通过 userId 关联（本包已按企业成员过滤）
- `rawPayload.files`：用户消息附件元数据（文件名/路径），二进制不在库中
