# 直接生成管道：源码与原链路复用清单

本版主入口是 `trace_to_skills.py`，只运行原始经历到冻结skills库的生成侧。完整命令见 [DIRECT_PIPELINE_README.md](DIRECT_PIPELINE_README.md)。

## 本轮新增算法文件

| 文件 | 职责 |
|---|---|
| `skilldemo/library_pipeline.py` | 串联分批输入、恢复、局部核对、全池聚合、封装与冻结；预算、锁和精确复入。 |
| `skilldemo/local_experience.py` | 抽取局部方法并核对动作来源、行动方、原评价范围、条件、依赖、反证；无损模型输入索引。 |
| `skilldemo/workflow_induction.py` | 程序对齐步骤、输入输出角色与依赖，保留成员条件路径，按正结构压缩收益合并。 |
| `skilldemo/library_export.py` | 把方法和边界写成标准SKILL.md，失败／冲突／计划不充当成功步骤，官方打包、冻结清单与验真。 |
| `skilldemo/experiment_input.py` | 导入τ²可见轨迹，保留原顺序、双方工具调用和回执，默认不导入隐藏金标。 |
| `import_experiment_traces.py` | τ²输入适配命令行。 |

## 直接复用的原链路文件

这里的“原链路”指此前独立Demo的链路，不是InsightWeaver生产代码。新管道没有调用企业服务。

| 原文件 | 本版复用的内容 |
|---|---|
| `skilldemo/pipeline.py` | `normalize_input`统一E/C/V、`prepare_events`整理回合、`Requests`保存请求／预算／精确响应复用、`write_json`保存中间产物。原legacy生成仍保留。 |
| `skilldemo/relational.py` | `prepare`构造关系输入、`compile_result`完成有界约束关系恢复；原任务／要求／尝试／反馈关系。 |
| `skilldemo/intake.py` | 原始会话、事件、顺序及回合整理，由前述输入准备调用。 |
| `skilldemo/evidence.py` | 双方工具证据、背景与稀疏评价的标准化与来源索引。 |
| `skilldemo/pair_detection.py` | 原问答片段、引用和候选任务的校验，由关系恢复调用。 |
| `skilldemo/recovery.py` | 原关系、要求及轨迹恢复约束，由关系恢复调用。 |
| `skilldemo/runtime.py` | 模型请求配置、结构化调用、解析、摘要指纹、技能格式校验。本轮增加两个请求用途及提示接入。 |
| `skilldemo/live.py` | 本机环境配置读取及运行时使用的技能／读取证据工具；新入口使用`load_env`。 |
| `skilldemo/bootstrap.py` | 定位现有OpenClaw官方skill-creator，并调用官方打包脚本。 |
| `skilldemo/creator.py` | 复用格式、文件和包的校验；不调用旧模型creator重新生成方法。 |
| `skilldemo/detection.py` | 被证据及分片模块引用的原文本辅助处理。 |

`skilldemo/workflow.py`、`relational_workflow.py`、`workflow_index.py`仍作为原`pipeline.py`的模块依赖及legacy算法保留，**新默认路径的聚合执行器是`workflow_induction.py`**。其他`skilldemo/*.py`随包保留：新运行的源码指纹会保存整个包，既避免缺依赖，也保留旧Demo测试的可运行结构；不表示新入口执行了用户／组织／自进化阶段。

## 外部官方依赖

官方封装使用以下本机安装文件，第三方运行时不复制进本仓库：

- `.runtime/node_modules/openclaw/skills/skill-creator/SKILL.md`
- `.runtime/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py`
- `.runtime/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py`

新机器可用原安装脚本 `python scripts/install_openclaw.py` 安装固定版本；Windows兼容修正在 `scripts/patch_openclaw_windows.py`。官方脚本缺失时，默认入口在模型调用前停止；显式`--structural-only`只做源码结构输出，不冒充官方封装。

模型配置使用本机`.env`或`--env-file`指定路径；配置字段见原 [LIVE_AGENT.md](LIVE_AGENT.md)。`.env`、运行时、原会话、付费请求响应与生成产物不随本次算法提交上传。

## 本版对应测试

核心新增测试是 `test_local_experience.py`、`test_workflow_induction.py`、`test_experiment_input.py`、`test_library_pipeline.py`及`test_library_export.py`。`tests/`同时保留旧路径回归。

```powershell
python -X utf8 -m unittest discover -s tests
```

此前本机安装依赖齐全的最终验收为416项通过；新机器未安装官方creator时，有关测试可能跳过，必须查看实际测试输出。结构检查不证明技能效用，完整真实验收边界见研究实现报告。
