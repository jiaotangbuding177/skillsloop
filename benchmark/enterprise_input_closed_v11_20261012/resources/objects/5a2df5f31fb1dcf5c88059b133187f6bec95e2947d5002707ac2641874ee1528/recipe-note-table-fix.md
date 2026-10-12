# 菜谱笔记表格不渲染诊断案例

> 笔记：`1912421418257397864` - "我的家常菜谱（合集）"
> 问题：`content` 字段是管道符分隔纯文本，GetNotes 预览不显示表格
> 解决：✅ **Markdown 表格格式**（`| 列1 | 列2 |`）可正常渲染
> 更新时间：2026-06-14

## 症状

在 GetNotes 中打开笔记，预览区域不显示表格，而是一行行 `"|"` 分隔的纯文本：

```
一、主食
名称 | 做法
米饭 | 米水比1:1.2，淘洗2遍...
馒头 | 中筋面粉500g + 酵母5g...
```

## 根因

GetNotes 的**预览渲染读的是 `content` 字段**，不是 `json_content`。

该笔记的 `json_content`（ProseMirror table 节点）完全正确，但 `content` 字段存的是管道符分隔的纯文本，没有使用 Markdown 表格格式。

| 字段 | 内容 | 作用 |
|------|------|------|
| `json_content` | ✅ 正确的 table 节点（tableHeader + tableCell） | 内部数据存储 |
| `content` | ❌ `"名称 \| 做法\n米饭 \| ..."` 管道符纯文本 | **预览渲染用**（GetNotes 读这个字段） |

## ✅ 正确格式：Markdown 表格

`content` 字段使用 **Markdown 表格格式**（`|` 分隔 + `| --- |` 分隔行），GetNotes 预览可正常渲染为表格：

```
一、主食

| 名称 | 做法 |
| --- | --- |
| 米饭 | 米水比1:1.2，淘洗2遍... |
| 馒头 | 中筋面粉500g + 酵母5g... |

二、凉菜

| 名称 | 做法 |
| --- | --- |
| 拍黄瓜 | 黄瓜拍裂切段... |
```

## 修复脚本

```python
import urllib.request, json

with open("/tmp/getnote_token.txt", "rb") as f:
    lines = f.read().split(b"\n")
token = lines[0].decode("utf-8")
csrf = lines[1].decode("utf-8")
did = lines[2].decode("utf-8")

note_id = "1912421418257397864"
url = f"https://get-notes.luojilab.com/voicenotes/web/notes/{note_id}"
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
    d = json.loads(resp.read())

c = d.get("c", {})
jc = json.loads(c["json_content"])
blocks = jc.get("content", [])

def block_to_md(block):
    """将 block 转为 Markdown 格式"""
    btype = block.get("type")
    if btype == "paragraph":
        texts = [n.get("text", "") for n in block.get("content", []) if n.get("type") == "text"]
        return "".join(texts)
    elif btype == "table":
        rows = block.get("content", [])
        lines_text = []
        for ri, row in enumerate(rows):
            cell_texts = []
            for cell in row.get("content", []):
                cell_parts = []
                for para in cell.get("content", []):
                    for n in para.get("content", []):
                        if n.get("type") == "text":
                            cell_parts.append(n.get("text", ""))
                cell_texts.append("".join(cell_parts))
            lines_text.append("| " + " | ".join(cell_texts) + " |")
            if ri == 0:  # 表头后加分隔行
                lines_text.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
        return "\n".join(lines_text)
    return ""

content_parts = []
for b in blocks:
    txt = block_to_md(b)
    if txt:
        content_parts.append(txt)

# 用空行分隔不同部分
full_content = "\n\n".join(content_parts)

# body_text 用 <br> 分隔（但服务器会清理，只保留纯文本）
body_parts = []
for b in blocks:
    btype = b.get("type")
    if btype == "paragraph":
        texts = [n.get("text", "") for n in b.get("content", []) if n.get("type") == "text"]
        t = "".join(texts)
        if t:
            body_parts.append(t)
    elif btype == "table":
        for row in b.get("content", []):
            cell_parts = []
            for cell in row.get("content", []):
                cell_parts.append("".join(
                    n.get("text", "")
                    for para in cell.get("content", [])
                    for n in para.get("content", [])
                    if n.get("type") == "text"
                ))
            body_parts.append(" | ".join(cell_parts))
full_body = "<br>".join(body_parts)

# PUT 更新
body = json.dumps({
    "title": c.get("title"),
    "json_content": c["json_content"],  # 保持原始字符串
    "content": full_content,             # Markdown 表格格式
    "body_text": full_body              # <br> 分隔纯文本
})
update_req = urllib.request.Request(url, data=body.encode("utf-8"), method="PUT", headers={
    "Authorization": "Bearer " + token,
    "Xi-Csrf-Token": csrf,
    "x-d": did,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.biji.com",
    "Referer": "https://www.biji.com/",
    "Xi-App-Client-Source": "getnote",
})
with urllib.request.urlopen(update_req, timeout=10) as resp:
    result = json.loads(resp.read())
print("h.c:", result["h"]["c"])  # 0 = 成功
```

## 关键结论

1. **GetNotes 预览渲染看 `content` 字段**，不是 `json_content`
2. **`content` 字段使用 Markdown 表格格式**（`|` 分隔 + `| --- |` 分隔行）可正常渲染
3. **`body_text` 会被服务器清理**（`<br>` 标签被移除），实际只起搜索/摘要作用
4. **永远从 `json_content` blocks 重建 `content`**，不要信任原始 `content` 字段
5. **json_content 的 ProseMirror table 结构必须正确**（table attrs + tableHeader + tableCell + paragraph attrs 完整），否则即使 content 格式对也无法渲染
