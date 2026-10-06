# conv_4bc7c073280e:learn01：沙箱附件读取排障

会话：conv_4bc7c073280e

本轮可学习：先核对实际runtime和workspaceRoot再映射文件路径；把去除/workspace前缀作为用户要求的局部重试，不能未经结果验证宣称修复

原文依据：使用 read 工具时，请直接去掉 /workspace 前缀

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：原始时序未独立核验；附件与产物字节未提供；方法适用性及任务结果未独立验收

## 用户需求／反馈

来源消息组：u_d15dfa3ed64c4d0874

[

  {

    "path": "AI 创作中心/生成小学三年级语文的清明的教案-conv_567a2331adcf/3年级语文_清明.md",

    "name": "3年级语文_清明.md",

    "mimeType": "text/markdown",

    "source": "workspace",

    "sizeBytes": 17508

  }

]给你传的参数是正确的呀，为什么你会read不到

## 用户需求／反馈

来源消息组：u_8c5f99738c936abab7

你查下openclaw开启了沙箱环境后，这个问题如何解决，是通过什么配置还是什么其他方式

## 用户需求／反馈

来源消息组：u_8b3123e5e22443f14f

"sandbox": {

        "mode": "non-main",

        "workspaceAccess": "rw",

        "scope": "agent",

        "docker": {

          "image": "python-node22:1",

          "readOnlyRoot": false,

          "network": "bridge",

          "user": "0:0",

          "binds": [

            "/opt/openclaw-shared-skills:/opt/openclaw-shared-skills:ro,z",

            "/opt/shared-workdspace:/opt/shared-workdspace:ro,z"

          ],

          "dangerouslyAllowExternalBindSources": true

        },

        "prune": {

          "idleHours": 48,

          "maxAgeDays": 7

        }

      }

## 用户需求／反馈

来源消息组：u_82411d6ba6fd9efb98

你目前在host的配置就是一个agent

## 用户需求／反馈

来源消息组：u_4bb52efa9c985561e6

我挪了一个位置，再读取试试

## 用户需求／反馈

来源消息组：u_1f9616a67ffa5271bb

使用 read 工具时，请直接去掉 /workspace 前缀；看是不是能读取成功

## AI处理／结果

来源消息组：a_cd166965e136751471

## 🎯 找到问题了！

根据 `openclaw sandbox explain` 的输出：

```
Effective sandbox:
  runtime: direct
  mode: off scope: agent
  workspaceAccess: none 
  workspaceRoot: /workspace/.openclaw/sandboxes
```

**关键发现：**
- `mode: off` - 沙箱模式**已关闭**
- `workspaceAccess: none` - 工作区访问为 `none`
- `workspaceRoot: /workspace/.openclaw/sandboxes` - 但工具仍然使用沙箱路径

**矛盾点：** 虽然 `mode: off`，但 `read` 工具的行为显示它仍在尝试访问隔离的文件系统。

---

## 📋 完整分析

### 问题根源

1. **附件来源**：你的文件通过聊天附件上传，存储在沙箱的 `/workspace/AI 创作中心/...`
2. **read 工具路径解析**：`read` 工具设计为访问 **host 工作区** (`/root/.openclaw/{session-id}/...`)
3. **路径不匹配**：沙箱内的 `/workspace` 和 host 的 `/root/.openclaw/...` 是两个独立的文件系统

### 这是 OpenClaw 的设计行为

根据文档：
> **For read/write/edit**: paths resolve against **host workspace**
> **For exec**: use **sandbox paths** under `/workspace`

这意味着：
- `read`/`write`/`edit` 工具 → 访问 **host 路径**
- `exec` 命令 → 访问 **沙箱路径** (`/workspace`)

当沙箱启用时，这两个路径空间是**隔离的**。

---

## ✅ 解决方案

### 方案 1：启用 `workspaceAccess: "rw"`（推荐）

修改 OpenClaw 配置，让文件工具可以访问沙箱工作区：

```json5
// ~/.openclaw/openclaw.json (host 端)
{
  "agents": {
    "defaults": {
      "sandbox": {
        "workspaceAccess": "rw"  // ← 添加此行
      }
    }
  }
}
```

然后重启 OpenClaw Gateway：
```bash
openclaw gateway restart
```

### 方案 2：使用 `exec` 读取沙箱文件

在沙箱环境下，用 `exec + cat` 代替 `read`：
```bash
cat "/workspace/AI 创作中心/.../文件.md"
```

### 方案 3：将文件复制到 host 工作区

```bash
cp "/workspace/AI 创作中心/..." "/root/.openclaw/76d362d5-0552-4b79-8d05-ce0bbb885d9c/"
```

---

## 💡 建议

**最佳实践**：在 `openclaw.json` 中配置：

```json5
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "non-main",
        "workspaceAccess": "rw",  // 允许文件工具访问 /workspace
        "scope": "session"
      }
    }
  }
}
```

这样 `read` 工具就可以直接访问 `/workspace/...` 路径下的文件了。

---

**需要我帮你检查或修改配置文件吗？** 或者你有权限访问 host 端的 `~/.openclaw/openclaw.json` 吗？

## AI处理／结果

来源消息组：a_897971afea7dacb2db

看到你的配置了！问题找到了：

## 🔍 配置分析

你的配置：
```json5
"sandbox": {
  "mode": "non-main",  // ← 只对非主会话启用沙箱
  "workspaceAccess": "rw",
  "scope": "agent",
  ...
}
```

但 `sandbox explain` 显示：
```
mode: off
workspaceAccess: none
runtime: direct
```

## ⚠️ 问题根因

**当前会话是主会话 (main session)**，而你的配置是 `"mode": "non-main"`，所以：
- 主会话 → **沙箱关闭** (`mode: off`)
- 非主会话 → 才会启用沙箱

但附件上传到了沙箱的 `/workspace`，而 `read` 工具尝试访问 host 路径，导致不匹配。

---

## ✅ 解决方案

### 方案 1：修改为所有会话都启用沙箱

```json5
"sandbox": {
  "mode": "all",  // ← 改为 "all"
  "workspaceAccess": "rw",
  "scope": "agent",
  ...
}
```

然后重启 Gateway：
```bash
openclaw gateway restart
```

### 方案 2：主会话也使用 exec 读取

保持现有配置，但在主会话中用 `exec` 读取沙箱文件：
```bash
cat "/workspace/AI 创作中心/.../文件.md"
```

### 方案 3：强制主会话也使用沙箱

```json5
"sandbox": {
  "mode": "all",  // 所有会话都沙箱化
  "workspaceAccess": "rw",  // 允许访问 /workspace
  ...
}
```

---

## 📌 为什么 `workspaceAccess: "rw"` 没生效？

根据文档，`workspaceAccess: "rw"` 只在 **沙箱启用时** 才有效：
- `mode: "non-main"` + 主会话 → 沙箱关闭 → `workspaceAccess` 不生效
- `mode: "all"` + 任何会话 → 沙箱启用 → `workspaceAccess: "rw"` 让 `read` 工具可以访问 `/workspace/...`

---

## 💡 推荐配置

如果你想让 `read` 工具在所有会话中都能访问 `/workspace` 下的文件：

```json5
"sandbox": {
  "mode": "all",  // 所有会话启用沙箱
  "workspaceAccess": "rw",  // 文件工具可访问 /workspace
  "scope": "agent",
  "docker": {
    "image": "python-node22:1",
    "readOnlyRoot": false,
    "network": "bridge",
    "user": "0:0",
    "binds": [
      "/opt/openclaw-shared-skills:/opt/openclaw-shared-skills:ro,z",
      "/opt/shared-workdspace:/opt/shared-workdspace:ro,z"
    ],
    "dangerouslyAllowExternalBindSources": true
  },
  "prune": {
    "idleHours": 48,
    "maxAgeDays": 7
  }
}
```

---

**你想修改配置吗？** 如果需要，我可以帮你编辑 `openclaw.json` 文件。或者你更倾向于保持现有配置，只在需要时用 `exec` 读取沙箱文件？
