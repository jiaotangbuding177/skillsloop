# 实际轨迹下载、逐步核验与模型出处

日期：2026-10-04。用户要求实际下载并逐点检查，不以文献描述代替文件检查。本轮仅下载公开数据和只读分析，未启动实验、微调或配对评测。

## 直接结论

1. RecreationWorld 当前公开发布包的全文件清单扫描没有找到完整 agent rollout 下载；公开任务运行时会新生成轨迹，这与已有轨迹公开发布不是同一件事。不能回答一个未取得的官方轨迹文件来自训练前还是训练后。
2. 本轮实际取得 ProCUA-SFT 的完整单条 JSON 和全部8张截图。官方卡片明确采集模型为 Kimi-K2.5；原文件 `metadata.pipeline=kimi`、Ubuntu VM、1920×1080、OSWorld式初始化、PyAutoGUI操作。这是生成下游SFT数据的教师轨迹，不是下游学生微调后的轨迹。原文件无精确模型checkpoint/API版本，不能声称是裸预训练base，也不能证明教师没有其供应方的既往训练。
3. 已有 AgentNet 样本是人工桌面演示及合成标注，不能将其称为某个模型增强前/后的执行。
4. 本地 RecreationWorld canary 来自原配置 GLM-5.3-Flash、无外部skills基线，没有经本项目额外SFT。Claude Code日志的 `claude-opus-4-8` 为兼容别名；实际共享网关请求及响应均标识 GLM-5.3-Flash。

## RecreationWorld 发布范围实查

下载 `Qwen/RecreationBench` 全量文件清单，共93,739项，固定revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95`。文件清单和路径扫描结果在 [审计目录](233_trajectory_audit/)。关键词命中的conversation/checkpoints/train均为参考网站图片或页面。扫描并非逐个下载所有资产，不把这个结果扩展为作者从未内部生成轨迹。

另下载官方网页脚本及公开analysis/leaderboard/gallery数据；它们提供汇总分析和展示资产，未发现完整rollout下载入口。论文§3.1说 Qwen3.8-Max 在 RecreationWorld agentic framework 中生成训练轨迹，按行为验证选择35,000条，再SFT Qwen3.7-Plus和Qwen-Flash-CPT。这里教师数据与训练后学生执行严格区分；论文描述不替代尚未公开取得的原始文件。[论文](https://arxiv.org/html/2609.22000v1#S3.SS1)、[公开包](https://huggingface.co/datasets/Qwen/RecreationBench)。

## ProCUA：实际下载的样本0028

- 来源：[官方数据卡](https://huggingface.co/datasets/nvidia/ProCUA-SFT)，revision `120de7e954f851c2d24399230367f2b01ff815f9`，首个tar.zst分片中的 `part_1/cpu-0047--20260303_074022/0028/trajectory.json`。
- 下载范围：32MiB压缩分片前缀；解码取得完整20,127字节JSON及8张1920×1080截图，不是全数据集下载。解码器读到JSON时已消耗6,029,450压缩字节，不能把它与HTTP下载总量混为一谈。
- JSON SHA256：`44c4cff2eb02d3ad641a40b6520148f492a01942692adab8d764f74c20eadeb6`。
- [原始JSON](233_trajectory_audit/procua_first_trajectory.json)、[逐步审计](233_trajectory_audit/point_by_point_audit.json)、[下载出处](233_trajectory_audit/procua_download_evidence.json)。
- 任务：将VS Code Window: Title从`${activeEditorShort}`替换为`${activeEditorLong}`，显示完整文件路径。

| 动作序号 | 实际操作 | 截图核验 |
|---|---|---|
| 初态 | VS Code设置页已打开 | 0-0，目标值含activeEditorShort |
| 0 | 向下滚动3格 | 0-1，设置页面滚动 |
| 1 | 向下滚动2格 | 0-2，目标输入框进入操作位置 |
| 2 | 点击输入框 | 0-3，输入框获得焦点 |
| 3 | Ctrl+A | 0-4，原值被选中 |
| 4 | 输入新标题模板 | 0-5，activeEditorLong清晰可见 |
| 5 | Enter | 0-6，标题栏发生变化 |
| 6 | 向上滚动3格 | 0-7，新设置保留 |
| 7 | done / success | 复用0-7，agent声明完成 |

8张截图已逐张视觉查看，操作与图像变化相符。局限：初态已打开设置页，不能证明其完成了从零启动与定位流程；没有打开一个实际文件展示完整路径，也没有独立成功评分。`osworld_setup.instruction`实际上是创建Desktop/test.py，沿用的evaluator检查文件存在，与本条新goal不相同，不能直接用它给新任务评分。只观察到模板设置改变，不把done当客观成功。

数据卡说明Kimi-K2.5同时承担目标生成、前置条件验证、桌面rollout；采集环境来自OSWorld式配置。未披露本样本精确采集harness源码版本或checkpoint hash。它是截图—动作交互，用户给一个目标后agent连续操作环境，不是用户每步参与的多轮会话。

## 两个既有样本对照

AgentNet `0030dc52-2a4a-4c0e-895b-48284c200efe` 有7步：打开GIMP、Ctrl+O、选择桌面图片、菜单点击与悬停、最后声明failure；`task_completed=false`，该字段由数据卡所述summarizer合成，不能当隐藏验证器分数。人工演示与自动补充文本分开解释。[官方卡](https://huggingface.co/datasets/xlangai/AgentNet)、本地原始文件 `research/experiments/218_recreationworld_glm_pipeline/external/AgentNet/schema_sample.json`。

本地RW `recreation_eval_baseline_1791032747410611525`：Claude Code 2.1.177、Playwright MCP connected、官方Web容器，205条JSONL记录、91个tool_use记录（未去重，不等同91次唯一执行）。工具含Bash/Read/Write及浏览器导航、snapshot、截图、点击；兼容日志别名不作为模型证据。共享账本012255的route指向该run，request model和model_reported均GLM-5.3-Flash，completed/response_complete=true。该run无skills_library；原生程序分0.0、VLM分null、score_passed=false。`passed=true`只是进程完成，不能称任务成功。历史API传输失败保留，未重写评分。

## 与研究设计的关系与未知项

证据支持：公开教师演示可做AutoSkill输入，来源不要求必须由GLM产生；但跨agent/环境迁移效果尚未验证。ProCUA桌面设置操作不等同RW软件复刻任务，两者不是官方train/test配对。不能用一个样本建立整个数据集质量或训练收益结论。

未知：官方RW训练池和35,000条原轨迹获取；ProCUA教师精确checkpoint及采集harness版本；外部GUI技能能否改善GLM的RW复刻评分。建议保持原GLM基线，再用独立训练来源沉淀并冻结技能后评测，不能把测试轨迹回流训练后仍称该题held-out。
