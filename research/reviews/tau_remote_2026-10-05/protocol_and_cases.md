# 远端 τ² 航空与电信：协议及配对案例只读审计

日期：2026-10-05。来源为用户指定远端快照 `14f5b59ab29351973429777fb013afafd15297ce`，本地导入目录 `research/imports/2026-10-05_tau_remote/repository_complete/`。本审计只读取保存产物、在内存复算检查并保存本文件；未运行模型、实验、服务或学习器，未改原实验、源码、README、STATE。案例为诊断性选择，不能当作总体收益估计或因果实验。

## 1. 协议能回答什么

两域都是原 AutoSkill 学习基线，**不是新实现的 R/W 算法**。267：官方 train30/test20，dev4、演化26，测试20×4×2；268：train74/test40，dev4、演化70，测试40×4×2。两者固定 τ² v1.0.1 / `fc0055dc4e0a316c3f83133267fbd6faaa770992`，消费者与用户模拟器均 deepseek-flash，OpenClaw 2026.9.7。B1增加冻结库及首轮原生 `$技能` 引用；不应把整个处理只描述为磁盘目录差异。

原始结果核验：两域采集 task ID 集合和学习 manifest ID 集合均恰好等于 evolution；两组测试 ID 均恰好等于 test，每题每组四轮。总种子42产生 trial0—3的实际种子 **670487、116739、26225、777572**，两组逐轮相同。匹配种子不意味着模型输出、用户措辞或整段会话完全一致。

267评分依据为 DB+COMMUNICATE；COMMUNICATE是字符串检查，不是主观满意度。本文两个航空案例 communicate_info为空，该项自动为1，真正区分是最终DB是否匹配。268主要评分是环境状态断言，**其中12/40题还要求ACTION，共48/160场/组**；不能称全域只有ENV。所审数据题只要求移动数据可用及至少200Mbps/Excellent，不是glm主裁判。`user_stop`或用户感谢只表示会话结束/认可，不能代替官方业务评分。绝对分仅适用于本固定版本和本地harness，不能直接比较论文排行榜；航空与电信评分对象不同。

原报告：267 B0=54/80、B1=58/80，差+5pp；268 B0=127/160、B1=119/160，差−5pp。两域配对区间均含0；不能据此证明稳定增益，也不能证明没有效应，或把全部差异归因到技能生成。

源：[267协议](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/protocol.md)、[268协议](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/protocol.md)、各目录的 `versions.json`、`split_manifest.json`、`runs/test/{no_skill,autoskill_library}.json`。

## 2. 分集、学习输入与文件完整性

- **未发现所审调用链把测试结果送入学习。** 采集/学习ID与演化集一致，学习脚本只遍历 `autoskill_input/trajectories/task_*.txt`；不能把这一检查扩大成所有外部实现绝无泄漏的证明。
- 官方split没有实体/模板隔离。267 manifest记录4个共享标识（其中含gift-card标识，不能全部解释成独立自然人）和14个共享reservation/flight标识；train15/test16动作签名相同、指令近似0.849。268共享19种故障组件，按类别复用指令模板。所得结论是官方分集内新组合/任务的复用，不是未见实体或未见故障类型的泛化证明。
- 268这12题均为`service_issue`，原任务明确期待assistant调用`transfer_to_human_agents`，同时环境仍为`no_service`。其中11题含`lock_sim_card_pin`，另一题是`contract_end_suspension|unseat_sim_card[PERSONA:Hard]`。因此此子集的转人工是规定验收动作，和本审数据恢复题的转人工失分必须分开。原full2285中含ACTION的题数不等于本split比例。第一条所审ACTION回执`dbfabb00-b631-407a-811d-bd0508549f9d`显示ENV与ACTION均为1；该任务`compare_args=[]`，不应把示例summary字串当作额外精确匹配要求。
- 267协议L31对“五题未覆盖”的类别描述不准确：manifest实际为**订票24/25/35/8，转人工13**；不是五个read-only/escalate边缘题。
- **采集结果需更正：**267 raw与学习manifest均19成功/7失败，均值19/26=0.730769，原final的0.72不准确；268 raw与学习manifest均**53成功/17失败**，均值0.757143，原final的52/18不符。当前学习文本逐条与raw按转换代码在内存重建的结果完全一致。
- 两域转换器把reward/termination只写manifest，学习器不读取该manifest，`success_only=False`。准确说法是**不提供最终验收/成败标签**；并非没有任何反馈，因为用户回复、工具成功/错误仍在文本。
- 调用ID未进入文本；工具返回最多4000字符。267采集中5个工具正文超过4000，实际截断。268无此长度截断，但另有双边工具事件丢失，见下一节。
- 当前快照未包含学习脚本指向的外部AutoSkill vendor，因此未独立复核该vendor内部如何使用文件名。268文件名含故障组件，fallback的 `data.task=f.stem`也带这种信息；是否某次fallback实际发生、或文件名进入作者提示，尚需原提取请求核实，不能仅凭脚本断言泄漏或排除该信息通路。
- 冻结库：267一个技能v0.1.1、无附件；268一个复合技能v0.1.35、29个references。原manifest明确有两个0字节文件：`device_side_remediation_checklist.md`、`no_service_diagnostic_ladder.md`。这是附件质量缺口，不证明已导致某个具体失败。
- 导入后技能Markdown物理SHA因Windows CRLF变化不同；**仅CRLF→LF后，所有31个冻结文件与原manifest精确一致**，输入数据文件物理SHA也与split manifest一致。不能把换行差异解释为实验期间技能被修改。
- 原读取审计的 `triggered=bool(read_skills)`只证明匹配到读取调用/结果路径；没有成功、完整正文或正文hash门禁。80/80和160/160应称历史审计的读取触发覆盖，不能称已核验完整成功阅读，更不能证明29个references均被读完。当前导入缺相应原native会话数据库，无法独立逐收据复核。

源：两域 `scripts/canonicalize_trajectory.py`（267 L26—55；268 L28—58）、`scripts/autoskill_build_trajectory.py` L40—57、`autoskill_input/trajectories/manifest.json`、`runs/collect/evolution.json`、`frozen_skills_manifest.json`；267 `scripts/scan_skill_reads.py` L138—140（268同类口径）。

## 3. 电信用户侧调用丢失：明确属于本实验输入适配

268采集70条raw有 **477个assistant侧工具调用、866个user侧工具调用**。转换器只在 `role=='assistant'` 分支输出工具调用；`role=='user'`只输出非空正文。因此866个用户侧调用的结构记录没有进入学习文本，用户工具返回仍进入`TOOL_RESULT`。不是用户行为完全不可见：许多动作还可从用户叙述、前一条指导或返回正文得知；丢失的是显式调用、动作发起者、参数与调用ID结构。

具体对照：演化task `[mms_issue]airplane_mode_on|bad_network_preference|bad_wifi_calling|break_apn_mms_setting|break_app_both_permissions|data_mode_off|data_usage_exceeded|unseat_sim_card|user_abroad_roaming_disabled_off[PERSONA:Hard]`，simulation `c5ef47dd-81a5-4db3-8f0f-c6c7efda3db1`。

- raw `messages[79]` 为无正文的user消息，带 `toggle_roaming({})`、requestor=user及真实调用ID；`messages[80]`返回“Data Roaming is now ON”。
- 学习文件 `task__mms_issue_airplane_mode_on_bad_network_preference_bad_wifi_calling_break_apn_mms_setting_break_app__2c9fa7.txt` L211为agent称已开通**线路**漫游，L213要求用户再打开**手机**漫游，L214保留上述返回，但没有user `toggle_roaming`调用记录。

这使两层状态的动作—结果关联更依赖叙述推断，属于当前实验canonicalizer适配限制，**不能概括为AutoSkill作者算法固有缺陷**。是否因此生成了错误条款及影响新任务，当前没有单项对照证明。

## 4. 航空正例：政策允许的取消重订与不允许的直接改目的地

task29 / trial0 / seed670487。B0 simulation `97a27963-4df5-48cb-ab2d-cacd62060bbf`；B1 `60babf90-7ec9-48aa-9eb6-8d5f6e3e6767`。以下消息索引均为raw JSON的**0起始数组索引**。

**用户目标：**把DTW–LGA往返改为DTW–JFK直飞，普通Economy、早到且最便宜；健康原因希望保险处理费用，后来明确要一件行李。

**B0实际做法：**搜索并取得确认后，m26直接`update_reservation_flights`把旧票换成飞JFK的两段，m28加行李。工具允许写入，但政策L111—113禁止改票改变origin/destination，明确API不替agent检查。m27旧reservation顶层destination仍LGA、航段却指向JFK；最终DB不匹配，reward0。用户m31感谢不改变该结果。

**B1实际做法：**m2/m8明确指出目的地变更不能直接改票；m17取得取消和重订的确认，m18 `cancel_reservation`，m19状态cancelled并退原686；m20 `book_reservation`创建DTW–JFK新票，m21实际新票返回、价格282及一件免费行李；最终DB匹配，reward1。这是实际完成，不是只承诺重订。

**技能关系与边界：**冻结航空skill L41要求及早指出不允许操作，L57写允许的cancel-and-rebook替代，L64—65要求真实工具证据与同意；行为与条款相容。但两组原本都拿到同一政策，单对不能证明是该条款导致B1选择，也不能排除随机会话差异。

源：[航空raw B0](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/runs/test/no_skill.json)、[raw B1](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/runs/test/autoskill_library.json)、`inputs/airline_policy.md` L101/L111—113/L147—149、`inputs/airline_tasks.json` task29 evaluation_criteria、冻结skill L41/L57。

## 5. 航空退步：真的改票成功，却没满足“最便宜”

task16 / trial1 / seed116739。B0 simulation `a9c51c5f-95fd-4c6e-99ed-c0985c86501f`；B1 `95fcfd53-57c6-43a8-ad8c-bf56703ac4b4`。

**目标：**ATL–PHL行程顺延一天，选最便宜普通Economy，退差额到原付款方式。

**B0：**m14搜索一站航班，m16/m18比较207和216；m22实际写入HAT110+HAT172，m23工具返回总价207、退款2580；DB匹配，reward1。

**B1：**m11同一搜索结果的十个可选组合已包含HAT110+HAT172=207及HAT227+HAT139=216；m14却称后者是最便宜，m16实际写入216方案，退款2571。用户m15同意、m19称满意，但原要求的最低价格没做到；DB不匹配，reward0，COMMUNICATE=1。

**定位：**这是可见候选比较/目标满足失败，不是写工具没执行。skill要求工具核实价格（L33/L43/L64），但没有展开一站组合全候选最小化流程；未发现条款要求选择较贵方案。可提出条款覆盖不足的假设，不能由本对认定生成侧错误导致退步。该任务又与演化task15近似且共享目标实体，因此也不能用它证明实体外泛化。

## 6. 电信退步：线路漫游开了，手机漫游仍没开

task `[mobile_data_issue]data_saver_mode_on|user_abroad_roaming_enabled_off[PERSONA:Easy]` / trial0 / seed670487。B0 simulation `c5246357-565f-40f9-b895-0582b0eeb68e`；B1 `3e0d888f-06e9-49f5-ac8c-79e6a3ff4b65`。

**目标：**用户在法国，移动数据不可用/很慢，公开m1明确要Excellent速度。评分也明确要求移动数据可用及200Mbps/Excellent；本例不支持“skill把局部Excellent标准错误推广导致失分”。

**B0：**m19网络状态明确手机DataRoaming=No；m21区分账户已开与设备未开，m22用户实际`toggle_roaming`，m25复核Yes；随后m32关DataSaver，m35测速275Mbps/Excellent，两状态断言均通过，reward1。

**B1：**m9读到线路`roaming_enabled=true`，但没有取得设备network_status，也未指导/触发`toggle_roaming`；只m24关闭DataSaver，m30/m38测速均No Connection，m40转人工。最终两状态断言均未过，reward0。

**技能已保留需要的条件：**电信skill L83明确“line roaming_enabled=true但device DataRoaming OFF，要单独打开设备漫游并复核”，L123再次写同一层级区别。因此这是消费者漏检查/漏执行的证据，不能称技能遗漏该条款。B1 m2公开自报技能读取受context/read预算限制；当前只有其自述和历史path触发审计，没有原native错误结果，故实际读取失败原因仍未独立核验。

**转人工不等于本题成功：**skill L134泛称“Escalation is a valid success path”，但此题验收要求设备数据与速度恢复，转人工成功只是技术动作成功。这个条款有作用范围风险；实际B1也转人工，但它是否受该措辞影响、还是因诊断/读取问题，不可由本对断定。正常政策允许的转人工及专门以转人工验收的其他任务不应一概否定。

源：[电信raw B0](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/runs/test/no_skill.json)、[raw B1](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/runs/test/autoskill_library.json)、冻结电信skill L83/L123/L134、对应simulation的reward_info.env_assertions。

## 7. 能支持与不能支持的研究结论

可支持三种位置分开审查：输入适配丢失用户侧动作结构；归纳产物有附件空白/转人工成功范围风险；消费者仍可能漏用正文已正确保留的条件。现有原始案例没有完成“仅改生成/恢复机制、固定其他条件、在新任务改善”的完整因果链，不能据此宣称新R/W已有效，也不能把单技能、混合失败轨迹或不显著总分当作生成算法失败的证明。

后续最有判别力的免费准备是：核查缺失native读取收据；固定完整双边事件输入并保留验收范围，再设计同信息、同消费者、同预算的对照。此建议不授权新运行。
