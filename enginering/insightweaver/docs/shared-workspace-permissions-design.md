# 共享工作区权限设计方案

## 背景

InsightWeaver 通过 Zclaw 功能对接 EvoMind/OpenClaw。当前文件区分为两类空间：

- 个人工作区：用户自己的 Zclaw workspace。
- 共享工作区：多个用户共同访问的公共空间，对应 EvoMind 的 shared workspace root。

本方案采用“InsightWeaver 作为权限网关，EvoMind 作为文件执行层”的设计：

- 权限管理、权限判断、审计语义全部放在 InsightWeaver。
- EvoMind 不理解业务用户、企业成员、产品角色，也不做共享工作区业务权限判断。
- 前端只能访问 InsightWeaver 的 `/api/zclaw/shared-workspace/*` 接口。
- 部署上必须保证 EvoMind 不直接暴露给终端用户，用户不能绕过 InsightWeaver 直接调用 `/api/km/shared-workspace/*`。

## 设计目标

1. 权限逻辑集中在 InsightWeaver，避免在 EvoMind 和产品后端两侧重复实现。
2. 支持企业成员角色的默认权限，以及管理端角色策略 / 成员覆盖。
3. 成员角色按「自己上传 / 他人上传」分策；运营保持扁平开关。
4. 文件主可对「他人」设置路径级 ACL，且权重大于企业策略；文件主对自己的操作仅由管理端控制。
5. 服务端强制校验，前端只负责体验层的按钮控制和提示。

## 权限点

共享工作区权限分为八类：

| 权限 | 含义 | 典型操作 |
| --- | --- | --- |
| `read` | 读取共享空间内容 | 查看目录、读取/预览文件、从共享空间复制到个人空间 |
| `write` | 移入或创建内容 | 新建文件、创建文件夹、上传文件、复制个人文件到共享空间 |
| `edit` | 编辑已有文件内容 | 在线编辑并保存共享空间文件内容 |
| `move` | 改变父目录 | 共享空间内部移动文件/文件夹（含子节点排序） |
| `rename` | 同目录改名 | 重命名文件或文件夹（父路径不变） |
| `delete` | 删除内容 | 删除共享空间文件、删除共享空间文件夹 |
| `download` | 显式下载 | `file-raw?download=true` 等附件下载（预览仍用 `read`） |
| `manage` | 管理权限 | 配置共享空间权限规则；默认也代表全部操作能力；绕过文件主 ACL |

`move` / `rename` 互相独立：父目录变化校验 `move`，basename 变化校验 `rename`，两者同时变化则都要满足。

`edit` 独立于 `write`：无移入权限时仍可编辑已有文件；有移入权限时也不自动获得编辑权限。

## 默认角色语义

企业共享工作区默认按 `EnterpriseMembership.role` 映射权限：

| 角色 | 权限 |
| --- | --- |
| `viewer` | `read` + `download` |
| `member` | `read` + `write` + `edit` + `move` + `rename` + `download` |
| `operator` | `read` + `write` + `edit` + `move` + `rename` + `delete` + `download` |
| `editor` | `read` + `write` + `edit` + `move` + `rename` + `download` |
| `admin` / `owner` | 全部（含 `manage`） |

系统级 `User.role = admin` 具备共享工作区全权限。

## 管理端可配置能力（角色策略 / 成员覆盖）

仅 `member` / `operator` 可在「共享工作区操作权限」页配置：

- **运营（operator）**：`write` / `edit` / `move` / `rename` / `delete` / `download` 各一项。
- **成员（member）**：
  - `write` 全局一项（不按归属拆分）
  - `edit` / `move` / `rename` / `delete` / `download` 拆成 **自己上传的文件（own）** 与 **他人上传的文件（others）**

存储仍用 `shared_workspace_permissions`，新增可选列 `audience`：`own` | `others` | `null`（null 表示不按归属，用于 `write`、运营全套与历史行）。

## 运行时解析顺序

对路径 `P` 上的操作者 `U`：

1. 计算角色默认权限。
2. 判定 `U` 是否为 `P` 的 path owner（`SharedWorkspacePathOwner`；无 owner 行按非本人）。
3. 叠加管理端角色策略 / 成员覆盖行：
   - `audience=own` 仅本人路径生效
   - `audience=others` 仅非本人路径生效
   - `audience=null` 始终生效
4. 若 `U` **不是** owner 且无 `manage`：再叠加文件主 ACL（`shared_workspace_owner_file_acls`，路径及祖先，后写覆盖先写）。文件主 ACL 为最终覆盖（可严可松）。
5. 若 `U` **是** owner：跳过文件主 ACL（本人操作只吃管理端 own 策略）。
6. `manage` 允许全部操作，并绕过文件主 ACL。

## 文件主 ACL（C 端）

表 `shared_workspace_owner_file_acls`：path owner 设置他人对本路径的 `edit` / `move` / `rename` / `delete` / `download`。

- 仅 path owner 可写（`GET/PUT /api/zclaw/shared-workspace/owner-acl`）。
- 不影响文件主自己的操作。
- 「跟随企业策略」= 清空该路径的 owner ACL 行。

## 服务端接口校验

| InsightWeaver API | 权限 |
| --- | --- |
| `GET .../root|children|path|file-content` | `read` |
| `GET .../file-raw`（预览） | `read` |
| `GET .../file-raw?download=true` | `download` |
| `POST .../file|folder|upload` | `write` |
| `PUT .../file-content` | `edit` |
| `PATCH .../path` | `move` 和/或 `rename`（按路径变化判定） |
| `DELETE .../path` | `delete` |
| 共享→个人复制 | 共享 `read` |
| 个人→共享复制 | 共享 `write` |

## 权限查询

```http
GET /api/zclaw/shared-workspace/permissions/me
```

返回 `canWrite` / `canEdit` / `canMove` / `canRename` / `canDelete` / `canDownload` / `canManage`，以及成员场景的 `byOwnership.own|others` 与 `ownedPaths`。

## 前端行为

- 无 `read`：不加载共享工作区树。
- 菜单按路径解析：本人路径用 `own`（或运营扁平），他人路径用 `others`；`ownedPaths` 上展示「权限设置」。
- 前端控制仅用于体验，不能作为安全边界。

## 路径可见范围（组织 × 成员，并集）

共享工作区「谁能看见某路径」由两层独立配置叠加（OR），互不清空：

| 层 | 存储 | 空 = 不启用 |
| --- | --- | --- |
| 组织层 | `shared_workspace_org_shares`（部门 / 部门小组） | 无行 |
| 成员层 | `shared_workspace_user_shares`（`userId`） | 无行 |

判定顺序：

1. 平台 admin / 企业 admin|owner（`bypassVisibility`）→ 可见
2. 路径 owner → 可见
3. 取 org/user grants 中**最长限制前缀**；该前缀上：
   - 仅组织 → 命中部门/小组
   - 仅成员 → 命中 `userId`
   - 两层都有 → 组织命中 **或** 成员命中
   - 两层都无 → 企业全员可见

API：`GET/PUT /api/zclaw/shared-workspace/org-shares` 同时读写 `departmentIds` / `departmentGroupIds` / `userIds`；`userIds: []` 只关闭成员层，不清组织层。

C 端「设置可见范围」为双区块（按组织 / 按成员）+ 实时「当前谁能看见」摘要，禁止三选一互斥。

## 部署边界

1. EvoMind 只在内网或后端私有网络中暴露。
2. EvoMind gateway token 只配置在 InsightWeaver API 环境变量中。
3. 浏览器端不能拿到 EvoMind baseUrl 或 gateway token。
4. 用户所有公共空间操作必须经过 `/api/zclaw/shared-workspace/*`。
