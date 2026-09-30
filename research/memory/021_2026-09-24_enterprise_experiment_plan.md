# 021 企业个性化Agent、真实模型配置与可执行实验计划

日期：2026-09-24；承接[020](020_2026-09-24_live_agent_paper_plan.md)。

## 用户已确认

- 提供阿里云Coding Plan Anthropic兼容服务凭据，授权接通真实模型消费；凭据不记录于本文件。
- 企业Web应用已有InsightWeaver，当前不接入；按接入后的员工个性化技能与持续改进Agent设计方案。此为场景假设，不是新增算法部署证据。
- 其余工作需详细可落实计划，尤其实验；用户可提供真实企业会话数据库和评估。数据位置、字段覆盖、验收含义及外部模型处理授权尚未确定。

## 本轮工作与证据

- 再读研究入口、章程、状态及020记忆，使用research-experiment-compass。按本项目完整生命周期范围应用，不套用其他项目生成侧/SOTA限制。
- 阅读本地Prisma的会话、消息、涌现观察/快照/候选、技能使用、组织审核版本、个人配置、产物和工时字段；整理实际表名与缺口。生产schema版本仍须与导出核对。
- 交付[详细执行计划](../reports/021_execution_plan.md)、[数据库与评估交接清单](../reports/021_data_handoff.md)、[可填写模板](../templates/021/README.md)。模板为空，不是合成实验数据。
- 文档相对链接检查通过；三个CSV模板可解析。未修改InsightWeaver业务代码，未连接生产数据，未开展正式企业实验。
- 已在本机demo被忽略的.env配置端点、anthropic-messages和qwen3.7-plus（官方示例的临时默认，用户未指定模型名），密钥不输出、不入研究制品。
- 初次原生OpenClaw通路失败：事件表记录assistant stopReason=error，errorMessage=fetch failed。无有效模型回答，不视为算法失败。默认代理TLS连接失败，沙箱内直连出现WinError10013。随后授权网络环境下仅重试无企业内容的控制技能；最终状态在下节补记。

## 关键洞察

**源码观察：**SkillUsageEvent缺完整版本hash和读取回执；GeneratedArtifact只有文件元数据；PersonalSkillConfig不保存完整技能包；HumanEfficiencyEvent.savedHours的计量来源不能由schema证明。不能把有字段等同于有可靠评测证据。

**方案建议：**增加个人偏好摘要强基线，排除只是记住风格的解释；历史反馈若针对旧回答，不能直接当作对新模型答案的在线反馈。先测后学、冻结库、独立新任务和保密审计集均保持。方法保留按独立有用方法计数，不按skill个数。

**设计假设：**少量规则任务轨迹与增量更新可能同时改善资源和个性化效果，尚无企业实证。完整应用设想可用于设计，但不允许将独立原型写成生产上线。

**服务观察：**[官方Coding Plan](https://help.aliyun.com/zh/model-studio/coding-plan)描述套餐使用和数据处理边界；[官方配置](https://help.aliyun.com/zh/model-studio/claude-code)给出Anthropic端点和qwen3.7-plus。小型用户触发控制测试与正式批量/多人企业实验不同，后者需合适服务和明确处理授权。没有企业数据外发。

## 待用户提供与下一步

首先提供DDL/数据库类型、本地导出路径、10—20个完整会话及评估定义；不要求生产密码或全量库。可先仅允许本地审计。再根据真实分布选择任务族、独立验收、运行预算和正式样本量。本轮已发异步交接问题，尚待答复。

本轮无新增企业效果实证发现；调用失败和通路成功均不能替代方法效果证据。更新README与STATE，保留020“未配置”作为历史状态。

## 真实通路最终状态

- 真实qwen3.7-plus产生2条模型响应：先调用read读取指定SKILL.md，再输出只在文件中出现的随机校验码。原生transcript支持`modelSkillControlPassed=true`。模型报告输入12、输出494、缓存读取4954、缓存写入5264，总tokens10724；这是服务usage汇总，不是实际现金账单。
- 但CLI在模型stop之后未在外层时限内正常退出，记录`cliCompletedNormally=false / UNKNOWN_TIMEOUT`，没有把该运行冒充正常完成。失败原记录：`enginering/demo/artifacts/live/live-failure-db956427ab.json`；从原生事件恢复、不含模型思考内容的证据：`enginering/demo/artifacts/live/live-7294d214f89f-recovered-evidence.json`。
- 已定位为模型最终响应之后的CLI返回/收尾异常，但未定位到具体清理函数。只读查看固定版本实现发现JSON在收尾后才输出，尚不能证明某一清理步骤是根因。
- 一次有界诊断尝试增加官方`--auth-env-only`，CLI拒绝其与`--config`组合，未调用模型；记录`artifacts/live/auth-probe-failure-c6bc54a661.json`。此路线淘汰，未写入业务实现。
- 结论：真实模型技能读取和信息消费控制验证成功；可稳定返回页面的完整CLI通路仍有收尾问题。该问题列为后续P0/W0最高优先项，在解决前不开展批量论文实验。不自动重复未知运行，不隐瞒本轮负结果。
