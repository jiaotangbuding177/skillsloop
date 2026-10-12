# 得到笔记 API 参考

## 认证与 Token

### 刷新 Token（推荐）
```
POST https://ddll-api.trytalks.com/account/v2/web/user/auth/refresh
Content-Type: application/json
Body: { "refresh_token": "<refresh_token>" }
```

响应：
```json
{
  "h": { "c": 0, "e": "", "s": 1781251019, "t": 6 },
  "c": {
    "success": true,
    "status": 2,
    "uid": 1805281,
    "token": {
      "jti": "a086f1c5-2217-4781-8510-a548f423c45c",
      "token": "eyJhbG...",
      "token_expire_at": 1781252819,
      "refresh_token": "AAAAAA...",
      "refresh_token_expire_at": 1788794800
    }
  }
}
```

> ⚠️ Base URL 是 `ddll-api.trytalks.com`，不是 `get-notes.luojilab.com`。

### Token 刷新特征
- `refresh_token` **不滚动刷新**（新旧 token 共用同一个 refresh_token），可重复使用
- `token_expire_at` ≈ 30 分钟（1781252819 约等于当前时间 + 1800 秒）
- `refresh_token_expire_at` ≈ 长期（1788794800 约 2026-09-07）

### Token 过期判断
| 信号 | 含义 |
|---|---|
| `exp` 未过但 API 返回 `LoginRequired` | 服务端已主动吊销，立即刷新 |
| `exp` 已过 | 正常过期，需要刷新 |
| `refresh_token_expire_at` 已过 | refresh_token 失效，需用户提供新 Cookie |

## 笔记 API（get-notes.luojilab.com）

### 笔记列表
```
GET /voicenotes/web/notes?limit=20&sort=create_desc
```

### 笔记详情
```
GET /voicenotes/web/notes/<note_id>
```

### 用户信息
```
GET /voicenotes/web/user/info
```

### 搜索
```
POST /voicenotes/web/notes/search
```

### 回收站
```
GET /voicenotes/web/notes/recycle_bin?page=1&limit=20
```

## 认证 API（ddll-api.trytalks.com）

| 端点 | 方法 | 说明 |
|---|---|---|
| `/account/v2/web/user/auth/refresh` | POST | 刷新 Token |
| `/account/v2/web/user/auth/login` | POST | 登录（可能需要手机号） |

## 公共请求头（所有 API 必须带）

| Header | Value |
|---|---|
| `Authorization` | `Bearer <GETNOTE_TOKEN>` |
| `Xi-Csrf-Token` | CSRF Token |
| `x-d` | 设备 ID |
| `Xi-App-Client-Source` | `getnote` |
| `Content-Type` | `application/json` |
| `Origin` | `https://www.biji.com` |
| `Referer` | `https://www.biji.com/` |

## 错误码

| h.c | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | — |
| 非0 | 业务错误 | 看 `h.e` 字段 |
| `LoginRequired` | Token 无效/过期 | 刷新 Token |
| 403 | 权限不足 | 检查 Authorization header |
| 404 | 端点不存在 | 检查 URL |