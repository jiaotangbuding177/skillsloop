# ProseMirror 表格格式模板

> 来源：note_id `1912620594143877392`（两列表格模板提供）
> 实测：按此格式构建的表格在笔记预览中正常渲染。

## 最小可工作表格（含完整 attrs）

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
          "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "列1"}]}]
        },
        {
          "type": "tableHeader",
          "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
          "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "列2"}]}]
        }
      ]
    },
    {
      "type": "tableRow",
      "content": [
        {
          "type": "tableCell",
          "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
          "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "数据1"}]}]
        },
        {
          "type": "tableCell",
          "attrs": {"colspan": 1, "rowspan": 1, "colwidth": null},
          "content": [{"type": "paragraph", "attrs": {"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}, "content": [{"type": "text", "text": "数据2"}]}]
        }
      ]
    }
  ]
}
```

## 三个关键格式要求

1. **table attrs 必须有 `{"commentIds": [], "class": null}`** — 没有会导致预览不渲染表格
2. **表头行用 `tableHeader` type**（不是 `tableCell`）
3. **paragraph attrs 必须完整**：`{"lineHeight": "100%", "textAlign": null, "class": null, "indent": 0}`

## 快速构建函数（Python）

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

# 示例：
table = make_table(["名称", "做法"], [
    ["米饭", "米水比1:1.2"],
    ["馒头", "酵母发面蒸制"],
])
```

## 已知错误格式（会导致预览空白或表格丢失）

- `table` 无 attrs：`{"type": "table", "content": [...]}` → 预览不渲染
- 表头行用 `tableCell`：`{"type": "tableCell", ...}` → 不识别为表头
- paragraph 无 attrs 或 attrs 缺少字段 → 预览异常