# Ubuntu／Windows全100个公开来源的演化素材充分性审核

日期2026-10-04；只公开来源与构建文档研究，不读隐藏tests，不运行模型或参考应用，旧STOP/三轮限制保持。

旧279桌面六项偏图形、文档、图编辑和文件输出；整个16项池对数值表达式、结构化聚合、棋盘规则、真实计时、音频seek/resume与科学绘图缺直接素材。因此最小补六项，每项两条公开观察→独立复刻→产物/状态自查流程。取得来源后停止扩充；高阶CAD、硬件/IME、RISC-V/perf与云backend保留OOD未知。

这不是100/250题实际覆盖率，未查看隐藏断言；原37条示例映射不是全量覆盖分母。`desktop_100_domain_audit.json`逐一登记Ubuntu50/Windows50；97份固定README已取得，3份未取得分别为FXGLSlidingPuzzle、PathLengthChecker与LaunchyQt，暂以公开sourceID分类，不能冒称行为已核。

| 公共来源主领域 | 行数 |
|---|---:|
|表达式/数值模式|3|
|开发/性能/模拟/日志/控件工具|7|
|文本/文档/字节编辑|13|
|文件列表/搜索/复制/归档|10|
|游戏规则/合法行动/终态|4|
|图结构/几何/CAD|7|
|图像/画布/注释|16|
|音频/视频/播放/序列编辑|8|
|阅读/训练/内容导航|8|
|凭据/哈希/安全删除|4|
|结构化数据/查询/科学绘图|6|
|输入法/键盘/叠加层/系统状态|5|
|计时/时间记录/计划表单|9|

领域行数是互斥人工归类，不是任务技能收益/断言覆盖率。来源类型可多领域；例如HotelManager有日期表单但不代表倒计时。

## 被旧16漏掉的直接素材

| 细分轴 | 公开任务数 | ID |
|---|---:|---|
|live_time_core|6|ubuntu/jmoerman-go-for-it, ubuntu/seadve-breathing, ubuntu/zidoro-pomatez, windows/envigit-pomodorotimer, windows/odest-iclock, windows/planshit-tai|
|dedicated_audio|5|ubuntu/clementine-player-clementine, ubuntu/digimezzo-dopamine, ubuntu/rncbc-qtractor, ubuntu/thp-wavbreaker, windows/jbe2277-musicmanager|
|audio_video_multimedia|8|ubuntu/clementine-player-clementine, ubuntu/digimezzo-dopamine, ubuntu/mifi-lossless-cut, ubuntu/rncbc-qtractor, ubuntu/thp-wavbreaker, windows/bartkessels-simpleconvert, windows/jbe2277-musicmanager, windows/thisismy-github-pyplayer|
|scientific_plot_core|2|ubuntu/kde-labplot, ubuntu/silx-kit-silx|
|scientific_network_or_spatial_visualization|2|windows/husonlab-splitstree6, windows/vagabond-k-dxftoelevationmodel|

实时核心6题；另外快速阅读/Teleprompter/Keypunch也涉及时间，可记reader辅助轴不混六题数量。专门音频5题（含播放器与编辑器）；广义音视频8题。科学数值绘图核心2题（LabPlot/silx），另2科学网络/空间视图(SplitsTree/DXF)，不能把它们全说为同种曲线图。原ScreenToGif是帧时间线，ActivityDiary是记录，均不等于这些直接素材。

## 六项补充与构建边界

| 固定源 | 主平台 | tag／SHA | 许可 |
|---|---|---|---|
|[GNOME Calculator](https://github.com/GNOME/gnome-calculator)|ubuntu|46.3 / 496cb9aa220b4cafe06d6b41452355c68492479c|GPL-3.0-or-later|
|[Tad](https://github.com/antonycourtney/tad)|windows|v0.14.0 / a144c545a7126652d1a0ac7b1e0d9b0ee9cfb809|MIT|
|[KReversi](https://github.com/KDE/kreversi)|ubuntu|v26.08.1 / ae30d8e7171ec9fa5b2861afd403ebeb075ebfc4|GPL-2.0-or-later code; GFDL docs and separately licensed themes/assets|
|[Veusz](https://github.com/veusz/veusz)|ubuntu|veusz-4.2.1 / b637be1018a473fa829d097ce48b8164078dd365|GPL-2.0-or-later|
|[Pomotroid](https://github.com/Splode/pomotroid)|windows|v1.7.1 / 4a02ac7bff9083dc5b2cc42fa7c4683c1fc15805|MIT|
|[Cozy](https://github.com/geigi/cozy)|ubuntu|1.3.0 / 4c978ec53f0d86de116e4db471821af5138f8edc|GPL-3.0-or-later; bundled python-inject has its own includedlicense|

### GNOME Calculator

Meson>=0.57; C/Vala; GTK4>=4.11.4; Adwaita>=1.4.alpha; GtkSourceView>=5.3; Soup>=3.4; Gee>=0.20; MPC/MPFR. 46.3 selected for Ubuntu24.04 compatibility, 51.0 retained as too-new candidate.
Ubuntu24.04 baseline comparison suggests build feasible; no build/run proof. Exact apt packages, fonts, locale and all transitive dependencies must still be fixed. Currency rate fetching excluded from offline tasks.

- 表达式与错误恢复：观察 在基本/高级模式键入2+3×4与带括号变体、删除重输和非法表达式，记录结果与错误标识 → 原创复刻 独立实现输入buffer、运算优先级、错误态与清除/纠正路径 → 自查 同数值输入的键盘与按钮结果一致；非法输入不返回虚假有效值，改正后恢复。负例：只拼接按钮文本或以从左至右求值冒充优先级。
- 数值模式与历史：观察 观察角度单位/数值进制切换与历史条目复用，记录显示和值的变化 → 原创复刻 分开数值、格式、角度模式和历史，切换格式不破坏数值 → 自查 已知角度与整数进制fixture符合参考结果；历史重新选用可再次计算。负例：将格式后的字符串当实际数值，切换模式重置或污染历史。

### Tad

Official source build: Node19.3/npm9.2 documentation, Lerna bootstrap and build-all.sh, desktop Electron31.0.1 and DuckDB; native dependencies and old node-sass require fixed versions.
Windows2022 build is not verified; use controlled packaged runtime or admitted node/native toolchain. Only local CSV/Parquet fixture; cloud SQL backends excluded; updater/DuckDB extension auto-fetch must be disabled or precached and verified offline.

- 过滤排序与真实导出：观察 导入含稳定ID、文本、数字、空值的CSV，单列过滤、数值排序、取消条件，再导出可见表 → 原创复刻 独立建模source行、视图条件、排序与输出行集 → 自查 输出CSV/Parquet解码后ID集合/顺序/空值与公开界面一致；取消过滤恢复全部行。负例：只隐藏行而导出全表、数字按字符串排序、空值当零。
- 透视聚合与列状态：观察 观察按类别分组、总计/数量、展开折叠、选列与列顺序 → 原创复刻 独立实现聚合层与显示状态，避免把汇总值再次计入 → 自查 对小fixture人工确定组数/总计；展开不改总计、隐藏列不改源数据。负例：只画相同表头或将聚合结果叠加重复计算。

### KReversi

CMake>=3.16; Qt6>=6.5 Widgets/Qml/Quick/QuickWidgets/Svg; ECM/KF6>=6.0 and KDEGames6. Source tag26.08.1 is fixed; future Ubuntu24 package/Flatpak runtime must include KDE6 stack.
Stock Ubuntu24.04 KDE5 packages are insufficient for this fixed modern KDE6 source; use pinned official KDE6 runtime/dependency container. QML board accessibility and deterministic human-vs-human mode require admission. Computer AI timing/choice excluded from deterministic first workflows.

- 合法与非法落子：观察 在人对人模式观察合法提示、合法落子的连续翻子、非法格点击与当前玩家 → 原创复刻 独立实现board状态和方向捕获规则，不从截图颜色硬编码下一盘 → 自查 固定初始局面合法/非法路径中棋子数、翻转集合和turn一致；非法行动不改变状态。负例：允许所有空格或只翻一个邻居、无合法动作仍强制玩家落子。
- 撤销与新局隔离：观察 观察多步后撤销、提示开关与重新开始 → 原创复刻 实现完整状态历史与reset，提示只是视图 → 自查 撤销恢复棋盘/分数/turn；新局清除旧history且再次首步不受上一盘污染。负例：只撤销最后一个落子不恢复翻子、reset保留旧轮次。

### Veusz

Python>=3.8, Qt>=6.3, SIP>=6.5, PyQt>=6.3 and NumPy per fixed INSTALL; C++ helper extensions and setuptools build. FITS/HDF5 are optional. Scope localCSV,2Dplot,SVG/PNG export.
Ubuntu24.04 Python/Qt baseline must be compared with exact pinned requirements; Qt6.10.2 in official binaries is not a requirement automatically satisfied by stock apt. Plotcanvas requires screenshots/coordinates; optional networking/data capture/plugins excluded.

- 数据到图形映射：观察 观察合成CSV列导入、X/Y分配、轴标题/范围、线与点样式 → 原创复刻 独立实现数据schema与plot坐标转换，分开widget树、数据与viewport → 自查 小数据图点数量/坐标/标签与参考一致；改变轴范围只改变视图。负例：凭初始图手绘曲线、混用列或缩放改数据。
- 文档与导出一致性：观察 编辑图层/标签后保存重开，导出SVG/PNG并改变输出尺寸 → 原创复刻 实现文档持久化和数据驱动导出 → 自查 重开保留dataset/轴/样式；解码输出尺寸与图形范围正确。负例：只保存截图或工具条不是真实图内容，导出忽略最终修改。

### Pomotroid

Tauri2/Rust2021/Svelte5; Node22+ per fixed CONTRIBUTING.md, npm and Rust/Cargo caches; native Windows MSVC/WebView2 or Ubuntu WebKitGTK4.1. Cargo includes bundledrusqlite/rodio/localwebsocket optionalserver.
Windows2022 needs fixed MSVC and WebView2 runtime, neither build nor GUI admission performed; tray/notification must remain local to reference VM. Updater/network disabled; optional WebSocketserver not actor observation channel.

- 暂停与继续的单一时钟：观察 观察start、短等待、pause、等待、resume、reset时显示与进度弧 → 原创复刻 独立实现单一单调时间来源、running/paused/reset状态机 → 自查 暂停期间剩余值保持、继续接续同round；容许固定显示粒度误差，不用每render重开interval。负例：暂停后后台仍倒计时或多interval让计时加倍。
- 轮次边界与统计持久化：观察 用公开设置的最短合法时长观察work→break、完成统计、重启记录 → 原创复刻 独立实现边界事件 exactlyonce、设置/会话状态与统计持久化 → 自查 一次完成只增加一次计数；重启统计保留，reset不伪造完成。负例：达到零反复统计、暂停/放弃被记完成。

### Cozy

Python3/Meson>=0.40,GTK4>=4.10,Adwaita>=1.4,PyGObject/gi-cairo,Peewee>=3.9.6,Mutagen,GStreamer1.0 codecs. README has Ubuntu-specific DEVELOPMENT instructions.
Declared GTK/Adwaita minima fit Ubuntu24.04 baseline; build/runtime not verified. Use synthetic local WAV chapters(no copyright/DRM/networkdrive); fixed GStreamer/audio sink, font/metadata library. macOS port discontinued, not selected.

- 播放与寻址状态：观察 导入两个合成WAV章节，观察play/pause/seek/切章、时长和进度 → 原创复刻 独立建模media身份、秒时间、playback状态和异步加载/seek → 自查 seek后声段/显示位置一致；暂停位置不推进，换章不会延用上一章时长。负例：仅移动进度条而媒体没跳转、异步回执覆盖新章节。
- 位置与库持久化：观察 播放/seek后关闭重开、搜索过滤书目、更改播放速度并观察 → 原创复刻 实现每媒体独立bookmark、库状态和播放速率 → 自查 重开回到同章节与位置(允许固定误差)；过滤不删除库记录；速率不改文件时长。负例：全库共用一个位置或搜索结果被误当已删除媒体。

## 来源隔离与准入

六项对全部200native来源精确repo命中0；50Web公开首页身份摘要的显式GitHub链接命中0。GNOME mirror→GitLab和KDEmirror→invent的别名已记录；SQLiteStudio→Letos被实际官方重定向识别并拒绝。KReversi不使用benchmark的国际象棋/扫雷/Sudoku/滑块规则；同KDEGames共享框架须披露，完整fork/code-similarity及匿名Web来源仍pending。不能把精确去重当所有家族已经完全隔离。

Calculator51.0要求过新，完整文档/SHA保留，主池选46.3以匹配Ubuntu24.04基础库。46.3、Cozy最低声明版本更适合Ubuntu24.04；KReversi26.08.1需要KDE6而不是Ubuntu24.04默认KDE5。Veusz/Tad/Pomotroid的Qt、Node、Cargo、媒体编解码和WebView依赖仍需固定；源码归档不能冒称可离线构建。正式运行accepted=0、trajectory=0、verifiedskills=0，控件访问树和canvas可观察性未验证。

本轮停止规则只保证首轮素材能力轴有代表，下一步是独立reference运行准入及训练verifier冻结；只有真实观察与完整执行轨迹才能进入AutoSkill，不手写预期技能当实证。原生actor只获运行UI，来源代码用于准备reference，不能把bench代码作为训练实现答案。

主要来源均为固定公开README/license/build docs，逐文件URL/SHA在`selected_candidates.json`、`public_candidate_evidence.json`和`additional_gap_candidate_evidence.json`；bench证据在`bench_public_domain_evidence.json`。官方项目入口：[GNOME Calculator](https://apps.gnome.org/Calculator/)、[Tad releases](https://github.com/antonycourtney/tad/releases/tag/v0.14.0)、[KReversi](https://invent.kde.org/games/kreversi)、[Veusz](https://github.com/veusz/veusz)、[Pomotroid](https://github.com/Splode/pomotroid)、[Cozy](https://github.com/geigi/cozy)。
