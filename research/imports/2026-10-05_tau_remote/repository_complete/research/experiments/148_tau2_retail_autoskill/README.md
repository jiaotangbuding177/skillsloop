# 148 · AutoSkill × τ²-bench Retail（文本域）

最新状态（2026-10-04）：**v4 配对评测完成**——B0 无技能 160/160（126×1.0，均值 0.7875）、
B1 有技能（`frozen_skills_v2` + v6 原生 `$技能` 引用）160/160（134×1.0，均值 0.8375）；
技能真实读取率 159/160（99.4%）；配对 +5.0pp（20 胜 12 负 128 平，p=0.215，CI 含 0）。
详见 `reports/final_report_v4.md`、`reports/v4_paired_report.md`、`reports/skill_read_audit_v4.md`。
历史批次（GLM 消费五技能库、0 读取缺陷时期）的产物与负结果原样保留。

历史状态（准备期）：不付费准备中。版本固定与分集审计已完成；适配器与桥接已实现；
付费运行由用户提供模型资源后执行——见 `blockers.md`。

## 目录

```
protocol.md / experiment.yaml / versions.json     协议三件套（版本、参数、执行顺序）
split_manifest.json / workflow_split_audit.md     分集与工作流覆盖审计（含 dev 选择、相关性发现）
source_audit.md                                   源码接口定位与适配改动清单
inputs/                                           冻结的零售任务/政策/db/split（哈希见 versions.json）
vendor/tau2-bench                                 τ²-bench v1.0.1（fc0055dc，未改）
scripts/                                          audit_split / openclaw_config / mcp_retail_bridge /
                                                  tau2_openclaw_agent / run_wrapper
tests/                                            离线单元测试（假 OpenClaw，无模型调用）
runs/ raw/ canonical/ autoskill_input/ autoskill_state/ frozen_skills/ ledger/ reports/   运行时产物
private/                                          审计明细（不入管线）
```

## 已完成（不付费）

```bash
# 分集与覆盖审计（可重跑；输出 split_manifest.json + private/workflow_coverage_detail.json）
python scripts/audit_split.py

# 版本核验：v1.0.1 的零售 tasks/split 与 main 逐字节一致（已在审计输出中固化）
```

## 环境（WSL）

```bash
# 依赖环境（已在 143 目录内创建）
python3 -m venv runtime_py
runtime_py/bin/pip install 'mcp>=1.0'
runtime_py/bin/pip install -e vendor/tau2-bench

# 离线单元测试（假 OpenClaw；不调用任何模型）
runtime_py/bin/python -m unittest discover -s tests -v

# 接线 dry-run（构建环境 + 适配器 + 会话目录，不跑模拟）
runtime_py/bin/python scripts/run_wrapper.py --phase dev --group no_skill \
    --tasks dev --result runs/dev/no_skill.json --dry-run
```

## 付费阶段（待确认后按 protocol.md 第 9 节顺序执行）

```bash
# 0) 预算中继（沿用 078 形态，新账本；三条路由：consumer / user / judge）
#    runtime_py/bin/python scripts/budget_gateway.py --ledger ledger/ ...   （待接入）

# 1) dev 真实联调（4 题，采集+评测链接通）
runtime_py/bin/python scripts/run_wrapper.py --phase dev --group no_skill \
    --tasks dev --num-trials 1 --result runs/dev/no_skill.json

# 2) 演化采集（70 题，每题 1 条；Collector 无技能）
runtime_py/bin/python scripts/run_wrapper.py --phase collect --group no_skill \
    --tasks evolution --num-trials 1 --result runs/collect/evolution.json

# 3) 归一化 + AutoSkill 官方离线对话路径 → frozen_skills/（待实现 canonicalize/learn 脚本）

# 4) 配对评测（40 题 × 2 组 × 4 trials，同 seed 配对）
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group no_skill \
    --tasks test --num-trials 4 --result runs/test/no_skill.json
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group autoskill_library \
    --tasks test --num-trials 4 --result runs/test/autoskill_library.json
```

环境变量（付费阶段）：`TAU2_RETAIL_RUN_ROOT`、`TAU2_RETAIL_GROUP`、`TAU2_RETAIL_SKILLS_DIR`、
`TAU2_RETAIL_RELAY_BASE`（consumer）、`TAU2_RETAIL_USER_MODEL/_BASE`（模拟器）、
`TAU2_RETAIL_JUDGE_MODEL/_BASE`（NL 断言判分）、`reports/model_resource.json`（consumer 模型 id）。

## 重要边界

- 本实验不改 vendor；不覆盖 078/110/115 的库、账本或结果；新账本独立。
- B0/B1 消费者与工具完全相同，仅 skills 目录不同；技能只以原生发现/read 使用。
- 工具调用由 τ² orchestrator 唯一执行（挂起-转发），写操作不会重复执行。
- test task 9 不得用于调提示、演示或生成技能；本目录未接触该题。
- 空格/未知用法：费用未知不填 0；基础设施错误按原生口径排除并公开数量与分母。
