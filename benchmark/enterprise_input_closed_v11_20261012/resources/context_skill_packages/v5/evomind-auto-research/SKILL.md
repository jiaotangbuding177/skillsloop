---
name: evomind-auto-research
description: 在 OpenClaw 中组织具有持久化阶段与角色提示的连续研究任务，记录材料、设计、实验、写作与反思，适用于用户明确启动研究项目或询问该项目进度。
---

# 连续研究工作区

这是实验环境的上下文拟造适配包。被动框架来自公开 Sibyl 固定提交 `c30c2168843a9dea8404cde4bab639c9ff8fc8b9`；EvoMind 原 OpenClaw 外层未找到。本包恢复所观察到的工作区与命令能力，不认证历史同版。角色提示位于 `third_party/sibyl_framework/sibyl/prompts/`，作为此包的参考资源使用。

从本 skill 目录执行，工作区使用当前任务独立路径，例如 `/workspace/evomind-auto-research`：

```bash
python scripts/sibyl_cli.py init --workspace /workspace/evomind-auto-research --topic-file /workspace/topic.txt
python scripts/sibyl_cli.py status --workspace /workspace/evomind-auto-research
python scripts/sibyl_cli.py next --workspace /workspace/evomind-auto-research
```

`next` 返回当前真实阶段、需要完成的材料，以及上游角色提示。结合当前用户需求和已经获得的材料执行该阶段；参考提示中的具体平台能力必须按本实验现有工具适配。保留来源、搜索证据、假设和观测的区别。量化交易研究需要验证数据区间、时间切分、交易成本、基线与回测证据；没有实际实验数据不能写实验成功或收益数字。

阶段完成后提交文件证据：

```bash
python scripts/sibyl_cli.py record --workspace /workspace/evomind-auto-research --stage literature_search --artifact context/literature.md
```

必须提供 `next` 所列的全部所需文件；`record` 仅核验文件与登记状态，不认证材料的学术质量。决策阶段需要实际结构化 `decision`，不以存在文件自动当作决策通过。检索、生成、工具执行、模型或GPU计算仍由任务执行者按真实需求完成，命令不会在后台启动全量研究队列。

`topic.txt`、`context/`、`idea/`、`plan/`、`exp/`、`writing/`、`logs/`、`status.json` 保存同一研究项目的连续状态。已有工作区保持原主题，不重新初始化覆盖。暂停或停止状态不会被 `next` 或 `record` 自动解除。

反思材料准备完成后：

```bash
python scripts/sibyl_cli.py evolve --workspace /workspace/evomind-auto-research
```

它读取当前工作区 `reflection/action_plan.json`，按固定上游规范化经验建议并登记原文件SHA，产出 `logs/evolution_inputs.json`，不会把建议冒充已验证的技能改进。本阶段之外的实际跨项目学习、技能更新与效果评测另需真实执行和验证。

兼容模块命令 `python -m sibyl.openclaw_adapter` 使用相同子命令。固定上游的直接提示接口是 `load_prompt('innovator', overlay_content='', workspace_path=workspace)`；观察到的 `load_prompt(Config(), 'innovator', workspace)` 是不同外层调用，不适用于本固定上游。
