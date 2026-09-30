# Domain Model: Quota & Billing

## Core Concepts

### Enterprise (企业)
A business entity that owns resources and has members. Has an `enterpriseKind`:
- **b2b**: Business-to-business enterprise
- **consumer**: Consumer-facing enterprise
- **evomind_consumer**: EvoMind consumer enterprise

### Quota Mode (配额模式)
Determines how token usage is tracked and limited:
- **batch**: Token quota is managed via batches with validity periods
- **conversation**: Quota is measured in conversation count
- **token**: Quota is measured in token count with monthly reset
- **unlimited**: No quota limits

### Post-Expiry Purchase Mode (到期后购买模式)
Determines what happens when quota expires. Each mode uses different data sources:

| Mode | Token Sources | Storage Sources | Account Validity |
|------|--------------|-----------------|------------------|
| **contact_admin** | Batch only | Default quota | Batch validTo |
| **self_purchase** | Batch (expired=0) + Consumer packages | Default + Consumer packages | Consumer monthly plan → Batch fallback |
| **admin_purchase** | Batch (expired=0) + B2B packages | Default + B2B packages | B2B seat allocation → Batch fallback |

**Account Validity (账户有效期)**: Determines if user can use the service. When expired, throws `ACCOUNT_EXPIRED`.
- **self_purchase**: Valid if has active `consumer_monthly_plan` OR batch is effective
- **admin_purchase**: Valid if has active `b2b_monthly_seat_plan` allocation OR batch is effective
- **contact_admin**: Valid only if batch is effective

**Data Source Isolation**: Each mode strictly excludes other modes' packages to prevent token leakage.

### Entitlement Batch (权益批次)
A grant of resources (token, storage, monthly_plan) to a subject. Key fields:
- **subjectType**: Who receives the grant
  - `enterprise`: Enterprise-level grant (no specific user)
  - `enterprise_user`: User-level grant
- **entitlementType**: What is granted
  - `monthly_plan`: Monthly subscription anchor
  - `token`: Token quota
  - `storage`: Storage quota
- **sourceType**: Where the grant came from
  - `b2b_monthly_seat_plan`: B2B seat-based monthly plan
  - `b2b_enterprise_plan`: B2B enterprise monthly plan
  - `consumer_monthly_plan`: Consumer monthly plan
  - `b2b_token_topup`: B2B token topup
  - `b2b_storage_topup`: B2B storage topup
  - `consumer_token_topup`: Consumer token topup
  - `consumer_storage_topup`: Consumer storage topup
  - `default_quota_batch`: Default quota batch
  - `admin_grant`: Admin-granted entitlement
- **status**: Current state
  - `active`: Currently effective
  - `scheduled`: Will become active in the future
  - `frozen`: Temporarily suspended
  - `expired`: Past validity period
  - `voided`: Cancelled/invalidated
  - `cancelled`: Cancelled by admin

### Effective Window (有效时间窗口)
The actual time range when a batch is effective for a specific user:

```typescript
effectiveFrom = member.validFrom ?? batch.validFrom
effectiveTo = member.validTo ?? batch.validTo
```

- **member.validFrom/validTo**: User-specific override dates (can be null)
- **batch.validFrom/validTo**: Batch-level dates
- Token usage is only counted within this window
- A batch is "effective" when: `now >= effectiveFrom && now <= effectiveTo`

### Batch Hierarchy (批次层级)

**Anchor Batch (锚点批次)**
- `subjectType: 'enterprise'`, `entitlementType: 'monthly_plan'`
- Represents the monthly plan itself
- Has `metadata.poolModel: true` for pool-based plans
- Children: Token pool batch + Storage pool batch

**Pool Batch (池批次)**
- `subjectType: 'enterprise'`, `entitlementType: 'token'` or `'storage'`
- Created from anchor batch for pool-based plans
- `sourceRefType: 'entitlement_batch'`, `sourceRefId: <anchorBatchId>`
- Represents the total token/storage pool for the plan

**Member Batch (成员批次)**
- `subjectType: 'enterprise_user'`
- Created when a seat is allocated from a pool
- Represents an individual user's allocation

### Package Record (套餐记录)
A user-facing view of entitlement batches, grouped by grant group or order. Shows:
- Plan name and type
- Components (token, storage amounts)
- Status (derived from batch statuses)
- Validity period

### Topup Inventory (补充包库存)
For B2B enterprises, purchased topups go into inventory first, then allocated to users.

## Access Control

### Platform Admin (平台管理员)
- `role: 'admin'` at platform level
- Can access all admin features
- `canAccessManagementBackend: true`

### Enterprise Admin/Owner (企业管理员/所有者)
- `role: 'admin'` or `'owner'` at enterprise level
- Can manage enterprise members and resources
- `isActiveEnterpriseAdmin: true`

### Enterprise Operator (企业运营)
- `role: 'operator'` at enterprise level
- Limited admin access
- `isActiveEnterpriseOperator: true`

### Access Flags
- **canAccessManagementBackend**: Platform admin only
- **canAccessTopupInventories**: Platform admin OR enterprise admin of B2B enterprise
- **canAccessOrganizationManagement**: Enterprise operator
- **canAccessEnterpriseMemberships**: Platform admin OR enterprise admin

## Status Derivation

Package record status is derived from its batches:
1. If any batch is `active` → status is `active`
2. Else if any batch is `scheduled` → status is `scheduled`
3. Else use first batch's status

## Key Relationships

```
Enterprise
── Quota Mode (quotaMode)
── Post-Expiry Purchase Mode (postExpiryPurchaseMode)
├── Members (EnterpriseMembership)
│   └── Role: admin/owner/operator/member
└── Entitlement Batches
    ├── Anchor Batch (monthly_plan, enterprise-level)
    │   ├── Token Pool Batch (token, enterprise-level)
    │   └── Storage Pool Batch (storage, enterprise-level)
    └── Member Batches (token/storage, user-level)
        └── Created from pool allocation
```

## Open Questions

1. ~~Should `frozen` status be shown in package records?~~ **已解决**：i18n key 缺失已修复，frozen 会显示为"已冻结"
2. ~~Should `expired` and `voided` statuses be shown?~~ **已解决**：只显示 `active` 和 `scheduled` 状态的套餐记录
3. What's the difference between `b2b_monthly_seat_plan` and `b2b_enterprise_plan`?
   - `b2b_monthly_seat_plan`: **当前使用**。Seat-based，创建池批次，需要席位分配（自动/手动）
   - `b2b_enterprise_plan`: **遗留/待废弃**。购买直接授予所有成员，不适合 B2B 场景，暂时保留

## Account Interop (账号互通)

**互通入口 (Interop Entry)**:
云之师侧跳转 Evomind OIDC authorize 的 UI 入口（侧边栏 ZClaw-EDU、welcome/student「开通个人版/去使用」）。账号互通的唯一合法通道。
_Avoid_: 第三方登录按钮、SSO 按钮（均指 Evomind 登录页旧入口，已移除）

**直通 (Direct Pass-through)**:
用户在云之师点击入口，经静默直达或一次云之师对外登录页后，直接以登录态落 Evomind 站内目标页（当前定稿落点 `/workspace`）。

**静默直达 (Silent Pass-through)**:
Hydra 已有认证会话且授权请求不带 prompt 时，skip=true 全程无登录页直达回调。与「首次停一次对外登录页」相对。

**三层兜底 (Layered Fallback)**:
OIDC 失败处理链：authorize 时带合法 `return_on_error` → 失败 302 回入口页 + 白名单错误码（云之师侧 toast 呈现）；无合法值 → 落 Evomind 登录页（最后一道网）。

**return_on_error**:
authorize 的可选参数，失败时回跳的入口页绝对 URL。仅接受 env `OIDC_ERROR_RETURN_ORIGINS` 白名单内 origin 的 https URL，否则忽略。

**反向互通 (Reverse Interop)**:
Evomind 作为 IdP（嵌入 `node-oidc-provider`），云知师作为 RP（ST thirdparty custom OIDC provider）消费，实现「Evomind 账号登录云知师」。与正向（云知师→Evomind）构成 mesh 双向。

**受限联合账户 (Restricted Federated Account)**:
云知师侧自动开户的账号形态：仅挂 `provider='evomind'` 身份、无独立口令/短信凭据，只能经 Evomind OIDC 登录。与云知师现有 ECNU 第三方登录产出的无口令联合用户同构。

**无感切换 (Seamless Switching)**:
用户在两侧系统间切换零额外步骤：sub 命中直登同一账号；手机号命中自动绑定；未命中自动开受限联合账户。全程不出现云知师注册页。

**授权最小化 (Minimal Consent)**:
反向授权页仅声明「允许云知师识别你的登录身份（含手机号）」，claims 只发 `sub` + `email`（手机号），不传姓名/头像等 PII。

## Technical Conventions

### Timezone Handling (时区处理)
PostgreSQL `timestamp without time zone` columns require explicit timezone handling in Prisma raw queries:

**Problem**: JavaScript `Date` objects passed to `$queryRaw` cause implicit timezone conversion (shifts by server timezone offset, e.g., +8 hours for Asia/Shanghai).

**Solution**: Format Date as timezone-free string + `::timestamp` cast:
```typescript
// ❌ Wrong: implicit tz conversion
AND "createdAt" >= ${validFrom}

// ✅ Correct: explicit tz-free format
const fromStr = validFrom.toISOString().replace("T", " ").replace("Z", "");
AND "createdAt" >= ${fromStr}::timestamp
```

**Affected**: `sumTokenUsageInWindow` and any raw query comparing Date parameters against `timestamp without time zone` columns.
