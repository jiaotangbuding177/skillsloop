# 限定范围 CodeGraphMCP 索引

只服务于 `enginering/insightweaver` 中的组织成员、个人／企业 skills 库、skills 涌现链路。业务源码保持不变。

## 从这里读

- [源码图谱报告](../reports/009_scoped_codegraph.md)：两张业务关系图、作用域、状态与源码入口。
- [semantic-graph.json](semantic-graph.json)：人工对照源码核验的 36 节点／46 关系，与 MCP 自动 import 图分开保存。
- [latest.json](latest.json)：当前成功快照的位置。
- 当前数据库：[graph.db](runs/20260920T062102167459Z/graph.db)。
- [manifest.json](runs/20260920T062102167459Z/manifest.json)：111 个源文件、原始文件哈希、摘录区间。
- [symbol-index.json](runs/20260920T062102167459Z/symbol-index.json)：MCP 节点映射回真实源码。`generated_projection=true` 表示派生文档，不是原生 Prisma 符号。
- [verification.json](runs/20260920T062102167459Z/verification.json)：520 节点，796 原始边，409 条两端可解析的边；建立快照前后源文件哈希一致。
- [queries](runs/20260920T062102167459Z/queries/overview.json)：概览、符号、文件上下文等原始 MCP 响应。

## 在 Codex 中使用

项目 [.codex/config.toml](../../.codex/config.toml) 已将 `codegraph` 指向 [serve_scoped.py](serve_scoped.py)，只启动当前限定快照。`codex mcp get codegraph` 已核对配置生效；当前会话没有动态注入新工具，重启 Codex 后可直接使用注册工具。

优先查询：

```text
GetSymbol(symbolName="SkillEmergenceProcessor")
GetSymbol(symbolName="SkillEmergenceEvaluatorService")
GetSymbol(symbolName="SkillSubmissionService")
GetSymbol(symbolName="EnterpriseService")
GetSymbol(symbolName="PersonalSkillConfig")
GetFileContext(filePath="apps/api/src/skill-emergence/skill-emergence.module.ts", hopDepth=2)
GetFileContext(filePath="apps/api/src/skills/skill-submission.service.ts", hopDepth=1)
```

MCP 返回 `scope` 中的路径是索引副本，实际阅读／修改请回到 manifest 中的 `source`，混合文件的源码行号保持一致。`SCOPED_SCHEMA.md` 是 Prisma 选定模型的 Markdown 投影，必须用其中 `Source:` 指向的原行号。

即使工具还未加载，仍可通过标准 MCP 协议查询：

```powershell
python -X utf8 D:/skillsgen-industry_track/research/codegraph/build_scoped_index.py --query GetSymbol --args '{"symbolName":"SkillSubmissionService"}' --label submission-check
```

## 刷新与范围

这是**有版本的限定快照**，不是实时跟随原代码库。MCP 的文件监视器只监视副本。源文件修改后先复核 [build_scoped_index.py](build_scoped_index.py) 的 PATTERNS 和 RANGES，再执行：

```powershell
python -X utf8 D:/skillsgen-industry_track/research/codegraph/build_scoped_index.py
```

每次生成新的 runs 子目录，保存哈希和原始 MCP 响应；全部查询与源哈希校验通过后更新 latest.json。固定行区间针对本次源码版本，源码位移时需更新区间，不能盲目刷新。semantic-graph.json 与报告为已核验的语义快照，刷新自动索引不会自动更新其中的业务结论。

纳入 skill-emergence、skill-analytics、skills 核心文件，成员／部门实现及对应控制器区段、相关前端页面和 API。混合职责文件仅保留相关片段；测试、模板体系、内置技能目录和外部模块内部逻辑不作本轮理解对象。实际精确清单以 manifest 为准。

## 本机兼容处理与可信边界

所用实现是 `dharamhbtik/code-graph-mcp` v1.1.0（MCP 自报程序集版本 1.0.0.0）。首次安装只做 Python 符号验证，未覆盖其 TS 解析。本轮在真实 TS 文件上发现并处理：

1. 发布包的 NodeProcessRunner 仍按相对上溯五级查找 `scripts/parse-js.mjs`。已复制原发布文件到独立 runtime 的预期目录布局。
2. .NET 向 Node stdin 写入 UTF-8 BOM，原脚本 JSON.parse 返回空节点与 error。本地 runtime 脚本只增加去除输入开头 BOM 的兼容处理，原 `bin/parse-js.mjs` 保留。

实际运行路径：`C:/Users/39835/.local/share/codegraph-mcp/v1.1.0/runtime/src/CodeGraphMcp/bin/Release/net10.0/CodeGraphMcp.exe`。

此处理没有改动业务仓库或第三方解析算法。原始失败快照和 stderr 保留在较早 runs 中；它们不是有效索引，不应使用。当前快照已验证 GetCodeGraph、GetSystemPrompt、GetSymbol、GetFileContext，另保存 GenerateDesignDocument 输出供比对。

解析器本身仍有局限：使用正则而非完整 TS 语义分析；把 NestJS `@Injectable` 标成 Angular；未覆盖类内方法、完整 TSX 组件及全部多行 import；部分 import 边无可解析端点。自动设计图不能替代业务调用关系。业务事实只以源码核验关系及证据为准。

本轮没有访问生产会话或凭据，没有启动应用或调用其 LLM／数据库。只运行本地 MCP 索引器和离线读取脚本。
