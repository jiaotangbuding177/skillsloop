# conv_b15887780f3c:learn01：天眼查接入初始化

会话：conv_b15887780f3c

本轮可学习：手工API Token不可用时查官方CLI与设备OAuth流程，授权后先验证连通性再查企业详情，不能以安装完成代替查询可用

原文依据：Device Flow 登录（OAuth，不需要手动输 Token）

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 用户需求／反馈

来源消息组：u_638016e97102aba036

怎么配置天眼查 API Token

## 用户需求／反馈

来源消息组：u_cb035956b5f2b1c1a0

怎么配置天眼查 API

## 用户需求／反馈

来源消息组：u_b6654846560c817fd5

帮我配置天眼查 API

## 用户需求／反馈

来源消息组：u_db596dbb5b26c0faef

好了

## AI处理／结果

来源消息组：a_8cee59e8d6acf6223b

找到官方配置方式了。天眼查有完整的 CLI + MCP 接入方案，两种方式：

---

## 方式一：CLI + Skill 模式（推荐）

安装天眼查官方命令行工具，通过 OAuth 授权登录。

### 第 1 步：安装 tyc-cli

```bash
npm install -g tyc-cli
```

### 第 2 步：Device Flow 登录（OAuth，不需要手动输 Token）

```bash
tyc login --no-open --no-block
```

会返回一个授权链接和 6 位授权码。你把授权链接在浏览器中打开，输入授权码完成授权后告诉我，我再执行：

```bash
tyc login --resume
```

### 第 3 步：验证

```bash
tyc company companies "上海胆大求索科技有限公司" --md
```

---

## 方式二：MCP 模式（配置到 .mcp.json）

如果客户端支持 MCP，直接配到 `/workspace/.mcp.json`：

**OAuth 模式（推荐）：**
```json
{
  "mcpServers": {
    "tyc-mcp": {
      "url": "https://mcp.tianyancha.com/"
    }
  }
}
```

**API Key 模式：**
```json
{
  "mcpServers": {
    "tyc-mcp": {
      "url": "https://mcp.tianyancha.com/",
      "headers": {
        "Authorization": "你的API_KEY"
      }
    }
  }
}
```

---

**建议走方式一（CLI + OAuth 登录）**，不需要手动申请 API Key，浏览器授权即可。你想试哪个方式？

## AI处理／结果

来源消息组：a_ee4bd5ee0ea78154e7

✅ **登录成功！** 验证一下连通性：

## AI处理／结果

来源消息组：a_0e8e45a167bc3cea98

连通成功！再查一下详细工商信息：
