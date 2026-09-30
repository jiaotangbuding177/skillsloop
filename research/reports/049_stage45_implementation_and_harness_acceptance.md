# 阶段4/5实现、真实案例验收与用户工作台

日期：2026-09-26。范围：独立 `enginering/demo`，遵循[046十二阶段契约](../contracts/046_twelve_stage_contract_user_revision.md)与[048阶段4/5交接契约](../contracts/048_stage45_handoff_contract.md)。本轮实现的是阶段4、阶段5及供后续阶段验收的个人工作台；不把一次功能验收写成企业效果实验。

**050后续审查说明：** 本报告是基于047快照、包含失败修复的分阶段开发验收；它不等于冻结当前版本后一次全新1→5运行。运行器、预算/缓存恢复及跨阶段ID等开跑阻断见[050实验前审查](050_first5_preflight_review.md)。原运行结果和失败历史保留。

## 交付与前后变化

| 项目 | 本轮前 | 本轮后及验收证据 |
| --- | --- | --- |
| 新版轨迹交接 | `task-trace-v2` 被旧学习器跳过 | 从047已验收轨迹读取来源、要求/反馈、attempt、未决项及使用依据；用途、owner、hash及预算在模型视图前检查 |
| 阶段4学习 | 旧路径按任务标题词面聚类，并以整任务结果分类 | 模型批量提出workflow轮廓、局部方法与轮廓关系；程序约束complete-link聚类；第二次批量合并为冻结workflow、方法归宿台账。UNKNOWN可以贡献有来源的方法，不伪造业务成功 |
| 阶段5生成 | 新版轨迹无生成通路 | NEW workflow进入独立OpenClaw creator会话；实际读取官方 `skill-creator` 后写出 `SKILL.md`，宿主检查覆盖/资源/内容边界并调用官方打包器，核对包内文件及hash。READY仍等待个人选择 |
| 技能使用界面 | 仅有研究后台 | `/skills`展示个人/获准组织技能及待采纳候选，支持查看、下载和采纳；`/chat`选具体版本发起真实模型对话，展示读取回执和交付文件。原后台保留在 `/` |

新版阶段4/5的逻辑流：

```mermaid
flowchart LR
  A[阶段3 当前有效TaskTrace] --> B[用途/权限/版本/证据门禁]
  B --> C[LLM提取workflow轮廓、局部方法及关系]
  C --> D[程序约束聚类]
  D --> E[LLM簇内方法合并]
  E --> F[程序校验台账、条件与来源；冻结workflow]
  F -->|NEW| G[独立OpenClaw creator会话]
  F -->|UPDATE| H[阶段9基准更新入口]
  G --> I[真实文件、官方打包及hash校验]
  I --> J[READY候选]
  J --> K[/skills个人采纳]
  K --> L[/chat选版执行与读取回执]
  L --> M[后续反馈与演化待验收]
```

代码入口：[workflow.py](../../enginering/demo/skilldemo/workflow.py)、[workflow_bridge.py](../../enginering/demo/skilldemo/workflow_bridge.py)、[creator.py](../../enginering/demo/skilldemo/creator.py)、[runtime.py](../../enginering/demo/skilldemo/runtime.py)、[server.py](../../enginering/demo/skilldemo/server.py)。新版记录仍复用 `records/events/runs` 三张表；旧schema回放和既有个人采纳、组织提交/审核流程保留。新增前端在 `enginering/demo/web/harness.*`，没有给会话增加“满意/完成”按钮。

## 038真实来源验收

从[047前三阶段隔离数据库](../cases/038_contract_multi_review/private/047-stages123-network/loop.sqlite)复制快照，阶段4只读取A/B两条生成轨迹，另外两条留出轨迹不进入提取、聚类、命名或生成。没有再次运行前三阶段，也没有用人工恢复轨迹替代模型输入。输入的历史合同/交付附件仍缺失，历史业务结果仍为UNKNOWN。

阶段4得到两条轮廓的 `SHARE_CORE` 关系，程序合为一个初始簇；归纳器从该簇产出两个范围较窄的NEW workflow，方法台账覆盖四项提议，未强制合成一个大技能。当前这是**一次案例输出**，不是“两个一定优于一个”的质量结论。阶段5从其中一个冻结workflow生成一份 `SKILL.md` 和可解包的 `.skill` 包，creator有成功读取官方说明的工具回执，包内文件与宿主声明hash一致。候选 `candidate-abcd184c56403210310a2e36` 达到READY后，由测试人员显式采纳为Alice个人库 `skill-079da6a6da354645` v1；采纳不代表企业用户真实选择。

一次creator运行先超时，记录为FAILED且用量UNKNOWN；一次显式重试生成草稿。首轮打包校验发现Windows换行导致包内字节不匹配，宿主改用二进制写入，再对**同一已完成草稿**重新校验和官方封装，没有为这一步新增模型调用。失败记录保留。私有无正文摘要见[阶段4/5验收摘要](../cases/038_contract_multi_review/private/049-stages45-acceptance/acceptance-summary.json)，技能包hash为 `9e884c19bd79b151727d545e3cf2a4ccbe42ef829a818560a51c1b736cd7abfa`。

采纳后两次真实OpenClaw对话均对个人skill v1留下 `FILE_READ` 回执。第一次缺买卖方立场，Agent追问；第二次在构造付款条款上明确买方立场，产生604字符回复和一份可下载Markdown交付文件。[后续消费摘要](../cases/038_contract_multi_review/private/049-stages45-acceptance/consumption-followup-summary.json)只证明选版、读取和文件交付，不证明法律正确、技能遵循程度或业务成功。该构造样本不是原始企业合同。交付中的法律引用和数值建议尚未经专业核验，不用于证明专业质量。

本轮完整软件回归为59项通过；本地HTTP核验了 `/`、`/skills`、`/chat`、工作台数据、技能详情及包下载，浏览器核验可见个人技能、可进入对话并选中版本。服务在[研究后台](http://127.0.0.1:8769/)与[个人技能库](http://127.0.0.1:8769/skills)、[对话](http://127.0.0.1:8769/chat)运行；此地址对应隔离验收数据，不是生产部署。

## 资源与边界

本轮新增阶段4/5有两次结构化请求、两次creator派发（其中一次超时），合计8次底层模型请求发起；可报告的三次成功run合计51,012 tokens，超时run用量缺失，现金费用未知。两次后续消费另有5次底层请求、55,190报告tokens。上述不是相对旧链路的同条件成本对照，**不能声称模型消耗至少不增加**。包数量为一份通过封装的技能，不等于“无效skills减少且有效skills保留”得到验证。

当前工作台只监听localhost，成员切换是研究用角色模拟，不是生产身份认证。creator工作区隔离不是操作系统沙箱，其工具配置仍允许主机命令执行；宿主对生成包做路径、覆盖、引用、字节和简单内容边界检查，但不能证明完全脱敏或语义正确。阶段6的企业真实采纳、阶段8/9反馈更新、阶段10/11组织审核及跨用户使用仍待独立案例验收。阶段4已经保留UPDATE精确基准的交接方向，不能把本轮NEW案例说成自进化闭环已验收。

## 可复验入口

- [Demo操作说明](../../enginering/demo/README.md)、[阶段4/5验收说明](../../enginering/demo/STAGES_45_ACCEPTANCE.md)记录命令、路径和失败历史。
- `python -m unittest discover -s tests -q` 在 `enginering/demo` 下验证程序契约；真实模型复验会产生额外消耗，应使用受控数据目录和明确额度。
- 后续阶段验收先在工作台选技能运行新任务，再把选版、读取、产物、用户反馈和技能版本绑定，不能仅凭点选判定已使用或已改善。
