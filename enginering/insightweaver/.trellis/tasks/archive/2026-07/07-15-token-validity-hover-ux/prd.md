# Token有效期hover显示和账号有效期简化

## Goal

优化 ZclawShell 组件中的 Token 和账号有效期显示交互，提升用户体验：
1. Token 余额通过 hover 交互显示续费入口
2. 账号有效期标签简化，减少视觉噪音
3. 即将到期和已过期状态提供明确的续费引导

## Background

当前 ZclawShell 组件（`apps/web/src/components/zclaw/ZclawShell.tsx`）在工作区侧边栏显示用户的 Token 余额和账号有效期信息。

### 现状分析

**已实现（代码探索发现）：**
- ✅ Token 余额 hover 时显示"补充 Token"按钮（第 489-526 行）
- ✅ Token 续费点击跳转到 token 补充包 tab（`emitOpenBillingPurchase("token")`）
- ✅ 账号有效期标签简化为"有效期"，hover 显示完整"账号有效期"（第 367-384 行）
- ✅ 账号无效时显示"已过期"并提供续费按钮（第 409-454 行）

**待实现：**
- ❌ 账号有效期状态为"即将到期"（expiring_soon）或"已过期"（expired）时，缺少续费按钮引导用户到月包充值 tab

## Requirements

### R1: Token 余额 hover 交互

**现状：** 已实现
- hover 时 Token 数字变为蓝色，右侧显示"补充 Token"按钮
- 点击后跳转到 token 补充包购买页面

**无需修改**

### R2: 账号有效期标签简化

**现状：** 已实现
- 显示"有效期"标签（`validityShort` i18n key）
- hover 时 Tooltip 显示完整"账号有效期"文本

**无需修改**

### R3: 即将到期和已过期状态提供续费引导

**现状：** 未实现
- 当前"即将到期"状态仅显示琥珀色徽章，无续费入口
- 当前"已过期"状态（当 accountValidity 存在时）仅显示红色徽章，无续费入口
- 续费按钮仅在 `showAccountInvalid` 分支（accountValidity 为 null）时出现

**需要实现：**
- 当 `accountValidity.status === "expiring_soon"` 时，在徽章下方添加续费按钮
- 当 `accountValidity.status === "expired"` 时，在徽章下方添加续费按钮
- 续费按钮点击后调用 `handleRenewClick()` 跳转到月包充值 tab（`emitOpenBillingPurchase("monthly")`）
- 根据 `postExpiryPurchaseMode` 决定显示"立即续费"按钮或"请联系管理员续费"文本

## Technical Notes

**关键文件：**
- `apps/web/src/components/zclaw/ZclawShell.tsx` - 主要修改文件
- `apps/web/messages/zh.json` - 中文 i18n 键值
- `apps/web/messages/en.json` - 英文 i18n 键值

**现有 i18n 键：**
- `renewNow`: "立即续费" / "Renew now"
- `contactAdminToRenew`: "请联系管理员续费" / "Please contact admin to renew"

**实现位置：**
- 在 ZclawShell.tsx 第 364-408 行的 `hasAccountValidity` 分支中
- 当前仅在第 389-407 行显示状态徽章
- 需要在徽章下方（第 407 行 `</div>` 之前）添加续费按钮逻辑

**参考代码：**
- 续费按钮实现可参考第 434-452 行的 `showAccountInvalid` 分支

## Acceptance Criteria

### AC1: Token hover 交互
- [ ] 鼠标悬停在 Token 余额上时，数字变为蓝色
- [ ] 悬停时右侧显示"补充 Token"按钮
- [ ] 点击 Token 区域任意位置跳转到 token 补充包购买页面

### AC2: 账号有效期标签
- [ ] 显示简化标签"有效期"
- [ ] 悬停时显示完整文本"账号有效期"
- [ ] Tooltip 样式与现有设计一致

### AC3: 即将到期状态续费引导
- [ ] 当状态为"即将到期"时，在徽章下方显示续费入口
- [ ] 自购买模式下显示"立即续费"蓝色链接按钮
- [ ] 点击"立即续费"跳转到月包充值 tab
- [ ] 管理员购买模式下显示"请联系管理员续费"灰色文本
- [ ] 联系管理员模式下不显示按钮

### AC4: 已过期状态续费引导
- [ ] 当状态为"已过期"时，在徽章下方显示续费入口
- [ ] 自购买模式下显示"立即续费"蓝色链接按钮
- [ ] 点击"立即续费"跳转到月包充值 tab
- [ ] 管理员购买模式下显示"请联系管理员续费"灰色文本
- [ ] 联系管理员模式下不显示按钮

## Out of Scope

- 后端逻辑修改（批次有效期回退已在之前任务完成）
- Token 余额显示格式调整
- 账号有效期日期格式修改
- 其他状态（active）的 UI 修改
