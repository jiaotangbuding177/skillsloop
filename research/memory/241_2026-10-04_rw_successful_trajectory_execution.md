# 第241轮：一次成功轨迹请求，失败保留与独立尝试

## 最新用户停止与三轮上限

用户明确“立刻停止，以后这样的迭代只允许三轮，没达到就是没达到”。2026-10-04 07:19:37 UTC已核对267 controller32588/start_ticks4383630及run_canary.py身份，写private/STOP，停止唯一任务容器rw238-recreation_eval_baseline_1791094782714342213并确认running=false，终止控制器；reports/user_stop.json保存证据。所有旧代码/轨迹/分/失败保留，268完整评分未启动，不恢复267、不新增纠正版本。以后同一任务此类纠正迭代最多三轮（首次计入），三轮未达门槛如实记录未达标，不以新版本重置计数；基础设施恢复需独立记录，不能借恢复名义增加模型能力纠正轮数。用户约束适用于后续同类研究执行，其他聊天独立实验不停止。

## 最新后续：265完整0.7006未通过，267实际启动

用户追问实际轮数、是否尚无轨迹及每轮耗时。核对各run/controller.log与metrics：DeepSeek同一corravale任务共17执行版本、18启动片段（238含2次，含失败/恢复/中止），旧218 GLM另1次不混计。8版本native_finished不等于8份有效应用：239默认模板、245无可用交付、246参考HTML采集原创性拒绝；250/254/255/257/264共5份实际应用交付、功能评分和公开轨迹。完整40视图评分251与265两次结束，0.6706与0.7006均低于0.75，因此通过成功门槛0份，并非一道题未执行完。最近257/264 actor约60/39分钟、437/309调用，265完整评分约27分钟/40调用；不推断所有任务典型成本。17轮来自故障处理与研究者追求成功的多轮纠正，不是官方单题必需重复数；当前不再自动追加新纠正版本。

本次收尾只读核验267同attempt仍running，409真实请求全部complete/空0、29 Write/Edit，output11959627字节，原PTY75605活跃，无终态错误。仍未最终交付/打分，不报成功。健康检查不调用模型，不改旧freeze/模型应用/其他聊天；继续已运行attempt后核验真实交付，成功未知。

用户追问“究竟在做什么，为何一条轨迹耗时/调用这么多，回答完再继续”。已明确回答：当前是官方ClaudeCode+Playwright复刻20评测页/40视图的完整网站，非单次问答；267运行约36分钟，292请求291完整/23写入编辑/7实际src变化，观察/比较/浏览器自查占大量调用。健康检查本身不调用模型，完整视觉评分另需40个judge请求，功能测试也耗时。研究者将成功要求扩为多轮源码纠正至0.75并追加逐页核对，增加重复成本，先前未充分说明范围已坦承；当前是纠正演示，不能作为原始模型一次baseline。当前继续同一attempt交付及验收，不把生成或正常退出当成功，不新增私有答案或手写应用。

265/full_visual_1791093098524327635原生全分0.7006<0.75，正式成功false。functional0.5644/visual0.8367/structural0.7887/quality0.8999；20页40视图981正权重判断全部可用，40真实请求完整且failed0、未完成0。build_result success，102源码前后/模型来源SHA相等、产物SHA16c0105640f474c65c873d66134fd4ce8c3b0fd8b67b857ba6a67f68b92196d9通过。依赖恢复已奏效，但模型实现不足仍存在；没有同候选挑高分重试。原264禁VLM及265完整分分别保存。same-provider self-judge、物理backend未知、纠正演示非baseline和canary排除限制保持。证据265/reports/trajectory_qualification.json。

旧265及264容器均stopped确认后，267/v17唯一原生agent已启动session75605、attempt recreation_eval_baseline_1791094782714342213、relayPID32599/8173、proxy8803；10运行SHA/102仅模型源码SHA与离线fixture已验收。只依据自有源码的公开内容/控制缺口提醒，无私有评价/分数给agent，不手写应用/不热改vendor。不改其他聊天。当前177真实响应完整/空0、6写入编辑（含比较辅助脚本），实际src/components/Layout.tsx与src/pages/ContentPages.tsx hash已变化；22公开导航路径含空初始/离线/搜索/两隐私页。无DOM脚本/私有评价读取/参考evaluate，两个网络命令之一自身预览、一条受限探测被阻止，原回执保留。norm.py仅对公开a11y快照去动态ref编号/空白用于比较，非DOM回放；报告工具按首次后续匹配事件关联，修正跨轮tool ID复用，不热改运行代码。

268/rw_web_complete_scoring_v3已独立准备，只改267来源/版本/路由8173身份，沿265成功依赖恢复/官方assertionVLM/并发2/完整覆盖与hash验收；未启动judge或另一agent。成功目标尚未实现，待267实际交付和功能分符合可达门槛后重新做独立完整评分，旧候选不反复评分挑高。

## 历史后续：264功能评分结束，265完整评分实际运行

264原生功能最终102/229（scripted78/140、agent_gen24/89），tier加权program0.5644；禁VLM旧总0.2822、score_passed=false，不能称成功。公开轨迹638动作/观察、41图像观察已导出到264/public_trajectory，凭据与私有reasoning不进入导出。原635vendor/318data与新10SHA保持，原容器停止，309真实响应全部完整。

265/v2独立完整评分已启动full_visual_1791093098524327635，冻结停止的264候选并--skip-agent评分；恢复原lock对应官方安装依赖链接，不改候选或评分。当前已完成原生构建、截图采集及scripted78/140，agent_gen仍实际运行，VLM请求尚未开始属于阶段顺序；完整通过尚未知。正式验收要求build success、完整20页40视图/正权重判断、API终态、源码前后及来源SHA、artifact hash和官方总分>=0.75。其他聊天与旧分/freeze不改。

独立266只读取官方公开参考文件名元数据（不取评价内容）以核对任务规模；普通WSL/Windows读取失败，但必要已授权外网权限下Windows成功取得原revision公开元数据。50 Web任务，corravale公开HTML25/参考文件240，为最少HTML；不是20评测页和318全任务文件的同一计数口径。下一项cresvia29/715。没有选择或启动另一任务，原最小canary仍合理；不能用权限网络错误推断模型故障。证据266/reports/public_reference_inventory.json。

267/rw_web_deepseek_public_content_v17已独立准备，尚未启动模型：仅264自有源码102SHA/10运行SHA，原UID1002网络封闭恢复fixture成功，没有session/evaluation数据。提醒依据自有ContactPage电话/email普通span、HomeGallery无点击行为、正文概括性文字，要求agent通过公开无障碍/截图/普通动作逐页准确比对文本、可访问名称、URL/真实行为，不提供私有断言或分数，不手写应用；禁止参考DOM/HTML回放。等待265完整评分终态，未并发重复启动；旧全部结果不改。

## 历史后续：264原生交付结束，真实通过仍待评分

264/attempt recreation_eval_baseline_1791089863418290376原生agent在约2026-10-04 05:36:31 UTC结束：309请求全部完整/空0，原生result success/is_error=false、非摘要最终文本2561字符；21 Write/Edit（含自己预览辅助文件），output11957104字节。6个实际source差异：App、Header、PrivacyStatementPage、MorePages、OfflinePage、data/site；public_behavior_checklist.md实际生成，记录搜索query、隐私声明路由/锚点/披露展开、菜单/页脚/直接reload/back。清单为model公开自查，非独立评分通过证明。

有限公开工具审计无私有评价读取、无written network/DOM采集脚本；最终src审计无inner/outerHTML、querySelector、iframe、fetch、参考截图引用或http目的地字面量。6个curl/evaluate探测回执按事件顺序核验，所有非自身预览调用均由门禁拒绝。工具ID跨轮复用会使全局dict关联误配，新增只读audit_blocked_calls.py已按事件顺序纠正；这不是运行故障因果结论。actor已结束，原生scorer及新Playwright测试进程实际活跃、磁盘充分；controller阶段日志不刷新不等于停滞。当前原功能评分未结束，265完整评分尚未启动，成功目标未实现。不改其他聊天/旧分/冻结。

## 历史后续：257完整评分未通过，264公开交互纠正与265依赖恢复

251/full_visual_1791087571222561011已结束：官方functional0.5411、assertion VLM0.800165、final0.6706<0.75，accepted_success_trajectory=false。40/40视图、20页、981条正权重原生判断全部可用，源码101 SHA前后/模型来源相等，产物hash验明。41真实请求中40完整、1供应商server_error经原生1/16重试恢复；非240秒截断。功能97/229，交互子组4/61，实际模型应用仍不足，不能把pipeline status=success当任务通过。

独立评分build_result=install_failed，缺yallist离线缓存；旧scored_artifact_sha256.json中official_rebuild=true为错误元数据，新trajectory_qualification.json明确更正，原文件/成绩保持。原worker结束时删除workspace/node_modules，但/workspace/shared/mockweb-template-deps/<原lock>/.complete及依赖仍在。一次性无网络容器恢复原lock对应链接，官方build_agent_output实际success、源码不变，未调用模型。不是改应用或下载新依赖；251旧分仅适用于已生成产物。安全check_scoring最终status遗漏started_epoch曾误显示0请求，报告工具现以不可变run标签时间过滤，恢复41/40/1，不重置账本。

264/rw_web_deepseek_public_interactions_v16独立新版本：仅恢复257模型源码101 SHA，无旧session/评价/私有测试。指导依据模型自有SearchPage提交preventDefault无效果、PrivacyPage已有/about/privacy-statement/链接但routeFor缺路由；agent需自行通过公开普通交互观察真实行为，不提供评分/私有断言或研究者应用代码。10运行SHA/UID1002离线恢复验收通过，旧257/251均stopped核对后唯一agent/session37469、loopback8172/proxy8802、relayPID68312启动。初期9完整/10请求、无编辑，真实browser_click/snapshot推进，尚未交付或验收成功。

265/rw_web_complete_scoring_v2已准备，未启动评分：沿251原生assertion/并发2/同资源self-judge，只在新容器恢复原官方依赖链接并核验lock、原依赖、.complete，正式验收还要求build_result=success。旧251源码/分/失败不覆盖。证据251/reports/trajectory_qualification.json、build_dependency_diagnosis.json、dependency_repair_admission.json，264/reports/phase_manifest.json、restore_admission.json，265/reports/preparation_manifest.json。未动其他聊天当前评测、148/315登记/103暂缓。

## 历史后续：参考自验与257纠正版本

257旧禁VLM评分最终97/229（scripted75/140、agent_gen22/89），加权program0.5411、旧50/50总0.2705、score_passed=false；原635vendor318data验明，生成容器stopped。并非97/229直接当0.5411，后者为原生tier加权功能。完整公开导出932动作与观察/50图、raw与observable SHA保留。251正式独立完整评分已启动full_visual_1791087571222561011/session95272：原生--skip-agent、assertion VLM、同已验收资源（self-judge限制）、并发2，原候选commit冻结，重新构建/采集/功能后视觉评分，记录真实请求/全viewport原生返回值/源码前后SHA。原禁VLM成绩不覆盖，不宣称通过。当前页面采集中/尚无VLM请求属于顺序预期。

257正式原生非摘要交付于2026-10-04 04:05:47 UTC附近：437请求全部完整/空0，65 Write/Edit，最终答复3334字符/output11938670字节。独立源码审计副本reports/final_source_review，未发现dangerouslySetInnerHTML/outerHTML/innerHTML/querySelector/iframe/fetch/localhost/screenshot或参考png引用；16网络字符串Bash命令均自己4173/5173预览，参考evaluate1次被阻止，无私有评价读取/写入networkDOM脚本。属于有限审计，不当形式安全证明。源码router保留尾斜杠地址已实际变更；仍有非根to的#兜底，但最终源码没有http(s)目的地字面量，不能仅靠此分支就断言当前活跃链接全坏或它是低分唯一根因。正式功能评分运行中，不能把437 complete/CLI success当任务通过，251完整VLM评分仍未启动。

257执行中已207真实响应全完整/空0、24编辑、output11936194字节，20实际公开页面路径；尚未最终交付/评分。有限工具审计5个网络字符串命令均为自己的localhost4173预览探测，无参考HTTP抓取；reference browser_evaluate1次被原门禁阻止。无written_network_or_dom_scripts/private_evaluation_reads，不等于安全性形式证明。

可选测试契约诊断的docker cp操作被自动审批明确拒绝：不允许复制私有评价测试，未执行，不以其他方式绕过；继续公开观察与已有官方报告，不需要该访问推进用户任务。没有私有答案给予agent。官方SiteServer/static_handler.py自身支持页面路径SPA回退已只读核对，不能将255低分解释为一般静态服务无路由支持。

256参考站自验v1直接CLI缺少官方worker设置的MOCKWEB_NODE_MODULES，@playwright/test缺失，功能total0；该0无效，原日志与源码保留。独立v2恢复官方worker原路径/opt/mockweb-bench/batch_run/node_modules，Docker network=none，--reference-candidate，无agent/API/VLM。实际228/229功能通过（scripted140/140、agent_gen88/89），官方tier_weighted功能0.9974989579；结构87/87。缺GT/禁用VLM总0.4987不当参考站不成功或模型能力0。结果路径256_recreationworld_reference_selfcheck/v2/run.json和eval_results。仍有1参考自验失败未逐项解释，不宣称评分完美；主要255功能负结果不能由缺测试依赖解释。

255最终522请求全完整/空0，36模型编辑，output11934153字节；公开1078动作/54图保留，77/229功能、program0.3885、总0.1942/score_passed=false，不能称成功。原源码仍明确把非根路径Link变成#并阻止点击；这是可公开源码观察，非私有测试反馈。

用户成功轨迹要求下，独立257/rw_web_deepseek_route_semantics_v15继续同排除canary，恢复255的101模型源码/资产/显式build文件，不恢复会话/评分/测试。只读旧源码生成公共行为纠正提醒：先验证真实链接、search query、直接路由/reload、可访问语义及实际自包含artifact，再改外观。不向agent提供分数/私有断言/参考HTML，不手写应用，不改vendor/算法。10运行SHA和101源码SHA验收；UID1002/networknone恢复fixture通过。旧255容器退出核实，唯一新进程session2573、loopback8171/8801、relayPID10254启动。正式success仍未证，251完整VLM评分未启动，其他聊天保持。

## 用户要求

用户要求“完成一次成功轨迹”。当前范围为RecreationWorld Web单题演示，不是250题批量；corravale.example继续排除正式held-out主结果。新资源仅RW，不修改其他聊天的学习实验或103暂缓。

## 已核验证据

- 238尝试1 `recreation_eval_baseline_1791051558705758062`：25完整请求，却以 `[Tool use interrupted]`结束，无主应用，原生no_usable_submission。
- 238尝试2 `recreation_eval_baseline_1791052105124286069`：57完整/58请求，末请求5.172秒URLError，原生infra_error/model_api_exhausted。不是240秒等待截断。部分状态保留。
- 独立239/rw_web_deepseek_transport_v2：3次有限连接重试，仅连接/临时HTTP错误，不重试模型no-code结果；4个不完整门禁、两次连接异常后成功、真实SSE验收通过，5源文件SHA冻结。0.0.0.0启动被自动审批拒绝后改成WSL127.0.0.1:8159，并停止旧Windows广泛绑定代理；Docker host网络访问loopback，官方agent仍原生netns隔离，不绕过拒绝。
- 239尝试 `recreation_eval_baseline_1791053354816382092`：101请求全部完整，生成数据/样式/Header/Footer，但App仍默认模板；浏览器resize回执成功，随后 `[Tool use interrupted]`。原生passed=true只是pipeline结束；score_passed=false、功能0/229，不是成功轨迹。[审计](../experiments/239_recreationworld_deepseek_transport_v2/reports/audit_recreation_eval_baseline_1791053354816382092.json)。全部原分/轨迹/失败保留。
- 独立240/rw_web_deepseek_delivery_hint_v3：官方vendor agent/评分不改，额外3句执行提醒“简短观察后先构建最小React应用，再逐页完善，结束前验证output/index.html”。改变输入指导，不能当原提示baseline。提醒文件实际在agent目录中保留，尚未核实完整上游prompt加载。独立目录和8789端口，启动时旧agent退出仅旧scorer存在；现旧239评分已结束、新240一个agent运行，当前72完整请求，主应用仍未交付。

## 未知与约束

`[Tool use interrupted]`的上游生成/兼容层原因未知；完整HTTP/finish不足以证明任务完成，不归为240秒超时。请求别名deepseek-v4-flash-vision-exp，服务自报deepseek/deepseek-v4.1-flash，精确checkpoint未证。VLM judge禁用，null不是judge故障。全部失败和freeze保持；挑出的成功演示不能估计无条件成功率，不替受测agent手写应用冒充轨迹。

## 下一步

继续240当前单题，核对真实源码、构建、浏览器运行与官方功能结果；收尾补充实际结果、证据路径和限制，不提前称成功。共享239账本按240 route/attempt独立归属，安全快照和新phase_manifest保留。

## 同轮后续实证：240遭524，241基础设施恢复

240实际写入主App/多路由组件，完成构建并在浏览器自查；第188请求供应商HTTP524、126.878秒，前187完整。旧有限重试名单漏524，因此只尝试1次；原生infra_error/model_api_exhausted、评测not_run。这是基础设施中断，不能把metrics的0当有效能力评分；旧失败/部分源码/会话保留。

独立241/rw_web_deepseek_infra_resume_v4将524加入有限重试，增加安全响应结构计数、不存payload；合成524＋URLError后成功、真实SSE、151快照SHA、语法验收均通过。只对已记录infra_error恢复，不对no-code模型结果恢复。旧容器stopped确认后保存同原生会话11e38f91-ef3a-466a-a2ea-d26e6adfa474、公开源码/public和原生projects；无凭据复制。独立本机8160代理/8790官方proxy，官方vendor与CLI二进制不改，启动shim只在CLI调用前恢复快照并用原生--resume同session（去initial --name），不改评分。

恢复首验实际App保持1934字节，agent继续缺失资源/构建/桌面与移动截图和菜单交互；当前15新增完整请求。这是恢复链路通过，尚非最终任务成功。240原失败没有抹掉，最终可用轨迹必须链接中断及恢复两个segment，不称无故障从头baseline。

## 后续：长会话恢复失败与短上下文独立版本

241最终50请求49完整；末请求4次HTTP524各约127秒，总515.177秒，原生infra_error且未评分。模型已更新App至2767字节、生成约6.56MB自包含output/index.html并完成多项浏览器检查，部分代码与原生会话均保留；这些尚非成功验收。

242/rw_web_deepseek_stream_resume_v5改真实上游SSE并保留同会话，完整工具流与截断拒绝通过，但首正式请求96.814秒后首SSE错误帧导致失败，无正常模型输出或源码推进。安全账本未捕获错误详情，原因未知，不能确认为上下文限制。其后独立随机六字符图像SSE识别正确、DONE/stop通过，排除了简单图片输入普遍不可用，但不证明大历史上下文可用。

243/rw_web_deepseek_checkpoint_v6独立保存242源码151SHA，旧容器stopped核实后，仅恢复模型生成的src/public/构建文件，不恢复旧projects或--resume。在官方初始任务输入前明确添加“基础设施检查点、保留现有实现、简短验证并交付”的提示，重新建立原生上下文；因此属于已披露检查点恢复演示，非原提示从头baseline。6源文件freeze、原218.check、真实SSE工具与图片、缺DONE/finish拒绝通过；loopback8162/官方proxy8792，官方vendor/评分不改。首3请求中2完整，工具正在检查现有实现，最终成功未证。新relay仅添加脱敏供应商错误记录，凭据不进产物/记忆。未启动250批量或改变其他聊天实验。

## 实质纠正：官方proxy文本化图片，旧视觉执行受污染

只读取得镜像内claude_code_proxy/translator.py并精确函数复现：_content_to_text没有image分支，tool_result的image/source/base64落入JSON序列化，发送为tool纯文本而非OpenAI image_url。243真实原生轨迹9图、830948编码字符；报告243/reports/image_transport_audit.json。这是已证基础设施缺陷，先前直接provider随机图片验收不能替代完整Claude链路验收，238—243的视觉观察不能称正确多模态执行。524具体因果仍未证明；243某524第2次50.439秒完整恢复的证据保留，不抹失败。

243明确停止原因是该已证图像传输污染，未评分，不伪记能力零分。只停止其精确容器，旧source/完整工作区/原生轨迹保持。244/rw_web_deepseek_vision_bridge_v7另建：官方vendor不改；relay仅将官方文本化的合法image JSON无损恢复image_url，原工具回执ID/文本保持，连续工具回执之后追加带来源ID的图片user消息。对普通文本/非法base64不改，不生成视觉答案。使用真实官方函数＋随机图＋工具回执＋修复＋provider全路径，六字符5JY8R8正确、DONE/stop、图片payload逐字保持通过；SSE文本/工具/三种截断拒绝通过。7源SHA/151源检查点/旧635vendor及318dataset验明后唯一新单题启动，loopback8163/proxy8793。

244另明确提醒：必要修复/build/浏览器检查通过后，最终text-only交付结束会话，避免已确认事项无限重查。作为检查点演示提示变更明确披露，不当原提示baseline。恢复原模型生成源码，不由助手手写应用，不改评分/其他聊天。当前尚未成功验收，待原生正常完成及官方分。

## 后续agent负结果：原创规则违规，另开干净执行

244正确多模态实际运行，逐请求记录image_url，最多已送19张真实图片。模型修改样式/移动布局并继续观察，但公开工具脚本在参考origin37557批量遍历14页、querySelectorAll('.nav-block')/递归children提取分组结构，并复用参考panel-header等类名。报告244/reports/authorship_action_audit.json、原native prompt lines406—413明确禁止该行为；这是agent合规失败，不是模型API故障，不能把高分结果称合规成功。尚未评分，不声称官方0.10封顶已实际施加。只停止精确244容器，原工作区/轨迹/源码/图像完整保留。

245/rw_web_deepseek_clean_vision_v8另建，从镜像干净官方脚手架冷启动，无源码/会话恢复，保留旧所有负结果。使用相同已验收视觉桥接、原模型/官方任务/评分；补充观察规则明确禁止参考origin browser_evaluate/run_code或脚本采集DOM/类/几何，只用截图/无障碍快照/普通交互，允许原协议二进制媒体。引导先构建、逐页完善、最终自包含交付/text-only结束；非原提示baseline，canary仍排除held-out主结果。旧身份stopped、7SHA与原635vendor/318data、SSE门禁通过，唯一新agent已运行，loopback8164/8794。目标仍为真实合规交付与官方通过，不以启动替代成功。

## 245空响应负结果与246非空输出门禁

245的正式attempt recreation_eval_baseline_1791065731641423473只有6次API，全部SSE完成，但末次stop无可见文本/工具调用，只有reasoning token计数；CLI空result成功不能当任务成功。App仍默认模板，原生no_usable_submission、score_passed=false，旧证据完整保留。供应商原生/v1/messages独立探测同样返回HTTP200/end_turn但无可见答案，不通过接入验收，不切换该端点。

246/rw_web_deepseek_clean_delivery_v9另建：非空文本或真实tool_calls是接受输出的必要条件，拒绝None/空白/空串/reasoning-only，四类型回放及正常输出通过；不把reasoning变成答案、不自动重试此类模型负结果。原任务后追加执行提醒，干净官方脚手架，无旧源码或会话恢复，7源freeze及原635vendor/318data验明，唯一新attempt recreation_eval_baseline_1791065946555636335、loopback8165/8795运行。当前164次真实请求完整返回，App4197字节、原生组件/数据已生成，正在构建；尚无最终成功/评分证据。

246观察限制：未见参考browser_evaluate/run_code，但公开工具用curl/正则读参考标题文本并读取CSS设计信息，未完全遵循补充的截图限定提醒。最终原创实现合规需结合实际代码/工具审计，不能因无脚本浏览器工具而提前称通过，也不将允许的单个设计token观察自动等同244批量DOM重放。所有版本均为已披露单题演示，不当无条件baseline或250完成；其他聊天及103暂缓保持。

## 246正式负结果与250原生观察门禁版本

246完整执行265请求全部SSE完成，实际App5460字节/交付约9.53MB；末输出为上下文摘要，并非明确交付声明。官方正常评分功能130/229（56.8%），program_score=0.5502、task_score=0.2751、score_passed=false；VLM仍禁用/null，不将program别名当纯功能分。只读进一步审计reference_action_review.json records195/199/207：curl取得14页HTML，以参考nav-block分组/正则抽取并保存navgroups.json供候选组件重放，明确违反原创规则；此前仅检查browser脚本工具不足以判断合规，本段更正上段未知判断。真实失败/原分/源码/freeze全保留，derived delivery_acceptance.json明确拒绝成功；旧audit的usable_verified_trajectory只表示存在部分通过功能断言，不能当任务成功。公开导出528动作/工具回执和31图片观察，排除私有推理与凭据。

250/rw_web_deepseek_observation_guard_v10是明确协议变体，不称原harness baseline：官方vendor、任务、评分及模型不改，但追加原生Claude Code managed PreToolUse钩子，禁用参考脚本DOM/HTML/CSS采集（含Bash curl/Python网络），保留Playwright截图/无障碍/交互、候选preview4173/5173及受控显式图片/字体下载；binary helper拒绝HTML/CSS/JSON/JS。Stop钩子拒绝默认模板/缺交付、摘要收尾及源码晚于交付构建。不代写模型应用或使用gold。依据官方 https://code.claude.com/docs/en/hooks 的原生事件与exit2阻止机制，10fixture用例通过，实际原生CLI允许Bash且阻止curl的真实模型验收通过；合成验收不进入正式benchmark源码/轨迹。初次验收脚本subprocess.call不接受input参数，在模型调用前失败，修正run后再验收，该错误不当正式任务结果。

旧246agent/scorer退出、原635vendor/318data和新10源SHA验明，新250干净脚手架，无旧源码或会话恢复；唯一正式任务已启动，loopback8166/proxy8796，relay84805，命令session94286。最终成功尚未证，需要实际原生完成、官方score_passed及独立原创审计。新工具约束是本轮为遵循原协议的实施选择，明确披露，不能当用户另行确认原提示baseline或benchmark增益。

## 完整评分缺口纠正与251独立准备

246原scores.json逐20页visual_ssim note=no_gt_screenshots，overall0；原dataset318文件有gt_layout/DOM JSON但无SSIM参考截图。native视觉禁用并不是API报错，但该数据不能提供有效SSIM视觉观测，旧task_score0.2751是functional0.5502×0.5＋缺失视觉被记0×0.5，最高也只能0.5，不能用它要求0.75完整成功或当视觉能力失败。此前本轮未在评分前拦截此缺口，现明确纠正。246原创违规和130/229功能不因该纠正被抹去。

更正program_score含义：当前冻结官方scripts/platforms/web/pipeline.py::_programmatic_only明确去除visual并重新归一化，原生246program0.5502是分组加权功能分，raw130/229=0.5677；不能继续沿用旧“混合SSIM别名”表述。task_score则仍是原生加权总分，VLMnull不当已完成视觉judge。

251_recreationworld_complete_scoring_v1独立准备，计划在模型交付结束、候选源码SHA固定后，官方runner.run_agent --skip-agent＋官方assertion VLM完整验收，不启动/代写agent，不改旧SSIM分或vendor。官方VLM判分函数＋真实同一授权资源的独立蓝色方块图像正/反断言通过（true/false），native_judge_admission.json；初次准备缺Pillow在API前失败，改标准库生成合成PNG，不改环境，合成不进正式轨迹。数据包有原生vlm_assertions.json；同资源生成/评分的self-judge限制和精确checkpoint未知必须披露，canary仍不进headline。250冻结judge-disabled配置不热改，其旧分保留并明确视觉缺测；251尚未运行正式候选评分。

## 250完整交付低分与252纠正演示

250原生最终result正常非摘要、1574可见字符，312请求全部完整；982原始记录、公开932动作/86图已导出。77/229功能（scripted58/140、agent_gen19/89）、70/87结构，official program0.3885/task0.1942/score_passed=false。没有API失败，不把能力低分归为基础设施。旧视觉缺测不能当视觉能力0，但即使视觉满分总分最高0.69425仍低于0.75，故251不为这个必然不通过的候选重复调用judge；保留完整原分/源码/freeze。

公开动作审计101网络相关Bash，仅1个非binary helper是自行写源码的heredoc且被阻止；两次browser_evaluate也被阻止，未发现私有evaluation读取或写入网络/DOM采集脚本。最终源码查无generic DOM renderer/dangerouslySetInnerHTML/参考port/screenshot背景模式；此为有限证据审计，不宣称门禁绝对防绕过。

252/rw_web_deepseek_link_fidelity_v11是明确纠正续作演示、非独立baseline，不是基础设施恢复。根因线索来自自身公开源码Link把多类dest改为#并阻止导航；指导agent通过允许的参考snapshot/交互核实实际文字与dest，不给旧分/私有测试/gold，不由研究者手写应用。仅恢复模型生成src/public与7项名单中的实际构建配置，86SHA；旧会话/trajectory/evaluation/task运行元数据不恢复。首离线fixture缺提示挂载导致启动前失败，无模型调用；补齐fixture后UID1002/86SHA/无evaluation/session验收通过。原250容器stopped确认、10新runtime SHA与原635vendor318data验明，唯一252启动，relay15161/loopback8167、proxy8797、session43443。251增加源码候选显式选择/启动锁及program>=0.5数学可达门禁；尚未启动正式评分。

252实际失败：attempt recreation_eval_baseline_1791073826370657046，9/10请求完整，第10真实SSE5帧/DONE、7.115秒后ValueError，receipt1791073888494712979。43raw/17公开tools仅读源码与公开snapshot，尚无源码修正；native错误终止、评测未运行，0不是有效能力分。旧ledger未记录具体门禁原因，精确空输出/其他协议原因不能补编。此不是早截断时间的证据；旧失败/原freeze/源码全部保留。

253/rw_web_deepseek_protocol_diagnostics_v12只补安全response_shape（finish_reason、可见/推理字符数、工具数、usage、自报模型）与本地固定ValueError原因码；不保存正文/推理文本、不把reasoning转答案、不放宽门禁或重试空模型输出。四离线合法/空输出/length/toolcall门禁与不存文本验证通过，UID1002/86源恢复仍通过、无模型调用。旧252容器退出后新10SHA/原635vendor318data验明，唯一253启动，relay16261/loopback8168、proxy8798、session3686，仍是公开观察纠正演示、非baseline，正式成功未证。

253 receipt1791074338985728058补到精确根因：真实SSE5帧/DONE/6.305秒，stop、正文0/工具0/推理文本0，usage自报64889 prompt/16 completion（reasoning_tokens19与total字段有不一致，不当精确物理计数）。是空模型回复被附加代理门禁转HTTP502，不是240秒截断或网络超时；不能将其当交付成功。原始空/失败及未评分状态保留。

254/rw_web_deepseek_native_empty_recovery_v13将协议完成与任务交付分开：真实stop空回复如实返回原生CLI，账本显式completed_empty_visible/字符计数/请求hash；代理不额外重采样、不制造文本或reasoning答案。原生CLI自己处理空回复，最终Stop门禁仍要求非空最终消息、非默认应用/实际output与源码构建新鲜度。独立本地合成server+真实官方CLI验证：第一次空、第二次非空，两个request hash不同，CLI正常非空结束、一个Stop；第一次空没有触发Stop，因此不误称Stop阻止了第一次空。另独立空Stop单元判断阻止通过。无真实provider调用、合成源码/轨迹不混benchmark。首生成脚本全局替换导致缩进错，启动前compile已拦截；限定首处后修正，不影响正式run。

旧253容器退出、UID1002/86源码恢复及新10SHA/原635vendor318data验明，唯一254启动，loopback8169/proxy8799、relay17506、session52768。仍为源纠正演示/非baseline，最终官方成功未证。原250program0.3885能力低分与252/253空回复错误保持，251尚未对正式候选启动视觉评分。

254已结束：193真实API全完整、空回复0，原生非摘要/非空2928字符交付，App3782字节/约11.7MB自包含HTML。公开审计3个网络字符串命令仅自身grep与本地预览（2被阻止）、一次browser_evaluate被阻止，无私有评分Read/参考网络DOM采集脚本；源码无参考端口/通用DOM renderer/截图背景痕迹。有限审计不是安全性证明。官方功能仍77/229（scripted58/140、agent_gen19/89），结构70/87、program0.3885/task0.1942、score_passed=false。源码App/router及output SHA与250均不同，排除旧构建被误测；此为agent实现负结果，不是本次API故障。VLM完美仍最多0.69425，故不浪费正式视觉调用或伪报成功，251继续未运行。

独立255/rw_web_deepseek_pagewise_fidelity_v14仅恢复254模型src/public与明确构建文件88SHA，无会话/私有评测。提醒基于自身源码可见的占位链接/无行为表单，要求逐页公开snapshot/普通菜单与点击验证，原文标签不改写、自己实现语义组件；未向模型提供测试/分数/gold。原生CLI/工具门禁/真实图片/空回复兼容与官方评分不改，非独立baseline。UID1002/88源码无网络恢复验收通过，新10SHA及原635vendor318data验明；旧254容器退出后唯一255启动，loopback8170/proxy8800、relay44490、session34847。所有旧分/失败与freeze保留，其他聊天不干预；成功仍未证，持续执行用户目标。

255已结束：原生20页公开导航/36源码编辑、522请求全完整/空0、2287字符非摘要交付；App3825字节/output11934153字节。原生功能仍77/229、program0.3885/task0.1942/score_passed=false，正式成功拒绝；1078公开动作54图及交付导出保留。最终有限审计27网络字符串命令含16受控图片下载与11自身预览，reference browser_evaluate一次被阻止；无私有评分Read/参考网络DOM脚本，源码无通用DOM renderer/截图背景等模式。读取联系页等Bash是对Playwright已经公开返回的YAML accessibility snapshot做文本选择，非参考HTML抓取。监控helper曾遭账本并发写入FileNotFoundError，已仅在报告探针容错并标明transient_receipt_reads；冻结10运行文件不改，不当API故障。

因250/254/255不同源码但功能结果一致，补启动256官方--reference-candidate无模型自验，直接评分冻结参考站，network=none、VLM关闭，不启动agent、不修改数据或评分、不将参考样本算模型成功。使用旧254已停止容器的本地独立clone，原候选/旧分全部保持。当前自验未结束；既往“agent实现负结果”解释须以评估契约自验有效为前提，不在自验未完成时宣称具体根因已定。

251尚未正式评分。官方Web evaluator只存视觉总分而未保存VLMJudgeResult.page_details，因此在未启动的251增只读原生返回值观察器，原vendor与计算不改：原始返回对象、参数、调用次数1与错误传播的离线验收通过，不调用模型。先用未准备checkout的基础image做离线fixture遇import路径缺失，启动前改为直接加载本机冻结vendor，并恢复-m的CWD导入语义后通过，无正式运行受影响。未来251的launch/eval_entry/observe_runner三SHA冻结、原生逐页裁决另存，仍以同模型self-judge/assertion模式披露，部分/失效裁决不接受。没有合格功能候选时不浪费视觉评分或填分。
