---
name: output-as-word
description: 将用户要求的分析、合同意见、岗位文档或其他已有内容输出为可编辑的中文 Word，并检查正文、表格及转换后的页面。
---

# Word 交付

本包是根据需要此技能的会话用途重建的实验环境能力，不是原 EvoMind 包，也不是演化算法产出的技能。不要把历史 AI 回复作为当前输出正文。

1. 读取当轮用户要求及可见资料，先确定正文和结构。保留用户指定篇幅、措辞、表格、加粗和附件要求。
2. 把实际内容写成 JSON：`title`，`sections`（`heading`、`paragraphs`、`bullets`），`tables`（`heading`、`columns`、`rows`）。可填 `provenance`。不要输出空模板。
3. 执行 `python scripts/artifact_tools.py render 内容.json --out /workspace/outputs/结果.docx`。脚本同时产生可阅读 Markdown，支持中文字体与表格。
4. 用 `python scripts/artifact_tools.py extract 结果.docx --out 内容检查.json` 核实实质内容。需要 PDF 或查看版式时，运行 `libreoffice -env:UserInstallation=file:///tmp/word-render-profile --headless --convert-to pdf --outdir /workspace/outputs 结果.docx`，再用 `pdftotext` 和分页渲染检查。提供实际产物路径。

旧 `.doc` 先用 LibreOffice 转成 `.docx`；扫描 PDF 先 OCR。不要把扩展名改为 `.docx` 来伪装格式。修改用户原模板时用 `revise` 子命令与逐段定位，不要重建整份合同丢失原条款。
