# 051 实验准备与复现入口

在项目根目录 `D:\skillsgen-industry_track` 执行。企业正文、模型原响应与技能交付留在038案例的 `private/`；本目录只存控制代码和去标识摘要。以[正式协议](../../protocols/051_targeted_first5_acceptance.md)和[结果报告](../../reports/051_targeted_first5_acceptance.md)判断实际状态，不能把脚本存在当成实验通过。

## 已执行的免费控制

- 初始准备：[summary.json](summary.json)，82项初版检查及真实安装OpenClaw对本地固定响应服务的读取/写入/打包。不是远端模型能力证据。
- 最终代码：[verification-final.json](verification-final.json)，85项检查通过；阶段5专用解析器保持上游runtime字节不变。
- 真正保存响应：[run05-real-prefix-dryrun-result.json](run05-real-prefix-dryrun-result.json)，原8条请求逐一精确匹配、前两个creator原草稿重新封装，第三creator在调用门前被人为阻断，网络尝试0。
- 原run01失败重放：[run01_failure_replay.md](run01_failure_replay.md)，同输入和响应重复出现同一引用拒绝。
- 原run03摘要勘误：[run03_mixed_status_correction.md](run03_mixed_status_correction.md)。正确状态FAILED，不能以旧mixed-summary中的PARTIAL覆盖主验收结果。
- 原run04血缘诊断：[run04_hash_lineage_diagnosis.md](run04_hash_lineage_diagnosis.md)。保存响应匹配失败发生在真实新调用之前，新增模型调用0。

## 三种不同的复现操作

### 1. 检查已有产物字节，不调用模型

```powershell
python enginering/demo/scripts/run_038_first5.py --data research/cases/038_contract_multi_review/private/051-first5-run05 --verify-results
```

这只查已登记文件和归档的hash，不能证明宿主处理可重复，更不是再次模型推理。

### 2. 完整保存响应重放，不调用模型

```powershell
python research/reviews/051_preparation/replay_saved_responses.py --source-run research/cases/038_contract_multi_review/private/051-first5-run05 --data research/cases/038_contract_multi_review/private/051-new-offline-replay
```

目标目录必须是全新目录。源run必须PASSED，当前应用源码/请求配置必须与冻结manifest一致；否则脚本拒绝。它从同一48原事件重建新库，按purpose和完整请求hash精确读取9个已保存响应，重验原草稿、执行官方打包并比较六类阶段投影及标准化技能内容。历史creator读回执会标为历史，不能称新发生的读取。不能改旧响应sourceHash来消除不一致。

### 3. 新模型独立推理，需要真实资源

```powershell
python enginering/demo/scripts/run_038_first5.py --data research/cases/038_contract_multi_review/private/051-new-independent-trial --daily-limit 12 --max-candidates 3 --preflight-only
python enginering/demo/scripts/run_038_first5.py --data research/cases/038_contract_multi_review/private/051-new-independent-trial --daily-limit 12 --max-candidates 3 --run
```

同一目录的预检/运行必须使用同一冻结配置。这个命令会请求真实模型，不能为了验证下载或查看产物而误运行；它不是本轮已经完成的另一次实验。远端输出可变化，代码/提示更改必须另开目录。`daily-limit`是宿主派发次数，creator内部多轮请求和tokens另算。

## 本轮有界续接入口

[run_saved_responses_creator_parser.py](run_saved_responses_creator_parser.py)仅适用于run03的精确检查点：1READY＋1FAILED完整creator响应＋1QUEUED，前四阶段已通过；从原事件新建库，复用8个响应并只允许最后1个候选的新creator派发。它会拒绝其他状态。旧run04的`run_saved_responses_one_creator.py`及更早续接脚本保留用于历史审计，不能替代最终入口。

所有包在阶段5是待个人选择的候选；本轮脚本不自动采纳、组织提交或发布。结构与封装通过后，任务层效果还需阶段6/7的实际消费检验。
