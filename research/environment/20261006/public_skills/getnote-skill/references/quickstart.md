# 得到笔记 API 快速参考

## 获取凭证

1. 打开 https://www.biji.com 并登录
2. F12 → Application → Cookies → www.biji.com
3. 复制：`token` → GETNOTE_TOKEN, `csrf_token` → GETNOTE_CSRF, `device_id` → GETNOTE_DEVICE_ID

## 列出笔记

```bash
curl -s 'https://get-notes.luojilab.com/voicenotes/web/notes?limit=20&sort=create_desc' \
  -H "Authorization: Bearer $GETNOTE_TOKEN" \
  -H "Xi-Csrf-Token: $GETNOTE_CSRF" \
  -H "x-d: $GETNOTE_DEVICE_ID" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://www.biji.com' \
  -H 'Referer: https://www.biji.com/' \
  -H 'Xi-App-Client-Source: getnote'
```

解析（用 note_id 查详情，或直接用列表里的 json_content）：

```bash
curl -s '...' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('总数:', d['c']['total_items'])
for i,n in enumerate(d['c']['list'][:20],1):
    print(f\"{i:2d}. [{n['note_type']}] {n['title']} | id={n['note_id']}\")
"
```

## 查笔记详情

```bash
curl -s "https://get-notes.luojilab.com/voicenotes/web/notes/<note_id>" \
  -H "Authorization: Bearer $GETNOTE_TOKEN" \
  -H "Xi-Csrf-Token: $GETNOTE_CSRF" \
  -H "x-d: $GETNOTE_DEVICE_ID" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://www.biji.com' \
  -H 'Referer: https://www.biji.com/' \
  -H 'Xi-App-Client-Source: getnote'
```

## 解析 ProseMirror JSON 内容

列表和详情中的 `json_content` 字段是 ProseMirror JSON，需解析提取纯文本：

```python
import json

def extract_text(node):
    if node.get('type') == 'text':
        return node.get('text', '')
    elif node.get('type') == 'hardBreak':
        return '\n'
    elif node.get('type') in ('paragraph', 'heading'):
        return ''.join(extract_text(c) for c in node.get('content', [])) + '\n'
    elif node.get('type') == 'tableRow':
        return ' | '.join(extract_text(c) for c in node.get('content', [])) + '\n'
    elif node.get('type') == 'tableCell':
        return ''.join(extract_text(c) for c in node.get('content', []))
    else:
        return ''.join(extract_text(c) for c in node.get('content', []))

doc = json.loads(json_content)
print(extract_text(doc))
```

## 更新笔记（PUT）

**⚠️ 必须同时传 title，否则标题被清空。**

```bash
curl -s -X PUT "https://get-notes.luojilab.com/voicenotes/web/notes/<note_id>" \
  -H "Authorization: Bearer $GETNOTE_TOKEN" \
  -H "Xi-Csrf-Token: $GETNOTE_CSRF" \
  -H "x-d: $GETNOTE_DEVICE_ID" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://www.biji.com' \
  -H 'Referer: https://www.biji.com/' \
  -H 'Xi-App-Client-Source: getnote' \
  -d '{"title": "笔记标题", "json_content": "<新json_content>"}'
```

## 用户状态（发芽信息）

```bash
curl -s 'https://get-notes.luojilab.com/voicenotes/web/user/sprout/user_situation' \
  -H "Authorization: Bearer $GETNOTE_TOKEN" \
  -H "Xi-Csrf-Token: $GETNOTE_CSRF" \
  -H "x-d: $GETNOTE_DEVICE_ID" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://www.biji.com' \
  -H 'Referer: https://www.biji.com/' \
  -H 'Xi-App-Client-Source: getnote'
```

## 已知坑

- **列表含全内容**：调用列表 API 后直接用返回结果中的 `json_content`，无需再查详情（省一次 API 调用，也避免 Token 过期后 403）。
- **urllib 偶发 ParseTokenFailed**：笔记列表 API urllib/curl 均正常；笔记详情 API urllib 偶发此错误，curl 稳定。遇到详情报错时换用 curl。
- **搜索端点需重新认证**：Token 过期后搜索返回 `LoginRequired`，列表和详情通常仍可用一段时间。
- **列表 API 在 Token 刷新后偶发 ParseTokenFailed**：实测刷新 Token 后，列表 API `GET /voicenotes/web/notes?limit=5&sort=create_desc` 返回 `{"message":"ParseTokenFailed"}`，但搜索 API 仍正常。Workaround：遇到列表 API ParseTokenFailed 且 Token 未过期时，改用搜索 API 查笔记 ID，或用详情 API 逐条查。可能是服务端对 URL query string 格式的 token 校验更严格。
- **搜索 API 是 GET 而非 POST**：查询参数直接拼接在 URL 中（`?keyword=<URL编码>&page=1&size=50`），无需 request body。
- **Token 截断**：execute_code / subprocess 字符串字面量中直接写 Token 会被截断（多行 JWT 或含特殊字符时）。正确做法：写入 `/tmp/getnote_token.txt` 后 read back，或用 `urllib.request` 直接拼接 `f"Bearer {token}"` 绕过 shell。
- **basic.ts 有语法错误**：`scripts/examples/basic.ts` 第 40 行 esbuild 解析失败，`require()` 在 tsx -e 模式也不 work。使用 Python urllib 模式最可靠。