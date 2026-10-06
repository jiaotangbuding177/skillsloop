# 2026-10-06 输入冻结及现有 R 接口核查

本记录只来自本地来源与代码的只读核查、标准库导出和完整性检查。未运行模型、读取凭据文件、执行历史命令或修改 Demo。实验运行和研究记忆由主代理统一记录。

## 冻结输入

- `private/frozen_source.json` 的 `sessions` 是六个 blind `model_inputs.jsonl` 原行；`messages` 的正文和全部来源 occurrence 完整保留。完整工具快照在根级 `tool_records`，按 `session_id` 对应会话。
- 六会话合计 129 条正文、30603 字符；另有 20 个附件元数据引用，附件字节不可用。11 条工具快照的 `args/output/error` 完整 JSON 序列化为 120596 字符。
- `private/ecv_input.json` 为 `E/C/V`；E 是 129 条消息加 11 个工具快照观察，C 是来源说明与客观元数据，V 为空。没有推断 `responseTo/runId`、任务配对或成功失败标签。`sourceOrder` 只表示原展示位置或快照导出位置，不是已认证时序。
- `private/input_manifest.json` 保存原文件字节 SHA256、六来源 canonical JSON SHA256、消息内容 SHA256 和覆盖清单。其 `jsonlLineUtf8Sha256` 为文本读取后归一化换行的 UTF8 行哈希；`private/input_integrity.json` 明确此口径，并另给原始 CRLF JSONL 字节行 SHA256，不静默替换已有产物。
- 独立核验确认六个原来源行完全相等、129 条正文和 aliases 完全相等、11 条工具参数／返回／错误完全相等。高置信凭据形状扫描只针对选中来源字符串，未发现所列模式；这不构成全面秘密认证，没有读取任何环境值或凭据文件。
- 11 条工具原 `message_id` 都不能与本批去重消息的 group／occurrence aliases 做精确匹配；保留来源锚点但不制造用户或任务归属。同一调用的不同 origin 快照分开保存。

`frozen_source` 的消息稳定键为 `group_id`，角色为 `role`，正文为 `content`；原消息 ID 在 `source_occurrences[*].id`，来源 group aliases 在 `source_group_ids`。工具稳定快照键为 `record_id`；同调用键为 `tool_call_id`；锚点字段为 `message_id/group_id/source_refs`。工具内容是完整嵌套 `args/output/error`，不能仅取 `output.content`。

## R 的现成调用链及适用限制

代码事实：`skilldemo.library_pipeline.prepare_batches(value, batch_sessions=4, batch_chars=48000)` 返回 `(experience, mapping, prepared)`；每批有 `payload/aliases/events/pairs/pending`。对于具备可靠回合链接和顺序的输入，R 单阶段可使用：

```python
# 示例仅说明现有接口；本次 role-grouped observation bag 未执行此路径。
from skilldemo.pipeline import Requests
from skilldemo.library_pipeline import prepare_batches, _recover

experience, mapping, prepared = prepare_batches(value, batch_sessions=1, batch_chars=explicit_budget)
requests = Requests(output_dir, max_calls=len(prepared), agent=client)
recovered = []
for batch in prepared:
    payload, aliases = batch['payload'], batch['aliases']
    check = lambda obj: _recover(obj, payload, aliases)
    proposal = requests.request('library_relational_extract', payload, check)
    recovered.append(_recover(proposal, payload, aliases))
```

这条调用只包含 R，不包含局部经验和 W。`library_pipeline.build` 默认继续局部经验及聚合，且预留 `2 * batch_count` 派发预算；`trace_to_skills.py` 没有 R-only 开关，并在 `--preflight-only` 前就 `load_env`。本轮没有调用 CLI。

本批不能当作上述可靠回合输入：原来源明确为 role-grouped，`chronology_verified=false`。`pipeline.prepare_events` 调用 `intake.assemble`；后者在无 `responseTo/runId` 时按最近用户位置关联助手。因此按原角色分组位置执行会把许多助手正文配给最后一个用户，这不是真实回合证据。本轮没有执行 `prepare_events/prepare_batches`，没有保存其伪配对。

## 可复用的候选约束及搜索

`skilldemo.relational` 的现有基础件：

- `_score(row)`：读取 `score`（缺省 0），拒绝 bool、非有限数和不在 [0,1] 的值；返回 float。它是排序值，非校准概率。
- `_reason(row)`：读取 `reason` 或 `explanation`，必须为非空字符串。
- `_cycle(edges)`：输入 `(source,target)` 边列表，返回有向环是否存在。
- `BEAM_WIDTH=8`、`MAX_OPTIONS=8`、`AMBIGUITY_MARGIN=0.10`；既有 `compile_result` 的有界搜索没有独立公开 solver 函数，搜索实现嵌套在该函数中。

既有编译器的具体约束：每个用户分片完整覆盖且精确引用来源；全部分片各有 1–8 个成员候选；CONFIRMED 只允许本分片声明的 seed 候选；未决候选不能强归属。关系引用必须同时有来源及目标的原文；非 UNKNOWN 关系仅在同一已确认任务内成立；要求变更／接受／拒绝等需用户来源；依赖不许成环。搜索按累计候选 score 排序及 digest 确定同分序；近最佳 0.1 内解释保留，存在剪枝导致的替代解释时成员标未决；不宣称全局最优或自然语言语义已验证。

**适配差异必须公开**：`relational.compile_result`／`pair_detection.validate` 假定已有 qN 问答对、用户分片和 aliases，并通过 `positions` 拒绝“指向未来”的关系。它们不是任意事件袋的验证器。`pair_detection.quote_ref` 同样绑定 user/assistant side 和 pair aliases；不能直接拿它证明本批未知配对。事件袋适配可复用 `_score/_reason/_cycle` 和有界候选思想，但若改变 pair schema 或取消位置作为真实先后约束，应标明为适配，不能称 Demo 原封运行。

## 模型客户端与 R 结果契约

`Requests(root,max_calls=3,agent=None,responses=None,reuse_requests=None)` 接受自定义 client；client 的 `mode` 描述真实模式，`run(purpose,payload,workspace)` 返回至少 `text`，并建议返回 `usage/runtime/modelRequestStarts/status/elapsedMs`。`text` 必须能解析为 JSON 对象。Requests 按 purpose＋payload＋request_config＋mode 计算请求身份、记录载荷和原回复，并对成功缓存重新验证；失败请求不自动再发，派发前检查 max_calls。实际 HTTP 启动数由 client 回执说明，不能用宿主派发数假装准确请求数。

默认 `OpenClawAgent` 对 `library_relational_extract` 直接做一次 structured-model-request，没有工具循环；支持 OpenAI chat-completions 或 Anthropic messages；R 默认 max_tokens=16000、temperature=0、检测超时默认180秒且限制为10–240秒。model/base/protocol 来自进程配置，API key 只用于请求头；本轮没有读取这些配置值。传输错误、空正文、length/max_tokens 截止会失败，代码没有自动重试。

R 原提议需要 `sourceHash,seeds,annotations,memberships,relations,observations,requirements,executionBindings,evaluationBindings`。`library_pipeline._recover` 调用 `relational.compile_result`，另拒绝跨独立会话的任务实例。编译结果根键为 `traces,memberships,unresolved,seeds,annotations,searchAudit,normalizationAudit`。trace 包括来源 IDs、要求时间线、类型化关系、观察、attempts、outcomeEvidence、工具证据、缺附件和未决记录等；无独立核验的业务结果／verification 为 UNKNOWN，semanticAccuracy 为 NOT_INDEPENDENTLY_VALIDATED。

## 字符／批次限制

- `normalize_input`：E 1–5000 行，user/assistant/tool；C 至多100项；V 至多200项。事件 ID／sessionId 非空且不超过300字符，单条 content 不超过200000字符；单会话 sourceOrder 不可重复。
- 默认批次最多4个完整会话、48000序列化字符；单会话超限拒绝，不截断。批次预算是完整 events/context/evaluations 的 JSON 长度，不是正文字符总数。
- `evidence.catalog` 超过110000 JSON字符拒绝；`relational.prepare` 超过160000的 `str(payload)` 长度拒绝。字符限制不等于模型上下文 token 上限。
- 仅做完整观察袋 JSON 大小盘点（不是 R 预检）：各会话携带全部 C 时，按 normalize_input 形状补 `runId=null`，字符数分别为40850、24942、118761、50231、37642、74332；全 ECV JSON 序列化272222字符。默认48000不足以接纳 d2c/e6/b5 三个完整来源；应显式冻结事件袋适配及预算，不自动截尾。

## 代码证据位置

- `enginering/demo/DIRECT_PIPELINE_README.md:16,43,49,61,84,88`
- `enginering/demo/trace_to_skills.py:22`（preflight前加载env）
- `enginering/demo/skilldemo/library_pipeline.py:28,61,71,96`
- `enginering/demo/skilldemo/pipeline.py:46,97,130,166`
- `enginering/demo/skilldemo/intake.py:91`（来源回合装配）
- `enginering/demo/skilldemo/relational.py:170,214,221,235,394,447,483,999`
- `enginering/demo/skilldemo/pair_detection.py:45,74`
- `enginering/demo/skilldemo/runtime.py:111,218,311`
- `enginering/demo/skilldemo/evidence.py:49,72,195`
