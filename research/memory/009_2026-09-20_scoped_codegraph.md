# 轮次 009：限定源码图谱理解与 MCP 索引

日期：2026-09-20。科研模式持续有效；这是源码理解与索引工作，不是业务开发授权。

## 用户已确认的范围

用户要求使用刚安装的 CodeGraphMCP，理解并索引 engineering 目录中组织成员关系、个人／企业 skills 库、skills 涌现相关链路。用户明确其他模块不需要理解，不计划修改其他模块。实际目录拼写为 `enginering/insightweaver`。不自动展开其他模块；相关外部功能只记录接口边界。

本轮与研究主线的关系：把以前仅基于链路文档的理解，映射到当前本地实现的服务、数据实体、状态和源码入口，供后续闭环讨论定位。

## 已完成及产物

- 先读 README、CHARTER、STATE，以及 003、006、008 相关记忆。
- 建立 [限定源码图谱报告](../reports/009_scoped_codegraph.md)，包含主流程、组织成员关系、三套候选／作业／审核状态、个人与企业库关系、后续阅读入口。
- [CodeGraph 索引说明](../codegraph/README.md)、[成功快照指针](../codegraph/latest.json)、[111 文件清单与哈希](../codegraph/runs/20260920T062102167459Z/manifest.json)。
- 原始 MCP 图谱 520 节点／796 边，其中 409 条两端有对应节点；另有 [36 节点／46 关系的业务证据图](../codegraph/semantic-graph.json)，与自动 import 图分开。
- 标准 MCP stdio 实际调用 GetCodeGraph、GetSystemPrompt、GetSymbol、GetFileContext、GenerateDesignDocument，响应保存于成功快照 queries 目录。前四种能力验证成功；自动设计图很浅，未将其作为完整业务图。
- `research/codegraph/build_scoped_index.py` 生成范围副本、Prisma 投影、哈希与查询记录；`serve_scoped.py` 启动最新成功快照。项目 `.codex/config.toml` 覆盖本项目 codegraph 指向限定快照，CLI 配置解析及真实启动器查询均通过。
- 验证 111 份业务源文件在索引前后哈希一致；业务证据图的节点、边、来源文件和行号校验通过。

## 工具观察及兼容处理

当前会话工具列表没有 codegraph，故直接通过该服务器的 MCP 协议调用。FastCtx 在初始读文件后连接中断（Transport closed），后续以 rg 和明确区间的 Python 只读读取兜底。

已安装实现为 dharamhbtik/code-graph-mcp v1.1.0。真实 TS 索引首次为 0 节点：发布包沿源码布局查找 parse-js.mjs，另有 .NET stdin UTF-8 BOM 导致 Node JSON.parse 失败。通过隔离 runtime 目录满足既有相对路径，并仅在 runtime 脚本去除输入开头 BOM；原 bin 包保留。修复后真实 TS 符号、上下文与图谱查询通过，全局 MCP 可执行路径已更新。失败快照／日志保留，不作为有效索引。

MCP 的 TS 解析依然是浅层正则，会把 NestJS Injectable 标成 Angular，不完整提取方法、TSX 与多行 import；Prisma 本身不受支持，故建立明确标识的 Markdown 模型投影。不能把所有原始边当成有效调用关系。业务图依据源码人工核验。

## 证据支持的观察

1. 成员关系由 EnterpriseMembership 连接 User／Enterprise。membership.department 为名称字符串；部门、小组、小组成员另有模型。小组成员 userId 是标量，不是显式 User 外键。
2. 个人库主键包含 enterpriseId/userId/skillKey；企业配置是 enterpriseId/skillKey。运行文件、展示配置、审核单和版本快照是不同对象。
3. 正常 run.completed 中，非隐藏且未选择 skill 的会话进入涌现观察；已选择 skill 的会话走使用统计。使用标志来自 skillIds，不代表已核验模型实际执行了技能。
4. Cluster／workflow 企业共享；候选评估、水位、覆盖、拒绝冷却按用户。路径建模按 cluster 最近最多 5 条样本取数，没有 userId 条件；不能据此推断实际发生数据污染或泄露。
5. 生成后先写隐藏个人草稿 AWAITING_CONFIRM；个人采纳使之可见；可配置自动采纳。组织提交与审核发布独立，SUBMITTED 不等于已发布。
6. 分析样本快照、个人进度、个人 revision 和组织版本均已存在；不能称系统没有快照或版本。快照的 upsert update 可改写，不能称严格不可变。
7. 当前规整 workflow 的输出字段没有包含门禁支持的全部高级信号；这只是静态接口差异，不是经过运行验证的效果结论。
8. 已核验使用统计路径未发现自动演化调用。常量中的 skill_evolution 名称不能当成已接通反馈闭环的证明。

证据位置与范围均在报告和 semantic-graph.json 中；涉及旧文档的陈述以本次具体源码为准。003、006、008 保留，不静默修改历史的“未读源码”事实。

## 假设、建议与未知

- 假设：本轮不新增算法有效性假设或创新结论。
- 建议：后续讨论或经授权开发，先按报告阅读入口定位；源码更新后检查摘要范围并重建索引，重新核验语义结论。
- 未知：部署版本、生产开关、真实用户数据与收益、KM 文件状态，以及未纳入范围的功能。没有业务运行验证或完整仓库审计。
- **本轮无新增运行实证发现。** 新增的是可追溯静态源码证据；没有接入生产会话或凭据，没有修改业务代码。

## 当前状态更新

已同步 README、STATE 和 CHARTER 的源码核验状态及限定范围。索引为静态快照，不会自动跟随原源码变化；本项目 MCP 仅查询该快照。后续开发、实验、部署、数据接入均未启动。
