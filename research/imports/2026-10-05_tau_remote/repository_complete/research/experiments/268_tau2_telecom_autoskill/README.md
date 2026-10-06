# 268 · AutoSkill × τ²-bench Telecom（文本域）

状态（2026-10-05）：**实验完成**——dev 4/4 ✓；采集 70/70（均分 0.75）；学习+冻结 ✓（1 复合技能，30 文件）；**配对评测 320/320 完成：B0 0.7937 vs B1 0.7438（−5.0pp，p=0.341），技能真实读取率 100%（160/160）**。最终报告：`reports/final_report_268.md`（含三域并列）；记忆 291。
学习口径：AutoSkill 原生链路盲提取（无成败标签；70 条=52 成功+18 失败混合）——解释时必须保留"无成败监督"限制。
运行保障与事故记录：自愈循环 + Windows 守护；WSL 循环重置事故见 `memory/280_2026-10-04_airline_telecom_domains_and_wsl_incident.md`。

- 协议：`protocol.md`；版本：`versions.json`；参数：`experiment.yaml`；分集：`split_manifest.json`
- 用户决策（2026-10-04）：telecom 用当前 deepseek-flash（接受 flash 级模型绝对分可能很低）；banking_knowledge 暂缓
- 本域特点：奖励 100% ENV_ASSERTION；用户模拟器带 30 个用户侧工具；任务 ID 编码类别/子问题组合/PERSONA

## 目录

```
protocol.md / versions.json / experiment.yaml     协议三件套
split_manifest.json / private/                    分集审计（含 dev 选择与相关组件）
inputs/                                           telecom 冻结数据（tasks/split/policy/manual/db，sha256 记录）
vendor/tau2-bench                                 τ²-bench v1.0.1（fc0055dc，由 148 逐字节复制，未改）
scripts/                                          同 267 管线（域参数化）
runtime_py/                                       本实验 venv（editable 指向本目录 vendor）
runs/ ledger/ reports/ private/                   运行时产物（ledger 独立）
```

## 批次计划

1. dev 联调（4 题，含用户侧工具链）→ 2. 演化采集（70 题）→ 3. 学习与冻结 → 4. 配对评测（40×4×2=320 场）→ 5. 报告
