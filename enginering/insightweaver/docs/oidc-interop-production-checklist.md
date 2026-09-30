# Evomind 生产互通变量清单

> 生成日期 2026-09-01。正反向互通（OIDC）生产部署所需变量全表。
> 侧向说明：**正向** = 云知师作 IdP，Evomind 作 RP（云知师账号登录 Evomind）；**反向** = Evomind 作 IdP（node-oidc-provider 嵌入），云知师作 RP（Evomind → 云知师 无感直达）。

## 一、确认项：path issuer 的 discovery 兼容

openid-client `discovery()` 按 RFC 8414 拼接 `<issuer>/.well-known/openid-configuration`，**带子路径 issuer 正常**（`https://<云知师生产API域名>/oidc` → `.../oidc/.well-known/openid-configuration`）。已本地实测：`OIDC_ISSUER_URL=http://localhost:8000/oidc`（带路径 issuer）全链跑通（discovery 200、authorize 302、token 200、RS256 验签全绿）——生产可直接使用带 `/oidc` 前缀的 issuer。

## 二、变量清单

| 变量 | 侧向 | 必填 | 语义 | 当前 dev 值 | 生产占位 |
|---|---|---|---|---|---|
| `OIDC_ISSUER_URL` | 正向 | 是 | 上游 IdP issuer（RP discovery 基址，可带子路径） | `http://localhost:8000/api/oidc` | `https://yunzhishi.zzz4ai.com:448/api/oidc` |
| `OIDC_CLIENT_ID` | 正向 | 是 | RP client_id | `evomind` | `evomind` |
| `OIDC_CLIENT_SECRET` | 正向 | 是 | RP client secret（与云知师侧登记一致） | `evomind-secret-local-0123456789` | 待云知师侧签发/对齐 |
| `OIDC_CALLBACK_URI` | 正向 | 是 | RP 回调（IdP 侧注册） | `http://localhost:8787/api/auth/oidc/callback` | `https://<evomind生产API域名>/api/auth/oidc/callback` |
| `OIDC_ERROR_RETURN_ORIGINS` | 正向兜底 | 否 | 失败回跳 origin 白名单（逗号；留空=关闭 return_on_error） | `http://localhost:3000` | 云知师前端生产 origin |
| `OIDC_PROVIDER_ISSUER` | 反向 | 是 | 我方 IdP issuer（**必须根、无路径**；生产强制 https，onModuleInit 校验） | `http://localhost:8787` | `https://<evomind生产API域名>` |
| `OIDC_PROVIDER_CLIENT_ID` | 反向 | 是 | 云知师侧 client_id | `yunzhishi` | `yunzhishi` |
| `OIDC_PROVIDER_CLIENT_SECRET` | 反向 | 是 | 云知师侧 client_secret（token 认证 = `client_secret_post`，见 service.ts 配置） | `evomind-oidc-provider-local-secret-0123456789` | 我方生成 → 同步云知师后端 |
| `OIDC_PROVIDER_REDIRECT_URI` | 反向 | 是 | 云知师 client 回调白名单（**逗号分隔双登记**；service.ts 已支持解析，单值向后兼容） | `http://localhost:3000/yunzhishi/auth/callback/evomind,http://localhost:8000/api/oidc/callback` | `https://<云知师生产前端域名>/yunzhishi/auth/callback/evomind,https://<云知师生产API域名>/oidc/callback` |
| `OIDC_IDP_COOKIE_KEYS` | 反向 | 否（生产建议） | IdP 交互/会话 cookie 签名密钥（逗号分隔；多实例/重启稳定；不配=启动随机，重启后旧交互失效） | （空，随机回退） | 固定随机密钥串（≥2 个方便轮换） |
| `OIDC_TRUSTED_CLIENTS` | 反向 | 否 | consent 自动同意白名单（逗号） | `yunzhishi` | `yunzhishi` |
| `OIDC_TEACHER_ENTERPRISE_ID` | 正向（教师入口） | 否（留空=关闭） | 云之师教师版组织 id：authorize `scene=teacher` 回调后自动直挂 active 成员（免审；pending 升级、rejected/disabled 不复活）；组织须先在生产库存在。**同一配置也是嵌入面板无套餐弹窗门控的来源**（Web 运行期读取，见下一行） | （空=关闭） | `d40c94e1-0679-4f69-bdfd-b303b4b33948`（云知师-教师版） |
| —（方案 C 嵌入占位） | 方案 C 嵌入（教师面板） | —— | 嵌入面板教师组织无套餐自动弹购买套餐弹窗：与上一行同源——Web 登录后经 `GET /api/auth/oidc/config/teacher-enterprise`（JWT）从 API 获取，API 服务端运行期读 SAE 环境变量 `OIDC_TEACHER_ENTERPRISE_ID`；**无需 Web 构建期/NEXT_PUBLIC 配置** | —— | 复用上一行 SAE 配置即可 |
| `OIDC_EMBED_TARGET_OVERRIDES` | 方案 C 嵌入（分组织分流） | 否（留空=关闭） | 嵌入态白名单目标组织覆盖：逗号分隔 `手机号-组织id`（手机号支持完整号或脱敏号）；命中且组织为用户 active 成员组织 → 嵌入落地强制到该组织，否则维持教师组织强制。**API 运行期读取**（SAE 应用环境变量），Web 登录后经 `GET /api/auth/oidc/config` 获取；无需 Web 构建期配置 | （空=关闭） | （空=关闭；启用时按需填，如 `138****8000-<组织id>`） |
| `NEXT_PUBLIC_OIDC_EMBED_ALLOWED_ORIGINS`（web） | 方案 C 嵌入 | 否（缺省默认集合） | 嵌入视图 `?embed=1&framer=` 白名单（逗号分隔 origin；非机密，构建期注入）；dev example 覆盖为仅 `http://localhost:3000`（代码缺省集合含生产域） | `http://localhost:3000`（dev example） | `https://yunzhishi.zzz4ai.com` |
| `OIDC_SUCCESS_RETURN_ORIGINS` | 方案 C 激活链路 | 否（留空=关闭） | 登录成功回跳白名单（`sso_success`，逗号分隔 origin；回调成功优先 302 回该域，云知师侧据此激活面板） | `https://yunzhishi.zzz4ai.com` | `https://yunzhishi.zzz4ai.com` |
| CSP `frame-ancestors 'self' + yunzhishi.zzz4ai.com` | 方案 C 帧围栏 | 是（生产） | next.config headers 输出（仅生产）；白名单外顶层站点 iframe 加载即被浏览器拒绝 | 不输出 | 输出 |
| `WEB_ORIGIN` | 双向 | 是 | 交互页登录回跳的 Web 登录页域 | `http://localhost:3100` | `https://<evomind生产前端域名>` |
| `NEXT_PUBLIC_EVOMIND_INTEROP_URL`（web） | 反向入口 | 是（生产注入） | 用户菜单「跳转到云知师」href（ZclawShell.tsx:42 已 env 化：`process.env.NEXT_PUBLIC_EVOMIND_INTEROP_URL ?? dev 值`；生产 SAE 构建注入） | （不设=fallback `http://localhost:8000/api/oidc/sso-start`） | `https://yunzhishi.zzz4ai.com/api/oidc/sso-start` |
| `API_CONFIG.BASE_URL`（web） | 反向交互 | 是 | `/oidc-bridge` 回跳 API 基址（web 侧配置） | `http://localhost:8787` | `https://<evomind生产API域名>` |

## 三、需用户/对端提供的生产值

1. 云知师生产 **API 域名**（`OIDC_ISSUER_URL`、`OIDC_PROVIDER_REDIRECT_URI` 第二值、`EVOMIND_INTEROP_URL` 用）
2. 云知师生产 **前端域名**（`OIDC_PROVIDER_REDIRECT_URI` 第一值、`OIDC_ERROR_RETURN_ORIGINS` 用）
3. Evomind 生产 **API 域名**（`OIDC_CALLBACK_URI`、`OIDC_PROVIDER_ISSUER`、`API_CONFIG.BASE_URL` 用）
4. Evomind 生产 **前端域名**（`WEB_ORIGIN` 用）
5. 正向 **`OIDC_CLIENT_SECRET`** 生产值（云知师侧 IdP 签发）
6. 反向 **`OIDC_PROVIDER_CLIENT_SECRET`** 生产值（我方生成后同步云知师后端）与 `OIDC_IDP_COOKIE_KEYS`（我方生成）

## 四、生产其它前置 / 已知限额

- **RS256 签名密钥仍为内存随机**（启动轮换，jwks 变化）：生产多实例/长稳建议阶段 2 预设 env 持久化（`oidc-provider.service.ts:68-75`），当前任一实例重启会使对端缓存 jwks 的验签短暂失败。
- 反向 provider 端点统一 **`/api` 前缀**（`/api/authorize /api/token /api/jwks /api/userinfo`，2026-09-01 方案②），仅 `/.well-known/openid-configuration` 保留在根（v9 硬编码）；生产网关/ALB 只需 **1 条额外规则 `/.well-known/* → API`**（`/api/*` 走常规转发）；交互页在 `/api/oidc/interaction/<uid>`（同属 /api 前缀）。
- Dev server 运行期间勿执行 `pnpm --filter @insightweaver/web build`（与 Next dev 共用 `.next` 目录冲突，见 2026-09-01 事故）。
