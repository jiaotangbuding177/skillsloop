# Skills 链路升级实施计划

## 018执行更新

本地v1适配已实现：任务采集与重建→规则分流→冻结输入→共享派发额度→原creator→完整草稿→个人采纳／原组织提审→使用证据回流。按用户最新要求不再等待新增远端API，采用[V1_ADAPTATION.md](V1_ADAPTATION.md)的分实例恢复与能力边界。以下“未实施”及阶段远端依赖为016历史规划；当前进度以IMPLEMENTATION/TODOLIST的018更新为准。生产迁移、真实KM联调和效果观察尚未执行。

日期：2026-09-20｜待决策收敛的开发计划，未实施。

## 目标与范围

在现有链路上，将“单问答完成→指纹→聚类→生成”升级为“运行事实→可修订任务→资格与增量判断→预算内生成或更新→显式发布→真实使用回执”。减少无效和重复产物，同时保留有用方法；模型消耗不通过增加分析器、修复或隐含重试扩张。

包含：skill-analytics、skill-emergence、skills库与提交／版本服务；Zclaw请求、工具、产物、技能加载的最小采集与发布适配；AgentRuntime中本链路的建模／usage接口；相关DB模型和skills页面。D02已确认：模型在原对话提出必要澄清，后台据反馈标记，不新增会话界面操作。

不包含：通用聊天重构、权限体系重建、组织成员功能扩展、计费系统改造、其他Agent算法、历史库自动清理、全量历史对话重新生成、Trace2Skill复现、论文实验。

## 前后变化

| 当前 | 升级 |
| --- | --- |
| completed且未选skill才入观察，默认SUCCESS | 用户运行均可采集；选择／加载／技术状态／业务结果分开 |
| 问答对和session消息数驱动分析 | 运行片段按ID，任务跨回合关联，独立任务计频 |
| 逐观察模型指纹 | 本地特征索引；不确定待关联，不新增模型判别请求 |
| SUCCESS与频次可单独放行 | 自动封口；目标、证据、可复用增量共同决定资格，未验证正常处理 |
| 企业共享workflow可含多用户材料 | 同表内v2按用户分区；用户提交、组织审核后的skill才跨成员复用 |
| 聚类workflow随当前数据变化 | 候选固定任务修订集合、工作流与基准包 |
| 使用skill的会话不进入演化 | 按实际已用skill归因；SUPPORT不改版，UPDATE合批 |
| 封装先写个人正式目录再隐藏 | 生成隔离草稿，采纳才发布；拒绝不影响正式版 |
| 外层job数／billing摘要 | 底层请求、内部修复、重试和未终止请求统一核算 |

## 分阶段交付与先后约束

| 阶段 | 改动 | 交付与退出条件 | 依赖 |
| --- | --- | --- | --- |
| P0 冻结契约 | 完成grill、确认runtime能力、固定测试夹具与迁移契约 | D01—D05及事实依赖明确，SPEC与TEST一致 | 当前准备 |
| P1 数据与运行证据 | 扩展Observation／Snapshot，补用户请求、终态、工具关联、实际skill加载回执 | 可采集失败／未知／使用skill任务；旧数据可读；幂等与迟到事件正确 | P0数据契约 |
| P2 本地任务重建 | 新纯函数关联器＋作用域索引／存储接口、自动封口与重开；替换模型指纹 | R0—R6和去噪可解释；无用户验收正常封口；重试／改稿不重复计频；trace模块0 LLM | P1；D02、D03已定 |
| P3 资格、增量与预算 | 统一Scheduler／Evaluator／Gate，来源哈希，NEW／UPDATE／SUPPORT／DEFER；统一预算适配 | 无额度不执行；无增量不封装；底层usage不可观测时模型路径不开启 | P2；D01、D04 |
| P4 受控提炼与草稿 | 批量方法提炼、统一学习契约、隔离完整包、内容增量检查 | 原格式校验通过、证据完整、无关有效步骤／文件保留 | P3；runtime隔离能力 |
| P5 发布与闭环 | NEW条件创建／UPDATE条件更新、组织候选绑定审核、版本加载回执、前端状态 | 拒绝不伤旧版，冲突不覆盖，组织权限不扩大，加载版本可核实；在途发布遇纠正如实记录 | P4；D05 |
| P6 兼容与启用准备 | 新旧读写切换、关闭后台生成开关、留存与恢复、回归验收 | 所有P0行为用例通过，开关可收回，未决外部依赖清零 | P1—P5 |

P1／P2可先具备采集和本地处理能力，但不以它们冒充完成演化。模型路径必须等预算控制和草稿隔离就绪后启用。阶段不是另开项目，所有阶段属于同一skills闭环。

## 代码落点

以下是范围白名单；新文件名是拟议，不表示已有。

| 落点 | 职责 |
| --- | --- |
| `packages/db/prisma/schema.prisma`及对应迁移 | 只扩skills相关表字段／索引／约束；复用既有模型 |
| `apps/api/src/skill-analytics/skill-emergence-recorder.service.ts` | 来源幂等、运行引用、sourceRevision、脱敏与快照类型 |
| `apps/api/src/skill-analytics/skill-emergence-processor.service.ts` | 修订claim／完成、任务存储调用、删去v2逐问答模型指纹 |
| 拟增 `apps/api/src/skill-analytics/skill-task-trace*.ts` | 纯关联规则、规范化引用、任务修订存储；不得直接调用LLM |
| `apps/api/src/skill-emergence/skill-emergence.scheduler.ts`、`skill-emergence-evaluator.service.ts`、`skill-emergence-gate.ts` | 按任务／证据调度、共同门禁、直接分流、scope隔离 |
| `apps/api/src/skill-emergence/skill-emergence.constants.ts` | v2契约／状态／提示输入字段；旧常量兼容 |
| 拟增本模块 `skill-emergence-learning-contract.ts`、`skill-emergence-budget.service.ts` | 校验学习输入输出、预算预留／对账 |
| `apps/api/src/agent/agent-runtime.ts` | 本链路批量建模输入、usage／请求ID／限额；不改其他Agent行为 |
| `apps/api/src/skill-emergence/skill-emergence-packaging.service.ts`、`skill-emergence.controller.ts` | 冻结候选、隔离封装、证据详情与动作接口 |
| `apps/api/src/skills/`中个人版本、提交和包处理服务 | 明确目标／基准、完整包发布、组织审核与实际版本加载 |
| `apps/api/src/zclaw/zclaw.service.ts`、相关runtime客户端及DTO | 仅新增技能事件适配、草稿／usage／版本接口；不得顺便重构通用消息与计费 |
| 现有skills候选列表／详情、API类型 | 展示NEW／UPDATE、验证状态、固定证据、差异、冲突与待处理原因 |

## 数据迁移与旧链路切换

1. 增量扩字段，旧Snapshot标记`legacy_sample`，旧结果注明`legacy_completion_inferred`；不把历史SUCCESS升级为客观验收。
2. 给旧reader显式kind过滤；新task修订走追加路径，禁止旧upsert写入它。
3. 同一Observation按`processingVersion`只归一个处理器；双读不等于双模型执行。先关闭v2模型开关做本地采集，再替换原指纹调用。
4. 调整Snapshot外键／保留规则前明确删除行为；用户删除后失效引用不再用于提炼，合法留存边界不被快照绕过。
5. 已待审legacy候选只沿用其NEW语义，不能推定UPDATE基准；切换时冻结可用证据，证据不足标明legacy，禁止虚构。
6. 只从新增采集开始；历史回填限确定字段，不调用模型。全量历史回算不在首版范围。

## 停用与恢复

- 开关分别控制v2采集／本地处理／模型生成／发布。停止生成后保留待办状态及已正式可用技能。
- 发生预算失控、候选证据串作用域、基准版本冲突或隔离失败时停止相关新作业；前台已发布技能保持原加载流程。
- 已发出而未确认终止的模型请求不得释放预算后立即重试；启动恢复先对账／收回lease。
- 数据库不通过删除新字段或任务修订来回退。运行旧writer时不能让它把v2记录重新走旧模型流程。
- 发布中断按幂等操作与回执恢复；不以“删除临时文件”代替确认正式文件是否已更换。

## 验收口径

TEST中的数据正确性、权限、幂等、版本、预算和兼容行为是软件验收。无效技能是否真实下降、有效能力是否保留是产品效果目标，不能由单元测试或少生成自动证明。本轮不设置论文实验或凭空承诺下降百分比。
