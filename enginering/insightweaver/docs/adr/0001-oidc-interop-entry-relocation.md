# 账号互通入口前移至云之师侧，三层失败兜底

互通入口从「Evomind 登录页第三方登录按钮」前移到云之师两个入口（侧边栏 ZClaw-EDU、welcome/student「开通个人版/去使用」），点击后同窗口顶层导航直达 Evomind `/api/auth/oidc/authorize`，成功直落 `/workspace`；失败经三层兜底回入口页。Evomind 登录页的两个 OIDC 入口（主按钮 + 换号链接）移除。

## Considered Options

- **双入口并存**（保留 Evomind 登录页按钮）：入口不唯一，用户面临「哪边登录」认知分叉，被否。
- **失败仅落 Evomind 登录页**：B 方案（同窗口导航）下用户被困在只有手机号登录的页面，需浏览器后退才能回云之师，兜底不完善，被否。
- **失败回跳云之师入口页**（选用）：authorize 新增 `return_on_error` 可选参数（仅接受 env 白名单 origin 的 https 绝对 URL），callback 失败时 302 回入口页并附白名单枚举错误码；无合法值时回退 Evomind 登录页。

## Consequences

- `prompt=login` 后端能力保留但暂不挂 UI；换号在云之师侧完成。
- 失败分流依赖 Redis state payload 存活（TTL 600s）；超期后落 Evomind 登录页（最后一道兜底）。
- 入口 URL 由云之师前端 env（`NEXT_PUBLIC_EVOMIND_SSO_AUTHORIZE_URL`）配置，留空回退普通首页链接作灰度开关。
- Evomind 侧新增 env `OIDC_ERROR_RETURN_ORIGINS`（`return_on_error` 白名单）。
