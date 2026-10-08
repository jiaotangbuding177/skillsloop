# 第294轮：用户明确允许外部传输，Squoosh第二轮真实接续采集

日期：2026-10-05（北京时间）。接续[292工作恢复](292_2026-10-05_recreationbench_work_recovery.md)、[290采集记忆](290_2026-10-05_rw_parallel_evolution_collection.md)。其他聊天同期293/Co-Gym292记录和状态保留。

## 用户已确认要求与授权

- 用户要求“请继续，并继续生成轨迹”。本项继续已授权26独立GUI pilot采集，不自动启动skills学习/250正式评测、扩容或恢复其他旧实验。
- 自动审批两次拒绝启动持续后台Docker/model执行，理由是既有会话、候选代码和截图向外部模型端点的精确传输授权未被认可。准备/验收完成后已提出具体确认：原 `https://claudex.org/v1`、`deepseek-v4-flash-vision-exp`，Squoosh自己的既有会话/代码和公开参考截图，第2轮、未达时最后第3轮。
- 用户随后明确“我允许发送”。这是本次外部传输与上述后台接续的明确授权。凭据未写入本记忆/报告；不把本次授权扩大为企业原始会话公开、组织发布或其他目的的数据外传。
- 持续有效：每canonical家族最多3轮含首轮、成功停，版本/设施恢复不重置预算；miniPaint3/3封存，旧corravale STOP保持。

## 证据支持的观察与本轮执行

### 1. 新执行版本与准入

目录 [293_rw_continued_collection](../experiments/293_rw_continued_collection/README.md)。实验目录编号293是在准备时建立，记忆采用294避免混同另一聊天的293，不是旧实验覆盖。

- 首轮Squoosh候选实际submitted/build success/native_returncode0，真实nested score0.5246、功能1/6、SSIM0.8826。五项失败来自独立训练验证器真实标题：原图导出像素、JPEG真实编码、WebP真实编码、resize输出尺寸、rotate导出方向。
- 新checkpoint只复制首轮自己的src/public/构建配置与全部raw session/tool-result文件，逐文件原/复制SHA核验。47个检查点文件，未复制evaluation/reference源码；actor只接收上述真实概括性失败反馈，不得到隐藏断言或标准补丁。
- 离线本地stub验收真实恢复路径、原生`--resume`参数、全部tool-result文件以及重复纠正拒绝；0模型调用。此fixture不是新的任务执行或真实能力证明。
- 新actor脚本、checkpoint、未改训练数据及配置共67文件在第2轮首agent前冻结。旧285/288/v27及评分/失败保持不变。
- 采用同官方vendor/image/原生Claude Code，当前轮固定3GiB/2CPU、NODE heap512MiB、独立proxy8793，既有relay8193。与首轮2→3GiB的历史资源变化分列，不称全链资源未变。worker要求可用内存>=5GiB，最多2 RW worker。

### 2. 第2轮真实运行，而非仅准备/心跳

实际attempt `squoosh_recreation_eval_1791158578555081942`，北京时间08:02:58左右controller启动。controller367584/start_ticks4539818，supervisor367583/start_ticks4539811，boot `255b5570-fab4-46e1-a9ff-c307b0bbb76a`。首轮session `040fcf5e-ec60-4923-95cb-41e85236ebad`与自有候选已恢复，容器内恢复marker和实际session增长已核对。

采样epoch1791159214：**44次实际API请求全部完整，失败0、在途0**；新route `/293/<attempt>/v1/chat/completions` 不与旧混合窗口route混计。controller与容器running、OOMKilled=false、实际cap3GiB/2CPU。原生session11,550,215bytes/1281行/0坏或半行，mtime实际推进；会话包含继承历史，不能称1281都是本轮新增。源码37文件、mtime1791159107实际更新，native Write/Edit已有增加；这证明模型正在真实实现/修改，不只是父进程存活。

累计恢复图像传输块2200包含每次请求回放历史，不是2200张独立图片。最初监督器已加载观察函数误读字段导致旧health_state图像数0；另建独立只读observer369254，按实际recovered_image_blocks写[current_health.json](../experiments/293_rw_continued_collection/reports/current_health.json)，不热改actor或冻结执行文件。后续巡检以该文件及active actor为准，不能据旧0声称无图片。

当前尚未第2轮最终交付/评分，**不宣称成功、提高或新完整轨迹已验收**。自动监督器在第2轮有效终态未达必要功能/视觉条件时才机械准备前轮checkpoint、另冻结并开始最后第3轮；满足指标则停并待最终审计。未知评分/worker错误不自动重跑；跨目录读取canonical已分配预算，不能第四轮。

收尾[启动实核](../experiments/293_rw_continued_collection/reports/start_acceptance.json)再次验明67冻结文件0变化、监督器/actor存活、真实原生resume及导出hash/工具配对通过；最新66API（65完整/1在途/0失败），原生session12,696,977bytes、源码37文件，无新OOM。此为更晚截面，保留上方44次初截面，不外推未来健康或最终分数。

### 3. 已有四次执行的机械素材整理

[导出清单](../experiments/293_rw_continued_collection/reports/existing_public_exports.json)：从已完成raw sessions机械抽取actor公开user/assistant消息、工具调用和回执，排除hidden reasoning块，不做模型摘要；按UUID及内容hash去除继承重复，保留首次出现的轮次、来源行/文件hash。

| 应用 | 已完成轮次 | 去重公开消息事件 | 唯一图片 | 调用/回执 |
|---|---:|---:|---:|---:|
| miniPaint | 3 | 1236 | 43 | 505/505 |
| Squoosh | 1 | 851 | 48 | 377/377 |

两者未匹配调用、孤立回执、UUID内容冲突均0；图像原字节/hash及逐轮索引、机械文本视图已保存。user角色可能是工具回执，不标真人会话。末轮评估保留原sidecar，不伪装成actor看过的回执；未注入synthetic success。当前第2轮尚在运行，不加入已完成导出。

适用范围：上述是本地机械数据层及结构对应证据，不是全部canonical因果、来源/原创性审计或AutoSkill实际输入验收。text-only学习器不会因为路径/hash而看见图像像素；长链截断/输入容量仍需之后核对。不会因此声称2条素材已正式学习或得到skills收益。

### 4. 下一参考准备与总体进度

固定Vite docs原来源commit `fdb2e6f63894d8c458c1778f3df77afe537f2bb2`的隔离reference构建准备已安排，archive SHA核验与原来源不变。准备进程370521当前waiting_resource；要求可用内存>=6GiB才启动2GiB/1CPU构建，本采样约3048MiB，故未启动构建/模型/GUI评测。即使构建成功仍需真实GUI、重置、独立verifier/负对照和来源家族准入，不自动启动actor。

后续更正上述等待截面：首版随后实际获得内存准入，构建在corepack prepare后因`pnpm`可执行shim不存在而FileNotFoundError退出，模型/agent调用仍0。原source_manifest/build.log/preparation_status失败全部保留。独立v2补`corepack enable pnpm`激活步骤、新构建路径和manifest，进程373967当前[waiting_resource](../experiments/293_rw_continued_collection/admission/vite_docs_v2/preparation_status.json)（约4478MiB<6144）；尚未验证v2实际构建成功，不把准备故障算作能力纠错轮。原参考commit/archive与旧actor均未改。

最新运行采样epoch1791159622：Squoosh第2轮72实际API全部完整/0失败，原生session12,738,691bytes、源码37文件，controller/container仍running、无新OOM，尚无新终态评分。保留前述44/66次截面，持续观察以动态current_health为准。

整体仍2/26准入：miniPaint3轮结束/Squoosh第2轮运行，其余24未准入。高质量成功验收0，RW skills学习和250正式评测未启动；既有corravale暴露及旧5+245历史保留，新250评测协议未冻结。

## 研究假设、限制与下一步

真实失败/代码修订/验证经验可能形成跨应用可复用技能，这是研究假设。当前新证据仅是安全接续准入、真实第2轮执行推进及已有记录机械整理；应用质量、技能数量/正确性、迁移收益和最终规模均未知。本实验关联闭环中的执行经验学习/演化/复用，不替代自然企业会话、个人采纳或组织治理实证。

继续观察第2轮交付/score/原始完整复制，按三轮规则接续或停止；导出第2/3轮时保持父链去重与真正被actor看到的反馈。资源就绪后完成Vite docs参考构建再验收，其他平台按宿主/工具条件逐项推进，不伪记失败或覆盖旧分。后续无需重跑launch脚本；用active、supervisor_identity和current_health精确核对现有身份。

关键产物：[实验入口](../experiments/293_rw_continued_collection/README.md)、[checkpoint准入](../experiments/293_rw_continued_collection/reports/checkpoint_round2_admission.json)、[离线验收](../experiments/293_rw_continued_collection/reports/checkpoint_offline_admission.json)、[freeze67文件](../experiments/293_rw_continued_collection/reports/freeze_squoosh_round2.json)、[当前健康](../experiments/293_rw_continued_collection/reports/current_health.json)、[Vite准备状态](../experiments/293_rw_continued_collection/admission/vite_docs/preparation_status.json)。
