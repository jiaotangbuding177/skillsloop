# 共享工作区文档标签解析 — 测试样例

目录：`docs/fixtures/shared-workspace-doc-tags/`

上传到**共享工作区**时，系统会读取 PDF / DOCX / PPTX / MD（及 TXT）正文前约 2000 字，匹配：

```text
【安全等级】：核心机密 | 重要数据 | 一般数据
【可见范围】：部门或小组名称
【可见成员】：成员显示名
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `01-core-secret.md` | 核心机密 + 管理 + zw；附入 AI 对话应被拦截 |
| `02-important.md` | 重要数据 |
| `03-general.md` | 一般数据 |
| `04-whitespace-robust.md` | 空格 / 全角空格 / 换行不影响解析 |
| `05-boundary-miss.md` | 无效等级与不存在的组织/成员 → 边界 toast |
| `06-core-secret.txt` | 同核心机密模板的 txt |
| `07-core-secret.docx` | 同核心机密模板的 Word（mammoth 可抽文本） |
| `08-core-secret.pptx` | 同核心机密模板的 PPTX（首页标签；老式 `.ppt` 不支持） |

## 使用注意

- 「可见范围」「可见成员」请改成你企业里**真实存在**的部门/小组名、成员显示名，否则会走边界提示。
- Word / PDF / PPTX：可用上述 Markdown 正文复制进 `.docx` / `.pdf` / `.pptx`（建议放在首页）后上传；解析链路与 MD 相同。
- 老式 `.ppt` 不支持文本抽取，请另存为 `.pptx`。
- 仅**上传时**解析一次；之后点「设置可见范围」不会再次解析。
