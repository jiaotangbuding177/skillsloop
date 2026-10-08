# macOS / Android 公开 GUI 训练应用候选证据

日期：2026-10-04。范围：公开源码与文档获取和筛选；未运行参考应用、模型、任务、评分、学习，也未改动既有实验或服务。

## 本轮交付

主池为 3 个 macOS 应用、3 个 Android 应用。六项均是**源码获取候选**，运行就绪数量为 0。根线程已下载固定源码归档；实际字节量以根线程取得的 acquisition manifest 为准。本子任务保存固定 README、许可证、构建声明及其 SHA-256，不下载大型源码包。

| 平台 | 应用 / 固定版本 | commit | 主许可证 | 选择理由与待验收问题 |
|---|---|---|---|---|
| macOS | [Hex Fiend v2.18.1](https://github.com/HexFiend/HexFiend/releases/tag/v2.18.1) | e2f91f1b7aff9a473c3b5aaf7c2e0cf3cb9e027e | BSD-2-Clause | 本地字节编辑、搜索、比较；自定义字节网格 AX 和完整构建信息待验收。 |
| macOS | [Gifski v2.23.0](https://github.com/sindresorhus/Gifski/releases/tag/v2.23.0) | 6fd12595617d1854c59f4ddca8e068fefa66c397 | GUI MIT；编码器 AGPL-3.0-or-later | 本地媒体设置、预览、导出；选 macOS 13.3 目标旧版，当前 v3 的 macOS 26 要求不兼容参考宿主。 |
| macOS | [MacPass 0.8.2](https://github.com/MacPass/MacPass/releases/tag/0.8.2) | 3256bc93ea94eb20b618c155e6a1b08e6fabe663 | GPL-3.0-or-later | 原生嵌套记录编辑、搜索、持久化；与 KeeWeb 的文件协议/依赖家族风险另行审查。 |
| Android | [Fossify Gallery 1.13.1](https://github.com/FossifyOrg/Gallery/releases/tag/1.13.1) | b28299dc33821eee8d108a9880ce87876cf31443 | 仓库 GPL-3.0；头文件授权范围待最终审查 | 本地媒体、相册、编辑；build SDK 36 / min 26，API 35 权限与安装待验收。 |
| Android | [Activity Diary v1.4.2](https://github.com/ramack/ActivityDiary) | 22593ca02b897132c5649f1219aa93448dc18b06 | GPL-3.0-or-later | 本地活动状态与历史记录；SDK 30 的旧构建链和 API 35 运行兼容需验证。 |
| Android | [Family Gem v1.2](https://github.com/michelesalvador/FamilyGem/tree/3aeb97f00cfe6b8f8efbb5c0164529f0a0e16c62) | 3aeb97f00cfe6b8f8efbb5c0164529f0a0e16c62 | GPL-3.0-or-later | 本地关系图、人物表单、GEDCOM 导入导出；SDK 35 适配声明清晰，vendored JAR 来源待审。 |

所有固定 SHA 来自公开 git tag 的 peeled commit 与对应 raw 文档。本轮 GitHub 匿名 API 返回 403，未取得 fork / archived 等 API 标志，不能据此声称不存在 fork。失败元数据保留于 public_metadata_manifest.json。

## 与 benchmark 对应的边界

source_identity_audit.json 将候选 canonical repo、已知旧地址和已知 upstream 与官方公共 source 元数据的 **全部 250 行**比较：native 200 行有 repo/commit，web 50 行没有公开 repo；六项及已知 aliases/upstream 的 exact identity matches 为 0。selected_candidates.json 中的 17 个能力对应关系都引用了存在的任务 ID。

这是公开**身份不重合**检查。它没有证明完整代码、依赖、产品家族或训练测试内容绝对隔离，也没有读取私有评测器来设计任务。后续须保留 canonical upstream 家族登记，并审查固定源码及依赖相似性。具体对应如下：

- Hex Fiend 与 macOS Erbele / Letos 的选择、编辑、菜单、状态检查，以及 Ubuntu Okteta 的字节编辑能力有关。
- Gifski 与 macOS LosslessCut / Image Shrinker / MP3Gain 的输入—参数—预览—输出链路有关。
- MacPass 与 macOS GPGFrontend 的本地结构化安全记录有关，另与 Ubuntu KeeWeb 共享 KeePass 文件格式域。
- Gallery 与 Android Doodle、Images-to-PDF、Amaze 的画布/媒体选择/文件输出/权限流程有关。
- Activity Diary 与 Android SimpleTimeTracker、TimePlanner、Goodtime 的当前活动和历史状态机有关。
- Family Gem 与 Android TimePlanner、MyBrain 的多屏表单、关系记录和本地持久化有关；**没有声称 genealogy 与 benchmark 的任务域相同**。

这些是源码侧与功能文档支持的**能力迁移假设**，不是已证实的 task distribution 匹配，更不是 skills 增益实验结论。

### MacPass / KeeWeb 家族说明

[MacPass 官方 README](https://raw.githubusercontent.com/MacPass/MacPass/3256bc93ea94eb20b618c155e6a1b08e6fabe663/README.md) 将它描述为原生 macOS KeePass 客户端，并把 KeeWeb 列为替代客户端；MacPass 自身依赖 KeePassKit。现有文档没有支持“MacPass 是 KeeWeb 产品 fork”的说法。但 KDBX 格式、密码学算法、库和产品谱系可能共享，不能凭不同 repository 排除污染。

因此它可作为待审候选，**严格应用家族隔离资格尚未成立**。如后续比较固定依赖/源码发现直接同源，应从严格主池移出，不能把换界面、平台或版本当作新家族。只能在独立验证后将相同协议的跨客户端迁移作为研究设置，明确披露。

## 观察 → 原创实现 → 自查的轨迹预期

RecreationWorld 对应的学习素材不是单纯完成参考软件上的用户任务。拟议轨迹包含：模型查看固定参考应用的公开 GUI 状态；多步观察输入与状态变化；写出独立的新应用实现；运行并自查所实现的行为和截图；任务内最多三轮总尝试沿用用户约束。参考源码只用于设施构建和泄漏审查，不能作为 agent 输入或实现提示。此处只定义候选流程，未授权本子任务执行。

每项 2 个具体候选流程与预期校验已记录在 selected_candidates.json：

1. Hex Fiend：受控字节编辑/保存重开；搜索/比较/无结果状态。校验实际文件 bytes、offset 和 changed regions。
2. Gifski：本地短视频导入与尺寸/FPS/质量设置；loop/bounce/speed/新输入状态。校验可解码 GIF、尺寸、帧数和动画 metadata；不混入新版 crop 功能。
3. MacPass：虚构数据库组与条目 CRUD/搜索；移动、锁定和重开。校验虚构结构及持久化，不用真实密码和插件。
4. Gallery：本地合成图片旋转/缩放/保存；相册多选移动与已验收的回收恢复。校验文件尺寸、方向、字节保留和列表成员。
5. Activity Diary：活动创建与 start/change/stop/备注；历史编辑及已验收的过滤。校验逻辑状态与事件顺序，不用精确墙钟时间评分。
6. Family Gem：三人虚构家庭与父子关系；微型 GEDCOM 导入、备注/事件修改及导出。校验链接和记录 round trip，不启用在线分享、地点推荐或付费合并。

训练任务的数值、步骤和验证器必须在参考 GUI 实际验收后冻结。拟议自查不等于官方评测已通过；没有把合成训练任务的自查结果当作 benchmark score。

## 离线与构建证据

- Hex Fiend：官方 [README](https://github.com/HexFiend/HexFiend) 描述本地文件编辑；.gitmodules 为空。猜测的项目文件路径 404 已保留，不据此断言项目不存在，须在根线程源码归档定位。字节面板 AX 待实机确认。
- Gifski：固定 [README](https://raw.githubusercontent.com/sindresorhus/Gifski/6fd12595617d1854c59f4ddca8e068fefa66c397/readme.md) 与 project deployment target 支持使用 macOS 13.3+；构建需要 Xcode、Rust、SwiftLint 与 Swift 包。编码器 [官方许可声明](https://github.com/ImageOptim/gifski/blob/main/README.md) 与 GUI 许可不同。所选旧版不是当前新版功能全集。
- MacPass：固定 README 的 recursive checkout / Carthage / Xcode 链路会产生外部依赖需求。0.8.2 [官方 release](https://github.com/MacPass/MacPass/releases/tag/0.8.2) 处理旧更新域名，获取只用 GitHub 来源。构建后使用完全虚构的本地 KDBX，不需要账号。
- Gallery：固定 [Gradle](https://raw.githubusercontent.com/FossifyOrg/Gallery/b28299dc33821eee8d108a9880ce87876cf31443/app/build.gradle.kts) 与版本目录给出 build SDK 36、min 26，选择 foss flavor。主 manifest 删除 ACCESS_NETWORK_STATE 不能证明 merged APK 无网络权限；离线核心与 scoped storage 须实际验收。
- Activity Diary：[隐私政策](https://raw.githubusercontent.com/ramack/ActivityDiary/22593ca02b897132c5649f1219aa93448dc18b06/Privacy-Policy.md) 支持本地数据核心；地图、定位和自愿 crash 邮件不进入训练流程。发布配置的账号文件与 debug 构建是否解耦须验证，不能预设 debug 构建失败或必须申请账号。
- Family Gem：[v1.2 构建声明](https://raw.githubusercontent.com/michelesalvador/FamilyGem/3aeb97f00cfe6b8f8efbb5c0164529f0a0e16c62/app/build.gradle) 的 compile/target 35 对齐参考 Android API 35。在线分享、GeoNames 和 premium merge 的限制不等于离线树编辑需要账号；只使用后者。vendored JAR 的许可与来源仍是准入项。

## 保留的排除与未知

- CotEditor：当前 macOS 26/toolchain 声明与参考宿主不匹配，图片资产为 CC-BY-NC-ND-4.0，尽管代码为 Apache；没有将其算作完全开源代码/资产主池。[官方 README](https://github.com/CotEditor/CotEditor)
- Family Gem v1.3：compile/target SDK 37.2；选择 v1.2 SDK 35，并保留旧证据/manifest，不覆盖。
- MyExpenses：未进入本轮六项主池；发布、付费和云服务依赖面较大。可作为后续离线免费核心备选，尚无固定源码准入结论。[官方项目](https://github.com/mtotschnig/MyExpenses)
- 无 macOS 实机/Android 安装、无 GUI AX/UiAutomator 导出、无重复性 reset 或独立实现运行证据。构建可行性、产品家族审查、全部资源许可、任务难度以及技能抽取率皆未证实。

## 本地证据路径

- selected_candidates.json：统一主池 schema、固定 SHA、流程、参考 task IDs、假设与风险。
- source_identity_audit.json / source_identity_audit.py：250 行身份比较及可复查脚本，无模型或网络调用。
- fixed_docs_manifest.json：初始固定公开文档的 URL / bytes / SHA-256；含 Family Gem v1.3 的旧证据。
- compatibility_docs_manifest.json：Family Gem v1.1/v1.2、Gallery SDK 版本及未取得的 Hex Fiend 项目路径。
- public_metadata_manifest.json：GitHub 匿名 API 403 的负证据。
- 各 repo 命名目录：固定 README、LICENSE、必要 Gradle / Xcode / manifest 声明。凭据和私有 evaluator 未纳入。

