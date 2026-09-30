# 049 阶段4/5实现、真实封装与个人工作台

日期：2026-09-26。

## 本轮问题与用户授权

用户要求完成阶段4、5的Demo改动及逐阶段端到端验收，交付**可用skills**；当前研究台应视为后台，另提供用户可用的harness，`/skills`能看到技能库并进行真实对话，以便后续自进化验收。本项开发和受控真实模型调用获得明确授权；不意味着永久切换科研模式、自动发布组织技能或接入生产InsightWeaver。

## 产物与证据

- [049实施与验收报告](../reports/049_stage45_implementation_and_harness_acceptance.md)、[Demo验收说明](../../enginering/demo/STAGES_45_ACCEPTANCE.md)、[Demo入口](../../enginering/demo/README.md)。
- 阶段4/5源码集中于 `enginering/demo/skilldemo/workflow.py`、`workflow_bridge.py`、`creator.py`，并改动 `core.py`、`runtime.py`、`bootstrap.py`、`front_stages.py`、`recovery.py`、`server.py`。用户界面为 `web/harness.html`、`harness.css`、`harness.js`。
- 受控企业案例元数据：[阶段4/5摘要](../cases/038_contract_multi_review/private/049-stages45-acceptance/acceptance-summary.json)、[构造后续消费摘要](../cases/038_contract_multi_review/private/049-stages45-acceptance/consumption-followup-summary.json)。私有源、完整模型输出、草稿和交付内容不复制到本记忆。
- 59项Demo软件测试通过，HTTP及浏览器核验 `http://127.0.0.1:8769/skills`、`/chat`，服务使用隔离验收数据并关闭自动学习。

## 观察（已运行，限本次案例）

1. 从047已完成的两条generation轨迹进入阶段4；另外两条holdout没有进入阶段4/5。模型给两个frame提出有具体共享步骤的 `SHARE_CORE`；程序聚成一簇。方法台账覆盖四项提议，归纳器产出两个较窄NEW workflow。这是实际输出，不预设一个簇必须只有一个技能。
2. 其中一个workflow经独立OpenClaw creator会话生成真实 `SKILL.md`；有官方creator文件的成功读取回执，宿主校验与官方打包后得到可下载 `.skill`。一次creator超时和一次Windows换行字节不一致失败均留存；后者通过宿主二进制写入并重验同一草稿解决，未为重验新增模型调用。
3. 测试人员显式采纳到Alice个人库，后续两次真实OpenClaw会话选中v1且均有 `FILE_READ` 回执；第一次请求缺业务立场，Agent追问，第二次构造付款条款补充买方立场后得到文本和Markdown交付文件。企业用户真实采纳、专业质量与业务结果均未评估。
4. 阶段4/5新增两次结构化请求和两次creator派发，底层请求发起共8次；三次有用量的run报告51,012 tokens，超时run缺用量。两次消费另报55,190 tokens。未测等预算旧链路对照或现金费用。

## 决策、更正与适用边界

- 更正[048记忆](048_2026-09-26_stage45_contract_design.md)的“尚未实施”：本轮已实施并通过上述功能验收；048作为设计历史保留。047“新版TaskTrace待阶段4适配”也由本轮更正，新版现在走专用workflow路径，旧schema回放仍保留。
- `READY`是候选可采纳，不自动等于用户接受；本轮采纳是测试人员为可用性验收操作，不是企业行为数据。组织共享仍须提交和审核。
- 生成包的程序校验只保证可读、结构/引用/覆盖/字节一致等有限性质；不保证法律正确、模型遵循全部方法或完备脱敏。历史原合同与交付附件缺失，业务UNKNOWN持续保留。
- 首次creator仅开放较少工具发生超时；受控重试开放必要的本机执行工具，但工作区隔离不是OS沙箱。这个安全边界必须在后续部署设计中补齐。
- 阶段4/5真实用量并未证明用户的“模型调用至少不增加”目标；技能数量为一份通过封装，也不能证明无效skills比例下降或有效能力保留。该项目仍需独立未来任务、质量评估与成本对照。

## 后续研究问题（尚未授权为本轮完成项）

1. 如何用该harness记录真实用户后续反馈与交付验收，保证选中、实际读取、遵循和业务效果分层？
2. 阶段8/9如何在精确skill版本及方法归因下形成UPDATE候选，并做配对新旧版本验证？
3. 如何在外部合同与专业标注下验证方法有效性、条件边界和内容安全，再量化无效技能与总成本？

已同步README索引、STATE与章程授权记录；历史负结果和缺失用量未删除。
