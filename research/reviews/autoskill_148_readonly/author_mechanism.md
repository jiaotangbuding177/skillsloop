# AutoSkill 作者机制与 148 实际入口只读核对

核对日期：2026-10-04。范围：原论文、论文指向的作者仓库、148 已有脚本和输入；没有启动实验、模型、embedding、服务或修改运行代码。本文是静态机制和已有材料核对，不是效果实验。

## 来源与版本

- 论文链接当前对应 **arXiv:2603.01145v2，2026-03-05**；v1 为 2026-03-01。论文直接列作者仓库 `ECNU-ICALK/AutoSkill`。[版本历史](https://arxiv.org/abs/2603.01145)、[论文 v2](https://arxiv.org/html/2603.01145v2)。
- 仓库核对使用 148 `versions.json:33` 登记的固定提交 **94c47ca488d4ba4117d20272e66d49b9877e68cf**，不是未固定的 main，也不是别名同名仓库。[作者固定仓库](https://github.com/ECNU-ICALK/AutoSkill/tree/94c47ca488d4ba4117d20272e66d49b9877e68cf)。
- 当前工作区和 `D:/skillloop` 均未找到脚本引用的 vendor；因此本轮独立核对的是上述上游固定提交与本地现存脚本/产物，**没有独立证明实际历史调用时 vendor 字节与上游相同**。`versions.json` 和 `source_audit.md` 是准备期 conversation 配置，不能覆盖 `final_report_v4.md:27`、`frozen_skills_v2_manifest.json:3` 和 `autoskill_build_trajectory.py:16/48` 所记录的实际 trajectory 路径。

## 必须认可的已有能力

论文 §3.1/3.4 描述用户提问驱动的候选抽取、近邻维护、add/merge/discard 和版本更新；它明确包含后续反馈引发的技能演化。论文的 query-only 证据规则不能用于概括后续仓库独立 trajectory 抽取器。论文没有提供本项目阶段2/3定义下逐问答归属准确率或交错恢复效果。[论文方法](https://arxiv.org/html/2603.01145v2#S3)。

| 作者原生机制 | 固定源码证据 | 对本项目问题的准确边界 |
|---|---|---|
| 接收轨迹、消息与事件，支持工具过程、失败过滤和可选截断 | `offline/trajectory/extract.py:22-123`：`extract_from_agentic_trajectory` 参数 `include_tool_events=True`、`success_only=True`、消息/事件上限默认0；非零上限取尾部。传给 `sdk.ingest` 的字段为 messages/events/metadata/hint。 | 不能说它没有轨迹或失败输入。文件/inline来源先经文本单元包装；`_record_from_unit:125-143` 设合成 `success=True` 并把单元视为完整轨迹。默认 `_parse_success:303-316` 缺标签为True，没有显式UNKNOWN状态。这是入口语义边界，不证明模型把原始失败学成成功。[抽取入口](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/extract.py) |
| 完整轨迹进入专用提示，学习工具编排、检查点、fallback和retry | `offline/trajectory/prompts.py:19-71`；要求聚焦主要完成分支、排除无关/不确定分支，偏好窄任务；不明确/无复用价值可返回空。维护提示按workflow与工具链身份判断、融合恢复路径。 | 有分支选择和鲁棒经验学习，不能宣称“没有反馈处理/错误恢复”。但抽取输出是技能字段，没有逐问答task_id、反馈指向、尝试→修订边等结构化恢复结果。它选择一条主链的表现是否足够处理多目标交错，待测。[轨迹提示](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/prompts.py) |
| 通过通道替换抽取与维护系统提示 | `prompt_runtime.py:53-71/140-155` 识别extract/repair/manage_decide/merge_gate/merge，包装SDK extractor/maintainer LLM并最终恢复。 | 实际trajectory没有继续沿用conversation的user-only系统提示；同一payload字段存在不等于相同证据政策。[提示运行时](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/prompt_runtime.py) |
| 每次ingest最多1候选，再维护入库 | `client.py:79-127` 将 `max_candidates_per_ingest` 硬钳到0或1；metadata仅抽出 `extraction_reference` 给extractor，其余交维护/来源记录。 | 这限制的是一次入库的候选数，不等于每会话永久只能1技能。多次调用/预分片可以学习多项；公平对照须计入分片调用和token成本。[SDK](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/client.py) |
| 原生conversation已有最近任务识别及上下文消歧指令 | `management/extraction.py:189-205` 使用最近3–6用户轮、目标/交付/操作类、topic boundary并优先最新活动任务；payload保留messages/events/primary_user_questions/full_conversation/hint；JSON失败有恢复/修复，调用异常默认可为空。 | 不能说AutoSkill完全无任务识别。该提示不是逐对任务图，且被trajectory专用提示替换。该文件直接JSON序列化payload，没有本轮观察到的统一抽取输入字符截断；修复仅把DRAFT取尾2500字符，不能误写为轨迹输入截断。[抽取核心](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/management/extraction.py) |
| 技能相似检索、前一技能线索、能力身份判别、语义合并和版本历史 | `maintenance.py:_upsert_candidate:485`、`_merge_with_llm:941`、`_merge:884`：可用previous_skill_id/进程内最后入库身份、规范化description身份、近邻；保留技能身份并patch bump；LLM失败退启发式；来源随candidate保存。 | 这是技能维护归属，不能等同问答→任务→尝试的关系恢复。LLM维护主要看技能字段/资源路径而非逐轮原轨迹证据；是否丢失反馈目标、错误修订依赖是待测问题。已有演化必须作为强基线保留。[维护源码](https://github.com/ECNU-ICALK/AutoSkill/blob/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/management/maintenance.py) |

代码行号按GitHub一基行号；Web工具展示行号从0起，本文已加1。以上精确功能描述来自固定源码，未把论文概念等同本地运行事实。

## 148 已有适配的单独事实

1. `scripts/canonicalize_trajectory.py:23-47` 从每个simulation输出一个 `task_<id>.txt`；保留 USER、公开AGENT、工具name/arguments、工具错误文字；**每条工具结果只保留前4000字符**（44行），未保留call/result id。不能称输入工具事件无损，也不能把此截断归为AutoSkill原生算法。工具对应关系暂由线性位置表达。
2. reward/termination写在 `autoskill_input/trajectories/manifest.json`；`autoskill_build_trajectory.py:44-51` 只取 `task_*.txt`，未读取manifest或传入metadata。因此本入口中评分/终态标签不是直接抽取信号；错误仍在正文可见。
3. 148显式 `include_tool_events=True/success_only=False`，并提供手写零售HINT（24-30行），包含身份核查、确认后写入、工具成功后再称完成等规则。这是适配提示先验，不应把所有这些规则的来源都归为模型从轨迹自主发现。
4. 最终清单记 `processed70/failed0`、3技能。它是现存产物的登记，不证明所有实际模型调用完整、每条均有有效经验或每个步骤均被正确学习；本轮未逐请求审计。
5. 可定位反例：`task_0.txt:32-33` 唯一可见exchange调用返回错误，46行agent却宣称成功，51行用户给出积极反馈。**观察仅支持“自报/认可和工具成功可能不一致”**；没有对应候选与原始抽取响应核对，不能据此断言AutoSkill已沉淀错误经验。`task_113.txt`也保留多次Order not found，说明失败事件没有被前置筛掉。

### plaintext角色和success字段怎样进入模型

固定 `extract.py:_record_from_unit` 将单元正文整体放入一个 `role=user` 的message；`_messages_from_record`优先返回这份messages，`_events_from_record`没有为它生成结构化工具events。因此本次 `AGENT_TOOL_CALL` / `TOOL_RESULT_ERROR` 是user消息内部的**文本标签**，模型可读其语义；不是被归一化回原始assistant/tool角色、tool_call_id或tool result关联。`include_tool_events=True`在这种包装下也不意味着结构化events非空。这由固定extract入口的转换足以确认；本轮未成功取到固定提交的`file_loader.py`，只成功读到main文件，后者只能作补充，不能作为固定版本逐字证明。

合成`success=True`经`_parse_success`用于success_only筛选，并写`trajectory_success` metadata。SDK ingest只从metadata拿`extraction_reference`供抽取；`LLMSkillExtractor.extract` payload不包含该metadata或trajectory_success。故**success flag不直接出现在本路径抽取prompt**，不能声称给模型提供了真实成功标签，也不能说包装True直接诱导模型学成功。模型看到的是完整轨迹包装措辞和正文中的成功/失败/反馈文本；其解释质量待查。

### 实际取得的固定raw源码及关键片段

以下链接均实际成功读取，使用完整SHA。行号为一基；不是只根据README推断。

- [extract.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/extract.py)：137-140行包含`"success": True`和单条user message；133行文本为`Treat this content as one complete trajectory/workflow context.`。303-316行成功启发式；89-92行记录trajectory metadata。
- [client.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/client.py)：105行`max_candidates = max(0, min(1, int(self.config.max_candidates_per_ingest)))`；101-112行仅把`extraction_reference`传给抽取。
- [prompts.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/prompts.py)：31行包含`focus on the principal success-driving chain`；29行要求学习checkpoints/fallback/retry；32行排除无关及不确定分支。
- [prompt_runtime.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/offline/trajectory/prompt_runtime.py)、[extraction.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/management/extraction.py)、[maintenance.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/management/maintenance.py)、[config.py](https://raw.githubusercontent.com/ECNU-ICALK/AutoSkill/94c47ca488d4ba4117d20272e66d49b9877e68cf/autoskill/config.py)：对应上表提示替换、payload、维护、默认配置证据。

## 阶段2/3可证伪问题（假设和建议，未执行）

- **任务覆盖假设**：同一来源单元包含A/B两项可复用任务时，单主链选择可能遗漏其中一项；逐问答多目标识别再分片可能提高覆盖。控制同一源证据、学习后端和总预算，比较任务召回、错误拼接、后续复用；若原生或等预算普通LLM分片同样恢复则不得宣称新增收益。不要用技能数增加代替有效覆盖。
- **反馈归属假设**：A尝试→B插入→指回A的延迟纠正中，显式feedback→attempt链接可能更可靠。可只重排完整公开轨迹、保留真实文本/回执，让原生trajectory、普通LLM整理、阶段2+3恢复与人工正确归属共用AutoSkill后端。主要看归属边准确率、要求/拒绝/修订保持率、无证据成功判定和下游效果；若不优于普通整理/原生，则否定复杂前处理必要性。
- **结果证据假设**：工具成功、用户认可、agent自报和UNKNOWN分开标注可减少错误经验采纳。评分标签或gold不能成为held-out学习泄漏；只允许明确定义的学习期可见结果证据。先比较不提供标签/保留公开工具证据/明确UNKNOWN，避免把结果标签改善错归为任务恢复算法。
- **成本与截断替代解释**：提高收益可能来自多次候选机会、长上下文保留、零售HINT或额外token，而非关系恢复。须保留原生默认及等预算强基线，并单列去HINT、完整/4000字符工具结果等适配因素。

本轮无新增效果实证发现。阶段2/3的候选贡献应定位为可回查的任务/尝试/反馈关系恢复及其可验证价值，不宣称首次会话任务抽取、首次技能演化、首次失败经验学习或已优于AutoSkill。
