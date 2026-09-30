# 实施记录：KM v1 全链路适配

## 018当前结果（2026-09-20）

按用户“尽量复用KM v1，继续完成全链路”的要求，已接通本仓从会话证据到技能使用后更新的完整业务路径。详细流程、开关、接口边界见[V1_ADAPTATION.md](V1_ADAPTATION.md)。下面017记录保留作历史，不再代表当前状态。

- **采集／任务：** 普通会话受理、准备失败、终态与心跳；丢失租约标记DISCONNECTED而不重执行业务；明确续作引用上一完整回合，提议与肯否反馈作保守关联；自动封口、迟到重开，未验证任务正常处理。
- **本地决策：** NEW／UPDATE／SUPPORT／DEFER；精确方法签名包含方法内容，不能仅凭目标相同丢掉新方法；固定候选输入和包hash，来源删除／变化会阻止继续采用过期证据。
- **v1生成：** 专用草稿key、原creator及原格式校验；禁用本链路自动市场修复和流重发；失败只恢复已有草稿。NEW／UPDATE共享数据库控制的外层派发额度。
- **采纳与演化：** 完整包冻结，个人UPDATE采纳前比对原包、逐实例写回和读回验证；支持部分失败重试与撤销恢复；真实加载包记录hash和PROMPT_INJECTED，继续积累使用反馈。
- **组织与兼容：** 组织提审读取冻结包，验证真实submission及hash，审核权限沿用原流程；零新表、不新增会话界面操作。组织技能改进先形成个人草稿供提审，不自动覆盖组织原条目。

### 实际验证

| 检查 | 结果与证据边界 |
| --- | --- |
| 范围内软件回归 | **143项通过，0失败、0跳过**；含任务规则、原分析／涌现回归、包格式／组织版本及Zclaw测试 |
| PostgreSQL真实集成 | 旧HEAD schema→017迁移→018迁移，在隔离PostgreSQL16执行；并发封口／发现、额度竞争、候选与草稿恢复通过 |
| v1适配测试 | 使用两实例接口替身，调用真实本地适配代码；NEW→采纳→SUPPORT→UPDATE→部分写失败→恢复→撤销、组织冻结包入口和隐藏草稿校验通过 |
| Prisma | schema validate、client generate通过；没有新增表 |
| Git diff | 空白检查通过；未提交／推送 |
| API全量类型检查 | **未通过**，仅报既有范围外 `relation-space/relation-data-plane-gateway.service.ts:225` 的 `anchorNodeIds`／`anchorNodeId`不匹配；本次修改文件未报类型错误 |
| 真实KM／生产 | 未连接真实KM执行creator，未迁移生产数据库或部署，未做论文效果实验 |

完整回归命令（cwd=`apps/api`）：

```powershell
# SKILL_TRACE_TEST_DATABASE_URL仅指定隔离的本地trace_test库；不填写则数据库用例会跳过。
node --import tsx --test --test-reporter=spec "src/skill-analytics/*.test.ts" "src/skill-emergence/*.test.ts" src/skills/skill-submission-version.util.test.ts src/skills/skill-zip.util.test.ts src/zclaw/zclaw-hidden-orchestration-skill-injection.test.ts src/zclaw/zclaw.stale-streaming-convergence.test.ts src/zclaw/zclaw-trace-packaging.test.ts
```

当前v1读→写→读回不是远端原子CAS；应用隐藏不是运行时沙箱；外层调用额度不控制KM内部多轮tokens。上述限制已经写进有效规格，不再以新增远端API作为完成本地链路的前置要求。减少无效skills、保留有效能力及总模型成本不增加仍是待观察的目标。

## 017历史实施记录

2026-09-20，研究轮次017。分支 `feature/20260920/skills-trace-upgrade`。已开始代码实现；**这不是完整技能生成／演化闭环的交付声明**。

## 当前已写入代码

| 部分 | 改后行为 | 源码 |
| --- | --- | --- |
| 对话收尾采集 | 普通用户对话无论是否选择skill，均可进入v2采集；保留每次技术运行的runId及上游工具状态；内部hidden调用排除 | `apps/api/src/zclaw/zclaw.service.ts` |
| 证据适配 | 技术完成不写业务SUCCESS；纯进度／简短澄清不当成交付；技能选择仅记SELECTED；清洗原文、记录截断和原内容hash | `skill-analytics/skill-conversation-evidence.ts`、Recorder |
| 规则核心 | R0幂等、独立目标优先、精确引用、明确续作、对象lineage、暂定新任务和歧义pending；不调用模型 | `skill-analytics/skill-task-trace.ts` |
| 修订与结束 | OPEN／SETTLING／SEALED、稳定期／空闲封口、迟到重开、旧稿累计引用；封口不改变事实hash，不推定用户接受 | 同上 |
| 持久化 | 原Observation、Snapshot扩展；同owner事务锁、追加task修订、isCurrent投影、精确引用GIN索引和留存期限 | `skill-task-trace.service.ts`、Prisma schema／迁移 |
| 直接分流核心 | 无使用记录可NEW；已用且唯一、基准可知才UPDATE；选择／实际使用不明或多个目标不明则DEFER | `learningRoute` |
| 调度和隔离 | 原Processor周期自动封口；旧逐问答处理限定processingVersion=1；v2不送旧共享workflow／creator | Processor |

服务当前在同一短事务内完成采集与关联，不调用外部服务，不引入异步任务claim。使用企业×用户的事务锁串行同一owner的跨会话关联和封口，避免裸max(revision)+1。任务事实历史只追加；旧修订的isCurrent投影允许更新。若未来拆成异步worker，仍需按SPEC补sourceRevision claim和fencing。

用户请求幂等来源采用`user-request:<requestEventId>`命名空间。相同来源的新技术运行合并runs并增加来源修订；相同事实重放不增加修订。旧业务次数不随重试和封口增加。

## 开关与迁移

- 默认不开启v2。唯一接受值：`SKILL_EMERGENCE_TRACE_MODE=capture`。
- **capture是仅采集模式，不是双跑／影子模式：新会话进入v2后不会继续走旧逐问答生成，当前也不会由v2生成新候选。** 不把暂停生成算作“降低无效skills”的效果。
- 沿用原分析总开关及周期；可配置`SKILL_EMERGENCE_TRACE_SETTLE_MS`（默认120000）、`SKILL_EMERGENCE_TRACE_IDLE_MS`（默认1800000）。这些不是已验证最优值。
- 迁移：`packages/db/prisma/migrations/20260920090000_skill_task_trace_capture/migration.sql`，零新表；包含部分唯一索引和任务修订必填约束。
- **新API部署前必须先迁移数据库，即使capture关闭也一样。** 本轮仅生成迁移和Prisma客户端，没有执行数据库迁移、连接生产库或部署。
- 回退开关阻止新v2采集，不将已有v2记录改成旧pending，不重放原业务。迁移回滚和旧版本清理行为仍需隔离数据库验证，不能直接删列。

## 明确未完成

1. 当前接入点是流处理finally。请求受理、进入流之前的准备失败、进程突然退出前的中间事件尚未持久化；不能声称运行埋点全覆盖。
2. 普通会话适配器当前提供保守词法意图，不解析可信跨消息／产物引用、lineage或模型proposal。核心函数接受这些结构化输入，但生产适配尚未接通；多个候选续作保留pending。多目标拆分、关系撤销和pending后续消歧待做。
3. 任务正文仍通过受控来源样本保存；超长正文有截断标记。后续完整LearningInput、方法单位、SUPPORT与条件去重、同基准合批、候选失效未完成。
4. 新服务未接入creator。预算预留／结算、隔离草稿、候选NEW／UPDATE字段、版本条件发布、组织snapshot提交均未实施；原技能包与组织审核流程未改。
5. 词法信号只用于提名和暂存，不是“正确识别所有有价值任务”的证明；真实会话召回、有效方法保留、skills数量和模型资源收益均未测量。
6. 事务锁、部分索引、迁移兼容和多实例并发尚未在真实PostgreSQL实例测试。当前服务测试使用事务替身，不能代替数据库测试。

## KM外部服务依赖

用户在本轮确认：**KM Agent由其他服务实现，当前没有其源码。** 本仓仅定位到客户端，因此不能通过修改客户端声称远端已经支持以下能力：

| 待对接能力 | 没有该能力时的行为 |
| --- | --- |
| EXT01：执行幂等、底层调用／tokens上限、完整usage和可查询终态 | 不开放宣称硬预算有保障的creator生成 |
| EXT02：只返回完整草稿包，不安装正式key | 不开放UPDATE自动封装 |
| EXT03：NEW expectedAbsent、UPDATE expectedRevision/hash原子写及操作回执 | 不用“先GET后PUT”冒充条件发布 |
| EXT04：完整同版本包读取及实际加载／使用收据 | SELECTED保持未解析，不伪造实际版本或归因 |

这些是对接要求，不是已存在端点。D04预算比较基准、D05自动采纳策略也仍未确认；没有填造默认额度或自动覆盖策略。

## 验证

- 原三组基线：17项通过。
- 新增22项测试；扩展到skills分析／涌现、包格式／组织版本和相关Zclaw回归，共**128项通过、0失败、0跳过**。
- Prisma schema validate及client generate通过；schema-only迁移生成通过。
- `git diff --check`通过。
- API全量`tsc --noEmit`**未通过**：未修改的`relation-space/relation-data-plane-gateway.service.ts:225`把`anchorNodeIds`传给仅声明`anchorNodeId`的`FocusSubgraphRequest`。本轮已构建workspace关系契约依赖后复查，仍为此错误；本次修改文件未报告类型错误。不把全量检查列作通过。

回归命令（cwd=`apps/api`）：

```powershell
node --import tsx --test --test-reporter=spec "src/skill-analytics/*.test.ts" "src/skill-emergence/*.test.ts" src/skills/skill-submission-version.util.test.ts src/skills/skill-zip.util.test.ts src/zclaw/zclaw-hidden-orchestration-skill-injection.test.ts src/zclaw/zclaw.stale-streaming-convergence.test.ts
```

本轮为本项授权使用开发入口和TDD技能。环境脚本要求的永久开发hook未安装，因为它会扩展项目默认科研模式；实际采用了测试先行、增量实现和范围内回归，未伪造流程检查通过。无提交、推送或部署。
