# 充值固定套餐方案

## 目标
- 充值金额不再由用户输入，改为选择固定套餐包。
- 套餐可配置：价格、购买积分、赠送积分、名称、排序、上下架。
- 订单与套餐绑定并保留快照，支付完成后按套餐积分入账。
- 兼容历史订单与现有钱包/积分流水体系。

## 数据模型调整
### 1) 新增套餐表（recharge_packages）
字段建议：
- id (UUID)
- name：套餐名称
- price：价格（单位分，int）
- credits：购买积分（BigInt）
- bonusCredits：赠送积分（BigInt）
- isActive：是否可用
- sortOrder：展示排序
- createdAt / updatedAt / isDeleted

索引：
- (isActive, sortOrder) 便于前台快速排序展示

### 2) 扩展充值订单表（recharge_orders）
新增字段：
- packageId：套餐外键（可空，兼容历史订单）
- credits：购买积分快照
- bonusCredits：赠送积分快照

说明：
- 订单保留套餐快照，避免套餐后续改价/改赠送影响历史订单入账。

## 后端 API 设计（NestJS）
### 1) 获取可用套餐
- GET /api/pay/wechat/packages
- 返回字段：id, name, price, credits, bonusCredits
- 仅返回 isActive=true 且 isDeleted=false 的套餐
- 排序：sortOrder ASC, price ASC

### 2) 创建订单（基于套餐）
- POST /api/pay/wechat/create
- 请求体：{ packageId: string }
- 逻辑：
  - 校验套餐存在且可用
  - 订单写入 price/credits/bonusCredits/packageId
  - 调用微信 Native 下单，金额使用套餐 price
  - 返回 outTradeNo/codeUrl/expireAt/套餐信息

### 3) 支付回调与对账入账
- 回调解密后校验订单金额与商户信息
- 成功入账：
  - 若 packageId 存在：积分 = credits + bonusCredits
  - 若无套餐（历史订单）：沿用 amount 充值（兼容）
- 继续使用 credit_ledger 记录入账（refType=recharge）

## 前端改动（Next.js）
- 充值页加载时请求 /api/pay/wechat/packages
- 选择套餐后发起下单请求
- 展示订单与套餐信息（名称/金额/积分/赠送）
- 若无可用套餐，提示“暂无可用套餐”

## 配置与运维
### 套餐配置方式：手动 seed
初始套餐（单位：分/积分）：
- 50 元加油包：price=5000，credits=500，bonusCredits=150
- 100 元加油包：price=10000，credits=1000，bonusCredits=400
- 200 元加油包：price=20000，credits=2000，bonusCredits=800

说明：
- price 使用分，前端展示换算为元
- credits/bonusCredits 为积分的整数值
- sortOrder 建议按价格从小到大设置
- isActive=true 上架

手动 seed 文件：
- `packages/db/prisma/seed/recharge_packages.sql`

生产建议至少 3~5 个套餐，保持价格与积分梯度合理

## 兼容与迁移
- 历史订单没有 packageId 时仍可正常入账
- 数据迁移新增字段默认值，避免线上报错
- 不影响现有 wallet 与 credit_ledger 结构

## 测试建议
- 创建订单：有效套餐/无效套餐/停售套餐
- 回调处理：金额不匹配/重复回调/超时补偿
- 入账校验：购买积分+赠送积分正确累加
