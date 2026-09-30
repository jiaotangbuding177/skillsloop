# 双模型共存方案

## 旧模型修复（b2b_enterprise_plan）
- memberLimit 自动填入当前成员数
- 字段只读，防止浪费
- 现有逻辑不变

## 新模型（b2b_monthly_seat_plan）
- 池分配模型
- 管理员手动分配席位
- 未分配席位留在池中
- 新增发放 + 分配 API
- 新增前端分配 UI

## 文件改动
- 后端：entitlement.service.ts, billing-plan.service.ts, entitlement.dto.ts, entitlement.controller.ts
- 前端：billing-plans/page.tsx, topup-inventories/page.tsx, API types