# conv_8fa8be214b9b:learn01：企业查询服务的认证故障隔离与数据来源区分

会话：conv_8fa8be214b9b

本轮可学习：遇到身份校验失败先确认官方接口凭据，公开搜索只能作为明确标注的回退来源；认证配置修改后先验证连接再查工商、股东和知识产权，避免把搜索内容冒称官方回执。

原文依据：MCP 接口返回"身份凭证校验失败"，可能该 Key 还未在企查查开放平台激活或有额度限制。

这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。

边界：历史执行顺序未核准；任务成功及新任务复用收益未独立验证

## 用户需求／反馈

来源消息组：u_5e8e375d89e0ca9091

请将 API Key：***HEX*** 配置进.mcp.json 中的 YOUR_QICHACHA_API_KEY
然后重启网关

## 用户需求／反馈

来源消息组：u_8f87d584f76229bbc9, u_13b931875e90c3fb66

使用企查查查询上海胆大求索科技有限公司的工商信息

## 用户需求／反馈

来源消息组：u_4e274ff672874a7666

请配置企查查MCP
{

  "mcpServers": {

    "qcc-company": {

      "url": "https://agent.qcc.com/mcp/company/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-risk": {

      "url": "https://agent.qcc.com/mcp/risk/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-ipr": {

      "url": "https://agent.qcc.com/mcp/ipr/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-operation": {

      "url": "https://agent.qcc.com/mcp/operation/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-executive": {

      "url": "https://agent.qcc.com/mcp/executive/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-history": {

      "url": "https://agent.qcc.com/mcp/history/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-legal-regulation": {

      "url": "https://agent.qcc.com/mcp/regulation/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-legal-case": {

      "url": "https://agent.qcc.com/mcp/case/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-document": {

      "url": "https://agent.qcc.com/mcp/document/stream",

      "headers": {

        "Authorization": "Bearer [隐藏]"

      }

    },

    "qcc-document-mcp": {

      "command": "npx",

      "args": [

        "-y",

        "qcc-document-mcp"

      ],

      "env": {

        "QCC_DOCUMENT_AUTHORIZATION": "Bearer [隐藏]"

      }

    }

  }

}

## AI处理／结果

来源消息组：a_ff9dbfc6e8964cc477

MCP 接口返回"身份凭证校验失败"，可能该 Key 还未在企查查开放平台激活或有额度限制。我先用 CLI 模式查询：

## AI处理／结果

来源消息组：a_54d5cb48846d5258d2

综合所有数据，以下是查询结果：

---

## 📋 上海胆大求索科技有限公司 — 工商信息

> ⚠️ **MCP 状态**：返回 `"身份凭证校验失败"`（错误码 100004），说明该 API Key **尚未在企查查开放平台激活**或已过期，需前往 [openapi.qcc.com/mcp](https://openapi.qcc.com/mcp) 确认。

以下信息基于公开搜索汇总：

### 基本信息
| 项目 | 内容 |
|------|------|
| **企业名称** | 上海胆大求索科技有限公司 |
| **成立时间** | 2020 年 |
| **注册资本** | 100 万人民币 |
| **所属行业** | 软件和信息技术服务业 |
| **经营状态** | 存续 |
| **企业类型** | 有限责任公司 |
| **注册地址** | 上海市 |

### 核心人物
| 项目 | 内容 |
|------|------|
| **法定代表人 / CEO** | **张琰彬** |
| — 其他身份 | 华东师范大学数据科学与工程学院研究生导师 |
| | 英特尔 AI Leader Coach |
| | OpenEduTech 实验室创始人 |

### 知识产权
| 类型 | 数量 | 详情 |
|------|------|------|
| **专利** | 4 条 | 含 "面向行业评估的多智能体协同任务分解与执行系统"（CN122242554A，2026年3月申请） |
| **商标** | 5 条 | — |
| **著作权** | 待查 | — |

### 对外投资
- 对外投资了 **1 家企业**

### 参考链接
- 🔗 [企查查](https://www.qcc.com/web/search?key=上海胆大求索科技有限公司)
- 🔗 [天眼查](https://www.tianyancha.com/search?key=上海胆大求索科技有限公司)
- 🔗 [专利新闻](https://m.sohu.com/a/1038720999_114984)

---

### 关于 MCP Key 的问题

你提供的 Key `***HEX***` 被企查查 MCP 网关拒绝。可能的解决办法：

1. **去企查查开放平台确认**：访问 [https://openapi.qcc.com/mcp](https://openapi.qcc.com/mcp) → 查看"我的接口"中 MCP 的 Key 是否正确
2. **首次使用需要先开通**：在开放平台找到 **MCP 服务** → 点击**申请开通** → 完成实名认证后才生效
3. **检查 Key 是否过期**：如果是从旧项目复制的 Key，可能已过期或被重置

如果需要，我可以帮你搜索更多关于这家公司的详细信息。

## AI处理／结果

来源消息组：a_7523e5adc2d63cea13

先验证一下连接的可用性：
