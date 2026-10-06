# conv_225bd23012eb:learn01：语音Agent配置页面定位

会话：conv_225bd23012eb

本轮可学习：Workspace Settings和具体Agent配置分开，Agent ID应从具体Agent页面地址识别；找不到ID时先纠正页面层级，不能在Webhook或Secrets设置里反复找。

原文依据：看到了！你现在停错层级了——这是 **Workspace Settings（工作区设置）**，里面是 Webhook、Secrets 这些全局配置，**Agent ID 不在这里**。

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：原始时序未独立核验；附件与产物字节未提供；方法适用性及任务结果未独立验收

## 用户需求／反馈

来源消息组：u_470a98b3de449e6b58

我现在需要ElevenLabs → ElevenAgents → 创建 Agent → 拿到 Agent ID，看到附件页面，该如何操作？
[附加文件: image (15).png (/workspace/对话附件/image (15).png)]

## 用户需求／反馈

来源消息组：u_391bc113c2fa006d0d

我找不到ID在哪儿

## 用户需求／反馈

来源消息组：u_d7844f7ef3e7be22d3

setting里面是这样的
[附加文件: image (18).png (/workspace/对话附件/image (18).png)]

## 用户需求／反馈

来源消息组：u_2df471de2f154a04bf

https://elevenlabs.io/app/agents/agents/agent_4201m1xhzhfqeds865be0h8kngmd?branchId=agtbrch_8901m1xhzks8f5xshy8e62v1gvzv

## AI处理／结果

来源消息组：a_683f2d9748c115eaa5

看到了！你现在停错层级了——这是 **Workspace Settings（工作区设置）**，里面是 Webhook、Secrets 这些全局配置，**Agent ID 不在这里**。

**正确路径：**

1. 看截图左侧菜单，往下找 **Agents** 下面的 **「My Agent」**（在 Configure 上方那行），**点它** 回到你的 Agent 页面
2. 进入 Agent 页面后，**看浏览器地址栏**：
   ```
   https://elevenlabs.io/app/agents/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```
   `agents/` 后面那串 UUID **就是 Agent ID**
3. 如果左侧没有 "My Agent"，就点菜单顶部的 **Agents**（回列表）→ 点开你的 agent 卡片 → 同样看地址栏

**怎么确认找对了：**
- Agent 页面里应该能看到 **Configure（配置）、Knowledge Base、Tools、Voices** 这些标签——这些是 agent 专属设置
- 你现在截图里的 **Workspace Secrets、Auth Connections** 这些是工作区级的东西，说明你点的是底部那个 **Settings**（工作区设置），不是 agent 设置

找到 Agent 页面后把地址栏 URL 发我，我帮你确认哪段是 ID ✅
