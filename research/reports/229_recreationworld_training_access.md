# RecreationWorld官方训练任务获取渠道核查

核查日期：2026-10-04。范围为论文、官方站、官方仓库与发布页、HF数据卡与API、ModelScope镜像。结论针对所核查公开入口，不把缺少搜索结果当作者明确拒绝发布。

## 结论

目前未找到论文官方训练任务池或35,000条训练轨迹的公开下载入口。已公开可获取的是250题held-out评测数据，以及运行/评测框架和环境准备脚本。不能把公开benchmark的reference目录、任务运行后产生的trajectory或环境框架称为论文训练任务集。

## 证据与渠道

| 渠道 | 实际核查 | 对获取训练任务的意义 |
|---|---|---|
| [论文§3.1与附录A.1](https://arxiv.org/html/2609.22000v1) | 从GitHub应用采训练任务，与评测集去重；7,000条/平台共35,000条筛选轨迹。公开资源表仅列网站、演示、harness、benchmark及镜像 | 训练池存在于论文实验描述，但未给独立清单/下载链接；35,000是轨迹数，不是应用任务数 |
| [GitHub README](https://github.com/QwenLM/RecreationWorld)与[发布页](https://github.com/QwenLM/RecreationWorld/releases) | README指向250题、平台指南、HF/ModelScope；发布页没有release附件 | 有自采轨迹所需执行底座，不等于训练应用包已经公开 |
| [HF数据卡源码](https://huggingface.co/datasets/Qwen/RecreationBench/blob/main/README.md) | all及五平台配置全为test；共250题，包含任务描述、参考准备资产、tests/fixtures/视觉标注 | 公开下载命令下载的是评测包，不能作为官方train获取命令 |
| HF只读API | author=Qwen、search=Recreation仅返回Qwen/RecreationBench；metadata目录只有五平台jsonl | 查询范围内未发现另一Qwen训练数据集；不声称已穷尽所有账号和私有仓库 |
| [ModelScope官方镜像](https://modelscope.cn/datasets/Qwen/RecreationBench)及repo/tree API | master根目录TotalCount=8：android、macos、metadata、ubuntu、web、windows、.gitattributes、README.md；最新commit2522774f0b18ed454496a6db99ae1044a9d68087 | 镜像未呈现独立训练入口，不是另一个train版本 |
| [官方项目站](https://recreation-bench.cc/) | 250 held-out应用；提供联系邮箱，没有train下载 | 可询问官方团队 |

HF root展示revision284341f，与此前固定版本一致。官方GitHub实时递归tree API本轮因匿名rate limit失败，未将null/total0误作空仓库证据；本地固定官方checkout检查未见train清单，只有250任务索引、trajectory记录工具与Web gt_generator等。ModelScope浏览器工具未返回正文，但其公开API成功返回上述目录。普通沙箱网络失败后只读必要权限请求HF/ModelScope成功，不把初次失败当数据不存在。

## 可行动的官方获取渠道

README明确列出 xiezhihui.xzh@alibaba-inc.com 和 gaochang.gao@alibaba-inc.com 作为问题联系入口；项目站也列同一邮箱。建议优先询问是否已发布/计划发布，以及能否提供研究使用访问。没有证据表明发信后必定获批。

我们需要优先获取可重新采GLM轨迹的训练任务，而不是必须拿到原模型轨迹：

1. 官方训练应用清单、平台、repo/commit与对250评测任务的去重映射。
2. 可运行参考包、instance/prompt、patches/fixtures，以及环境版本与build/launch配置。
3. 训练任务验证器/评分资产及参考自验结果；若受限，明确哪些可提供、如何自行验收。
4. 数据/软件许可、再生成轨迹并用于AutoSkill抽取的使用与分享条件。
5. 可选：35,000条轨迹、动作/截图schema、任务ID映射和成功筛选规则。

仅收到GitHub应用名不等于环境齐备；仅收到trajectory也不等于能在同任务上重新运行GLM。若作者只给部分平台/任务，应明确子集归属，不称完整官方训练池。

## 作者询问信草稿（未发送）

Subject: Access to RecreationWorld training tasks for skill-learning research

Dear RecreationWorld team,

We are studying reusable skill extraction from agent trajectories using AutoSkill, with GLM-5.3-Flash as the agent. We would like to generate trajectories on RecreationWorld training tasks and evaluate a frozen skill library on the held-out RecreationBench tasks using paired runs with and without skills.

We found the public 250-task test release and execution framework, but could not locate the training-task pool described in Section 3.1. Could you point us to its public release, or advise whether research access is available?

Our primary need is the training task inventory with pinned references, prompts, environment/build/launch configurations, fixtures and verifiers, together with the train/evaluation deduplication mapping and applicable usage terms. Access to the 35,000 trajectories and their task mappings would also be useful, but is optional because we plan to collect our own trajectories.

If only a subset can be shared, or a release is planned, please let us know the scope and expected availability.

Thank you.

## 对实验路线的影响

228的路线方法上成立，但暂时缺官方训练输入，不能声称可直接启动官方train→250test全链路。申请作者资源是最直接路径。若无法取得，另采与250去重的新应用属于我们构造的训练任务；拆250做交叉学习属于派生子集，两者均须独立协议，不能冒充原官方train/test。未获新指令前不重划250，不启动批量、不发送消息。
