# 第285轮：独立演化集合首题已启动真实轨迹采集

## 用户已确认要求

- 用户明确“开始生成轨迹”，承接283方案和284规模讨论。当前26个独立应用是首批pilot；50应用扩容建议未获确认，本轮没有据此扩容。
- 每个canonical应用家族最多三轮完整agent执行/交付/反馈，首轮算一轮，成功即停。旧corravale17次迭代STOP不恢复，不因改版本重置轮次。
- 为后续skills沉淀采集素材；本项仅启动新演化应用的轨迹采集，不自动学习或启动250题评测。

## 证据支持的观察

目录：`research/experiments/285_rw_evolution_collection`，版本`rw_evolution_collection_v1`。26候选来源登记保留，现仅miniPaint实际准入1/26，其他25尚未准入，不能称全队列运行或已有26条轨迹。

miniPaint固定MIT源码版本4.14.3、commit `a79733eb803fc97084ef0ee4faa96b031e69e1c0`，来源279归档SHA `21f1cadb54397f21927194d762fcef32282b0b2ec501a2cfaf65af9008c34fb4`。复制固定浏览器产物48文件，离线沙盒实际运行，页面脚本错误0。未读取250题隐藏测试/真值，新编训练验证器依据本参考实际行为生成。

六个检查覆盖编辑器/画布、两色真实像素绘制、撤销重做、新建尺寸、缩放复位、JSON项目导出。初次参考4/6，两个错误是准备期验证器假设不符（参考缩放会重绘显示canvas、项目尺寸在info内），保留初次失败与诊断后、模型执行前修正。最终官方Playwright执行参考6/6、静态无功能负对照0/6，failed/skipped分别0/0及6/0。

使用官方截图函数自采桌面/移动两视图以及DOM/layout/regions。独立训练视觉合同采用官方SSIM/LPIPS路径与实际GT，VLM显式不参与；不冒充RecreationBench250的完整program/VLM分数。官方参考自验实际functional1、visual_ssim1、组合1；原生metrics外层却报告task_score0。两份原产物均保留，新接受报告明确从`eval_results/scores.json`核验，不热改vendor或把外层0解释为参考能力失败。最终训练接受另要求functional6/6、visual>=0.85、真实build success、原创性审计通过。

官方setup权限隔离实测通过：agent能写自己的工作区，不能直接读参考目录/隐藏evaluation。初次actor保持官方原始prompt与CLI；没有旧corravale源码、session、补充提示、resume_cli替换。固定官方vendor commit `b5cda868f44932dc84ea68e3b3053bc418621aa3`及镜像ID `sha256:603d4b4f22fc32a7d0bb2e034db9f9afc1d5597f6116cfb35d2fa1e244d34c3d`，新phase35SHA和源码包在首次agent前冻结。

模型请求沿当前用户指定`deepseek-v4-flash-vision-exp`/原受控provider资源，独立8190 relay，无损恢复官方proxy序列化的图片。两次单独标签准入真实识别随机四色顺序及正确工具参数，非应用轨迹。供应商返回model字段`deepseek-v4.1-flash`；这与请求别名不同，物理checkpoint未知，记录而不冒称已核实模型身份。凭据仅受控文件入内存，记忆不含凭据。

首轮task `minipaint.training` / attempt `recreation_eval_1791121638371741570`，controller48903、Linux start_ticks845864，boot `255b5570-fab4-46e1-a9ff-c307b0bbb76a`。13:47 UTC左右实际启动。原生浏览器preflight screenshot54422bytes通过，actoruid1002无外部网络，只允许原生模型与参考站relay。

收尾初快照epoch1791121808：33实际API、32完成/1进行中/0失败，累计传输29图片块（多次请求可重复带历史图，不当29张独立图）。原生86事件/411599bytes/0半行，真实浏览器navigate/screenshot/click/hover及Bash/Read记录；35freeze全通过、唯一controller与容器存活。此时**完整已验收轨迹0**，第一轮正在观察/复刻，不能称成功。

最后截面epoch1791122107：75实际API、74完成/1在途/0失败，原生194事件/1167417bytes/0半行、5截图调用与4实际Write，源码文件9，35SHA全部保持、唯一身份存活，第一轮仍运行。207是累计历史图片传输块而非独立截图数。已将初监控硬编码`private_scorer_read:false`纠正为`originality_and_source_access_audit:pending`：工具计数本身不能证明未读取私有数据或原创合规；权限setup证据与最终动作/来源审计须分别报告。监控脚本在reports、未热改冻结执行文件。任务登记同步miniPaint1/3运行，不再保持通用pending误标。其余25仍待准入。

新外部container入口终态无64MiB上限复制完整原生sessions，记录逐文件来源/目标SHA；尚未终态，完整性需要之后核验。额外只读观察器每30秒保存真实API/原生事件/冻结快照，结束时保存原始score引用并标记待轨迹/原创性审计；不调用模型、不自动起第二轮、不改冻结源。

## 研究假设与建议

- 本参考预计产生画布状态、颜色、撤销/redo、菜单/导出等复刻与调试素材，尚非实证skills收益或高质量成功保证。
- 26来源不代表26有效轨迹或多平台技能充分。先验收首条完整图文事件链，再推进同等准入的候选。

## 未知项与下一步

- 第一轮交付、最终功能/视觉评分、原创性、完整图片与工具回执/原生sessions导出仍待结束核验；空技能/失败轨迹不得静默丢弃。
- Ubuntu其他候选需原生构建/验证器，Windows/macOS/Android宿主仍需就绪；其余Web也未在本轮启动。
- 三轮是上限，第一轮失败不会隐式启动未冻结纠正提示或无限重试。计数器已分配1/3，不能重跑启动器。继续纠正须保留本轮完整结果并明确计入下一轮。
- 250评测、AutoSkill建库没有启动，旧实验及其他聊天保持；现完成的是**首题真实采集启动**。

## 关键产物

- `285_rw_evolution_collection/reports/{phase_manifest.json,frozen_sources.zip,reference_acceptance.json,model_acceptance.json,active_rollout.json,health_monitor_state.json,collection_status.json}`。
- `admission/minipaint/{source_manifest.json,verifier/admission*.json,verifier/diagnostic.json,gt/}`；初次失败不删除。
- `datasets/released/web/minipaint.training/`：独立训练输入，不是250评测实例。
- `runs/setup_1791121436387431557/`、`runs/eval_1791121462550917574/`、`runs/recreation_eval_1791121638371741570/`及独立安全API账本。
