# 第283轮：26应用演化轨迹采集方案与skills输入合同（尚未启动）

日期：2026-10-04。接续[281来源充分性](281_2026-10-04_rw_250_evolution_pool_sufficiency.md)，来源仍为26主候选＋1MacPass候补，不继续扩充。用户要求“依据这个，开始生成演化集轨迹，先给我方案和你的期望产出……会在本次产出的轨迹集上构建skills库，所以这一步很关键”。

## 用户要求与本轮完成范围

新采集工作为用户意图范围，但用户明确先给方案，本轮先完成方案和只读证据审计。没有实际模型、GUI、构建、安装、轨迹生成、学习、评分或旧实验恢复；不创建自动评测。原三轮限制与旧RW STOP保持，其他聊天资源/原生学习决定未改。[详细方案](../reports/283_rw_evolution_trajectory_plan/PLAN.md)、[机器可读建议协议](../reports/283_rw_evolution_trajectory_plan/collection_protocol.proposed.json)均标未激活。

## 证据支持的观察

1. 新26 reference运行accepted仍0；现有端到端主要是Web历史corravale示例，并非五平台正式准入。Windows11 Home32GiB级/WSL24.04现存；Docker Desktop stopped，而独立WSL dockerd供其他实验使用，不操作。未发现已准入Windows/macOS SSH交互目标，当前/dev/kvm用户无读写权限，adb/emulator/qemu/xvfb-run未在PATH；这些是当前只读快照，不能断言全机/外部账户绝无资源。[运行审计](../reports/283_rw_evolution_trajectory_plan/runtime_audit.md)。
2. 官方RW pinned vendor `b5cda868f44932dc84ea68e3b3053bc418621aa3` 的 `scripts/core/agent_invocation.py` 默认完整run72000s/单模型请求1800000ms/工具180000ms，max_turns=None，并有initial/continue/resume会话合同。三轮是至多三次完整agent调用/正式提交及验证反馈，不是三次工具调用。26全部运行、都三轮且每轮用满20h的极端上界1560worker-hours，实际速度/费用未测；不能许诺一天结束。没有恢复240s旧API截断。
3. 基础新harness应从218官方固定vendor加必要传输/视觉适配构建独立freeze，不能继承267/v17针对corravale的hint/guard/人工指导为“官方原生基线”。旧17轮结果/STOP仍保留。
4. 原生RW采集session复制默认64MiB上限且可best-effort跳过；stdout/session有重复，工具user角色不等于真人多轮。既有218例205行/91tool_use+91tool_result、91监控PNG，但原图像块递归计数10；监控图不等于全部进入模型。新合同须标图像consumer、事件关联与hash；跳过/不可读不能称完整trace。[合同审计](../reports/283_rw_evolution_trajectory_plan/trajectory_contract_audit.md)。
5. 官方 `extract_from_agentic_trajectory(data或file)`均扁平为一条user text并synthetic success=True，这不是benchmark成功。官方 `sdk.ingest(messages,events)`存在，可配合原生offline trajectory提示上下文作外部适配；现有218/208没有此适配验收。不热改vendor或假称传JSON即可保结构。
6. 当前AutoSkill connector是text-only，图像path/hash/base64不让抽取看像素；实际connector还可能tail-clip长输入，0限制不是无限。每ingest候选数 `client.py:114` 硬夹0–1；26完整链各提取一次候选上界26，维护后可能更少。不是所有其他粒度总上界或26最终技能保证。processed不独自证明API/解析/embedding无故障或模型成功；本轮没做抽取。

## 拟执行方案（建议，尚未冻结/激活）

- 保持一应用一完整复刻任务（U7/W5/M3/A6/Web5），62主池流程为探索/核验维度，不拆62题或改成闲聊。先明确完整本地核心scope，成功后不因困难缩水。
- 参考GUI/工具/截图/fixture/reset/权限隔离先准入。训练验证器来自独立训练reference，不使用250私有tests/gold；参考通过、负对照能失败、规则/视觉判据冻结后才调用agent。检查或视觉未完成保留UNKNOWN，不能填0或用退出0当任务成功。
- 新采集沿用用户RW视觉资源别名 `deepseek-v4-flash-vision-exp`，真实供应商身份/图像/工具/finish验证后记录；不改其他聊天模型或账本。起步1worker，容量实测后最多2个独立桌面/worker。
- 拟选五平台各1已准入题作首样（Squoosh/Calculator/Caesium/To-Day/OpenCalc仅初建议，未冻结），计入26/三轮额度，不能另起免费canary或成功后重跑凑数量。Web/Ubuntu12候选可优先准备；Windows5/mac3/Android6缺原生宿主/通道保留waiting_resource，不伪Web替代。
- 首轮空candidate/无skills；失败后轮继承自己的原代码＋真实冻结训练验证反馈，最多三次完整模型执行/提交含首次，成功停，第三轮未达仍停止，取最后提交不挑高分。正常轮内探索/编码/自查可多步，禁止正式评分反馈后无限模型修订。版本、workflow、端口不重置家族计数。若基础设施中断必须完整重启agent，也占三轮；同attempt接续须证明无额外纠错和假重试。
- 不同应用之间不传经验/代码或增量skills；本批结束交用户建库，本轮不擅自启动学习或250评测。
- 四层交付：raw CLI/session/images/candidate/API证据；完整按序公开family chain及1–3轮父链；机械native文本学习视图和逐轮索引；外部真实outcome/质量/使用量/hash。保留成功前失败和最终未成功，不只留最高分。没有LLM预总结或手写skills。
- actor实际可见反馈保留；最后轮裁判若actor没看过只存sidecar，不伪造agent工具回执。extra labels或multimodal/structured输入由后续学习版本明确选择，不能暗中通过metadata/hint送入，也不能套用另一聊天tau原生盲提取决定。
- 首样先核对raw→canonical→学习视图的事件/回执/图像/实际入模数量和输入容量，证明“不只是文件存在”。原始数据不静默裁剪，SDK完整输入尚需适配准入。

## 期望产出与未知项

目标26个完整应用链、26–78完整轮次，以26全部准入且执行为条件。若仅部分平台可用，交真实子集与缺资源登记，不称26/五平台完成。成功/纠错对数、耗时/费用、最终skills条数与250题增益未知；不能把上界当成功数量。

素材预期支持输入/状态探测、合法动作/错误恢复、数据/持久化/导出、时间/播放、窗口焦点/权限、最后编辑后运行与视觉核验等类别，这是假设不是已生成技能。任务/轮次/调用回执/图片consumer/feedback-candidate-hash可追溯是数据质量目标；只有实际核验通过后才能说到达。

## 下一步

按“先给方案”本轮交方案，未启动新模型采集。执行从新reference/训练verifier与图像/记录通道准入开始；Windows/macOS/Android真实宿主属于要解决的资源门禁。来源池freeze保留，不扩充；原vendor/旧run/STOP与其他聊天未改。拟协议和报告hash可复核，不是已经通过的执行配置。
