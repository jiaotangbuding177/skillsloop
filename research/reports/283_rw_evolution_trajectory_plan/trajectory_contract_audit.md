# RecreationWorld 演化轨迹输入合同审计（只读方案，2026-10-04）

## 状态与范围

本轮核对本机冻结的官方 RecreationWorld 采集模块、官方 AutoSkill SDK、218 的公开 AgentNet 导入包装与 208 的 Co-Gym trajectory 包装。未运行模型、AutoSkill、GUI 应用或评分，未修改 vendor、旧实验、服务与旧 STOP。未读取隐藏测试或私有金标准。26 主候选仍是来源候选，尚无新演化轨迹、技能或运行准入结论。本报告提出的是下一版本需要实现并验收的输入适配合同，不把方案写成已存在功能。

先读了 research/README.md、CHARTER.md、STATE.md 与 memory/281。用户已经要求每道演化任务最多三轮（首轮计入），完整保存真实失败；本次仅方案，不恢复旧 corravale 迭代。282 的 tau 原生盲提取决定是另一个域的明确决定，不自动改写本项 RW 的学习合同。

## 核心结论

1. **当前 AutoSkill 学习链路是文本输入，不会读取截图像素。** agent 执行时使用视觉模型、raw 中含图片、提取输入含图片路径/哈希/base64/image_url，都不等于 AutoSkill 学到了图像。218 已明确把截图当 provenance 留存；当前官方 LLM 请求最终只有 system/user 字符串。
2. **当前公开 `extract_from_agentic_trajectory(data=...)` 也没有保留结构化消息入口。** `data` 和 `file_path` 都先转换成文本 unit，再包装一条 user 消息，并赋导入器 `success=True`。传入 `{messages, events}` 不会绕过这一转换。该 success 不是 benchmark 成功，`success_only=False` 也不会自动恢复真实 outcome。
3. **官方 SDK 确有结构化入口 `AutoSkill.ingest(messages, events, ...)`。** 可在官方 `activate_offline_prompt_runtime(channel="offline_extract_from_agentic_trajectory")` 上下文使用它，以保留官方 trajectory 提示剖面、抽取、维护、embedding、入库算法。需要新外部适配器；现有 218/208 包装未实现这个入口，不能宣称现成 file importer 已支持结构化 RW JSONL。
4. **每次原生 `ingest` 最多提出一个技能候选。** 完整应用链一条输入、26 个主候选各提取一次时，首次提出候选数至多 26，最终可因空提取、更新、合并或丢弃而更少。不能承诺一应用多技能，也不能把 64 条任务流程举例当 64 条已产出轨迹。
5. **`processed` 不等于任务成功，也不能单独证明抽取无基础设施错误。** 官方默认可把 LLM 调用异常、空回复或 JSON 修复失败转换为 `[]`。必须同时核对真实完成/失败账本、原生 result、embedding 证据与产物，区分正常空候选和真实故障。

## 一、现有原始轨迹实际是什么

### 官方 RW 采集保留的材料

冻结 `scripts/core/trajectory.py` 将 agent CLI 的 stdout JSONL 保存为 `trajectory.jsonl`，同时复制 CLI 自身 session/rollout JSONL 至 `sessions/`。`proxy_logs/` 可保留逐请求的诊断证据。多种 CLI schema 不同，不存在一个已验收的通用 RW `messages` JSON 标准。

原模块 session 复制默认设置 64 MiB 单文件门槛；过大文件被跳过，读取失败也可被 best effort 忽略。它不是自动保证无缺失的完整轨迹。新采集合同必须逐文件登记已捕获、跳过、不可读与来源时间范围；有缺口标记 `capture_complete=false`，保留缺口事实。若需要更改采集门槛，应先冻结新版本，不热改旧 collector 或旧 run。

原模块将 CLI 的 `result`/`turn.completed`/`turn.failed`/`error` 等终止记录与进程退出分开解释。CLI 正常结束、工具调用结束和任务目标达成都不是同一件事；某些达到 max-turns/max-budget 的终止 subtype 仍可被视作 CLI completed。不能据退出码 0 或最后一条正常消息填 `task_success=true`。

### 对本机既有例子的 schema 检查

只检查字段、类型和数量，未输出模型文本、reasoning、base64 或凭据。

| 材料 | 只读观察 | 含义 |
| --- | --- | --- |
| 218 首条本地 raw `trajectory.jsonl` | 205 行；system 1、assistant 112、user 91、result 1；91 `tool_use` 与 91 `tool_result`；递归发现 10 个 image block，分为 source 型 5、file 型 5 | `role=user` 中大量是工具回执，不能把 91 条 user 自动解释为 91 次人类对话 |
| 同一 main session JSONL | 285 行；除 user/assistant 还有 custom-title、agent-name、queue-operation、last-prompt、attachment | session 与 stdout 有重复和额外 CLI 元数据，需要稳定事件去重，不把两份直接拼接当更多交互 |
| 同一 `tool_use_screenshots/manifest.jsonl` | 91 条，sequence/event_key/tool_name/截图 basename；completed 87、failed 4；对应截图目录的 91 个 PNG 都存在 | 截图应按 manifest 目录解析相对路径；failed 是工具步骤状态，不是 4 条整题失败；原 manifest 没有截图 SHA 字段 |
| raw 工具回执 | 53 条显式带 `is_error`，其中 true 4、false 49；其余缺此字段 | 缺字段必须保留缺失，不能自动补成 false；四个工具错误可出现在后来完成的同一任务中 |
| 264 历史 public export | 638 个 observable：319 tool_use、319 tool_result；36 个回执显式 `is_error` | 已有动作/回执公开导出先例，可作为适配参考；不是本轮 26 应用的新数据，不能重计或证明新管道已就绪 |

图片块、动作后的环境截图、工具返回的图片可能是同一文件的不同表示，也可能不同。新 image manifest 应明确 `image_id`、原始 URI/相对路径、SHA256、大小、媒体类型、来源事件和捕获时间；不凭数量把两种截图等同。

以上 schema 检查来源固定为 `research/experiments/218_recreationworld_glm_pipeline/runs/recreation_eval_baseline_1791032747410611525/recreation/trajectory.jsonl`、同目录 `sessions/recreation_agent_main_6297834f-3dcf-41fd-a0d1-7ffcaabea2a5.jsonl` 与 `tool_use_screenshots/manifest.jsonl`；历史公开导出为 `research/experiments/264_recreationworld_public_interactions_v16/public_trajectory/actions_and_observations.jsonl`。它们仅用于现有格式核验，不是新演化池的数据。

## 二、官方 AutoSkill 能消费的结构与限制

### 公共 trajectory importer

`offline/trajectory/extract.py:42–48` 把文件 unit 或 `data_to_text_unit(data)` 再变为 `_record_from_unit`。`136–154` 的 `_record_from_unit` 生成一条 `role=user` 文本并设置 `success=True`。该文本可含完整工具回执，但不是原生结构化 events。

内部 `_collect_records`、`_messages_from_record`、`_events_from_record` 存在结构化解析逻辑，不能据此宣称公共 `data` 入口不会先扁平化。内部 `_parse_success` 还会把缺失结果默认作 true，不能表示 UNKNOWN；图片内容 helper 只取 text/content，不会进行图片解码。

`file_loader.py` 单文件按文本导入；目录递归按文件排序，不是事件时间。直接给包含 images、outcomes、session、源码和诊断的 bundle 根目录会改变样本边界，并可能把非文本内容当文本解码。建议显式选择经过验收的一条完整公开 chain，不依赖目录自动扫描。

### 可采用的原生结构化入口（待实现验收）

官方 `AutoSkill.ingest` 接受 `messages: List[Dict[str, Any]]`、`events: List[Dict[str, Any]]`、`user_id`、`metadata` 和 `hint`；至少有 messages 或 events。适配方案可以保持下面的调用关系，但本轮未执行它：

```python
with activate_offline_prompt_runtime(
    sdk=sdk, channel="offline_extract_from_agentic_trajectory"
):
    sdk.ingest(
        user_id=namespace,
        messages=public_messages,
        events=ordered_public_events,
        metadata=provenance_only,
        hint=frozen_contract_hint,
    )
```

这沿用官方实现，而不是另写抽取/维护算法；但 bypass generic 文件包装是新的输入适配选择，必须有新 phase version 与 freeze。它不是 public `extract_from_agentic_trajectory` 的既有格式保证。

建议 `messages` 保留公开任务要求和真实对话文本，`events` 是一份含稳定 `sequence` 的完整公开事件流，涵盖要求、可见反馈、assistant 公开动作/答复、工具请求、完整回执、环境观察、产物检查。跨 messages/events 使用事件 ID 关联，并明确 events 为时间顺序依据，避免把相同回执重计两次。官方 `_format_full_conversation_context` 是先列 messages、再列 events，本身不会全局时间归并；不能声称仅使用两个数组就能保持全局交错顺序。

`metadata` 对 extraction 的明确可见扩展是 `extraction_reference`；维护还接收 metadata。若本 RW 方案选择 outcome 只作审计，应把成败/分数存外部 sidecar，不通过 metadata、hint 或消息暗中重新送进学习模型。本决定只适用于新 RW 方案，不改 208 旧输入，也不反向扩散到 tau 规则。实际执行中的公开错误、实际返回的测试/自查结果、用户可见反馈仍属于轨迹内容，不删除来制造无失败示例。

### 截图不会成为视觉学习输入

`LLMSkillExtractor.extract` 将 messages/events 连同字符串 full_conversation 序列化为 JSON 字符串，再调用 `_llm.complete(system=..., user=...)`。官方 `LLM` 接口的 user 参数是 `str`；当前 OpenAI/generic connector 生成 system/user 两条文本消息。没有多模态 image content 的构造或图片文件加载。

因此 structured events 中的截图 URI、图片 hash 或 image_url 也只会成为文本。原生 SDK 接口接受 dict，不等于支持读取 dict 中的图片像素。218 的图片验证/hash证明文件存在和来源一致，不能证明像素进入抽取。actor 可以是 vision 模型，learner 仍是 text-only。

本方案可以学习真实文本工具行为与公开观察、可见错误和自查过程。若 actor 或工具已经在真实执行时产生文本描述、DOM、accessibility、OCR，可以带明确来源保存；不得事后捏造截图描述。另加 VLM caption 或升级 AutoSkill connector 为 multimodal 都是新的模型处理环节/实现变更，需要单列版本、预算、输入对照和验收，不能称现有 native 抽取天然支持，也不在本轮授权范围内。

### 完整消息数不等于完整 LLM 输入

`max_messages_per_record=0`、`max_events_per_record=0` 关闭导入器按条数截断，但 connector 仍按 `max_input_chars` 实际使用的 `text_units` 限额截断。`truncate_system_user` 保留 system 头和 user 尾；设置限额为 0 会得到空 user，不能拿 0 当禁用截断。抽取 payload 还同时包含原消息/events 和 `full_conversation`，可能重复材料。

新适配验收必须比较完整序列化 payload 的单位数、最终 connector 实际请求与哈希，不只看原文件大小或条数。超模型/connector容量时标记该 chain 不满足完整输入准入，先制定并冻结处理版本；不能静默删早期错误、取末尾或只抽最好的一轮后仍称完整链学习。

### 空技能、失败与计数

官方 `client.py:114` 将 `max_candidates_per_ingest` 强制夹在 0–1：`max(0, min(1, int(self.config.max_candidates_per_ingest)))`；这不只是 `config.py:72` 默认值为 1。链级提取一次只会提出 0 或 1 个候选，维护可更新既有技能。26 完整 chain 首次各提取一次的候选上界是 26；不是 26 个最终技能保证，也不是所有可选学习粒度的总上限。若改成逐轮至多 78 次 ingest，候选上界与重复/融合过程会改变，这是另一种明确的学习编排，不能悄悄切换来扩大技能数量。

`management/extraction.py:298–352` 显示默认 LLM 异常/空回复/不可修复 JSON 可返回空候选。空候选要分类为：已完成合法空结果、模型/网络失败、解析/修复失败、输入不完整、未尝试。`processed` 只是 SDK 调用结束计数。建议验收同时绑定完整输入哈希、真实 API complete/fail、官方提取结果、所有 embedding 操作和最终技能导出；不改官方算法来强行生成技能，也不把真实失败归为合法 no-skill。

## 三、建议的新输入合同（非现成官方文件格式）

一个主候选应用对应一个完整演化任务链；任务必须来自公开独立训练应用及自定可验证目标，而不是照抄 bench 隐藏 verifier。链内每轮从明确初始状态开始，允许继承前轮公开反馈与先前实现，继承方式冻结并记录。

| 层 | 必须保留 | 用途与限制 |
| --- | --- | --- |
| `raw/` | 原 CLI stdout/session/transport诊断来源，真实模型/provider名称、agent/harness版本、系统/app commit、初始状态、操作顺序、时间、工具回执、完整错误、实际终止原因、实际产物/实现快照与哈希 | 受控原始证据；不把私有 reasoning、凭据、gold 或隐藏评分脚本复制进公开提取输入 |
| `images/` 与 manifest | 原始像素文件、event关联、SHA、媒体类型、捕获状态、失败/缺失记录；相对路径可移植 | 原多模态证据，供以后视觉研究；当前 text-only learner 不读取像素 |
| `public_trace.json` | `schema_version`、chain/round IDs、按 sequence 完整公开事件、角色和事件类型、工具名、call/result ID、参数、完整回执文本、显式错误字段及缺失状态、实际公开观察、产物检查、图片引用 | 适配为官方 sdk.ingest 的 messages/events；删除仅凭角色推断 user 反馈/人类交互的错误 |
| `outcomes.json` | agent/工具/采集/infra/任务/评分分别记状态；native终止、独立训练自查记录；score数值或 null 与来源； UNKNOWN理由；未运行/暂缓；目标是否有可信验证 | 审计 sidecar，不把 null/未完成视觉评分填0，也不通过 generic synthetic success 混淆 |
| `chain_manifest.json` | 最多3轮含首轮、parent_round_id、前后实现哈希、真实可见feedback引用及来源、暴露/污染记录、全部输入/图片/产物哈希、重复session映射、complete状态 | 防17次隐式挑高重试；保留成功前所有失败和没有成功的链 |
| `learning_manifest.json` | 本地冻结SDK/adapter/prompt/model/embedding/config、namespace、输入边界、完整实际LLM输入哈希、总数/合法空/失败计数、原生results/embedding/导出证据 | 仅在适配器准入后生成；当前没有新26库结果 |

建议事件的最小语义字段如下；字段不是 AutoSkill 强制 schema，而是外部 adapter 的待验收合同，SDK events 可以接收 dict：

```json
{
  "sequence": 17,
  "event_id": "chain-x/r1/e17",
  "round_id": "chain-x/r1",
  "kind": "tool_result",
  "role": "tool",
  "tool_call_id": "call-x",
  "tool_name": "actual tool name",
  "content": "complete public receipt text",
  "is_error": null,
  "is_error_field_present": false,
  "images": [{"image_id": "img-x", "relative_path": "images/img-x.png", "sha256": "..."}],
  "source_record_refs": ["raw/trajectory.jsonl:123"],
  "content_origin": "observed execution"
}
```

null 与缺失状态必须定义；不能用这个占位例子充作实轨迹。完整错误细节留在实际回执与受控证据，而不是仅存一个 `failed` 标签。错误链包含失败前观察、错误、可见反馈、后续纠正与自查；在文本证据充分时有形成恢复/验证类 skill 的研究预期，当前未做抽取或效果实证。

### 三轮链路与反馈

- `round_index` 为 1–3；第一轮计入。达到目标即可结束，不为高分继续刷。三轮都未达到也正常保留事实，没有第四个纠正轮。
- 每个后继轮显式链接前轮、版本和实际给予模型的反馈。来自用户、模型公开自查、公开训练 verifier、工具错误的反馈分别注明来源；不把分析人员后来推测的原因伪装为当时已给模型的内容。
- 本轮方案的独立训练 verifier 可以验证训练 app 上的公开目标。bench 隐藏评分细则、评测 gold 或先前 bench 分数不能自动搬入后继演化 prompt。
- infra transport retry 单独记账，不能把多个完整重新实现 episode 伪装成基础设施重试绕过三轮。真正 infra 中断导致不完整素材时保留并区分，不自动当 agent 失败、成功或零分。恢复/重试策略由正式执行 freeze 明确。
- 全链包含零分、未交付、UNKNOWN 与未成功的有效 agent 行为；不按高分筛选。若后续选择 Rejection Sampling，必须另列研究条件，不能改写这里的失败保留与完整链合同。

## 四、下一阶段应先验收的接口证据

本轮未实现/运行以下验收。建议在用户批准正式执行后、首个真实学习任务前，用不含企业信息的本地结构 fixture 和 SDK spy 检查：

1. stdout/session重复不重计，按真实事件顺序保持所有工具调用与回执，一对多/缺回执/缺图片均显式标记；三轮 parent、反馈与版本闭合。images逐文件hash和相对路径解析正确，采集缺口不伪装完整。
2. 对同一公开链，spy确认 SDK ingest 收到 messages/events 原结构，工具回执/真实错误不丢失，不再出现 importer `success=True`；官方 offline prompt wrapper生效；不改 vendor/算法。删除敏感/私有信息须有安全映射摘要，不泄露被删除内容。
3. spy核验实际HTTP是文本还是多模态，当前应明确 text-only；序列化重复计入输入单位，实际请求未被tail-clipping。不要仅以“原始图片存在”证明视觉进入学习。
4. outcome sidecar与CLI/工具/API/评分证据分别对齐，导入processed与任务成功不同；原生合法空候选和LLM/JSON/embedding故障分别有真实证据。失败不覆盖，新的基础设施重试namespace独立。
5. 首条真实 chain 经过准入后才学；所有26输入都完成、有官方结果和embedding证据、库导出hash通过，才称对应文本技能库就绪。技能数量与bench提升仍是结果而非准入假设。

## 来源与可复核位置

- 官方 public trajectory入口与 synthetic record：[extract.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/offline/trajectory/extract.py:42)、[synthetic record](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/offline/trajectory/extract.py:136)、[file_loader.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/offline/trajectory/file_loader.py:17)。
- 官方结构化SDK与最多一候选：[client.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/client.py:85)、[prompt_runtime.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/offline/trajectory/prompt_runtime.py:150)。
- 文本payload、错误空结果与顺序格式：[extraction.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/management/extraction.py:157)、[错误处理](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/management/extraction.py:298)、[两数组格式](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/management/extraction.py:891)。
- HTTP文本消息与限额：[openai.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/llm/openai.py:130)、[units.py](/D:/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill/autoskill/utils/units.py:255)。
- 官方raw collector/终止状态：[RW trajectory.py](/D:/skillloop/research/experiments/218_recreationworld_glm_pipeline/vendor/RecreationWorld/scripts/core/trajectory.py)。
- 旧text-only包装：[218 trajectory_ingest.py](/D:/skillloop/research/experiments/218_recreationworld_glm_pipeline/scripts/trajectory_ingest.py)、[218 learn_external.py](/D:/skillloop/research/experiments/218_recreationworld_glm_pipeline/scripts/learn_external.py:63)、[208 prepare.py](/D:/skillloop/research/experiments/208_cogym_212_trajectory_learning/scripts/prepare.py:48)。
- 来源主池/旧STOP：[memory281](/D:/skillloop/research/memory/281_2026-10-04_rw_250_evolution_pool_sufficiency.md)。

### 本次审计源码 SHA256

| 相对 AutoSkill 根目录文件 | SHA256 |
| --- | --- |
| autoskill/offline/trajectory/extract.py | fbcefb6df5d6027e68df256d505e3c26c9aacf9f56cd2723a520294c175d2e5d |
| autoskill/offline/trajectory/file_loader.py | 38796c90d9414aa84b4254e436eda2ff311d7059e0a22799aafdd95299df1535 |
| autoskill/offline/trajectory/prompt_runtime.py | ec09d8dbb1c7f55198ba518779934afbe89ef3438243f562dc51f2c42a5de0ec |
| autoskill/client.py | 64b901d60b9181dc85a7fbf944ed0888fbcfdbc3aea6c2ff856368104af16aa6 |
| autoskill/management/extraction.py | a69ed1092bae5499e2599c0f6f252a768c984033c81f93eb2dff014b8ccd6969 |
| autoskill/llm/openai.py | b9d3be7d4be84b13ce18ff418bc27f983058a6e081408d86a4b9c71e08425ebd |
| autoskill/utils/units.py | 9fd00b1e22ce2ab54e18a1a4c7c1a1a86c0c1c6a5ee83e09adc3214368bdd3eb |

其他核对文件：RW collector `0364a42c85d0fe4874d434ebb90c568cd9e5c513dfb923a1e5516d4075075877`；218 trajectory_ingest `ee70057f8562315e046d92781b143198967fb3a1e984b229718aabcc8033f672`；218 learn_external `ecab4f0111eedf79128bb5d1a19b9679efcbd4bb8e332e3c1c26f6ee2cef2785`；208 prepare `41163ca113607293ce858b72aaf59e0b96bdb7b154dd1e752aaa0f3787020853`。

这些SHA是本次只读查看源码的指纹，不是完整运行环境freeze验收。当前未新增实轨迹或技能，也未证明 transfer/视觉学习增益。
