# Trace2Skill 原生强基线接通实验

本目录与之前的 ECNU 简化试跑完全分开。原试跑、失败和费用不覆盖。

## 采用的原链路

固定作者源码 `3d0b52a140f002a512930252b613c49048f7d5ac`。成功轨迹使用作者单次成功分析及原解析器；失败轨迹使用作者 Agentic 诊断、最小修复和真实外部评分，只有通过标记才可进入学习。下游使用作者 MAP、分层 MERGE、定位翻译、程序修改和默认格式检查／修复。完整演化目录本身就是技能交付物，另加的归档不修改内容。

`native_runner.py` 只负责编排这些函数；`audited_runtime.py` 负责记录真实请求和 Windows Bash 兼容；`cache_isolation.py` 隔离失败分析缓存。作者源码不改。`profiles.json` 明列发布命令默认合并批5与论文v5合并批32的差异，本轮付费演化选择32。受服务资源限制并行度4，公开校准执行串行，不比较论文延迟。

## 企业数据与本轮局部案例

来源仍是当前真实数据的13分区、1224会话、719局部学习候选。`enterprise_readiness.json` 与 `private/enterprise/qualification_registry.jsonl` 登记全部来源；32个来源哈希及4042个消息成员已复核。24个任务族提案只是外层规划，不是作者算法生成的24个技能。

本轮可客观核验的局部案例来自现有 DATA 主题：每人年薪折算月薪。完整用户与AI正文保留；同一回复内现金、团队、文件断言仍未知。`private/enterprise_analysis_001` 保存实际成功分析及明确领域边界；原任务名词和可见材料说明做了公开的领域接口替换，未换掉分析器、输出结构或最多3条经验的限制。

`private/enterprise_evolution_001` 使用作者原始人工 xlsx 技能作为初始技能，属于 **Self-deepening**。不声称复现从零生成初稿的 Creation 设置。该案例只有1条成功经验，所以原生 MERGE 被跳过；不能补造轨迹凑这个步骤。最终技能见 [交付说明](deliverables/README.md)。

## 校准与执行门槛

公开校准拟单独使用作者 verified400 中的13-1、17-35，不替换企业主数据。评分区补上源数据已有的工作表名，避免原裸范围误评分另一张表。初始技能、原消费者、原评分器和全部轨迹均保留。

工资消费验收是研究人员事先构造的两道新任务，每组比较相同四个工资值；它们不是新增企业历史、公开benchmark或论文增益实验。`salary_controls.py` 创建输入与独立真值，原评分器的正确／错误样例已通过免费核查。采用相同原消费者、工具、模型和seed41，分别隔离加载初始和演化技能；模型不拿真值。

在 LibreOffice 实际缓存控制通过之前，不启动公式任务。已保存的失败控制证明原重算脚本的“成功”文字不足以验收；必须实际读到计算值，同时拒绝除零错误。MSI只在本项目内解包，不作系统安装。任何后续 Windows 宏兼容都单独记录。

## 免费控制与付费结果分开

- `private/offline_equivalence_utf8_final/result.json`：原机制的合成捕获／回放，包括2 MAP、1 MERGE、2定位翻译及默认修复；0模型，不代表效果。
- `private/outer_rollout_guard_audit_20261006_2/result.json`：实际原消费者及输入复制，在模型前明确停止；0模型。
- `private/cache_isolation_control_20261006_v2/result.json`：原客户端构造与缓存隔离；0模型。
- `private/salary_controls_free_001/free_audit.json`：两道新题的原评分正反例；0模型。
- `private/enterprise_real_call_replay_001/result.json`：原SDK及算法精确回放保存的三份真实响应，完整请求／原网络body SHA／method／URL一致，三个生成文件SHA与付费产物全等；0新模型／网络。只证明保存结果可重现，非独立模型复跑或业务收益。
- `private/model_probe_001`、`private/enterprise_analysis_001`、`private/enterprise_evolution_001`：实际付费请求、参数、响应及用量逐次保存。真实调用数以请求账本为准，不使用演化器的估计计数。

启动时必须 `python -X utf8 -B`，从 `private/runtime_preflight/runtime` 工作目录执行，那里有实际检查器。凭据只通过进程环境传入，不写源码或说明文件。每次运行新建目录；冻结源码、输入、配置和预算，结束复核，失败也保留。

实际格式检查器源于OpenClaw2026.9.5，本地SHA及真实正反例见 `runtime_readiness.json`；按作者原调用运行，但不能认证论文同版本。两个既有付费阶段保存了外层wrapper哈希，未保存完整旧源码；回放没有补造这一缺项。未来入口已增加完整编排源码副本与结束哈希复核，初始／最终技能、原核心及完整请求响应仍可查。

当前Windows公式缓存未通过，现有Docker单次隐藏启动后有界及延迟检查仍无可用服务。`linux_runtime/` 已备环境模板，尚未构建。公式执行入口要求实际缓存控制通过的环境证明，否则在API前停止；公开校准与新工资题消费均未运行。

## 尚不能宣称的结果

ECNU响应模型名为 `qwen3.8-flash`，不是论文模型；接收思考开关参数不证明实际模式生效。作者原弱初稿／准确初始化提示未在当前发布版本找到；固定commit早于论文v5，版本映射未证。学习验证选seed41/42/43、独立留出和各主题多技能生成仍须另作实验。719条登记不是719条认证成功轨迹，本轮也不证明技能增益或轨迹恢复优势。
