# 微信充值（Native 扫码）设计方案

## 1. 目标与范围
- 目标：用户在系统内完成“充值”，走微信支付 Native（扫码）方式；支付成功后余额入账。
- 范围：下单、支付、回调验签、到账、对账补偿、异常处理、审计与监控。

## 2. 支付形态与流程概览
- 支付形态：Native（扫码）
- 下单接口：`POST /v3/pay/transactions/native`
- 返回值：`code_url`（二维码内容）
- 前端：Next.js 渲染二维码
- 用户扫码支付 → 微信回调 → 后端验签与入账

### 2.1 流程步骤（落地版）
1. 用户发起充值（前端）：调用 `POST /api/pay/wechat/create`。
2. 后端创建订单：状态 `PENDING`，生成 `out_trade_no`。
3. 调用微信下单接口：获取 `code_url`。
4. 前端展示二维码（Next.js 渲染）。
5. 微信回调：验签 + 解密 + 幂等处理。
6. 支付成功：订单标记 `SUCCESS`，余额入账，写资金流水。
7. 前端轮询订单状态：提示充值成功。

## 3. 配置与环境变量
- `WX_MCH_ID`：商户号
- `WX_APP_ID`：公众号/小程序 appid（需绑定商户）
- `MCH_SERIAL_NO`：商户证书序列号
- `WX_API_V3_KEY`：APIv3 密钥
- `MCH_PRIVATE_KEY_PATH`：商户私钥路径（PEM）
- `WX_PUBLIC_KEY_PATH`：微信支付平台公钥路径（PEM，注意轮换）
- `WX_NOTIFY_URL`：回调地址（公网可达）
- `WX_ORDER_PAY_TIMEOUT_MILLS`：支付超时（建议 30 分钟）
- `WX_PAY_TEST`：测试拦截开关（开发/测试环境）

### 3.1 回调地址
- 你的回调域名：`https://dl.zzz4ai.com`
- 建议回调路径：
  - `https://dl.zzz4ai.com/api/pay/wechat/notify`

## 4. 订单号规则（推荐）
格式：`IW + yyyyMMddHHmmss + 6位随机数`

示例：`IW20250109153045983712`

特点：短、可读、无隐私暴露、低冲突率。

## 5. 数据模型设计（Prisma）
### 5.1 充值订单（recharge_order）
- `id` (uuid)
- `userId`
- `amount` (int, 分)
- `currency` (CNY)
- `status` (PENDING, PAYING, SUCCESS, CLOSED, FAILED)
- `wechatOutTradeNo`（唯一）
- `wechatTransactionId`
- `payType` (NATIVE)
- `expireAt`
- `paidAt`
- `notifyRaw` (json)
- `createdAt`, `updatedAt`

## 6. API 设计（NestJS）
### 6.1 创建 Native 充值订单
```
POST /api/pay/wechat/create
body: { amount: number }
return: { outTradeNo, codeUrl, expireAt }
```

### 6.2 查询订单状态
```
GET /api/pay/wechat/status?outTradeNo=...
return: { status, paidAt }
```

### 6.3 微信回调
```
POST /api/pay/wechat/notify
return: { code: "SUCCESS", message: "OK" }
```

## 7. 微信 Native 下单请求（关键字段）
```
POST /v3/pay/transactions/native
{
  appid: WX_APP_ID,
  mchid: WX_MCH_ID,
  description: "账户充值",
  out_trade_no: <生成的订单号>,
  notify_url: "https://dl.zzz4ai.com/api/pay/wechat/notify",
  amount: { total: <金额(分)>, currency: "CNY" }
}
```

## 8. 回调验签与解密（必须实现）
1. 取 header：
   - `Wechatpay-Signature`
   - `Wechatpay-Timestamp`
   - `Wechatpay-Nonce`
   - `Wechatpay-Serial`
2. 使用 `WX_PUBLIC_KEY_PATH` 验签。
3. 使用 `WX_API_V3_KEY` 解密 `resource.ciphertext`。
4. 校验 `mchid` / `appid` / `out_trade_no` / `amount.total`。
5. 幂等处理：若已 `SUCCESS`，直接返回成功。
6. 成功时更新订单 & 余额。

## 9. 前端二维码渲染（Next.js）
- 在 `apps/web` 新增充值页 `/recharge`。
- 后端返回 `code_url`，前端渲染二维码。
- 轮询订单状态（每 2-3 秒）。

## 10. 超时与补偿
- `WX_ORDER_PAY_TIMEOUT_MILLS` 建议 30 分钟。
- 定时任务扫描 `PENDING` 且超时订单：
  - 调微信查询接口确认支付结果。
  - 未支付则标记 `CLOSED`。

## 11. SAE 部署建议（证书处理）
- SAE 环境变量提供配置。
- 私钥/公钥可通过密文环境变量写入 `/tmp/wechat/*.pem`。
- `MCH_PRIVATE_KEY_PATH` 与 `WX_PUBLIC_KEY_PATH` 指向上述路径。
- `MCH_SERIAL_NO` 与商户证书序列号一致。

## 12. 监控与对账
- 关键日志：下单失败、回调验签失败、金额不一致、对账差异。
- 指标：支付成功率、回调延迟、补偿成功率。
- 对账：每日拉取微信账单与本地订单比对。

## 13. 目录组织建议
- `apps/api/src/modules/pay/wechat/`
  - `wechat.service.ts`
  - `wechat.controller.ts`
  - `wechat.dto.ts`
  - `wechat.signature.ts`
  - `wechat.config.ts`
