# Q评测交接：28道改造题、49道强匹配题、全部WRD

本包供专门AI评审Agent对已有产物评质量分Q。当前选定结果已经齐备，尚未执行Q评分。

分支：`codex/q-evaluation-handoff-20261025`。仓库：[jiaotangbuding177/skillsloop](https://github.com/jiaotangbuding177/skillsloop)。

## 已确认范围

| 组别 | 选取范围 | 记录数 |
| --- | --- | ---: |
| AutoSkills | 当前28道改造题，包含20题既有结果及8题补跑 | 28 |
| Trace2Skills | 当前28道改造题，包含20题既有结果及8题补跑 | 28 |
| NoSkills | 冻结49道强匹配题的当前结果 | 49 |
| WRD | 当前250题全部选中结果 | 250 |
| 合计 | 唯一的任务×方法记录 | 355 |

先评28道改造题的四组112条，再完成其他243条。355条实际request题面与当前任务逐一相同，1090个请求输入绑定的实际SHA及大小一致；原有16条AS/TS缺口已补齐。最新T0197采用retry2已完成结果。进程状态为failed的4条记录仍包含在355条中，按真实内容评Q，不能整题自动归零。

## 直接交给评审Agent

从本目录读取 [AGENT_EVALUATION_GUIDE.md](AGENT_EVALUATION_GUIDE.md)，随后使用 [JUDGE/queue.jsonl](JUDGE/queue.jsonl)。不把COORDINATOR目录作为质量先验，也不要把仓库已有的旧750交接包当成本包标准。

```text
python tools/verify_handoff.py --deep
python tools/materialize_case.py --case CASE-0001 --out review_work
```

第二条命令生成 `review_work/CASE-0001/`，里面的 `outputs/` 是该选中结果的原始实际产物，`logs/` 是必要时取证的原生日志。任务与rubric路径由命令返回，均在本包内，不依赖原D/E盘。每例评分后必须保留draft并自review，再提交reviewed结果。

可把下面这段作为专门评审Agent的起始指令：

> 进入handoff/20261025_q_evaluation，先读AGENTS.md及AGENT_EVALUATION_GUIDE.md，运行资料校验，再按JUDGE/queue.jsonl逐例评Q，优先priority=0的112条。仅使用当前任务、输入、同版rubric及该case实际产物，必要时再取日志；不读COORDINATOR的身份/成本/旧成绩。D5必须有真实像素证据，缺失内容与评测故障分开，同一缺陷只主责扣一次，Q不乘TSR；按SCORING/result.schema.json输出，每例draft之后自review。不得重跑业务、修改原件或根据方法身份调整分数。未完成项和UNSCORED如实保留。

## 下载与LFS

EVIDENCE下6个ZIP使用Git LFS，共86,239,083字节；解压前原始证据约261.9MB。正常安装Git LFS并克隆本分支即可取得；若当前下载的是LFS指针，须拉取真正的证据对象：

```text
git clone --branch codex/q-evaluation-handoff-20261025 --single-branch https://github.com/jiaotangbuding177/skillsloop.git q-review
cd q-review
git lfs pull --include "handoff/20261025_q_evaluation/EVIDENCE/*.zip"
cd handoff/20261025_q_evaluation
python tools/verify_handoff.py --deep
```

GitHub网页下载的源代码ZIP可能只有LFS指针。校验工具会拒绝把指针当证据包；不能把下载未完成判为Agent未交付。不要执行构建脚本重新从本机源路径取数据，远端评审只需要verify和materialize工具。

## 资料布局

| 目录或文件 | 内容 |
| --- | --- |
| `DATA/tasks/` | 当前250题完整委托及689个实际输入绑定 |
| `RUBRICS/` | 当前250题2631项；改造28题338项，新旧结构各自schema、来源和AI复核记录 |
| `JUDGE/queue.jsonl` | 355个匿名case，包含可移植的任务、rubric和证据定位，无方法/成本/TSR字段 |
| `EVIDENCE/evidence-*.zip` | 每个case实际outputs、辅助文本、request/response、原生工具轨迹及可取得用量/终态证据 |
| `COORDINATOR/case_key.jsonl` | 评分结束后解盲使用的case→任务/方法/原episode映射 |
| `COORDINATOR/selected_runs.jsonl` | 355条原选中记录及实际对齐依据，历史说明与当前实际核验分开 |
| `COORDINATOR/historical_attempts.jsonl` | 10个本轮替换历史尝试，只作审计，不进入355评分分母 |
| `COORDINATOR/alignment_audit.json` | 355份request、1090输入绑定、355结果源的实际核对 |
| `COORDINATOR/file_provenance.jsonl` | 所有复制文件的原路径/原SHA与包内路径/发布SHA |
| `COORDINATOR/redaction_report.json` | 凭据扫描与排除范围，原始源文件未修改 |
| `MANIFEST/` | 构建摘要、文件SHA清单及最终核验报告 |
| `SCORING/` | 输出schema和明确未评分的结构模板 |
| `tools/` | 无模型调用的校验、按case解包工具；build仅保留制作来源，不供远端重跑 |

所有355个选中episode的最终outputs按原文件名和字节收录，不只复制与预期名字相同的文件。完整原生轨迹的实际入口包括 `logs/openclaw_transport/session_events.jsonl`、`logs/openclaw_transport/evidence/events.jsonl` 与 `session-branch.json`；不是要求必须存在一个叫session.jsonl的文件。ZIP内run_manifest给出逐文件SHA，外层manifest另核对归档本身。

排除网关认证/账号、profile/config、runtime_code、host_api_queue原始网络请求、private目录及整份工作区里的skills依赖副本。保留Q所需的真实产物、工具返回和原生轨迹。日志中的方法名可能造成失盲，因此先产物评审，必要时再读日志并记录失盲，不能声称严格双盲。题目T0039明确标为测试字符串的模拟密码属于安全审查输入，按原字节保留，不冒充真实凭据。

## 当前口径与边界

- 五维权重30/20/20/20/10，条目0/0.5/1，维内等权；每个分数有实际证据，Q独立于TSR。
- 最新文件交付政策为 `type_count_nonzero_format_open`，已取消精确文件名校验。rubric中的具名文件只是证据角色，不因改名本身扣Q。不要恢复早期TSR的精确文件名要求。
- 缺产物或语义空壳仅影响依赖项，原权重保留；解析/渲染/裁判故障为UNSCORED，不能默当0或删分母。
- 35个WRD为历史定向资源复用，215个为后续整库可选使用；无技能中35个当前原生、14个历史条件。不同历史预算/环境条件保留在协调资料中，不能称全355完全同条件实验。
- 旧运行记录中个别comparability文字还写“未补跑”；本包以实际request/输入SHA核验和新增56条AS/TS证据为准，旧文字仅保留来源身份。
- 本包只含本轮选中355和明确附带的10个替换历史尝试，不声称包含整个项目所有旧失败/制作费用。原始历史及费用没有删除或重写。
- Q仍未校准，未来AI评分标探索性。本包无新Actor/Judge调用，没有预填Q，也不预设任何方法优越。
