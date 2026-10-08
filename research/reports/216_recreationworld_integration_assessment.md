# RecreationWorld 接入研究闭环的可行性评估

日期：2026-10-03。范围：阅读和源码审查，不部署、不运行新实验、不改变当前 208 学习。

## 结论

可以将官方 RecreationWorld 作为独立的 hybrid computer-use 任务环境、执行与评测底座，将 SkillsLoop/AutoSkill 放在官方轨迹输出与后续任务执行之间。不是现成的企业会话技能闭环，也不是通用纯 GUI 办公 benchmark；任务是探索参考应用并交付可运行的独立复刻源码。

该判断来自论文、官方任务卡及公开源码静态审查，尚无本地端到端兼容实测。接入收益、技能产出和机器吞吐均未知。

## 已核实的上游能力

- 官方论文：[RecreationWorld, arXiv:2609.22000](https://arxiv.org/html/2609.22000v1)。输入为任务描述和运行参考应用，agent 自主探索、编码、运行、检查与修复。参考是行为 oracle；隐藏测试由参考运行验证并经人工复核冻结。论文以筛选的 35,000 轨迹做 SFT；这不同于本项目外置 skills 学习，不据此声称完整训练轨迹已公开。
- 官方框架：[QwenLM/RecreationWorld](https://github.com/QwenLM/RecreationWorld)。五平台各50题，共250题；环境、原生工具、批量控制器与评测可复用，框架 MIT，参考资产遵循各自上游许可证。
- 官方数据：[Qwen/RecreationBench](https://huggingface.co/datasets/Qwen/RecreationBench)。公开 test250；任务包独立于仓库，包含参考与测试，不能只下载 Dataset Viewer 的索引就声称环境齐备。文件树显示总约23.9GB，本轮未下载全部任务。
- [Linux部署文档](https://github.com/QwenLM/RecreationWorld/blob/main/docs/providers/linux.md)支持用户管理 ECS/Docker 或 FC Sandbox；并非必须购买官方云服务。
- [Web部署文档](https://github.com/QwenLM/RecreationWorld/blob/main/docs/providers/web.md)提供 Playwright MCP、冻结任务包、metrics、轨迹、截图、候选产物；正式评分需要网络隔离，VLM judge需显式开启。

## 与项目的关系

共同点是：任务执行产生轨迹，运行反馈验证产物，再将经验用于后续任务。差异在于：上游学习目标是参数微调与混合GUI/编码能力，本项目学习对象是可审计、可检索、可复用并持续演化的skills；企业会话、个人/组织共享和反馈采纳不由上游提供。

建议闭环：官方任务与隔离环境 → 官方原生CLI agent执行 → 原始会话、工具回执、截图、代码产物和评分 → 本项目轨迹治理与官方AutoSkill抽取/维护 → 冻结skills库 → 同一原生CLI执行留出任务 → 官方评分对比。

跨任务skills只能进入被授权的agent工作区。隐藏测试、参考源代码与评测答案保持隔离；学习材料限定于agent可见执行记录和允许的反馈，不能把评测答案转成技能。按应用/源码家族划分学习与评测，避免同项目多平台泄漏。使用公开test题做交叉学习时须称新的交叉验证协议，不能冒称官方未改动test成绩；优先另建不重叠演化应用池。

## 源码审查证据

本轮公开源码快照位于 `research/references/216_recreationworld/source/RecreationWorld-main/`；仅下载与阅读，没有安装或执行。main快照尚不构成正式实验冻结版本。

- `scripts/core/agent_invocation.py`：原生Claude Code/Codex统一调用；initial/continue/resume，默认72000秒任务预算，原始进程与terminal JSONL区分completed/budget_exhausted/terminated/infra_error。不是SP Agent或OpenClaw的现成适配。未知agent名会归入claude，不能以传入openclaw就宣称支持。
- `scripts/core/agent_config.py`：原生CLI与MCP配置，默认单agent、禁联网检索和人类问答工具。这不是Co-Gym模拟用户协作协议；若研究人机协作需新版本。
- `scripts/core/model_endpoint.py`：模型端点协议配置存在，但不证明当前8000接口已兼容Claude Code/Codex，更不证明图像输入可用。论文GLM-5.3只收结构化GUI、不收截图像素；GLM-5.3-Flash端点必须独立验收，不能混为同配置。
- `scripts/core/trajectory.py`：同时采集stream JSONL与原生session，统一五平台；session拷贝默认64MiB上限，超限跳过而非截断。正式技能学习必须检查采集完整性，保留本地全记录或使用上游配置，不把被跳过日志当完整轨迹。
- `src/recreation_bench/result.py`：None明确为未评分，与0不同；outcome_class区分completed/data_error/infra_error/terminated，另有reason_code/result_complete/retryable。复用这些字段有助于延续本项目有效0、未交付与UNKNOWN的证据纪律，不保证上游无bug。
- 搜索SKILL.md、skills目录、AutoSkill/OpenClaw，仅发现Android脚本一条Claude skill安装注释，未见统一跨任务发现/学习/维护/冻结/复用接口。可由原生agent消费外接库，但正式挂载、读取证据与重置隔离尚需验收，不能认为注释已经实现技能设施。

## 建议的最小接入

先做Web独立pilot，保留官方完整harness与评分；选不同类别的少量任务验收参考启动、原生工具、源码提交、评分和日志完整，再扩到官方50道Web。Ubuntu作为第二平台，Windows/macOS/Android后续独立配置。该顺序是工程建议，不是已验证成本结论；Android官方建议32vCPU/128GiB/KVM，不应默认当前电脑具备。

外接模块只承担轨迹入库与脱敏、分集/版本、skills原生安装与读取审计，以及学习阶段调度。评分不自写，原生CLI不换成自写agent loop。无/有skills使用同模型、原生CLI版本、MCP、任务环境与预算；同时报告官方Prog/VLM、构建启动、成本/工具调用、错误类别和技能读取，而非只比技能数量。

需要单独预检：任务包与fixture、隔离和reset、原生CLI模型协议、视觉输入、独立VLM judge、构建依赖、日志尺寸及资源预算。论文任务级20小时为最大允许预算，不代表每题需要20小时；若缩短须统一两组并披露新协议。

## 当前边界

本轮完成资料审查与接入建议。没有启动RecreationWorld实验，没有改208冻结输入/代码/模型或中断原学习。开放集能检验技能迁移，但不能替代企业会话主线的真实需求、共享治理与使用反馈证据。
