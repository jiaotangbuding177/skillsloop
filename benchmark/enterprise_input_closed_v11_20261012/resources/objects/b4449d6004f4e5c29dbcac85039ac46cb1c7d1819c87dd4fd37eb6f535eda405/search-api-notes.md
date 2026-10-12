# GetNotes 搜索 API 实测记录

## 搜索端点

```
GET https://get-notes.luojilab.com/voicenotes/web/notes/search?keyword=<URL编码>&page=1&limit=50
```

## 响应结构

```json
{
  "h": { "c": 0, "e": "", ... },
  "c": {
    "items": [ ... ],      // 注意是 items，不是 list
    "total": 212,
    "has_more": true
  }
}
```

## 字段说明（搜索返回）

| 字段 | 示例 | 说明 |
|------|------|------|
| `note_id` | `1912421418257397864` | 笔记 ID（搜索用此字段，**不是 `id`**） |
| `title` | `"<hl>我的家常菜谱</hl>（合集）"` | 含高亮标签 |
| `content` | `"鸡胸肉切丁+<hl>料酒</hl>+淀粉..."` | 含 `<hl>` 高亮标签，需 strip |
| `ref_content` | `""` | 始终为空字符串，**不要使用** |
| `body_text` | `"一、主食<br>二、凉菜<br>四、蒸菜<br>..."` | 含全部章节标题，可判断笔记类型 |
| `created_at` | `"2026-06-10 16:47:19"` | 创建时间 |

## 高亮标签去除

```python
import re
content = re.sub(r'<[^>]+>', '', item.get("content", ""))
title = re.sub(r'<[^>]+>', '', item.get("title", ""))
```

## Token 过期判断

Token 过期后搜索 API 返回：`{"message":"LoginRequired"}`

刷新后重试即可。

## 翻页逻辑

```python
all_items = []
for page in range(1, 100):
    url = f"https://get-notes.luojilab.com/voicenotes/web/notes/search?keyword={keyword}&page={page}&limit=50"
    # ... fetch ...
    if not d["c"]["has_more"]:
        break
    all_items.extend(items)
```

## 列表 API vs 详情 API

| 字段 | 列表/搜索 API | 详情 API |
|------|-------------|---------|
| `content` | ✅ 含完整正文（表格 `\|` 分隔） | ❌ 空 |
| `body_text` | ✅ 含全部章节结构 | ❌ 空 |
| `json_content` | ✅ 完整 ProseMirror JSON | ✅ 完整 ProseMirror JSON |

**结论**：永远优先用列表/搜索 API 的 `content` 字段获取正文，详情 API 只用于获取 `json_content` 做结构修改。

## 本次搜索"蒸菜"结果

- 关键词 `"蒸菜"` 搜索：212 条命中，但大多数是误匹配（搜索是按字匹配，"蒸"字出现在任何位置都算）
- 真正含"蒸菜"的笔记通过关键词 `"家常菜"` 找到菜谱合集，再在正文中定位到"四、蒸菜"章节
- 菜谱笔记 ID：`1912421418257397864`