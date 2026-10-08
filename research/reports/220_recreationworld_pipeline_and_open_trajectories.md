# RecreationWorld、公开轨迹与独立实验管道

## 用户确认的范围

用户2026-10-03明确选择RecreationWorld，要求调研公开轨迹并搭建实验管道，沿用GLM-5.3-Flash。允许独立基础设施和功能验收，不改变208正在进行的Co-Gym学习、旧库/分数/冻结；103检索依赖题仍暂缓。本文是搭建与功能验收记录，非250题完成或skills收益报告。

## 公开来源的实际边界

| 来源 | 官方公开内容 | 建议用途与限制 |
|---|---|---|
| [xlangai/AgentNet](https://huggingface.co/datasets/xlangai/AgentNet) | 22.6K人工电脑任务、动作/截图，文字观察/推理由发布方合成；MIT；Windows/macOS/Ubuntu | 可作外部执行经验输入，保留合成观察标记与真实未知/失败标签；主要GUI操作，向Web应用复刻迁移效果未知 |
| [nvidia/ProCUA-SFT](https://huggingface.co/datasets/nvidia/ProCUA-SFT) | 93,566条模型执行轨迹，trajectory.json与截图分片；CC BY4.0 | agent工具/环境轨迹较贴近学习对象；固定revision与应用家族隔离后使用，不能当真人持续对话 |
| [Qwen/RecreationBench](https://huggingface.co/datasets/Qwen/RecreationBench) | 250题、五平台公开测试任务和评分设施 | 是可执行任务包，不等于已公开35K论文训练轨迹；后者下载尚未核实。当前只取独立canary，不入技能学习池 |

这些轨迹大多是初始任务后与环境/工具多步交互，不是企业用户与agent持续多轮改要求的自然会话。它们可验证执行经验到skills、消费和任务结果链路；不能替代本项目企业闭环的部署与用户反馈证据。

## 独立部署与真实验收

目录：[218管道](../experiments/218_recreationworld_glm_pipeline/README.md)。官方[RecreationWorld源码](https://github.com/QwenLM/RecreationWorld)固定commit b5cda868f44932dc84ea68e3b3053bc418621aa3，公开任务revision 284341f8fc3d6680dd57ca5414fed92a0fe33b95。官方执行/评分源码没有语义修改。Docker固定工具依赖，Claude Code原生CLI与Playwright MCP、官方Anthropic/OpenAI代理；模型通过原8129/8000共享累计账本，不复制生产凭据，不重置计数。

1. 随机视觉nonce两次识别和原生工具参数一次均真实通过，共3次HTTP200。不是仅接受图片字段，而是识别随机图中内容。
2. Web corravale.example下载前按最少文件数/名称排序确定，318原始文件全部SHA核验，只作基础设施canary、排除最终统计。Windows不能存问号路径，staging用路径哈希并在WSL恢复原POSIX名称。
3. 保留v1 Windows CRLF失败和v2缺reference.tar.gz失败，infra_error与原null分不改为0。按Git原LF恢复并将公开reference/site按官方归档契约打包，原站点文件不改；setup恢复exit0。
4. 官方参考候选评分exit0：program_score=0.9975，228/229功能断言通过。视觉逐页no_gt_screenshots，native overall visual=0、task_score=0.4987。缺GT导致的数值零不能当有效视觉质量结果，该总分禁止进入正式效应统计。
5. 单题无技能CLI canary真实运行：严格浏览器参考预检通过；原生Read、Write、导航/截图/点击及图像块与工具回执已出现；原账本精确GLM-5.3-Flash且真实完成tool_calls。最终任务尚未结束，不能宣称基线评分完成。
6. 官方共享VLM judge调用原GLM，对真实参考截图固定前4条公开断言完成调用和解析验收；新增独立v3适配器/报告目录启用原生视觉断言评分，不热改活跃v2源码或freeze。v3还需全题981断言验收。GLM同时当agent和judge，与论文judge不同，偏差与一致性需要研究对照。

官方CLI默认关闭Skill工具。本研究消费协议是派生配置：共同CLI自身加载的CLAUDE.md说明；有技能组加入名字/描述/路径目录，按需原生Read读取SKILL.md。不得称开启了官方Skill工具或论文原样prompt。目录挂载/提到技能不算消费，需真实Read调用及成功回执。旧208库不用于这个新实验。

## 完整外部轨迹验收与负结果

AgentNet固定revision d76ee50a63fad81cfdbe576416757d7c2091ed50，按文件顺序首条7步GIMP示范：发布方task_completed=false。通过公开分片ZIP中央目录和HTTP Range取对应7张真实图，约5.5MB压缩图；检查ZIP CRC/大小/PIL解码、原动作顺序及所有SHA，不伪造图片或改成功标签。

原生AutoSkill extract_from_agentic_trajectory对完整canonical逐题处理，success_only=False、消息/事件不限，真实processed1/failed0/skipped0，upserted0、empty_library=true；此次没有embedding操作。该负结果保留，不挑另一条成功案例覆盖。学习器当前文字动作和明确标记的发布方合成观察，图片作为可回查来源；不声称AutoSkill读取了像素。6个输入契约测试通过，覆盖缺图/歧义/顺序丢失/损坏/路径与UNKNOWN处理。

来源GIMP桌面编辑与当前Web复刻题家族不同，这只是当前单条canary隔离审计；扩大输入与评测池须重新按应用/网站/项目家族审计，不能以单条检查声称全量去泄漏完成。ProCUA暂只核对公开索引与许可，尚未下载。

## 下一步与未解决项

- 完成当前原生agent canary并保留真实低分/错误；v2缺GT视觉结果不纳入正式对比，v3经完整原生判定再接受总分。
- 按预先固定来源顺序和家族隔离扩大外部轨迹池，再学习非空语义库；空候选正常保留，不按成绩或产出挑样本。
- 验证真实SKILL.md Read回执与语义embedding后，固定无/有技能相同任务/预算/CLI/评分的配对协议，保留成本、失败、覆盖与置信区间。尚未启动250题或自动配对评测。
- 当前仅Web环境。Windows/macOS/Android/Ubuntu五平台全部搭建与论文等价judge不是本轮已完成事项。

证据见218目录reports/{model_acceptance,reference_packaging,judge_acceptance,agentnet_frames,external_acceptance_manifest,current_api_evidence}.json、reports/judged_v3/，以及runs和autoskill_state。数据许可与来源应随未来库/报告保留；研究收益是待检验假设。
