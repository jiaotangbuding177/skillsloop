# 第295轮：RW进度核对——Squoosh三轮结束，Vite参考构建完成

日期：2026-10-05，北京时间10:46左右。本轮接续读取README、CHARTER、STATE及[294记忆](294_2026-10-05_rw_squoosh_continuation_authorized.md)，随后核对实际评分、容器、原始文件、freeze与独立API账本；没有新增模型或评分调用。

## 用户已确认要求

本轮用户“看看进度”。此前“继续生成轨迹”“我允许发送”授权持续有效，最多三轮含首次、成功停、旧corravale STOP、miniPaint封存不变。状态核对不授权第四轮或自动开始skills学习/250正式评测。

## 证据支持的观察

[本轮实核报告](../experiments/293_rw_continued_collection/reports/295_terminal_progress_audit.json)为本地只读审计。第294轮的运行中与Vite等待资源截面仍保留，但当前状态已改变：

| Squoosh轮次 | 北京时间执行区间 | 分钟 | 功能 | SSIM | 最终分 | API完整/总数 |
|---|---|---:|---:|---:|---:|---:|
| 2，1791158578555081942 | 08:02:58—08:43:08 | 40.17 | 1/6 | 0.8826 | 0.5246 | 169/169 |
| 3，1791161014230915331 | 08:43:34—09:08:02 | 24.47 | 1/6 | 0.8826 | 0.5246 | 94/94 |

真实nested `recreation/eval_results/scores.json`均与controller结果对应，has_compile_errors=false，但功能未达6/6。两轮主要指标与首轮相同，未观察到评分改善；不能把正常完成或视觉达标称为复刻成功。为什么纠正没有改善尚未作因果分析。

- 两轮controller已退出；docker实核均exited、ExitCode=0、OOMKilled=false。supervisor与只读observer按boot/PID/start_ticks核对均已退出；`continuation_status.json`为`three_round_budget_exhausted`。不重启launcher、不追加第四轮。
- 第2轮完整复制5文件，共15,148,559bytes、主session1682行；第3轮5文件，共16,997,696bytes、主session2004行。重新计算原清单source/copied SHA及实际大小全部一致，JSONL无坏行。数字包含继承历史，不能累加成唯一新素材量。
- 第2轮67、第3轮69冻结文件重新SHA核验，变化0。独立`/293/<attempt>/`账本中第2轮169、第3轮94请求全完成，失败/在途均0；不与旧288混合route成本混计。
- 原评分器未发现leak/egress/scrape处罚；originality仍为monitoring_only，homepage `gt_too_small`导致containment=null。因此这不是全面原创性已证明，canonical因果/语义及学习输入验收仍pending。

Vite docs v2于约08:32:34完成固定来源构建：returncode=0、327站点文件，状态`build_completed_pending_gui_verifier`、model_calls=0、runtime_accepted=false。[实际状态](../experiments/293_rw_continued_collection/admission/vite_docs_v2/preparation_status.json)与build.log对应。首版pnpm shim缺失的失败保留；本轮没有重新构建、启动Vite actor或执行GUI/评分验收。构建完成不等于第三个应用已准入。

## 当前总体进度及未知项

26主候选中仍2/26准入：miniPaint、Squoosh各3轮，共6次正式应用执行均已结束；最后分分别0.4228、0.5246，成功验收0。其他24未准入，其中Vite参考构建已完成、GUI/重置/verifier/负对照待验。旧corravale STOP不变。

已有公开机械导出仍只覆盖miniPaint三轮及Squoosh首轮；本轮新两轮raw已核验存储完整，但尚未合并到新的去重公开学习视图。完整canonical与AutoSkill长输入、图像实际消费仍待验收。RW skills学习及250正式评测均未开始，不声称26链完成、技能收益或官方35,000训练轨迹已获得。

## 研究假设与工作建议

失败链是否可沉淀可复用技能仍是研究假设。此负结果与主线中执行经验学习/使用后纠正有关，只支持“这两次接续没有改善本应用指标”，不能外推学习无效或模型普遍无法改进。

下一步推进Vite真实GUI、重置、独立训练验证器与负对照准入；将Squoosh新增两轮另建去重公开视图并核对actor实际看到的反馈，不把裁判sidecar当作actor回执。其余平台继续按宿主条件逐项准入；保持两应用三轮封存，不自动开始学习或250评测。
