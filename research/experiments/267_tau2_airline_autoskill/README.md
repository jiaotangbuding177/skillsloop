# 267 · AutoSkill × τ²-bench Airline（文本域）

状态（2026-10-05）：**实验完成**——dev 4/4 ✓；采集 26/26（均分 0.72）；学习+冻结 ✓（1 技能库）；**配对评测 160/160 完成：B0 0.675 vs B1 0.725（+5.0pp，p=0.503），技能真实读取率 100%（80/80）**。最终报告：`reports/final_report_267.md`；记忆 289。
学习口径：AutoSkill 原生链路盲提取（无成败标签；26 条=19 成功+7 失败混合）——解释时必须保留"无成败监督"限制。
运行保障与事故记录：自愈循环 + Windows 守护；WSL 循环重置事故见 `memory/280_2026-10-04_airline_telecom_domains_and_wsl_incident.md`。

- 协议：`protocol.md`；版本：`versions.json`；参数：`experiment.yaml`；分集：`split_manifest.json`
- 用户决策（2026-10-04）：airline 与 telecom 均用当前 deepseek-flash 消费者/模拟器；banking_knowledge 暂缓（无官方 split）
- 架构与纪律沿用 148（挂起-转发 MCP bridge、v6 原生 `$技能` 引用、判分补丁、独立账本、失败如实记录）

## 目录

```
protocol.md / versions.json / experiment.yaml     协议三件套
split_manifest.json / private/                    分集审计（含 dev 选择与相关性发现）
inputs/                                           airline 冻结数据（tasks/split/policy/db，sha256 记录）
vendor/tau2-bench                                 τ²-bench v1.0.1（fc0055dc，由 148 逐字节复制，未改）
scripts/                                          run_wrapper / tau2_openclaw_agent / mcp_retail_bridge /
                                                  openclaw_config / model_relay / audit_split / 分析脚本
runtime_py/                                       本实验 venv（editable 指向本目录 vendor）
runs/ ledger/ reports/ private/                   运行时产物（ledger 独立于 148）
```

## 批次计划

1. dev 联调（4 题）→ 2. 演化采集（26 题）→ 3. AutoSkill 学习与冻结 → 4. 配对评测（20×4×2=160 场）→ 5. 报告
