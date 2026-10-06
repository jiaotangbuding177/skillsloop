# Skills Loop：独立科研 Demo

纯文件实验入口：`python -X utf8 trace_to_skills.py --input <X文件> --output <新目录> --max-calls 2`。当前默认是关系恢复、局部证据核对、程序工作流归纳和冻结技能库；每批两次模型提议，聚合／封装不调用模型，无账号／数据库前提。先用 `--preflight-only` 核对实际批次数与预算。见[直接实验管道说明](DIRECT_PIPELINE_README.md)及[实施计划与验收矩阵](DIRECT_PIPELINE_PLAN.md)。原十二阶段入口和 `--algorithm legacy` 继续保留。

这是企业会话驱动 skills 涌现与持续演化的独立原型。真实对话、技能封装草稿与消费由 OpenClaw 执行。新的启发式管道把原消息、工具调用与结果、公开政策和稀疏评价一起输入：一次模型请求提出任务与关系，程序进行有界联合恢复，再用关系和结果范围约束workflow聚类与技能条款。重复聚合材料按无损索引传输；新技能正文由程序按冻结步骤及范围组装，保留模型草稿审计，仍由官方校验打包。Python 标准库负责SQLite事务、版本治理和本地页面。无 InsightWeaver、KM Agent、Redis、PostgreSQL 依赖。

真实模式默认使用 `heuristic`，旧路径保留为 `legacy`。新旧算法必须使用独立数据目录，不迁移旧库或覆盖旧实验。个人工作台 `/skills` 与 `/chat` 继续支持采纳、查看、下载、选版和真实对话，研究后台在 `/`。新算法见[实施规格](HEURISTIC_PIPELINE_SPEC.md)、[计划](HEURISTIC_PIPELINE_PLAN.md)与[本轮验收](HEURISTIC_PIPELINE_ACCEPTANCE.md)，历史验收见[阶段4/5](STAGES_45_ACCEPTANCE.md)、[旧方法契约](MULTITRACE_SPEC.md)、[Windows兼容](OPENCLAW_COMPATIBILITY.md)。

## 快速启动

在 PowerShell 中：

```powershell
cd D:\skillsgen-industry_track\enginering\demo
python scripts/install_openclaw.py
python demo.py doctor
```

安装脚本将 Node 26.1.0 与 OpenClaw 2026.9.5 安装到本目录 `.runtime`，不修改全局 Node 或现有 OpenClaw 配置。本机已经安装，可直接启动。

先体验无密钥合成闭环：

```powershell
python demo.py serve --mode replay --port 8765
```

打开 http://127.0.0.1:8765 查看研究后台，或进入 http://127.0.0.1:8765/skills 与 http://127.0.0.1:8765/chat 使用个人工作台。回放回答和技能是固定夹具，只演示链路。

真实 OpenClaw 模式（另一个终端／端口）：

```powershell
$env:DEMO_MODEL = '你的模型ID'
$env:DEMO_BASE_URL = 'https://api.openai.com/v1'
# 通过本地安全配置设置 DEMO_API_KEY；不要把密钥提交到仓库或发到聊天。
python demo.py serve --mode openclaw --learning-algorithm heuristic --port 8766
```

`DEMO_MODEL_API` 默认 `openai-completions`，要求服务提供兼容的 Chat Completions 接口；任务识别还支持 `anthropic-messages`。`DEMO_AGENT_TIMEOUT` 默认 180 秒，本机真实封装任务设为 300 秒；任务识别单请求超时由 `DEMO_DETECT_TIMEOUT` 控制（默认180秒，上限240秒）。未配置模型／密钥时真实模式明确失败，不退回夹具。启动时默认读取本目录 `.env`，进程环境优先；修改配置后重启服务。`DEMO_NETWORK_MODE=direct` 可绕开无效代理。配置模板、真实技能读取回执和 `live-check` 见 [真实模型操作说明](LIVE_AGENT.md)。

默认开启自动学习：回答稳定10秒后触发任务识别并封口，每2秒扫描。聚池等待120秒吸收同类任务，单例到期也处理，最多8条独立任务。用`--settle-seconds`、`--idle-seconds`、`--pool-wait-seconds`调整；`--no-auto-learn`关闭自动派发。`--daily-limit 20`限制每成员每UTC日任务识别与学习的**合计派发**，失败计入；不是内部请求或tokens硬预算。预算耗尽或识别无效时保留来源，不用词法规则补判，也不自动付费重试。

## 算法与可观察状态

```mermaid
flowchart TD
 A[原始消息与工具事件] --> B[来源 / 调用索引与问答视图]
 V[公开上下文与稀疏评价 可为空] --> B
 B --> C[一次模型提议任务 / 要求 / 关系 / 结果绑定]
 C --> D[程序联合恢复 / 要求继承 / 尝试与反馈轨迹]
 D --> E[用途/权限/使用基准门禁]
 E --> F[LLM提取workflow轮廓和方法]
 F --> G[程序约束聚类]
 G --> H[簇内方法合并 / 来源与关系依赖条款台账]
 H -->|NEW| I[冻结workflow]
 H -->|UPDATE| J[阶段9精确版本更新入口]
 I --> K[独立OpenClaw会话读取creator并写出SKILL.md]
 K --> L[宿主校验与官方打包]
 L --> M[/skills个人选择]
 M --> N[/chat选版执行、读取回执与产物]
 N --> O[反馈和后续演化]
```

启发式模式形成兼容当前治理的标准轨迹，保留要求的不同维度、真实动作与可见交付、反馈指向、稀疏评价范围和未决项。失败轨迹可保存高质量经验，缺结果的过程保持未验证；任务总分不会证明每个步骤都成功，准备做与自称完成不会变成已执行能力。阶段4仍由模型提出流程兼容关系，程序检查complete-link及全簇关系约束，合并时生成可回查的条款台账；阶段5沿用独立creator和官方包格式。历史047/049测试对应legacy路径，高频/重要性排序和训练模型尚未实现。

候选 `UNKNOWN` 可以正常生成和审核；不需要用户说“满意”。`SEALED` 仅表示暂时稳定；`COMPLETED` 仅表示运行结束；`CONTEXT_INJECTED` 仅证明把选中版本交给 agent，不能证明遵循技能或取得收益。只有实际反馈才改变证据。

技能包采用 `SKILL.md`（YAML name/description）与辅助文本文件；保留原项目市场信息五节，不把轨迹 JSON 当技能格式。新封装检查每个方法与每个工作流步骤的范围。UPDATE 必须保留未涉及文件；个人更新与组织发布检查基准版本及哈希；回滚产生新版本。组织 skill 的个人采纳形成个人分支，更新组织库仍须提审。

同会话上一稿经权限和哈希检查后交接到新工作区的 `inputs/history`，由agent读取后写本次 `outputs`；历史输入副本不计新交付。缺失或被修改的旧文件保持不可用，不猜内容。未来个人偏好仍通过后台候选与个人采纳更新技能库。

旧schema的提炼/更新在冻结基准上提出patch并由宿主应用；新版NEW workflow交独立creator会话制作文件，再由宿主验证、打包。个人/组织注册指 demo 版本库；选用时将获准的具体版本安装到该次 OpenClaw 工作区。对话中显式调用 `/skill-creator` 不会自动获得组织共享权限。技能库提供 `.skill` 下载，任务会话和运行记录提供交付文件下载。

## 导入与后续评估

页面“任务会话”可导入 JSONL，每行一个技术终态回合：

```json
{"session":"sample-1","requestId":"turn-1","user":"整理报告，必须先核对退款再汇总收入","assistant":"核对步骤与交付物……","status":"COMPLETED"}
```

支持 COMPLETED / FAILED / DISCONNECTED / CANCELLED。重复 requestId 不重复入库。不接受手填 skills 使用回执；要测试演化，请实际从 demo 库选择技能执行。页面支持导出当前成员的会话、轨迹、候选、版本、决策事件与运行证据。真实与回放默认数据目录分开；禁止跨模式复用同一数据库。

```powershell
python -m unittest discover -s tests -v
python demo.py replay --data artifacts/my-replay
python scripts/check_openclaw.py
python scripts/check_heuristic_pipeline.py
```

`check_heuristic_pipeline.py`默认使用明确标记的合成模型夹具，实际执行宿主校验、文件读取和官方打包，验完整使用反馈与版本治理。`--live`使用现有真实配置完成阶段1—5；`--live --exercise-use-and-update`追加有限真实消费与合成用户反馈验收。每次创建新目录、冻结输入和代码快照、保存全部失败attempt，不自动付费重试。这些是通路验收，算法语义准确率与benchmark增益另行测量。

启发式入口 `Loop.import_experience` 或 `/api/import-experience` 接收 `events/context/evaluations`。context是带来源的公开文本数组；evaluations是明确对象、要求版本和作用范围的评价数组，可为空。完整格式见实施规格；禁止直接传入整个benchmark的reward_info或隐藏金标。脚本支持 `--live --input-experience path.json` 处理显式指定的数据，原始企业正文应保留在受控运行目录。

## 文件职责与边界

- `skilldemo/core.py`：任务、候选、额度、个人／组织版本状态机。
- `skilldemo/detection.py`：第2阶段结构化任务抽取契约、分窗与来源校验。
- `skilldemo/recovery.py`：第3阶段轨迹关系、尝试、反馈及执行引用恢复。
- `skilldemo/evidence.py`、`relational.py`：新E/C/V证据规范化与一次提议后的有界关系恢复。
- `skilldemo/relational_workflow.py`：新轨迹对方法、结果范围、聚类和条款的程序约束。
- `skilldemo/workflow.py`、`workflow_bridge.py`：第4阶段轮廓/方法聚合及第5阶段交接。
- `skilldemo/creator.py`：公开文件、覆盖、引用、内容及打包验证。
- `skilldemo/runtime.py`：真实 OpenClaw CLI 适配、合成夹具、包校验。
- `skilldemo/store.py`：SQLite 事务和事件／运行记录。
- `skilldemo/server.py`、`web/`：本地观察及操作界面。
- `PLAN.md`、`SPEC.md`、`TEST.md`、`TODOLIST.md`：实现约束与交付状态。

这是本机单进程科研 demo。角色选择用于验证业务边界，不是生产登录认证；只监听 localhost。原始会话与密钥不进入组织提审包，但生成包仍需人工检查隐私。数据目录包含会话明文，应按研究材料管理。024已开放本地文件、Python/exec及技能封装，配置允许浏览器和Web工具；后两者仍依赖运行环境，企业工具尚未接入。消息发送和子agent派发仍关闭。exec在主机运行，工作区限制不是操作系统级沙箱。

官方依据：[OpenClaw agent CLI](https://docs.openclaw.ai/cli/agent)、[Skills 格式](https://docs.openclaw.ai/tools/skills)、[源码与版本](https://github.com/openclaw/openclaw)。实际兼容性以本机固定版本契约测试为准。

## 047/049 新版阶段链路

当前真实模式默认走046新版契约：原始事件 → 问答对象 → LLM逐对任务标注 → LLM轨迹关系恢复＋程序组装。[输入输出与边界](STAGES_123_SPEC.md)｜[实施计划](STAGES_123_PLAN.md)｜[验收记录](STAGES_123_ACCEPTANCE.md)。页面「任务轨迹」新增前三阶段状态、问答原消息和候选标注。

真实案例验收命令：`python scripts/check_038_stages123.py`。该命令读取受控038原70消息及source_index，不读取人工recovered_trajectories。会调用已配置的真实模型，默认预算按成员计8次；原文与完整结果存放案例private目录。

049已让新版TaskTrace通过专用阶段4/5链路进入workflow聚类和真实skill封装；旧版学习器仍只处理其原schema。一次受控038案例产出可用个人skill，并在构造后续任务中真实读取和交付文件，详见[阶段4/5验收](STAGES_45_ACCEPTANCE.md)。054补通新版UPDATE工作流至stage9，并完成已有技能真实消费、构造个人反馈、轨迹回流、局部补丁、个人v2采纳及新会话对照，见[自进化案例](../../research/reports/054_personal_skill_evolution_case.md)。企业采纳、跨用户组织复用和连续无人值守更新仍需单独验收。
