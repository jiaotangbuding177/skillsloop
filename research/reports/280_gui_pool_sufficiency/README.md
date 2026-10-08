# 250题目标下的独立演化来源集合：补齐后停止扩充

日期：2026-10-04。**原16项不够均衡；已补11项，取得27个固定版本来源。MacPass因KeePass家族关系未排除转候补，主集合26个候选任务，足够作为首轮受控skills演化实验的素材池，现在停止搜集与下载。**这个判断针对主要行为类别的来源材料，不代表运行就绪、成功轨迹足量、250题全部受益或论文效果成立。

## 实际取得与登记

| 平台 | 主候选任务数 | 固定来源 |
|---|---:|---|
| Ubuntu | 7 | Xournal++、Flameshot、Heimer、GNOME Calculator 46.3、KReversi 26.08.1、Veusz 4.2.1、Cozy 1.3.0 |
| Windows | 5 | WinMerge、ScreenToGif、Caesium、Tad 0.14.0、Pomotroid 1.7.1 |
| macOS | 3 | Hex Fiend、Gifski、To-Day 2.0 |
| Android | 6 | Fossify Gallery、Activity Diary、Family Gem 1.2、OpenCalc 3.2.1、Shattered Pixel Dungeon 4.0.1、Package Manager 7.0 |
| Web | 5 | Squoosh、miniPaint、StackEdit、Vite docs、Actual Budget 26.9.0 browser client |
| 条件候补 | 1 | MacPass；不参与本轮“足够”的依据，旧279来源和证据保留 |

- [来源池](application_pool.json)：27个repo/commit、许可、构建证据、拟议流程与来源风险；归档累计311,322,152 bytes（296.90 MiB），26,742个普通文件。
- [演化任务登记](evolution_task_registry.json)：一个来源应用对应一个完整“观察参考→独立复刻→运行自查”任务，26主任务＋1候补。64条流程是任务内的公开观察/检查场景，**不是64条真实轨迹，也不是把复刻任务改成零散点击题**。
- [追加来源校验](source_integrity_verification.json)：11个新归档/清单/9,678文件SHA全部通过；原279的16来源验证报告与manifest hash保持。精确repo身份与原生200行/198repo无重合；这不能证明完整fork、模板或共享依赖隔离。
- [250题公开来源审计](benchmark_250_source_audit.json)：官方ID集合逐项一致、五平台各50、无重复/缺项。类别与能力关联来自公开README或参考页面身份/路径，不读隐藏tests/gold，不产生评测覆盖率。

## 为什么补这些，以及为什么停

原16项偏图像、文本和导出，缺少输入到精确结果、规则状态、复杂表单/组合筛选、实时计时、音频传输及科学数据绘图的直接素材。追加Calculator/OpenCalc、KReversi/Shattered、Tad/Veusz、Actual Budget、Pomotroid/Cozy，加上To-Day菜单状态及Package Manager只读系统状态，补齐主要行为槽；保持五个平台各有独立参考候选。

| 主要素材类别 | 来源依据举例 | 可沉淀的过程假设，尚非已生成技能 |
|---|---|---|
| 文档、图像、导入导出与持久化 | Xournal++、StackEdit、miniPaint、Caesium、Gallery、Gifski | 修改后重开核对、坐标/模型分离、撤销与输出工件检查 |
| 层级、列表、结构记录 | Heimer、Family Gem、Activity Diary、To-Day | 区分选中/编辑/显示状态、跨视图保存、排序/过滤恢复 |
| 输入到精确结果、表格与科学图 | Calculator、OpenCalc、Tad、Veusz | 控制变量探测、错误输入恢复、数据→列表/坐标轴输出验证 |
| 离散规则与合法/非法动作 | KReversi、Shattered Pixel Dungeon | 不只画棋盘/界面，探测动作前置条件、回合/复位状态 |
| 计时、播放、暂停恢复 | Pomotroid、Cozy | 观测真实时间推进/暂停/寻址，检查边界和重开恢复 |
| 系统状态、菜单与权限元数据 | Package Manager、To-Day，平台本身窗口/焦点 | 同步真实状态与显示；Package Manager限非root查询，排除安装/卸载/debloat |
| Web导航、表单、查询与视图状态 | Vite docs、Actual Budget，其余3项Web | 多字段/负例反馈、组合条件清除再应用、响应式和路由检查 |

250个评测应用不要求配250个训练应用。[论文§3.1](https://arxiv.org/html/2609.22000v1#S3.SS1)披露从GitHub选多样五平台训练应用并与评测去重，未给公开完整训练应用清单或最小应用数；35,000是采集并筛选的轨迹数，不能作为本项目必须取得35,000个问题的要求。这里“26个足够开展首轮”是本研究的设计判断，依据[停止规则](decision_criteria.md)，不是作者阈值或样本量检验结论。

CAD、特定传感器/IME、原生加密核心、高级编译/数据库/backend、某些Web booking/checkout业务规则，以及平台特定的迁移效果仍未知。保留这些OOD/专项困难，不为了消除每个稀有领域而无限扩充。参考准入失败时仅替换失败能力槽的候选，不重开无上限搜集。

## 保留的否定、更正与实施边界

1. GNOME Calculator 51.0要求过新GTK/Adwaita，主选固定46.3；Package Manager 7.9目标SDK37，主选固定7.0的SDK33。否定版本/证据保留。KReversi仍要求Qt6.5/KF6/KDEGames6；Tad有Electron/Node及DuckDB扩展离线风险；To-Day的Xcode/Swift包与AX缺陷、所有来源的字体/依赖/资产许可与GUI准入仍待验收。源码下载不能替代运行成功。
2. 更正279：论文[§4.2](https://arxiv.org/html/2609.22000v1#S4.SS2)/[C.3](https://arxiv.org/html/2609.22000v1#A3.SS3)明确Web50是44个合成参考＋6个公开网站派生参考，不能把44个`.example`全推成未知真实商业原站。完整共享模板近重复审查仍待完成。
3. 更正279中Doodle映射：`patzly/doodle-android`是动态壁纸/主题应用，不是绘图画布；原映射撤出足够性依据。真实Markers才是绘图类。37个历史bench ID映射只是存在性核对，不是37/250覆盖率。
4. 初次Actual Budget解包遇到Windows MAX_PATH，保留失败后以扩展路径原样保存同commit长文件名并全SHA通过。本机bundled Python随后缺stdlib，未修全局环境，改用已有系统Python3.11完成下载/核验；这是研究工具故障，不是应用/模型失败。未修改实验服务。
5. 原279来源/旧RW结果/STOP及其他聊天均保留。本轮没有参考运行、模型调用、采集轨迹、技能抽取或评测；运行accepted=0。不是官方train split或35,000 SFT数据的替代披露。参考原生准入与独立训练verifier先完成，才能实际采集。
6. 每个应用家族最多三轮含首次；多个流程、版本或跨平台端口不重置次数。26主任务全准入时最多78轮，不等于78条成功轨迹。没有自动恢复旧corravale迭代；其既有17次调试暴露单列，未来250题评测不能直接宣称全未见/干净held-out，正式分集与历史暴露须另审。

详细领域证据：[桌面100题](desktop/desktop_sufficiency_report.md)、[Mac/Android100题](mac_android/bench_100_application_audit.json)、[Web50题](web/sufficiency_report.md)。**来源扩充到此结束。**下一阶段的具体任务边界/参考GUI/重置和训练验证器依据真实准入结果冻结；不得把本页的预期流程或skills假设作为实验产物。
