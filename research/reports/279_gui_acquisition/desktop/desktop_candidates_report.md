# Ubuntu / Windows 独立 GUI 训练候选获取与证据

日期：2026-10-04。公开来源获取与科研设计；没有执行应用、模型、任务、评分或 AutoSkill 学习。旧 RecreationWorld STOP、同题最多三轮（含首次）、其他聊天服务保持。根线程已取得以下六个主候选的固定源码归档；实际归档大小、展开文件 SHA 由根线程 acquisition manifest 统一记录。本子报告不把源码下载称为环境验收。

## 与 RecreationBench 的关系

本批不是“使用这些软件完成办公操作”的另一个 benchmark。计划仍采用 RecreationWorld 的同类 **公开 GUI 观察 → 独立复刻实现 → 交互与输出工件自查** 链路。应用操作序列是给模型观察状态转换的探针，预期提取的是如何判断和复现 GUI 行为的技能；agent 不直接读参考程序源码照搬。

根线程公开 `bench_source_catalog.json` 固定 Qwen/RecreationBench revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95`。200 条 Ubuntu/Windows/macOS/Android source repo 全局归一（大小写、末尾 `/` / `.git`）后，六候选无精确 repo 匹配。另 50 Web 行没有 source repo，故“精确 repo 无匹配”不升级为“代码、视觉、所有 fork 家族均完全去重”。本轮 GitHub API 403 rate limit 错误已独立保留；公开 git refs / 固定 raw 文档成功，完整 fork graph 未由 API 验明。

详细结果：`selected_candidates.json`（主候选＋候补＋每应用 3 组行为探针、skills 假设、负例）、`cross_platform_source_audit.json`、`desktop_public_fixed_evidence.json`。每仓库独立 evidence 目录保存固定 SHA 的 README / LICENSE / 构建文件及公共 ref 原文。

## 六个主候选

| 平台 | 应用／固定版本 | 固定 commit | 许可证据 | 与 bench 的具体能力对应 |
|---|---|---|---|---|
| Ubuntu | Xournal++ v1.3.8 | `938bdb8de4d32f38f48dd7f6544886722157a848` | GPLv2 LICENSE；组件／图片分别保留 notice | Pencil2D 的画布、工具属性、撤销、保存；Marker 文档编辑；PhotoFlare 图像与导出 |
| Ubuntu | Flameshot v14.0.0 | `e408812d77ff1835957f85796c4cf737466bd69d` | 主代码 GPLv3+；logo FAL1.3；按钮 Apache2；少量 GPL2/LGPL | Ksnip / HotShots 的选区、标注、保存；Screenshot Stager 的图像状态 |
| Ubuntu | Heimer 4.5.0 | `d3153c52f27c23d4ec4143205e9b84c7321e0a7e` | 代码 GPLv3，图像 CC BY-SA3（未另注明者） | Dia / Camunda Modeler / JetUML 的节点、连接、标签、布局、历史与持久化 |
| Windows | ScreenToGif 2.43.2 | `a4d0a67c2131cd048ceec86cd40afc2f1a06f2fd` | Ms-PL `LICENSE.txt` | Screenshot Stager / HotShots 的图像编辑；LosslessCut 的序列、时间线、异步输出能力 |
| Windows | Caesium Image Compressor v2.8.5 | `bc4f6bbb4bbe128bb09345454592affa5d6eb79b` | GPLv3 LICENSE；Rust／Qt／WinSparkle 另审 | Image Viewer、EXR Converter、Automatic Thresholding 的队列、参数、预览、输出一致性 |
| Windows | WinMerge v2.16.58.2 | `5f689ef907ec427192bb17d120f0dbb24f1e213b` | GPLv2 `LICENSE.md`；13 外部 gitlink 分别审计 | FileManager 的目录与选区；Logbert 的多窗格文本、筛选；ParquetViewer 的列表 model/view（仅有限相关） |

这些映射是能力与环境相关性判断，不是每个功能都等同、也不是已证实的跨题迁移。优先覆盖图编辑、截图标注、媒体序列、批量处理、文本／文件状态等多种 GUI 模式，避免为了“小”只选计时器或计算器，导致轨迹单一。

## 固定来源、构建与离线风险

- **Xournal++**：固定 commit 日期 2026-09-25；CMake ≥3.18 / C++20、GTK3、Poppler、libxml/libzip/librsvg，并有 audio/qpdf/Lua/GtkSourceView 可选组合；非 Release 默认 cpptrace FetchContent。先预置依赖、字体／主题／固定 PDF/PNG fixture，再核离线启动。原 README 明示笔迹组件来自 Xournal，不当完全原创代码。[固定构建文件](https://github.com/xournalpp/xournalpp/blob/938bdb8de4d32f38f48dd7f6544886722157a848/CMakeLists.txt)
- **Flameshot**：固定 commit 日期 2026-06-10；Qt6 / C++20 / CMake ≥3.22，Qt-Color-Widgets 固定 SHA 和 KDSingleApplication tag 外部预取，非 Ubuntu 平台 QHotkey 是 master，故只分配 Ubuntu；自定义 prefix 文档要求 CMake ≥3.29。截图仅用于隔离虚拟桌面 fixture，优先 X11，Wayland portal 权限另验。默认 Imgur OFF，不调用上传。原文声明来自 Lightscreen/KSnapshot 的片段已保留。[固定 README](https://github.com/flameshot-org/flameshot/blob/e408812d77ff1835957f85796c4cf737466bd69d/README.md)
- **Heimer**：固定 release commit 日期 2025-03-16，不能称 2026 新发行；Qt5 ≥5.9.5 / CMake / C++17，Qt6 ≥6.2.4 显式开启。XML ALZ、undo/redo、PNG/SVG 提供比较清晰的状态验证。画布不是默认有语义访问树的标准按钮。[固定 README](https://github.com/juzzlin/Heimer/blob/d3153c52f27c23d4ec4143205e9b84c7321e0a7e/README.md)
- **ScreenToGif**：固定 commit 日期 2026-07-26；固定项目 target `net9.0-windows7.0`，WPF 和 WinForms，README 要求 .NET9 Desktop Runtime（或更高）。需预先固定 .NET9 SDK/runtime、NuGet、native 依赖；首批只导入公开本地帧并编辑／导出 GIF/PNG，不要求 webcam、实际屏幕或 FFmpeg 视频编码。[固定项目文件](https://github.com/NickeManarin/ScreenToGif/blob/a4d0a67c2131cd048ceec86cd40afc2f1a06f2fd/ScreenToGif/ScreenToGif.csproj)
- **Caesium**：固定 release commit 日期 2025-05-07；Windows10 1809+64bit、Qt6（binary Qt6.8）、Rust cargo、libcaesium 外部 tag 与 WinSparkle0.7 zip。源码 zip 缺依赖时不能说离线可编译；核心队列转换无需账号，但 updater 应独立禁止／断网验证。PNG/JPG/WebP 参数与真实解码结果验，避免 encoder 版本差异造成字节比较假失败。[固定 README](https://github.com/Lymphatus/caesium-image-compressor/blob/bc4f6bbb4bbe128bb09345454592affa5d6eb79b/README.md)
- **WinMerge**：固定 commit 日期 2026-08-27；MSVC v143 / VS2022+、MFC/ATL、Windows10 SDK；发行工具含 7Zip/Inno/Python/Pandoc/MSYS2。13 个外部 gitlink 未在 codeload 中包含，`DownloadDeps.cmd` 还会网络取依赖。因此主源码已取得，但原始构建依赖完整性为 pending。可之后验固定官方 portable 作 reference；只比较 fixture copies，不安装 shell extension。[固定构建文档](https://github.com/WinMerge/winmerge/blob/5f689ef907ec427192bb17d120f0dbb24f1e213b/README.md)

以上 docs 给可核验的工具版本和来源，不声称已经运行或构建通过。GUI 参考实现与复刻实现的原生构建语言可不同，harness / 工具协议 / 状态观察与验证资格要对齐；不能只因为同为 GUI 就称与原 bench 设置完全一样。

## 轨迹为什么有 skills 素材预期

预期可迁移经验包括：

1. **由干预判断状态作用域**：改变一处参数、多个对象／多个队列项，区分当前工具默认值、单对象属性与批量规则。
2. **把 model 状态与 view 状态分离**：节点连边、帧排序／选区、坐标缩放、文本差异范围，观察动作后才建模，避免截图好看但交互无效。
3. **按用户事务实现 undo/redo 和持久化**：一动作一历史事务、保存重开核语义，而非只检查成功通知。
4. **用实际工件验异步完成**：队列终态与输出文件可解码／尺寸／帧时长／文字／hash交叉确认；错误项隔离，取消不冒充成功。
5. **控制离线复现设施差异**：固定字体/DPI/locale、工具/依赖版本、fixture、输入与输出目录，不让模型把设施失败误学成产品使用规律。

这些只是可采集的流程与候选 skills 假设。未保证每应用能沉淀多个技能，未把 README 特性变成经验技能，未先拟造成功轨迹。每应用未来最多三轮含首次；真实失败、空候选、AutoSkill 合并都保留，不为凑技能数量刷分。公开测试的私有评分断言/gold/参考源码不进入技能素材。

## 被保留但不入主池的候补

- **NotepadNext v0.15**：独立 repo 不足以去重。其 README 直接声明 Notepad++ reimplementation，与 Windows bench `amirreza-tabeshfard-at-netcore-notepadplusplus` 存在同产品家族近似风险，且自报若干 half-working implementations；已取得源码保留，主池换 WinMerge。[固定来源](https://github.com/dail8859/NotepadNext/blob/fc4c807cf2b755b37d40de27cf29a5268c7c2fc5/README.md)
- **Czkawka 12.0.2**：README 明确旧 GTK4 frontend 最后 release、不再新 binary，维护转向 Krokiet(Slint)；core 活跃不等于 GTK 活跃。冻结 GTK 可作探索候补，主池换 Heimer，旧归档不删除。[固定说明](https://github.com/qarmin/czkawka/blob/f9be31f586f9473a91b9fe3785b7ba76ddaecf44/README.md)
- **Foliate 3.3.0**：离线 EPUB 类相关但 GJS/GTK4/libadwaita/WebKit 与 `foliate-js` gitlink 增加环境工作；保留文档候补，不作为首批主池。[固定来源](https://github.com/johnfactotum/foliate/tree/6846cf62ef3ff4f0162f1b288f44d6dcce5f1a19)

下一步是六应用 runtime / 原生访问树准入验收及公共 fixture／本地自建验证器设计，失败先留证；本轮仅获取，未越权启动。完整原论文训练应用名录仍未知，本批称“依原文原则自行获得的训练候选”，不声称复现原35,000数据池。
