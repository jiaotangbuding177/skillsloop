# eval250 一轮三臂完整结果 + Q 评分方法交接包

快照日期：2026-10-21。数据来源是 **一轮 250 原生 OpenClaw 执行**，不是后来的多轮 v2 测试集。

## 1. 这个包是什么

用于把“完整 750 条结果”和“Q 五维质量评分方法/指南”交给另一个 agent，继续做 Q 评分或结果复核。

包含：

- 250 题 × 3 臂 = **750 条完整结果**（NoSkill / AutoSkills / Trace2Skills）。
- 逐题模型轮次、工具次数、耗时、TSR 结果。
- 逐题 token 表（实测 + 估算拆分）和逐次调用明细。
- Q 评分 rubric、评分政策、质量适配器/worker、调用说明。
- 750 条结果对应的本地 attempt/output 路径清单（路径存在性 750/750）。

**不包含**：原始企业输入、凭据、完整 750 份输出工作区（体积大）。输出工作区在本机 `output/20261015_transport_recovery_round2/execution/attempts/`；路径见 `MANIFEST/750_output_refs.jsonl`。如果接收方不在同一台机器，需要另外打包这批输出。

## 2. 数据口径（先读）

| 项目 | 说明 |
|---|---|
| 数据集 | `enterprise-mixed-one-request-eval-v1`，250 题，单次委托 |
| 执行器 | 原生 OpenClaw，glm-5.3-flash，24 模型调用 / 40 工具 / 8192 每 call / 196608 总输出 / 1800 秒 |
| 组数 | NoSkill / AutoSkills / Trace2Skills，各 250 |
| 结果快照 | 2026-10-16 12:31:24（Asia/Shanghai） |
| TSR | 机械交付：全部公开具名交付文件存在且非空；不是内容质量分 |
| 模型轮次 | 一次模型 API 生成计一轮；含 READ/写计划；失败/截断末次请求也计入 |
| Q | **本批 750 条没有 Q 分数**；Q 是独立五维评分，方法/材料在本包，需另外执行 |

### 750 条结果分布

| 方法 | 任务数 | PASS | FAIL | UNSCORED |
|---|---:|---:|---:|---:|
| NoSkill | 250 | 249 | 1 | 0 |
| AutoSkills | 250 | 247 | 3 | 0 |
| Trace2Skills（历史适配版） | 250 | 249 | 1 | 0 |

平均逻辑轮次：NoSkill 10.62，AutoSkills 12.05，Trace2Skills 12.90。  
平均工具：9.62 / 11.06 / 11.89。  
平均耗时：263.6s / 355.4s / 356.6s。

### token 不是全实测

- 实际模型调用：NoSkill 2,656；AutoSkills 3,016；Trace2Skills 3,230。
- 有真实 usage 的调用：249 / 244 / 252。
- **完整实测的题：0/250（三组都是）**。
- 其余用 GLM-5.3-Flash 官方分词器 + 同题/同服务锚点估算。
- 估算总 token（每题平均）：NoSkill 629,880；AutoSkills 718,033（+14.0%）；Trace2Skills 762,998（+21.1%）。
- 这是量级估算，不是精确账单；逐题实测/估算拆分见 `DATA/750项逐题_token实测与估算.csv`。

## 3. 文件索引

### DATA/

| 文件 | 内容 |
|---|---|
| `current_version_750_results.json` | 原始 750 条结果（每条含 task/arm/score/execution_status/actual_model_calls/actual_tool_calls/api_budget/attempt_ref 等） |
| `750项逐题_token实测与估算.csv` | 750 行逐题 token；列含 measured/estimated input/output、actual_calls、logical_rounds |
| `全部调用_token实测与估算.json` | 逐次调用的实测/估算明细（约 19MB） |
| `三基线与各类任务_token补算.md` | token 估算方法、覆盖率、误差与分类汇总 |
| `三基线各类任务_token汇总.json` | 机器可读 token 汇总 |
| `三组基线评测指标与完整统计表.md` | TSR、轮次、工具、耗时、分类统计（完整 750） |
| `三组token和轮次对比_简明版.md` | 白话版；轮次准确，token 未记全 |
| `逐题轮次与token记录情况.md` | 每题记录覆盖情况 |
| `统计数据.json` | 轮次/token 统计原始数据 |

### Q_METHOD/

| 路径 | 内容 |
|---|---|
| `rubric_release/250题质量评分细则.md` | **评分指南**（逐题细则、维度、锚点） |
| `rubric_release/rubrics.jsonl` | 250 题 rubric；本释放版含 **2643** 个 items（注意：其他文档提到的 2677 可能含额外增补/不同版本，使用前核对） |
| `rubric_release/scoring_policy.json` | D1 .3 / D2 .2 / D3 .2 / D4 .2 / D5 .1；0/.5/1 锚点 |
| `rubric_release/README.md` | rubric 释放说明 |
| `rubric_release/index.json` | 题号索引 |
| `rubric_release/human_review.jsonl` | 人工复核记录（可能为空/待审） |
| `quality_modules_v4/README.md` | **Q 适配器/两阶段评分调用指南**（prepare / DRAFT / CHECK） |
| `quality_modules_v4/adapter.py` | 质量证据准备与两阶段接口 |
| `quality_modules_v4/worker.py` | 评分 worker |
| `quality_modules_v4/legacy_sources/` | 证据投影、引文核验、judge_v5 等依赖 |
| `evaluation_contracts.jsonl` | 每题交付对象、quality_focus、五维权重 |
| `catalog.jsonl` | 题号/类别/需求与材料来源性质（无 task→source 映射） |
| `examples/partial_quality_results_snapshot.jsonl` | 旧的部分 Q 结果快照，仅作输出格式示例，**不是本批 750 的 Q** |

### MANIFEST/

| 文件 | 内容 |
|---|---|
| `750_output_refs.jsonl` | 750 条 task/arm → 本地 attempt_ref、score、轮次、工具、output_tokens_charged、attempt_exists |
| `validation.json` | 750 条计数、各臂 PASS/FAIL、attempt 存在数、rubric 题数/items、Q 未评分声明 |
| `file_sha256.json` | 本包全部文件 SHA256/bytes |

## 4. 另一个 agent 怎么继续

### 4.1 先确认数据

1. 读 `DATA/current_version_750_results.json`，确认 750 条、三臂各 250。
2. 读 `DATA/三组基线评测指标与完整统计表.md` 与 `DATA/750项逐题_token实测与估算.csv`。
3. 不要声称 token 是全实测；引用时保留“实测+估算”标签。

### 4.2 找输出文件

`MANIFEST/750_output_refs.jsonl` 给出每条结果的 `attempt_ref`。本机路径示例：

```
D:\skillloop\output\20261015_transport_recovery_round2\execution\attempts\<task>__<arm>__...
```

本包校验时 750/750 个 `attempt_ref` 都存在。若接收方没有这台机器的路径，需要另外获取输出工作区压缩包；不要用 `current_version_750_results.json` 里的分数冒充完整产物证据。

### 4.3 Q 评分

按 `Q_METHOD/quality_modules_v4/README.md`：

1. `adapter.prepare(final_run_dir, case, fresh_out_dir, environment_path=..., turn_dir=..., messages_path=...)` — 0 模型调用，准备原生产物、图片、证据。
2. `adapter.build_phase_request(prepared, phase='DRAFT', out_dir=...)` — 只构造请求，不 POST。
3. `adapter.score_phase(...)` — 必须提供冻结的 `frozen_contract_path`，其中 `allow_model_post=true`、`model='ecnu-max'`、adapter/worker/legacy receipt/transport 的 SHA 匹配、绝对 deadline 有效；每 phase 最多 1 次 POST，无自动重试。
4. DRAFT 后同一盲号做 CHECK；最终用 CHECK，不取两次高分。
5. 保留原始失败、费用、raw 响应；不要为了分数重跑或改提示词。

**Q 是探索性、未校准**：人工校准为空；不得把 Q 当作已校准正式分；不得把 UNKNOWN 当 0；不得用 TSR×Q 归零。

### 4.4 需要特别注意

- 本批 750 结果没有 Q；`Q_METHOD/examples/partial_quality_results_snapshot.jsonl` 只是旧格式示例。
- 750 结果包含 18 条 `FAILED_ATTEMPT_RETAINED`，但其 `score` 字段来自选定结果/重试链；不要简单按 execution_status 重新判分，按 `result_origin` 和原始 attempt 证据处理。
- 数据集 manifest 明确没有 task→source/family/skill 映射；不要把任何启发式配对写成官方映射。
- 不要上传/分发原始企业输入或凭据；本包只含 rubric、结果与路径清单。
- 运行 Q 前核对 `rubric_release/rubrics.jsonl` 的 items 数（本释放版 2643）与你要用的 2677 版本是否一致；不一致先解决版本，不要混用。

## 5. 完整性

- 750 条记录：3 臂各 250。
- `attempt_ref` 存在：750/750。
- rubric：250 题，2643 items（本释放版）。
- 包内文件：298 个，约 41.3MB（含 18.9MB 逐次调用 token 明细）。
- 所有文件 SHA256 见 `MANIFEST/file_sha256.json`。
