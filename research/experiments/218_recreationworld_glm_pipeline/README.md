# RecreationWorld × GLM × AutoSkill：独立管道

用户2026-10-03授权调研公开执行轨迹并搭建管道。此目录与115/196/208运行、库、端口和成绩隔离。当前版本 `rw_web_glm_pipeline_v2_lf`；v1 Windows CRLF基础设施失败保留在history和runs，未记agent零分。

## 数据与边界

官方源码commit `b5cda868f44932dc84ea68e3b3053bc418621aa3`；官方测试包revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95`。318文件的corravale.example由下载前“文件数最小、名称排序破同分”确定，仅基础设施canary，从最终统计排除。源包按SHA校验，WSL路径 `/var/tmp/skillloop_rw218/datasets/released` 保留POSIX问号文件名；Windows staging用路径哈希，不重命名benchmark内部资源。

公开训练候选：

| 来源 | 类型 | 当前核验 |
|---|---|---|
| [AgentNet](https://huggingface.co/datasets/xlangai/AgentNet) | 22.6K人工示范，文字推理由发布方合成，MIT | 固定revision下1条7步JSON与7张真实截图完整验收；官方AutoSkill processed1/failed0/skipped0，返回0技能 |
| [ProCUA-SFT](https://huggingface.co/datasets/nvidia/ProCUA-SFT) | 93,566条模型生成执行轨迹，CC BY4.0 | 官方API索引/卡片核验；tar.zst含trajectory.json与截图，尚未本地下载 |
| [RecreationBench](https://huggingface.co/datasets/Qwen/RecreationBench) | 250题测试任务包 | 可执行环境不是已采集轨迹；论文35K训练轨迹公开下载未核实，不把测试包当训练集 |

AgentNet/ProCUA与应用复刻存在领域差异，不能宣称同分布或保证技能增益。测试题及其reference/tests/ground truth不得入学习池；训练来源按应用/网站/项目家族审计，保留所有真实失败/UNKNOWN，不按成绩选择。

## 已实现入口

PowerShell下载固定任务，WSL执行官方Linux脚本。现有Python：`/var/tmp/skillsloop078/runtime_py/bin/python`。

```powershell
./scripts/Prepare-Inputs.ps1
./scripts/Get-Trajectory-Sample.ps1
```

```bash
cd /mnt/d/skillloop/research/experiments/218_recreationworld_glm_pipeline
PY=/var/tmp/skillsloop078/runtime_py/bin/python
$PY scripts/pipeline.py materialize
$PY scripts/pipeline.py check
$PY scripts/pipeline.py setup
$PY scripts/pipeline.py reference
$PY scripts/pipeline.py canary --arm baseline
```

`freeze`仅用于新的准备版本，不能为绕过运行中失败更新freeze。`probe`已真实验证两个随机图像和原生工具参数；3次调用均HTTP200。还须实际canary证明Anthropic代理、原生Claude CLI、浏览器MCP与截图链路。镜像使用原Dockerfile；派生Dockerfile218仅把容器内GitHub下载改为固定commit相同源码COPY，不改执行/评分代码。Ubuntu缓存摘要已与官方注册表一致；原官方Dockerfile/首次构建失败均保留。

Docker运行仅挂本项数据/结果/入口；保留官方非root agent、隐藏评分root目录和网络namespace。SYS_ADMIN/NET_ADMIN用于创建封闭namespace，agent由官方setpriv丢弃全部capabilities。模型只经原8129累计账本，真实凭据留在原服务，容器只有local占位符。无STOP时锁防双启动；每次attempt独立命名、结果不覆盖。官方metrics的infra_error/score null不能当0；真实低分不挑高重试。

## 学习与消费

`trajectory_ingest.py`逐题验证所有截图存在、唯一、可解码、SHA和原序，缺图直接拒绝；真实UNKNOWN保持null。动作和发布方观察完整保留，合成观察明确标注，thought不入学习输入。当前AutoSkill仍是文字trajectory学习：截图保留作来源，不声称SDK读取了像素。

`learn_external.py`调用官方 `extract_from_agentic_trajectory`，success_only=False、消息/事件不限、原GLM和ECNU1024维、原生维护/导出；新空命名空间、旧共享代码只读、embedding证据复用已验收adapter。输入manifest须含公开来源和与eval家族隔离审计、逐输入SHA；截图缺失不接受，失败/部分库保留。完整GIMP失败示范已通过一次真实功能验收，返回0候选，没有触发embedding；不把空库当技能消费验收，不按产出挑换样本。

官方CLI默认 `--disable-slash-commands`，因此此研究采用显式派生消费协议：共同的CLI原生 `.claude/CLAUDE.md`说明，技能组只增加名称/描述/路径目录，模型按需用原生Read读导出的SKILL.md。不改官方agent循环，不预读全部技能正文。不能称启用了官方Skill工具，也不能称论文原样prompt基线。

```bash
$PY scripts/pipeline.py canary --arm skills --library libraries/<accepted-label>
$PY scripts/audit_skill_reads.py runs/<attempt>
```

只接受本218新库；不借用运行中的208库。审计只报原生Read调用，须另外检查成功tool回执与完整native session后才认定消费；提到技能、目录已挂载均不算。无/有技能使用相同CLI/任务/模型/基础上下文/预算/评分和独立干净容器，不把canary或调试重试放入正式效应统计。

## 尚未验收

- 运行状态以reports/pipeline_status.json及对应原生metrics为准；启动不代表端到端通过。
- 完整截图单条验收已通过；大样本家族隔离、非空语义库及真实SKILL.md Read消费仍待验收。单条验收不证明数据集技能产出。
- v2参考评分原生program_score=0.9975，但公开包缺GT截图，SSIM逐页no_gt_screenshots却总visual=0，原task_score=0.4987保留且禁止作为正式对比。不是agent失败；不补造GT或覆盖原分。
- 官方VLM judge用GLM与固定4条公开断言已真实通过调用/解析验收。新增独立`scripts_judged/pipeline.py`、`reports/judged_v3/`版本`rw_web_glm_pipeline_v3_glm_judge`，使用官方视觉断言与GLM独立judge路由，加入archive SHA及judge acceptance门禁；v2源码/冻结/活跃run保持。GLM也作为agent，judge与论文不同且非独立模型，需要披露偏差；尚未完成981断言全题评分。
- 没有启动250题全量、自动配对评测或改变原Co-Gym定时任务。

## 已验收及下一入口

v1 CRLF与v2缺归档两次基础设施失败均保留；源站点原文件不改，按官方契约打包`reference.tar.gz`并保存SHA，setup恢复exit0。6项输入契约测试通过。v2原生CLI单题canary已启动：实际浏览器导航/截图/点击、文件写入与图像输入已出现，原生工具ID去重统计保存在对应run的`native_transport_acceptance.json`，上游账本精确GLM模型。该run仅管道验收，非正式基线。

```bash
# v3独立配置，沿用同一锁，不与v2活跃任务双启动；先等待旧canary结束
$PY scripts_judged/pipeline.py check
$PY scripts_judged/pipeline.py reference
$PY scripts_judged/pipeline.py canary --arm baseline
```

AgentNet仅取所需截图：公开分片ZIP中央目录定位 → HTTP Range → 原ZIP CRC/长度 → PIL解码 → 原序canonical SHA；脚本在`external/AgentNet/`，不属于或修改旧冻结agent运行。来源GIMP失败示范不涉及当前Web复刻评测家族，审计只适用这一条与当前canary；扩大实验必须重新审计全量来源家族。
