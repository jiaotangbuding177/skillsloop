# 得到大脑（Get笔记）配置指南

## 获取凭证

SDK 需要三项凭证，均来自浏览器 Cookie。

### 步骤

1. 打开 https://www.biji.com 并登录
2. 按 F12 打开开发者工具
3. 进入 **Application**（应用程序）→ **Cookies** → **www.biji.com**
4. 复制以下三个 Cookie 的值：

| 环境变量 | Cookie 名 | 用途 |
|----------|-----------|------|
| `GETNOTE_TOKEN` | `token` | JWT 认证令牌 |
| `GETNOTE_CSRF` | `csrf_token` | CSRF 防护令牌 |
| `GETNOTE_DEVICE_ID` | `device_id` | 设备标识 |

### 设置环境变量

```bash
export GETNOTE_TOKEN="eyJhbGci..."
export GETNOTE_CSRF="abc123..."
export GETNOTE_DEVICE_ID="e152c212..."
```

## 验证连接

设置环境变量后运行验证脚本：

```bash
cd scripts
GETNOTE_TOKEN="$GETNOTE_TOKEN" \
GETNOTE_CSRF="$GETNOTE_CSRF" \
GETNOTE_DEVICE_ID="$GETNOTE_DEVICE_ID" \
npx tsx -e '
const { GetNoteClient } = require("./src/index");
const c = new GetNoteClient({ token: process.env.GETNOTE_TOKEN, csrfToken: process.env.GETNOTE_CSRF, deviceId: process.env.GETNOTE_DEVICE_ID });
(async()=>{
  const r = await c.notes.count();
  console.log("连接成功，笔记总数:", r.total);
})().catch(e=>console.error("连接失败:", e.message));
'
```

## Token 过期处理

JWT Token 有有效期（通常几周到几个月）。如果请求返回鉴权错误：

1. 重新登录 https://www.biji.com
2. 按上述步骤重新获取三个 Cookie 值
3. 更新环境变量

## 注意事项

- `note_id` 是 64 位整数，在 JavaScript 中以字符串形式处理，避免精度丢失
- 不要将 Token 提交到版本控制
- 建议在 `.env` 文件中配置，并加入 `.gitignore`
