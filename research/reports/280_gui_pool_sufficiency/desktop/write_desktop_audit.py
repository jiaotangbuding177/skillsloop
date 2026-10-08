"""Materialize public-source domain audit and proposed workflows; no experiment execution."""
import collections,datetime,json,pathlib,re
R=pathlib.Path(__file__).resolve().parent
OLD=R.parents[1]/'279_gui_acquisition'
catalog=json.loads((OLD/'bench_source_catalog.json').read_text(encoding='utf-8'))
evidence=json.loads((R/'bench_public_domain_evidence.json').read_text(encoding='utf-8'))['records']
E={r['instance_id']:r for r in evidence}
groups={
 'image_canvas':('图像/画布/注释','Xournal++/Flameshot/Caesium/ScreenToGif/miniPaint/Gallery', '''ubuntu/adrienverge-photocollage ubuntu/ksnip-ksnip ubuntu/libresprite-libresprite ubuntu/pencil2d-pencil ubuntu/wicklets-wick-editor windows/0xmartin-bmpeditor windows/colorcop-colorcop windows/derek-rein-exr-converter windows/dragonofmercy-image-viewer windows/galfar-imaginglib windows/geeeekexplorer-nju-graphics windows/mfl28-boundingboxeditor windows/mitchcurtis-slate windows/obiwankennedy-hotshots windows/rajitharanasinghe-automatic_thresholding windows/thejoefin-screenshot-stager'''),
 'graph_cad':('图结构/几何/CAD','Heimer/FamilyGem（图关系）；高阶CAD和科学网络仍OOD', '''ubuntu/camunda-camunda-modeler ubuntu/gnome-dia ubuntu/solvespace-solvespace windows/husonlab-splitstree6 windows/mdadali-lazcad windows/prmr-jetuml windows/vagabond-k-dxftoelevationmodel'''),
 'document_editor':('文本/文档/字节编辑','Xournal++/WinMerge/HexFiend/StackEdit', '''ubuntu/fabiocolacio-marker ubuntu/giuspen-cherrytree ubuntu/kde-okteta ubuntu/marktext-marktext ubuntu/notepadqq-notepadqq ubuntu/ranrar-marco ubuntu/texworks-texworks ubuntu/wxmedit-wxmedit windows/alexey-t-atsynedit windows/amirreza-tabeshfard-at-netcore-notepadplusplus windows/hellowrc-stickyhomeworks windows/stevethekiller-killerpdf windows/yanglr-tinynotepad'''),
 'reader_learning':('阅读/训练/内容导航','StackEdit/Vite文档/ActivityDiary；快速阅读与语言训练未直接代表', '''ubuntu/bragefuglseth-fretboard ubuntu/bragefuglseth-keypunch ubuntu/buggins-coolreader ubuntu/darazaki-spedread ubuntu/nokse22-teleprompter ubuntu/ollm-opencomic windows/ebookprojects-uchmviewer windows/vocabhunter-vocabhunter'''),
 'file_utility':('文件列表/搜索/复制/归档','WinMerge/Caesium/Gallery；压缩、复制碰撞、系统清理为残余', '''ubuntu/aleksey-hoffman-sigma-file-manager ubuntu/alphaonex86-ultracopier ubuntu/cboxdoerfer-fsearch ubuntu/ib-xarchiver ubuntu/kde-krename ubuntu/matteo842-savestate ubuntu/shundhammer-qdirstat windows/alessio-vivaldelli-filemanager windows/deadlydog-pathlengthchecker windows/no-faff-installerclean'''),
 'time_record_forms':('计时/时间记录/计划表单','ActivityDiary提供记录，尚无真实倒计时；补Pomotroid', '''ubuntu/jmoerman-go-for-it ubuntu/seadve-breathing ubuntu/zidoro-pomatez windows/enrimilan-hotelmanager windows/envigit-pomodorotimer windows/odest-iclock windows/plaintool-notetask windows/planshit-tai windows/varianus-ovonote'''),
 'calculator':('表达式/数值模式','旧16无；补GNOME Calculator', '''ubuntu/qalculate-qalculate-qt windows/rubendavidroy-calculator windows/sj14-calculon'''),
 'structured_data':('结构化数据/查询/科学绘图','旧16有列表但无关系型过滤/聚合或数值绘图；补Tad/Veusz', '''ubuntu/amalshaji-dbcooper ubuntu/kde-labplot ubuntu/silx-kit-silx ubuntu/sqlitebrowser-sqlitebrowser windows/mukunku-parquetviewer windows/viniciussanchez-dataset-serialize'''),
 'media':('音频/视频/播放/序列编辑','ScreenToGif/Gifski提供帧序列；旧16无音频play/seek/resume；补Cozy', '''ubuntu/clementine-player-clementine ubuntu/digimezzo-dopamine ubuntu/mifi-lossless-cut ubuntu/rncbc-qtractor ubuntu/thp-wavbreaker windows/bartkessels-simpleconvert windows/jbe2277-musicmanager windows/thisismy-github-pyplayer'''),
 'game_rules':('游戏规则/合法行动/终态','旧16无；补KReversi，规则不同于测试棋类', '''ubuntu/kde-ksudoku windows/beryx-fxgl-sliding-puzzle windows/blueskyson-qt-pac-man windows/sauce-code-cuckoo'''),
 'developer_tools':('开发/性能/模拟/日志/控件工具','WinMerge/Tad提供通用查询与输出状态；RISC-V/perf/API/控件生命周期仍OOD', '''ubuntu/kdab-hotspot ubuntu/mortbopet-ripes ubuntu/usebruno-bruno ubuntu/wxformbuilder-wxformbuilder windows/couchcoding-logbert windows/gragra33-logviewercontrol windows/vagabond-k-vagabondk.indicators'''),
 'security':('凭据/哈希/安全删除','MacPass提供合成vault工作流；哈希/擦除策略仍OOD', '''ubuntu/keeweb-keeweb ubuntu/pwsafe-pwsafe windows/viniciussanchez-bcrypt windows/xerodays-securefileshredder'''),
 'system_input':('输入法/键盘/叠加层/系统状态','基础表单/布局为近似；IME/全局hooks/设备账号状态仍OOD', '''ubuntu/mijorus-smile windows/comtel2000-fx-experience windows/evotecit-informationbox windows/phaiax-key-n-stroke windows/samsonwang-launchyqt'''),
}
assigned={}
for key,(label,material,ids) in groups.items():
    for tid in ids.split():
        if tid in assigned:raise ValueError('duplicate '+tid)
        assigned[tid]=(key,label,material)
target={r['instance_id'] for r in catalog['tasks'] if r['platform'] in ('ubuntu','windows')}
assert set(assigned)==target,(target-set(assigned),set(assigned)-target)
axes={
 'live_time_core':['ubuntu/jmoerman-go-for-it','ubuntu/seadve-breathing','ubuntu/zidoro-pomatez','windows/envigit-pomodorotimer','windows/odest-iclock','windows/planshit-tai'],
 'dedicated_audio':['ubuntu/clementine-player-clementine','ubuntu/digimezzo-dopamine','ubuntu/rncbc-qtractor','ubuntu/thp-wavbreaker','windows/jbe2277-musicmanager'],
 'audio_video_multimedia':['ubuntu/clementine-player-clementine','ubuntu/digimezzo-dopamine','ubuntu/mifi-lossless-cut','ubuntu/rncbc-qtractor','ubuntu/thp-wavbreaker','windows/bartkessels-simpleconvert','windows/jbe2277-musicmanager','windows/thisismy-github-pyplayer'],
 'scientific_plot_core':['ubuntu/kde-labplot','ubuntu/silx-kit-silx'],
 'scientific_network_or_spatial_visualization':['windows/husonlab-splitstree6','windows/vagabond-k-dxftoelevationmodel'],
}
records=[]
for tid in sorted(target):
    e=E[tid];key,label,material=assigned[tid]
    records.append({k:e[k] for k in ('instance_id','platform','difficulty','repo','commit')}|{'domain_primary':key,'domain_label':label,'domain_evidence_basis':'fixed public README' if e.get('public_readme') else 'public source identity; README missing; conservative provisional classification','public_readme':e.get('public_readme'),'public_readme_url':e.get('url'),'public_readme_sha256':e.get('sha256'),'material_correspondence_hypothesis':material,'task_hidden_behavior_inspected':False,'actual_task_coverage_proven':False,'residual_specialism_ood':key in ('developer_tools','system_input','graph_cad','reader_learning','file_utility','security')})
counts=collections.Counter(r['domain_primary'] for r in records)
counts_platform={p:dict(collections.Counter(r['domain_primary'] for r in records if r['platform']==p)) for p in ('ubuntu','windows')}
audit={'schema':'skillloop.public_desktop_100_domain_audit.v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'all Ubuntu50 and Windows50 public source identities; fixed README retrieved97; no hidden tests or scores','classification_count':100,'public_readme_retrieved':sum(bool(e.get('public_readme')) for e in evidence),'primary_domain_counts':dict(counts),'domain_counts_by_platform':counts_platform,'fine_axes':{k:{'count':len(v),'task_ids':v,'scope':'public project domain, not assertion-level benchmark coverage'} for k,v in axes.items()},'coverage_percent':None,'coverage_percent_reason':'Domain taxonomy and prospective material mapping do not measure tests or skill transfer. 37 prior example IDs are not a250 coverage denominator.','records':records}
(R/'desktop_100_domain_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
def flow(name,observe,implement,check,negative):return {'name':name,'observe':observe,'implement':implement,'check':check,'negative_example':negative,'status':'proposed public behavior; reference runtime observation and independent verifier not yet admitted'}
specs=[
 ('ubuntu','GNOME Calculator','GNOME/gnome-calculator','GNOME__gnome-calculator__46.3','GPL-3.0-or-later',
  'Meson>=0.57; C/Vala; GTK4>=4.11.4; Adwaita>=1.4.alpha; GtkSourceView>=5.3; Soup>=3.4; Gee>=0.20; MPC/MPFR. 46.3 selected for Ubuntu24.04 compatibility, 51.0 retained as too-new candidate.',
  'Ubuntu24.04 baseline comparison suggests build feasible; no build/run proof. Exact apt packages, fonts, locale and all transitive dependencies must still be fixed. Currency rate fetching excluded from offline tasks.',
  ['ubuntu/qalculate-qalculate-qt','windows/rubendavidroy-calculator','windows/sj14-calculon'],
  [flow('表达式与错误恢复','在基本/高级模式键入2+3×4与带括号变体、删除重输和非法表达式，记录结果与错误标识','独立实现输入buffer、运算优先级、错误态与清除/纠正路径','同数值输入的键盘与按钮结果一致；非法输入不返回虚假有效值，改正后恢复','只拼接按钮文本或以从左至右求值冒充优先级'),flow('数值模式与历史','观察角度单位/数值进制切换与历史条目复用，记录显示和值的变化','分开数值、格式、角度模式和历史，切换格式不破坏数值','已知角度与整数进制fixture符合参考结果；历史重新选用可再次计算','将格式后的字符串当实际数值，切换模式重置或污染历史')]),
 ('windows','Tad','antonycourtney/tad','antonycourtney__tad','MIT',
  'Official source build: Node19.3/npm9.2 documentation, Lerna bootstrap and build-all.sh, desktop Electron31.0.1 and DuckDB; native dependencies and old node-sass require fixed versions.',
  'Windows2022 build is not verified; use controlled packaged runtime or admitted node/native toolchain. Only local CSV/Parquet fixture; cloud SQL backends excluded; updater/DuckDB extension auto-fetch must be disabled or precached and verified offline.',
  ['windows/mukunku-parquetviewer','windows/viniciussanchez-dataset-serialize','ubuntu/sqlitebrowser-sqlitebrowser','ubuntu/amalshaji-dbcooper','ubuntu/kde-labplot'],
  [flow('过滤排序与真实导出','导入含稳定ID、文本、数字、空值的CSV，单列过滤、数值排序、取消条件，再导出可见表','独立建模source行、视图条件、排序与输出行集','输出CSV/Parquet解码后ID集合/顺序/空值与公开界面一致；取消过滤恢复全部行','只隐藏行而导出全表、数字按字符串排序、空值当零'),flow('透视聚合与列状态','观察按类别分组、总计/数量、展开折叠、选列与列顺序','独立实现聚合层与显示状态，避免把汇总值再次计入','对小fixture人工确定组数/总计；展开不改总计、隐藏列不改源数据','只画相同表头或将聚合结果叠加重复计算')]),
 ('ubuntu','KReversi','KDE/kreversi','KDE__kreversi','GPL-2.0-or-later code; GFDL docs and separately licensed themes/assets',
  'CMake>=3.16; Qt6>=6.5 Widgets/Qml/Quick/QuickWidgets/Svg; ECM/KF6>=6.0 and KDEGames6. Source tag26.08.1 is fixed; future Ubuntu24 package/Flatpak runtime must include KDE6 stack.',
  'Stock Ubuntu24.04 KDE5 packages are insufficient for this fixed modern KDE6 source; use pinned official KDE6 runtime/dependency container. QML board accessibility and deterministic human-vs-human mode require admission. Computer AI timing/choice excluded from deterministic first workflows.',
  ['ubuntu/kde-ksudoku','windows/beryx-fxgl-sliding-puzzle','windows/blueskyson-qt-pac-man','windows/sauce-code-cuckoo'],
  [flow('合法与非法落子','在人对人模式观察合法提示、合法落子的连续翻子、非法格点击与当前玩家','独立实现board状态和方向捕获规则，不从截图颜色硬编码下一盘','固定初始局面合法/非法路径中棋子数、翻转集合和turn一致；非法行动不改变状态','允许所有空格或只翻一个邻居、无合法动作仍强制玩家落子'),flow('撤销与新局隔离','观察多步后撤销、提示开关与重新开始','实现完整状态历史与reset，提示只是视图','撤销恢复棋盘/分数/turn；新局清除旧history且再次首步不受上一盘污染','只撤销最后一个落子不恢复翻子、reset保留旧轮次')]),
 ('ubuntu','Veusz','veusz/veusz','veusz__veusz','GPL-2.0-or-later',
  'Python>=3.8, Qt>=6.3, SIP>=6.5, PyQt>=6.3 and NumPy per fixed INSTALL; C++ helper extensions and setuptools build. FITS/HDF5 are optional. Scope localCSV,2Dplot,SVG/PNG export.',
  'Ubuntu24.04 Python/Qt baseline must be compared with exact pinned requirements; Qt6.10.2 in official binaries is not a requirement automatically satisfied by stock apt. Plotcanvas requires screenshots/coordinates; optional networking/data capture/plugins excluded.',
  ['ubuntu/kde-labplot','ubuntu/silx-kit-silx','windows/husonlab-splitstree6','windows/vagabond-k-dxftoelevationmodel'],
  [flow('数据到图形映射','观察合成CSV列导入、X/Y分配、轴标题/范围、线与点样式','独立实现数据schema与plot坐标转换，分开widget树、数据与viewport','小数据图点数量/坐标/标签与参考一致；改变轴范围只改变视图','凭初始图手绘曲线、混用列或缩放改数据'),flow('文档与导出一致性','编辑图层/标签后保存重开，导出SVG/PNG并改变输出尺寸','实现文档持久化和数据驱动导出','重开保留dataset/轴/样式；解码输出尺寸与图形范围正确','只保存截图或工具条不是真实图内容，导出忽略最终修改')]),
 ('windows','Pomotroid','Splode/pomotroid','Splode__pomotroid','MIT',
  'Tauri2/Rust2021/Svelte5; Node22+ per fixed CONTRIBUTING.md, npm and Rust/Cargo caches; native Windows MSVC/WebView2 or Ubuntu WebKitGTK4.1. Cargo includes bundledrusqlite/rodio/localwebsocket optionalserver.',
  'Windows2022 needs fixed MSVC and WebView2 runtime, neither build nor GUI admission performed; tray/notification must remain local to reference VM. Updater/network disabled; optional WebSocketserver not actor observation channel.',
  ['ubuntu/jmoerman-go-for-it','ubuntu/zidoro-pomatez','ubuntu/seadve-breathing','windows/envigit-pomodorotimer','windows/odest-iclock','windows/planshit-tai'],
  [flow('暂停与继续的单一时钟','观察start、短等待、pause、等待、resume、reset时显示与进度弧','独立实现单一单调时间来源、running/paused/reset状态机','暂停期间剩余值保持、继续接续同round；容许固定显示粒度误差，不用每render重开interval','暂停后后台仍倒计时或多interval让计时加倍'),flow('轮次边界与统计持久化','用公开设置的最短合法时长观察work→break、完成统计、重启记录','独立实现边界事件 exactlyonce、设置/会话状态与统计持久化','一次完成只增加一次计数；重启统计保留，reset不伪造完成','达到零反复统计、暂停/放弃被记完成')]),
 ('ubuntu','Cozy','geigi/cozy','geigi__cozy','GPL-3.0-or-later; bundled python-inject has its own includedlicense',
  'Python3/Meson>=0.40,GTK4>=4.10,Adwaita>=1.4,PyGObject/gi-cairo,Peewee>=3.9.6,Mutagen,GStreamer1.0 codecs. README has Ubuntu-specific DEVELOPMENT instructions.',
  'Declared GTK/Adwaita minima fit Ubuntu24.04 baseline; build/runtime not verified. Use synthetic local WAV chapters(no copyright/DRM/networkdrive); fixed GStreamer/audio sink, font/metadata library. macOS port discontinued, not selected.',
  ['ubuntu/clementine-player-clementine','ubuntu/digimezzo-dopamine','ubuntu/rncbc-qtractor','ubuntu/thp-wavbreaker','windows/jbe2277-musicmanager','windows/thisismy-github-pyplayer'],
  [flow('播放与寻址状态','导入两个合成WAV章节，观察play/pause/seek/切章、时长和进度','独立建模media身份、秒时间、playback状态和异步加载/seek','seek后声段/显示位置一致；暂停位置不推进，换章不会延用上一章时长','仅移动进度条而媒体没跳转、异步回执覆盖新章节'),flow('位置与库持久化','播放/seek后关闭重开、搜索过滤书目、更改播放速度并观察','实现每媒体独立bookmark、库状态和播放速率','重开回到同章节与位置(允许固定误差)；过滤不删除库记录；速率不改文件时长','全库共用一个位置或搜索结果被误当已删除媒体')]),
]
def norm(s):
    s=s.lower().rstrip('/').removesuffix('.git')
    for prefix in ('https://github.com/','http://github.com/','https://gitlab.gnome.org/','https://invent.kde.org/'):
        if s.startswith(prefix):s=s[len(prefix):]
    return s
web=json.loads((OLD/'web_bench_identity_audit.json').read_text(encoding='utf-8'))['identities']
apps=[]
for platform,name,repo,folder,license,build,caveats,mappings,flows in specs:
    m=json.loads((R/folder/'public_fixed_metadata.json').read_text(encoding='utf-8'))
    exact=[x['instance_id'] for x in catalog['tasks'] if x.get('repo') and norm(x['repo'])==norm(m['repo'])]
    alias={'GNOME/gnome-calculator':['https://gitlab.gnome.org/GNOME/gnome-calculator'],'KDE/kreversi':['https://invent.kde.org/games/kreversi']}.get(repo,[])
    links=[]
    for row in web:
        for link in row.get('github_links',[]):
            if repo.lower() in link.lower():links.append(row['task_id'])
    apps.append({'platform':platform,'name':name,'repo':m['repo'],'tag':m['tag'],'commit':m['commit'],'license':license,'build_evidence':m['fixed_docs'],'build_requirements':build,'source_caveats':caveats,'workflows':flows,'bench_correspondence':[{'task_id':t,'basis':'public application category or behavior capability inference, not same-source or proven transfer'} for t in mappings],'source_isolation':{'all200native_exact_matches':exact,'aliases':alias,'all50web_explicit_source_matches':links,'web_anonymized_origins_unresolved':True,'full_fork_or_code_similarity_checked':False,'generic_framework_overlap':'Shared GTK/KDE/Qt/React libraries are disclosed; independent source product does not prove complete absence of common code.'},'runtime_accepted':False,'reference_application_run':False,'model_or_task_execution':False,'proposed_workflow_count':len(flows)})
assert all(not x['source_isolation']['all200native_exact_matches'] for x in apps)
assert all(not x['source_isolation']['all50web_explicit_source_matches'] for x in apps)
selected={'schema':'skillloop.desktop_sufficiency_minimum_additions.v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'six source candidates admitted at documentation level only; root coordinates source archives','stop_expanding_after_additions':True,'basis':'Found six previously unrepresented core capabilities in old16; no app-per-bench or genre-quota requirement','selected_candidates':apps,'rejected_or_held':[{'repo':'https://github.com/GNOME/gnome-calculator','tag':'51.0','commit':'51d9861b35bb3e2e69c182a0b6f6a5f84c382f0a','reason':'GTK4>=4.17 andAdwaita>=1.8 too new for stockUbuntu24.04; docs retained, sourcebuild not performed; use46.3'},{'repo':'https://github.com/pawelsalawa/sqlitestudio','canonical_redirect':'https://github.com/pawelsalawa/letos','reason':'Same renamed product as macos/pawelsalawa-letos benchmark; rejected across-platform alias audit'},{'repo':'https://github.com/KDE/kmines','reason':'Minesweeper layout/rules near Mac/Android test app; source not selected, use distinct Reversi rules'},{'repo':'https://github.com/galculator/galculator','reason':'Old stable release/docs and maintenance evidence weaker; use supportedGNOME46 fixedsource'}],'residual_ood':['parametric3D_CAD','RISC_V_simulation','perf_profiling','IME_global_hooks','live_sensor_hardware','advanced_cloud_database_backends','encryption_or_erasure_algorithm_validation'],'source_pool_sufficiency_claim':'Prospective basic behavior/material axes only; not250 task or hiddenassertion coverage, not empirical skilltransfer','runtime_accepted_count':0,'trajectory_count':0,'verified_skill_count':0}
(R/'selected_candidates.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
summary=['# Ubuntu／Windows全100个公开来源的演化素材充分性审核','','日期2026-10-04；只公开来源与构建文档研究，不读隐藏tests，不运行模型或参考应用，旧STOP/三轮限制保持。','','旧279桌面六项偏图形、文档、图编辑和文件输出；整个16项池对数值表达式、结构化聚合、棋盘规则、真实计时、音频seek/resume与科学绘图缺直接素材。因此最小补六项，每项两条公开观察→独立复刻→产物/状态自查流程。取得来源后停止扩充；高阶CAD、硬件/IME、RISC-V/perf与云backend保留OOD未知。','','这不是100/250题实际覆盖率，未查看隐藏断言；原37条示例映射不是全量覆盖分母。`desktop_100_domain_audit.json`逐一登记Ubuntu50/Windows50；97份固定README已取得，3份未取得分别为FXGLSlidingPuzzle、PathLengthChecker与LaunchyQt，暂以公开sourceID分类，不能冒称行为已核。','','| 公共来源主领域 | 行数 |','|---|---:|']
for key,cnt in sorted(counts.items()):summary.append('|'+groups[key][0]+'|'+str(cnt)+'|')
summary += ['','领域行数是互斥人工归类，不是任务技能收益/断言覆盖率。来源类型可多领域；例如HotelManager有日期表单但不代表倒计时。','','## 被旧16漏掉的直接素材','','| 细分轴 | 公开任务数 | ID |','|---|---:|---|']
for key,ids in axes.items():summary.append('|'+key+'|'+str(len(ids))+'|'+', '.join(ids)+'|')
summary += ['','实时核心6题；另外快速阅读/Teleprompter/Keypunch也涉及时间，可记reader辅助轴不混六题数量。专门音频5题（含播放器与编辑器）；广义音视频8题。科学数值绘图核心2题（LabPlot/silx），另2科学网络/空间视图(SplitsTree/DXF)，不能把它们全说为同种曲线图。原ScreenToGif是帧时间线，ActivityDiary是记录，均不等于这些直接素材。','','## 六项补充与构建边界','','| 固定源 | 主平台 | tag／SHA | 许可 |','|---|---|---|---|']
for a in apps:summary.append('|['+a['name']+']('+a['repo']+')|'+a['platform']+'|'+a['tag']+' / '+a['commit']+'|'+a['license']+'|')
for a in apps:
    summary+=['','### '+a['name'],'',a['build_requirements'],a['source_caveats'],'']
    for f in a['workflows']:summary+=['- '+f['name']+'：观察 '+f['observe']+' → 原创复刻 '+f['implement']+' → 自查 '+f['check']+'。负例：'+f['negative_example']+'。']
summary += ['','## 来源隔离与准入','','六项对全部200native来源精确repo命中0；50Web公开首页身份摘要的显式GitHub链接命中0。GNOME mirror→GitLab和KDEmirror→invent的别名已记录；SQLiteStudio→Letos被实际官方重定向识别并拒绝。KReversi不使用benchmark的国际象棋/扫雷/Sudoku/滑块规则；同KDEGames共享框架须披露，完整fork/code-similarity及匿名Web来源仍pending。不能把精确去重当所有家族已经完全隔离。','','Calculator51.0要求过新，完整文档/SHA保留，主池选46.3以匹配Ubuntu24.04基础库。46.3、Cozy最低声明版本更适合Ubuntu24.04；KReversi26.08.1需要KDE6而不是Ubuntu24.04默认KDE5。Veusz/Tad/Pomotroid的Qt、Node、Cargo、媒体编解码和WebView依赖仍需固定；源码归档不能冒称可离线构建。正式运行accepted=0、trajectory=0、verifiedskills=0，控件访问树和canvas可观察性未验证。','','本轮停止规则只保证首轮素材能力轴有代表，下一步是独立reference运行准入及训练verifier冻结；只有真实观察与完整执行轨迹才能进入AutoSkill，不手写预期技能当实证。原生actor只获运行UI，来源代码用于准备reference，不能把bench代码作为训练实现答案。','','主要来源均为固定公开README/license/build docs，逐文件URL/SHA在`selected_candidates.json`、`public_candidate_evidence.json`和`additional_gap_candidate_evidence.json`；bench证据在`bench_public_domain_evidence.json`。官方项目入口：[GNOME Calculator](https://apps.gnome.org/Calculator/)、[Tad releases](https://github.com/antonycourtney/tad/releases/tag/v0.14.0)、[KReversi](https://invent.kde.org/games/kreversi)、[Veusz](https://github.com/veusz/veusz)、[Pomotroid](https://github.com/Splode/pomotroid)、[Cozy](https://github.com/geigi/cozy)。']
(R/'desktop_sufficiency_report.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
print(json.dumps({'audit_rows':len(records),'readmes':audit['public_readme_retrieved'],'domain_counts':dict(counts),'fine_axis_counts':{k:len(v) for k,v in axes.items()},'selected':len(apps),'flows':sum(len(a['workflows']) for a in apps),'exact_native_matches':0,'explicit_web_matches':0},ensure_ascii=False))
