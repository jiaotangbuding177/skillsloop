# RecreationWorld 对应的独立开源 GUI 应用来源池

日期：2026-10-04。用户本轮授权按照论文思路获取高质量开源 GUI 应用，要求与 RecreationBench 对应，并具备适合 skills 沉淀的轨迹预期。本轮执行公开来源获取和研究设计，不运行模型、应用、学习或评分；旧 RW STOP、同题最多三轮含首次及其他聊天实验保持。

## 已完成与证据

已实际下载**16个应用来源**：Ubuntu／Windows／macOS／Android各3，Web4。固定 commit 源码归档共153,239,413字节（146.14 MiB），解包17,064个普通文件，保存每个归档及逐文件 SHA256。正式数量、压缩字节数与文件数以[source_acquisition_manifest.json](source_acquisition_manifest.json)和[source_integrity_verification.json](source_integrity_verification.json)为准。[application_pool.json](application_pool.json)把每个应用的源码、许可、版本、构建依据、公开行为流程与 bench 能力映射放在一起。

这批是我们构建的独立应用来源池，**不是论文未公开的官方训练应用清单，也不是35,000条轨迹**。源码获取已完成；原生运行准入、验证器和轨迹采集尚未完成。没有把文档中“可本地运行”升级为本机已启动的实证。

最终核验：16个归档及inventory hash通过，17,064个解包文件逐一hash通过，无文件失败；41条拟议行为流程已汇总。[能力映射核验](bench_correspondence_audit.json)中的37个不同公开bench task ID全部存在。此处通过仅指源码取得完整性和身份／映射核对，运行准入仍为0。

## 与原文和 benchmark 的关系

[论文§3.1](https://arxiv.org/html/2609.22000v1#S3.SS1)明确从 GitHub 的高质量开源 GUI 应用构造五平台训练任务，覆盖领域、语言、框架和复杂度差异，并与评测集去重。作者具体训练应用清单、搜索流程及每应用采样次数未披露。因此本次使用这些原则构造自己的池；参考[§4.3和附录C.3](https://arxiv.org/html/2609.22000v1#S4.SS3)的可运行、交互、固定版本等 benchmark 构建要求作为**我们的操作筛选标准**，不声称这是作者完整训练配方。

任务形式保持原文的混合循环：**操作运行中的参考 GUI → 推断行为 → 编写独立实现 → 构建和启动 → 操作自己的实现并核对功能与画面**。未来 skills 的素材来自这个循环中的动作、观察、失败和修正；仅点击参考应用的一段操作记录不等同于完成 RecreationWorld 复刻轨迹。

| 平台 | 主候选来源 | 与 bench 对应的行为能力／候选技能素材 |
|---|---|---|
| Ubuntu | [Xournal++](https://github.com/xournalpp/xournalpp)、[Flameshot](https://github.com/flameshot-org/flameshot)、[Heimer](https://github.com/juzzlin/Heimer) | 画布、工具／选区状态、图结构、撤销与导出；区分屏幕坐标和对象坐标，验证保存后重开的语义状态 |
| Windows | [ScreenToGif](https://github.com/NickeManarin/ScreenToGif)、[Caesium](https://github.com/Lymphatus/caesium-image-compressor)、[WinMerge](https://github.com/WinMerge/winmerge) | 时间线／文件列表、参数驱动输出、比较／合并、撤销；确认最终导出或保存的文件内容，而非只检查静态界面 |
| macOS | [Hex Fiend](https://github.com/HexFiend/HexFiend)、[Gifski](https://github.com/sindresorhus/Gifski)、[MacPass](https://github.com/MacPass/MacPass) | 输入变化、查找／替换、拖放导入、分组编辑、持久化；以合成文件／数据库做输入—状态—输出的闭环 |
| Android | [Fossify Gallery](https://github.com/FossifyOrg/Gallery)、[ActivityDiary](https://github.com/ramack/ActivityDiary)、[Family Gem](https://github.com/michelesalvador/FamilyGem) | 媒体／记录／关系树、多页导航、表单、返回栈、权限与重启；验证编辑状态跨页面和重新启动后是否保持 |
| Web | [Squoosh](https://github.com/GoogleChromeLabs/squoosh)、[miniPaint](https://github.com/viliusle/miniPaint)、[StackEdit](https://github.com/benweet/stackedit)、[Vite文档站](https://github.com/vitejs/vite) | 浏览器文件输入／输出、图层与撤销、多文档和预览、本地持久化、响应式交互；文档站另覆盖多路由、目录和主题导航 |

上表的对应是**能力层面的研究假设**，逐应用的具体 bench task ID 和行为流程见[桌面设计](desktop/selected_candidates.json)、[macOS/Android设计](mac_android/selected_candidates.json)、[Web设计](web/selected_candidates.json)。Web 的三个本地工具比官方多为内容／文档站的50题更重状态，故额外选固定Vite v8.0.7的`docs/`文档站，对应webpack／Rust／Keycloak等公开内容站的导航和响应式行为；这仍不能证明同一任务分布或迁移收益。Vite根源码是构建依据，训练参考范围是文档应用，不是让agent实现整个Vite编译器。每条流程都有拟观测结果；精确默认值、菜单、行为与断言必须先在固定参考版本上实际核验。

## 来源隔离与筛除

取得官方固定 dataset revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95` 的250条**公开来源身份**，只保存 task ID、platform、difficulty、repo、commit，没有访问隐藏测试／gold。四个原生平台200条对应198个不同 canonical repo；主候选与这些 repo 没有精确重合。[来源目录](bench_source_catalog.json)和[完整性／精确去重核验](source_integrity_verification.json)可复核。

对50个 Web 任务另核验已公开参考首页标题、canonical 与显式 GitHub 链接，保存身份摘要及内容 hash，没有保存 HTML 全文或获取测试资产：[Web身份审计](web_bench_identity_audit.json)。未发现主候选的显式来源命中；但是匿名 `.example` 原站身份及完整 fork／近重复图仍无法全部证明。**精确 repo 去重通过不等于所有来源家族隔离已最终验收**，正式训练池冻结前仍需补核验。

- NotepadNext 虽 repo 不同，但明确复刻 Notepad++，与 bench 的 Notepad++ 产品家族有风险，隔离并改选 WinMerge。
- Czkawka 固定版本 GTK 前端停止继续发行，移作候补并改选 Heimer；不把整个项目的活跃开发冒充 GTK 继续维护。
- CotEditor 的图片许可和当前版本宿主要求不合适，未入主池。
- Vue docs 的文档许可证明确排除全部图片，图片来源未齐，未入主池；改选根MIT许可的Vite文档来源，第三方依赖／个别资产仍需准入审查。
- Family Gem v1.3 的 Android SDK37.2 与当前准备版本不匹配，保留其来源／归档，主池固定 v1.2、compile/target SDK35。
- Taskflow 没有核到完整许可证文件且质量证据不足；Laverna 旧依赖、CyberChef 全功能规模过大，均未入主池。

已下载的筛除来源和旧版本分别保留，未删除或覆盖。[首批9个来源](preliminary_9_source_manifest.json)、[FamilyGem改版前15个来源](preliminary_15_source_manifest_familygem13.json)保存筛选历史。MacPass 与 KeePass 客户端共享格式／部分库，与 KeeWeb 等产品的家族关系仍需细审；不能只因 repo 名不同断言完全独立。

## 适合沉淀 skills 的可验证预期

候选优先包含两种以上可变状态和有实际输出的多步操作。我们预期有机会沉淀以下经验，但**没有预先写成技能塞入库，也不保证一应用产多个技能**：

1. 最小改动探测：改变一个输入、颜色、尺寸或选择状态，核对输出，避免照着初始截图猜行为。
2. 状态建模：分开当前工具、选中对象、文档内容、视口／导航和持久化状态，避免联动错误。
3. 产物检查：保存／导出后重开、刷新或重新启动，检查文本、尺寸、格式、关系和记录是否真实保持。
4. 画面与功能一起检查：完成最后一次代码修改后再构建、操作和截图，记录仍存在的缺陷。
5. 错误恢复：保留构建、权限、异步加载或状态错误及修正证据，区分环境故障和实现未达标。

未来采集完整 GUI／代码／工具回执轨迹，并交给官方 AutoSkill trajectory 入口；技能是否生成、是否合并或为空由真实抽取维护结果决定。论文使用 verifier 对高分轨迹做 rejection sampling；我们的技能演化设计还应独立保留失败和修正轨迹，不能把负结果改记成功，也不能用测试集成绩挑素材。当前只有**来源和素材预期**，没有高质量轨迹、成功率或技能增益的实证。

## 尚未就绪及下一步

源码归档不包含自动下载的全部子模块、包依赖或原生运行环境。WinMerge声明13个子模块、MacPass声明1个，尚未取得；Hex Fiend的`.gitmodules`文件为空，不能把仅文件存在误报为有子模块。Qt／GTK、.NET、Rust、Node、Android SDK、字体、媒体编码器和旧 Gradle 版本等仍需按各候选固定。StackEdit 的老依赖、Gallery SDK36、ActivityDiary 旧 target 的 Android35 权限行为必须实测。Vite文档构建需固定Node／pnpm／VitePress；外部Algolia或在线Playground不能作为离线参考核心。详情均列在逐应用记录。

下一步应先把候选转为独立 reference package：安装受控依赖、构建／启动、离线核心功能、原生访问树、固定合成 fixture、重复执行公开行为自验、版本和许可完整性；再按运行中的参考结果制作并冻结自己的训练验证器。源代码用于参考环境准备，原生复刻 actor 只获得官方允许的运行界面；Web 可观察服务出的 HTML／样式／脚本／资源，不能取得受保护验证器或直接把目标参考当运行时交付物。

全部通过后才能生成正式轨迹；沿用户约束，每题最多三轮含首次，失败保留，不继续第4轮。外部应用池与原250 benchmark 如何组成下一阶段演化／测试，需独立协议；本轮没有重划此前5题／245题方案，也没有恢复旧实验或自动启动评测。
