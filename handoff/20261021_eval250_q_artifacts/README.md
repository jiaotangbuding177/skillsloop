# eval250 实际产物与评测输入（Q 评分用）

这是 `handoff/20261021_eval250_q_scoring` 的配套数据包，补上云电脑真正需要的“实际生成的文档/表格/网页”和“评测输入”。

## 1. 包里有什么

压缩包：`eval250_q_artifacts.tar.gz`（约 66MB，解压后约 125MB）

解压后：

```
artifacts/
  T0001__autoskill/
    outputs/        # 该次运行的最终交付文件（递归）
    root/           # 直接写在 workspace 根目录的额外交付文件
    meta/           # attempt_receipt.json, request.json, delivery_score.json, response.json
  ... 共 750 个 task__arm 目录
inputs/
  T0001/            # task.json + prompt.txt + inputs/ 原始评测输入
  ...
  evaluation_contracts.jsonl
MANIFEST/
  artifacts_index.jsonl   # 750 行：task/arm → 目录、score、执行状态、轮次、工具、文件数/字节
```

覆盖：250 题 × 3 臂 = **750 个 attempt 目录**；250 个任务输入目录。  
未包含：完整 4.4GB 工作区中的 `openclaw_transport/` 日志、`private/`、`workspace/logs/`、`workspace/work/` 等中间目录；Q 评分不需要这些，若需要审计再另行提供。

## 2. 怎么解压

Linux/macOS：

```bash
tar -xzf eval250_q_artifacts.tar.gz
```

Windows：

```powershell
tar -xzf eval250_q_artifacts.tar.gz
```

校验：

```bash
sha256sum -c SHA256SUMS.txt
```

## 3. 和 Q 方法怎么配合

Q 评分方法、rubric、适配器、两阶段调用说明在同一个 GitHub 分支的：

```
handoff/20261021_eval250_q_scoring/
```

关键文件：

- `Q_METHOD/quality_modules_v4/README.md` — prepare / DRAFT / CHECK 调用说明
- `Q_METHOD/rubric_release/250题质量评分细则.md` — 评分指南
- `Q_METHOD/rubric_release/rubrics.jsonl` — 250 题 rubric
- `Q_METHOD/evaluation_contracts.jsonl` — 每题交付对象/质量关注点

对每个 `artifacts/<task>__<arm>/`，把其中的 `outputs/`、`root/` 作为最终产物；`meta/attempt_receipt.json`、`request.json`、`delivery_score.json` 用于映射和证据；`inputs/<task>/` 是评测输入原始文件。具体 `prepare()` 参数按 `quality_modules_v4/README.md` 传入。

## 4. 重要边界

- **token 仍是“实测+估算”**：完整实测 0/250 题；不要用结果 JSON 里的 PASS/FAIL 反推 Q。
- **Q 未评分**：这批 750 条只有 TSR/轮次/token；Q 需要按方法另跑，探索性、未校准。
- **18 条 `FAILED_ATTEMPT_RETAINED`**：`artifacts_index.jsonl` 保留真实执行状态和 score；不要按状态自行重判，按 `result_origin` 和原始 meta 处理。
- **输入是去标识/重建数据**：未包含原始企业凭据；不要重新分发到公开渠道。
- `outputs/` 是最终交付集合，不是完整工作区；如果 Q 需要某次运行的原生渲染证据，适配器应从这些最终文件重新渲染，而不是引用旧日志。

## 5. 完整性

- 750 个 attempt 目录，250 个输入任务目录。
- `MANIFEST/artifacts_index.jsonl` 750 行。
- `SHA256SUMS.txt` 为压缩包校验。
