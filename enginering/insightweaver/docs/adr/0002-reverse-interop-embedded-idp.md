# 反向互通：mesh 双向 + 嵌入 node-oidc-provider 作 Evomind IdP

账号互通扩展为双向 mesh：云知师（IdP: ST+Hydra）→ Evomind（RP: openid-client）已实现；反向 Evomind → 云知师按「Evomind 内嵌 `node-oidc-provider` 作 IdP，云知师用 ST thirdparty custom OIDC provider 作 RP」落地，两端零新增容器、零 license 障碍，用户无感切换（sub 直登 / 手机号自动绑 / 未命中自动开户受限联合账户 + 审计）。

## Considered Options

- **hub（中央 broker IdP）**：接入系统 ≥3 时最优；当前仅 2 个系统，用户拍板维持 mesh，留扩展口。
- **独立部署 Ory Hydra 作 Evomind IdP**：与云之师同栈、一致性好；但 +1 容器运行时与运维面，用户拍板改为嵌入方案。
- **手写 OIDC Provider**：Ory 选型文明确否决（≈重写 70% Hydra）。
- **authlib 自建 RP（云知师侧）**：依赖已声明但零使用，需自实现 state/nonce/验签且另建 ST 灌会话，弃用；采用 ST thirdparty custom provider（ECNU 先例同构）。

## Consequences

- Evomind API 内 `node-oidc-provider` 与 `openid-client` 共存（同仓库既当 IdP 又当 RP）。
- 授权最小化：仅 `sub` + `email`（手机号），与正向对称；自动开户账号仅可经 Evomind OIDC 登录（受限联合账户，ECNU 同构）。
- 生产部署：反向两端零新容器；云知师生产唯一新增 Hydra 属正向阶段 2 前置（`yunzhishi-03` P0-补 已定形态）。
