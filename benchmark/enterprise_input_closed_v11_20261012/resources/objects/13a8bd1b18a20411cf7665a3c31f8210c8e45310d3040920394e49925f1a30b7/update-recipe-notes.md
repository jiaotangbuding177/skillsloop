# 更新含表格笔记的完整工作流

## 核心结论（先看这个）

| 数据 | 正确来源 |
|------|---------|
| `json_content`（ProseMirror 结构） | **详情 API** `GET /voicenotes/web/notes/<id>` |
| `content`（纯文本预览） | 从详情 API 的 json_content blocks **自己重建** |

**错误做法**：从列表 API 获取 json_content + 直接用列表 API 的 content 字段——这会导致 section header 段落文字丢失（"一、主食" 等章节标题变成空字符串）。

**根本原因**：列表 API 返回的 json_content 中，section header 段落（如 Block 0: "一、主食"）的 `content` 是空数组 `[]`，而详情 API 返回的同名字段才是完整的（`[{"type": "text", "text": "一、主食"}]`）。

---

## 完整脚本模板

```python
import subprocess, json

# 1. 读取凭证
with open("/tmp/getnote_token.txt") as f:
    parts = f.read().strip().split("\n")
token, csrf, did = parts[0], parts[1], parts[2]
auth = "Bearer " + token
NOTE_ID = "<note_id>"

# 2. 从详情 API 获取完整 json_content（含章节标题）
detail_url = f"https://get-notes.luojilab.com/voicenotes/web/notes/{NOTE_ID}"
cmd = [
    "curl", "-s", detail_url,
    "-H", "Authorization: " + auth,
    "-H", "Xi-Csrf-Token: " + csrf,
    "-H", "x-d: " + did,
    "-H", "Accept: application/json",
    "-H", "Content-Type: "application/json",
    "-H", "Origin: https://www.biji.com",
    "-H", "Referer: https://www.biji.com/",
    "-H", "Xi-App-Client-Source: getnote"
]
result = subprocess.run(cmd, capture_output=True, text=True)
d = json.loads(result.stdout)
c = d["c"]

jc_raw = c["json_content"]          # 原始 ProseMirror JSON 字符串
jc = json.loads(jc_raw)
blocks = jc["content"]

# 3. 修改 blocks（如：在某 table 追加一行）
para_attrs = {"lineHeight": "100%", "textAlign": None, "class": None, "indent": 0}

def make_para(text):
    return {
        "type": "paragraph",
        "attrs": dict(para_attrs),
        "content": [{"type": "text", "text": text}]
    }

def make_data_cell(text):
    return {
        "type": "tableCell",
        "attrs": {"colspan": 1, "rowspan": 1, "colwidth": None},
        "content": [make_para(text)]
    }

new_row = {
    "type": "tableRow",
    "content": [
        make_data_cell("新菜名"),
        make_data_cell("做法描述。")
    ]
}

# 假设目标 table 在 blocks[13]，追加新行
blocks[13]["content"].append(new_row)

# 4. 从 json_content blocks 重建 content 字段
# 关键：text 节点是 paragraph 的直接子节点，没有多层嵌套

def get_para_text(block):
    """提取 paragraph 块的纯文本——text 节点在 block['content'] 直接下层"""
    parts = []
    for node in block.get("content", []):
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
    return "".join(parts)

def get_table_text(block):
    """提取 table 为 Markdown 表格格式（含 | --- | 分隔行）"""
    lines = []
    for ri, row in enumerate(block.get("content", [])):
        cell_parts = []
        for cell in row.get("content", []):
            for para in cell.get("content", []):
                for node in para.get("content", []):
                    if node.get("type") == "text":
                        cell_parts.append(node.get("text", ""))
        lines.append("| " + " | ".join(cell_parts) + " |")
        if ri == 0:  # 表头后加 Markdown 分隔行
            lines.append("| " + " | ".join(["---"] * len(cell_parts)) + " |")
    return "\n".join(lines)

content_lines = []
for block in blocks:
    btype = block.get("type")
    if btype == "paragraph":
        text = get_para_text(block)
        content_lines.append(text)
    elif btype == "table":
        content_lines.append(get_table_text(block))

full_content = "\n".join(content_lines)

# 验证：打印章节标题，确认提取正确
for line in content_lines:
    if "、" in line and len(line) < 15:
        print("Section:", line)

# 5. PUT 更新
jc_updated = json.dumps(jc, ensure_ascii=False)
body = json.dumps({
    "title": c.get("title"),
    "json_content": jc_updated,
    "content": full_content,
    "body_text": full_content
})

update_cmd = [
    "curl", "-s", "-X", "PUT", detail_url,
    "-H", "Authorization: " + auth,
    "-H", "Xi-Csrf-Token: " + csrf,
    "-H", "x-d: " + did,
    "-H", "Accept: "application/json",
    "-H", "Content-Type: "application/json",
    "-H", "Origin: https://www.biji.com",
    "-H", "Referer: https://www.biji.com/",
    "-H", "Xi-App-Client-Source: getnote",
    "-d", body
]
result2 = subprocess.run(update_cmd, capture_output=True, text=True)
resp = json.loads(result2.stdout)
print("Update h.c:", resp["h"]["c"])  # 0 = 成功
```

---

## 关键要点

1. **Token 从文件读取**，不用环境变量（execute_code 沙箱中 Token 不会被截断）
2. **`json_content` 从详情 API 获取**——详情 API 的 json_content 含完整 section header 段落文字，列表 API 的 json_content 里 section header 段落是空的
3. **`content` 从 json_content blocks 自己重建**——用上面正确的递归提取函数（text 节点是 paragraph 的直接子节点）
4. **`json_content` 保持原始字符串格式**：`json.dumps(jc)` 后直接 PUT，不做 `json.loads()` 再 `json.dumps()` 造成二次序列化
5. **tableCell 的 paragraph 必须带完整 attrs**：`{"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}`
6. **避免重复 PUT**：每次 PUT 前读一次最新状态，确认是增量修改而非重复执行
7. **列表 API 的正确用途**：搜索笔记、找到 note_id，**不用于**获取 json_content 和 content 的源数据