# 第279轮：取得五平台独立 GUI 应用来源池

日期：2026-10-04。前序：[277训练应用来源披露核验](277_2026-10-04_rw_training_application_selection_disclosure.md)；旧设计：[272五种子／245测试方案](272_2026-10-04_rw_five_seed_evolution_design.md)。

## 用户已确认要求与本轮边界

- 用户要求“按照他的原文的思路”获取一批高质量开源 GUI 应用，要与 bench 对应，并有适合 skills 沉淀的轨迹预期。
- 用户此前明确停止旧corravale任务，未来同题迭代最多三轮含首次、失败如实保留。本轮只获取公开来源并研究设计，未恢复旧STOP、未发起模型／应用／轨迹／学习／评分运行。
- 这项来源获取授权没有自动重划此前五平台各1题演化、其余245题一次测试的协议；下一阶段用独立外部应用池替代种子和评测250仍需另定明确协议，不自动扩大运行次数。

## 证据支持的观察与已完成产物

1. [论文§3.1](https://arxiv.org/html/2609.22000v1#S3.SS1)明确GitHub高质量开源GUI、五平台多样和与评测去重；未公开具体训练应用名单。本次自行构造来源池，不能称作者官方训练任务／35,000轨迹。Benchmark构建细则只作为本次操作筛选参照，不推定作者训练配方。
2. 实际取得**16个固定commit来源**，Ubuntu／Windows／macOS／Android各3，Web4：Xournal++／Flameshot／Heimer；ScreenToGif／Caesium／WinMerge；HexFiend／Gifski／MacPass；Fossify Gallery／ActivityDiary／FamilyGem；Squoosh／miniPaint／StackEdit／Vite docs。主池归档153,239,413 bytes＝146.14MiB，解包17,064普通文件，归档和文件清单逐项SHA保留，不仅给链接。
3. 来源证据整合到[application_pool.json](../reports/279_gui_acquisition/application_pool.json)：固定SHA／许可／构建依据／离线核心／原生访问接口未知／41个观察→独立实现→自查流程和技能假设。能力映射引用37个公开bench任务ID，已与官方250目录核验，无不存在ID；这只验证关联任务存在，不证明迁移效果或私有测试覆盖。
4. 官方HF固定revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95` 的250条公开source身份已取得，去掉task/eval paths；200原生行对应198不同repo。主池canonical repo精确重合0。50Web公开首页身份全部读到，保存标题／canonical／显式GitHub链接摘要和hash，不保存全文，不取得隐藏测试/gold；仍有匿名原站身份／完整fork图未知。
5. 已筛除并保留：NotepadNext与bench Notepad++产品家族风险→WinMerge；Czkawka GTK停止继续发行→Heimer；CotEditor图片许可／新宿主不匹配；Vue docs图片许可全部排除→Vite MIT文档站；Taskflow完整许可证据不足、Laverna旧依赖、CyberChef全功能规模大未入主池。FamilyGem v1.3 SDK37.2保留来源/源码，主池另存v1.2 SDK35，旧版本未覆盖。
6. 最终源码核验通过：16个归档和inventory hash、17,064个解包文件逐项hash均通过，file failures＝0；见[核验文件](../reports/279_gui_acquisition/source_integrity_verification.json)。这是完整性核验，不是运行验收。运行accepted＝0、轨迹＝0、已验证skills＝0。完整fork/匿名Web来源与MacPass/KeePass协议／依赖家族关系未消除，不写绝对无污染。

## 研究假设与建议

预期素材包括最小输入变化探测、全局工具／对象／文档／视口状态区分、撤销与重做、保存重开／导出回读、导航和权限恢复、最后修改后运行核验。它们来自真实未来GUI探索＋代码复刻＋结果自查循环，不能只录点击参考应用就叫完整RecreationWorld轨迹，也不能由人工把拟议经验预写入skills库。

Web三工具偏重本地交互，与官方多为内容／文档站的50题不同；额外取得Vite docs以覆盖多路由／导航／主题／响应式内容站，训练参考是docs应用而非整个Vite编译器。对应是能力类别假设，没证明同分布或增益。抽取可能产零技能或合并重复技能，不预设每应用多个技能。

论文用verifier筛高分轨迹；我们的skills研究需独立保留失败和修正轨迹，区分应用来源质量与实际轨迹质量，不根据测试成绩选素材，不伪造成功或技能数量。未来继续用户三轮上限。

## 未知项与下一步

- 源码包没有补齐原生GUI运行环境和全部第三方依赖。WinMerge13子模块／MacPass1子模块未取得；HexFiend `.gitmodules`为空，不能误报其有子模块。Qt/GTK/Poppler/字体/.NET/Rust/Node/AndroidSDK与旧Gradle还需受控准备。
- Gallery SDK36、ActivityDiary旧SDK30在官方Android35准备的权限／构建行为未实测；Gifski编码库AGPL与GUI MIT、图片／字库／依赖许可均按原来源分开保留。
- 先原生启动、离线核心、访问树、合成fixture和可重复公开行为验收，再制作并冻结独立训练验证器和reference package；当前没有正式可采轨迹的应用准入。
- 来源用于环境准备；原生actor只操作官方允许的运行参考，Web允许观察服务出的HTML/样式/脚本/资源，但不能读取受保护验证器或提交依赖参考的重放程序。
- 不运行旧RW／不变更其他聊天Co-Gym实验、服务或模型凭据；本轮未读取受控凭据。

汇总入口：[279来源池报告](../reports/279_gui_acquisition/README.md)。代码／版本／字节与hash：[实际取得清单](../reports/279_gui_acquisition/source_acquisition_manifest.json)；细则：[桌面](../reports/279_gui_acquisition/desktop/desktop_candidates_report.md)、[macOS/Android](../reports/279_gui_acquisition/mac_android/candidate_report.md)、[Web](../reports/279_gui_acquisition/web/candidates.md)。
