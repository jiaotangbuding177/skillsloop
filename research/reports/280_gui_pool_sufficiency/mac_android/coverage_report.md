# 280：macOS / Android 演化应用池的首轮充足性审查

本轮只做公开来源调研、固定文档获取和分类，不执行 GUI、模型、学习、评分或旧实验。279 的来源、负结果和 MacPass 候选记录均保留。全部“可迁移技能”均是待验证假设。

## 判断与停止条件

279 的三个 Mac 候选与三个 Android 候选不能直接推出覆盖两平台 100 个评测应用。其主要素材集中在编辑、媒体参数、活动记录和关系记录；游戏规则、数值输入输出、原生任务清单、系统权限/包信息几类材料不足。本轮仅增加四个独立来源：To-Day、OpenCalc、Shattered Pixel Dungeon、Package Manager；不再为每个罕见后端追补应用。

四项补充已经满足本子任务的最小增补目标，可以停止继续搜集，进入后续环境与任务准入。联合根线程的其他平台补充后，是否构成首轮 250 题演化候选池，应使用根线程完整分类表判断。本子池单独不声称 250 题完整能力覆盖，也不承诺每题提分。首轮“够用”指具有可设计公开观察→独立复刻→自查任务的代表性共同行为素材；不指每个专用算法都有同类训练应用。

计时、音频传输和科学绘图不能被本轮新增强行替代。To-Day 是任务清单，不能算倒计时器。ActivityDiary 的时段/历史不是实时倒计时、pause/resume、通知验证。Shattered 是游戏规则/画布状态，不算音频 seek/pause/resume 或科学绘图。原生输入法、传感器/GPS、密码/OTP/OpenPGP、系统服务、蓝牙和特定金融/3D/编译后端仍保留具体 unknown。其他平台若有音频/计时/绘图应用，其跨平台迁移也需要实验验证。

## 完整 100 个公开应用身份审查

`bench_100_application_audit.json` 与 CSV 各有 100 行，严格对应官方 revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95` 的 macOS 50、Android 50 个公开 `instance_id`，无缺项、重复或额外任务。字段包括来源 repo/commit、一个主类别、公开功能依据、共同行为候选、具体未知能力和证据层级。它不是隐藏测试内容审查；没有读取测试/evaluator，也没有将 279 的 37 个示例映射当作覆盖率。

|公开用途主类别|应用数|本子池的材料及限制|
|---|---:|---|
|文本/代码/知识|14|Hex Fiend 的本地编辑状态、StackEdit 的独立文本观察；编译/引用/图谱后端未知|
|结构记录/任务|13|To-Day、ActivityDiary、FamilyGem 的 CRUD/list/tree/state；SQL/业务后端未知|
|计时|10|活动时段/记录仅部分共有；倒计时、墙钟与通知未知|
|游戏/规则|10|Shattered 的动作观察与状态探查；Go/2048/数独/扫雷/词典等具体规则未知|
|数值/变换|6|OpenCalc 的输入/结果契约；代码转换、hash、图形与单位转换未知|
|媒体产物|14|Gifski、Gallery、miniPaint 的参数/预览/输出；录音/3D/PDF等后端未知|
|媒体播放|3|Gallery 的本地选择/浏览；音频/视频传输及后台生命周期未验证|
|文件/搜索/归档|7|打开/保存/选择状态只是部分共有；完整归档/索引/文件操作未知|
|系统/权限/设备|17|Package Manager 的只读包/权限详情和 To-Day 菜单状态；IME/壁纸/覆盖层等未知|
|传感器/导航|4|本子池无对应核心实现证明|
|安全|2|不借助 MacPass 候补宣称加密/OTP 核心覆盖|

这些数值仅是应用主类别的分布，不是覆盖率、预期增益或运行成功率。同一类别包含不同操作和后端。逐行 `shared_coverage_status` 只有 `partial_shared_ui_hypothesis` 或 `unknown_core_coverage`，没有实测覆盖声明。

98 个应用取得固定版本公开 README/补充文档。Markers 固定 README 缺失，用官方当前仓库的公开用途说明；PhotoFlare 固定 README 缺失，用当前官网 CE 的用途说明。两项明确标记“当前公开身份，非固定版本行为证明”。FitoTrack 官方来源是 Codeberg，初次 GitHub-only 文档尝试的无效 URL 已保留为采集负结果，补充采集使用正确的固定 Codeberg 路径；不能把该采集错误解释为应用或模型失败。

## 四个补充来源

|应用|固定来源|许可与工具链依据|补齐类别|
|---|---|---|---|
|To-Day|[release-2.0 / 7d98f4c](https://github.com/trozware/To-Day/tree/7d98f4ca02d630474cab88233b2d80b476ba6ca1)|MIT；SwiftUI/Xcode，部署目标 13.0/13.1，Sparkle 依赖待锁定；README 记录菜单 VoiceOver 限制|Mac 本地任务清单、排序、完成/隐藏状态|
|OpenCalc|[v3.2.1 / e80aef9](https://github.com/clementwzk/OpenCalc/tree/e80aef9452992ce46b3931edd562cae567bb7a6f)|GPLv3；compile/target 35、min 21；tag v3.2.1 的源配置仍为 versionName 3.2.0，保留标签差异|Android 数值输入、编辑、结果和历史|
|Shattered Pixel Dungeon|[v4.0.1 / e9defd0](https://github.com/00-Evan/shattered-pixel-dungeon/tree/e9defd0444c96d2fce3de5ec297c3398be8b7c55)|GPLv3；SDK 36/min21、AGP9.2、LibGDX；[官方桌面构建指南](https://github.com/00-Evan/shattered-pixel-dungeon/blob/e9defd0444c96d2fce3de5ec297c3398be8b7c55/docs/getting-started-desktop.md)明确支持桌面 JAR/macOS app|游戏菜单/画布/规则状态，Android及桌面潜在可用|
|Package Manager|[v7.0 / f13008b](https://github.com/SmartPack/PackageManager/tree/f13008b9204ce916fc9773b8ae52376db585457b)|GPLv3+；SDK33/min23、AGP7.3.1、F-Droid flavor；初选 v7.9 因 SDK37 否定并独立保留|只读 package/user/system list、权限与 manifest 详情|

每项在 `selected_additions.json` 给出两个具体的公开观察→独立复刻→自查任务草案、可验证状态、构建风险、公开来源和预期技能假设。八个流程只是草案，不是已执行轨迹。精确源码字节/文件数以根线程实际获取及 SHA 验收记录为准，本子线程只获取小规模公开文档。

Package Manager 固定任务不执行安装、卸载、启用/禁用、root、Shizuku 或 debloat，仅在受控 fixture app 上观察只读包和权限详情。其 Manifest 中存在系统操作权限不意味着本轮授权操作系统。Shattered 的随机关卡不能被假定可完全确定性重放，也没有授权为控 RNG 热改源码；首轮限定短的可观察菜单、库存和规则状态流程。

## 来源与家族隔离边界

`source_identity_audit.json` 将四个新增应用及已知 alias/upstream 与全部 200 个原生 source rows（198 个不同 repo）和 50 个公开 Web 身份记录比对，没有发现声明身份的精确重合。OpenCalc 的旧 `Darkempire78/OpenCalc` 地址纳入 alias；Shattered 明确派生自 Pixel Dungeon，两上游身份纳入比对。Package Manager Credits 明确承认部分代码来自 Kernel Adiutor、Split APK Installer 等，并保留完整依赖/代码来源的未知项。

零精确重合不能推出“绝对无污染”：公共库、借用代码、资产、隐含 fork 和 Web 页面漏报来源仍需下一阶段检查。MacPass 的 KeePass 协议/库及 benchmark KeeWeb 的应用家族风险没有消失，本轮将其作为 conditional reserve，不用来证明正式池足够；不删除或覆盖 279 历史。

## 对 279 的明确更正

`android/patzly-doodle-android` 的固定公开 README 描述的是动态壁纸、主题、动画和电量行为，不是绘图画布。真正公开用途为压力敏感触摸绘图的是 [dsandler/markers](https://github.com/dsandler/markers)。本轮分类已改正，279 原示例映射保持为历史记录并由根线程新增更正引用。Gallery 对 Doodle 只能作为图像呈现的部分迁移假设，不能当作触控绘画覆盖。

## 下一阶段准入

本子池运行就绪 0、生成轨迹 0、生成技能 0、测评分数 0。本轮不能回答任何迁移增益。下一阶段应冻结依赖与许可证/资产来源，验证 macOS AX/Android UiAutomator 或截图回路、真实离线启动、local fixture/reset、独立 recreation 任务和只用公开行为的自查器。原生 OS 未就绪属于准入工作，继续下载更多应用无法替代它。当前停止来源扩充不等于启动实验；旧 STOP 和最多三轮的迭代约束继续保持。
