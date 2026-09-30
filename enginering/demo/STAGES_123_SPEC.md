# Demo 前三阶段：当前实现契约

依据 research/contracts/046_twelve_stage_contract_user_revision.md 第5节。仅升级会话采集、任务识别、轨迹恢复；第4阶段及后续生命周期另行适配。

## 输入与输出

1. `POST /api/import-events`：actor、entries、purposeSplit、可选initialization。每个事件含 id/sessionId/role/content/sourceOrder/status；可选 responseTo/runId/sourceTimestamp/attachments。保留原事件ID和正文；缺时间不伪造。显式responseTo优先，其次唯一runId，否则助手按源顺序邻接；工具无明确关联则保留未归属。输出可回查QAPair，不做任务归属。
2. `POST /api/stages`：完整问答按同成员、同会话、同用途批量交给模型；每对得到候选任务、目标分片、OPEN/CONTINUE/RETURN/SUBGOAL/NON_TASK/UNRESOLVED及引用。程序验证来源、片段非重叠、用户文本覆盖和候选存在。信息查询也可是真实任务；本阶段不判断skill价值。
3. 模型核验候选成员，选择来源片段ID恢复反馈、要求变化、可见文本和执行声称；程序组装TaskTrace。初始要求引用首个目标片段原文，后续明确要求变化形成delta版本。输出包括非连续成员、attempts、feedbackEdges、requirementTimeline、observations、unresolved、artifactAvailability、initializationEvidence。同一回合不因多条助手进度生成几十个attempt。

来源引用只能证明原文存在，语义关系仍标 `MODEL_INFERRED_SOURCE_CHECKED`。缺合同/交付文件不伪造产物；技术done、助手声称、用户接受、业务验收分别记录。`SEALED`仅表示当前输入快照已处理，不表示用户任务成功。

## 完成与异常边界

- `source_event`、`qa_pair`、`pair_annotation`、`pair_detection`、`trace_recovery`、`front_status`等对象复用records；预算和执行复用runs，未增加数据库表。
- 重复导入幂等；同ID正文冲突拒绝。原正文为null时，可在其他元数据完全相同条件下显式设置`repairMissingContent:true`补齐，旧原事件留在source_event_history。
- 缺正文问答保留pendingPairs，不当作NON_TASK。原事件会话只读，不与在线chat/旧预配对导入混用session；这样不会把holdout历史意外加入生成会话。
- 稳定后自动处理，不加会话标记操作。相同输入和模型提示不再付费；宿主校验器版本变化会重新核验已存模型输出，模型提示变化则重新派发或等待预算，不能以结构合格绕过新的语义要求。
- detect_pairs/recover_trace计入原每用户每日共享学习预算；失败也记账。无静默模型重试，无词法兜底冒充语义识别。无效输出保存运行结果但不发布trace。
- 在模型等待期间材料变化，不覆盖新输入；已存旧trace标为SUPERSEDED。
- stage3新版trace明确标`TRACE_AVAILABLE_STAGE4_ADAPTER_REQUIRED`，旧discover跳过，防止新语义被旧CORRECT=失败规则误读。旧回放链路继续保留。

## 当前明确限制

- 当前处理单位是有界的完整session快照，并非每个session只能有一个任务。新增问答会重新识别当前session；尚未实现新schema的跨窗口增量或跨session关联。
- 阶段2总输入超过60,000字符或阶段3超过110,000字符，明确延期保留材料，不截断。长度界限是本地字符预算，不等于精确模型token界限。
- 模型错误可能通过结构检查；需要真实任务标注和独立样本评估语义准确性，不能用本次工程验收代替。
- 当前每个已归属问答至少提取一项助手观察，未承诺对所有历史助手声称做穷尽语义标注；所有助手原文仍可回查。
- 技能生成、专业正确性、企业收益与长期资源不增加不在本次验收结论之内。

## 软件验收覆盖

原ID保真、重复导入、显式回复/运行关联、孤立事件、无人工replyTo、缺正文和显式补齐、同对多目标、重复助手归属拒绝、初始化证据、holdout隔离、跨用户隔离、预算暂停/继续、无效JSON缓存不重试、输入竞态、初始要求与最终交付分开、阶段4门禁。真实模型另跑038原70事件及独立A-B-A/多目标控制，结果见STAGES_123_ACCEPTANCE.md。
