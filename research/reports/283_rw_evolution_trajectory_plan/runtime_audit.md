# RecreationWorld 演化轨迹运行设施只读审计

日期：2026-10-04。范围：26 主候选的运行方案准备，未启动应用、模型、评分、安装或部署；未恢复旧 RW STOP、Docker Desktop，未修改其他聊天 Co-Gym/tau 服务、共享 README/STATE 或官方 vendor。FastCtx 本轮未出现在可调用工具中，使用系统 Python 3.11 与显式系统 PowerShell 仅读本地资料/宿主状态。

## 当前可证事实

- 已先读取 research/README.md、CHARTER.md、STATE.md 的当前有效段和 memory/281_2026-10-04_rw_250_evolution_pool_sufficiency.md。原26主候选为 Ubuntu7、Windows5、macOS3、Android6、Web5；MacPass为条件候补。来源池不是作者官方 train，也不是已执行轨迹。
- reports/280_gui_pool_sufficiency/evolution_task_registry.json 当前 runtime_accepted_count、model_calls、trajectory_count、verified_skill_count 全0。26全部准入时最多78个完整尝试，78不是成功轨迹预期。64观察流程包括候补，且不是64独立任务。
- 官方固定源码入口：experiments/218_recreationworld_glm_pipeline/vendor/RecreationWorld，manifest记载 commit `b5cda868f44932dc84ea68e3b3053bc418621aa3`。官方任务索引 revision `284341f8fc3d6680dd57ca5414fed92a0fe33b95`。本轮只读，不更新旧 freeze。
- 现有真实运行证据集中在 Web corravale canary。218/reports/pipeline_status.json及对应metrics证明原CLI任务执行/评测链路完成，但program_score=0、vlm_score=null、score_passed=false，不能称成功复刻或完整视觉评分。238/reports/model_acceptance.json证明直接API两项真实图像与工具协议探测通过，供应商响应自报deepseek/deepseek-v4.1-flash；238自身canary为transport_failure，不可用它宣称native全链路通过。264有完整交付、公开交互轨迹与程序分，仍是带额外指导的历史corravale演示，formal_baseline_accepted=false。
- 267_recreationworld_public_content_v17/reports/user_stop.json保留explicit_user_stop、restart_forbidden=true、future_corrective_round_limit=3；旧controller与容器停止证据保留。本轮不恢复其流水线。

## 宿主只读快照

Windows实际查询：Windows11家庭版中文版build26200，24逻辑CPU，物理内存34,056,994,816bytes（约31.72GiB），当次可用约11.42GiB。HypervisorPresent=true；VirtualizationFirmwareEnabled=false是WMI观测，不能据此单独判硬件虚拟化关闭。未发现Docker Desktop/com.docker.backend、Android emulator/qemu或sshd进程；服务查询未返回sshd/vmms，vmcompute正在运行。WSL列表：Ubuntu Running/version2；docker-desktop Stopped/version2。未查询或更改个人会话/凭据。

已运行Ubuntu的仅读快照：Ubuntu24.04.2，kernel6.6.87.2-microsoft-standard-WSL2；dockerd PID377/containerd PID260和/var/run/docker.sock存在。它是目前其他聊天依赖的原生WSL Docker，不能因Desktop停止而误停/重装它。/dev/kvm存在但当前用户无读写权限；adb、emulator、qemu-system-x86_64、xvfb-run未在PATH；ssh和docker在PATH。WSL MemTotal16,226,468KiB、MemAvailable13,955,240KiB。只读访问没有启动容器、查询镜像拉取或恢复Desktop集成。

以上是该时点观察；命令不存在、未见本地验收证据不等于全机或外部账户绝对没有资源。现有Web镜像/历史artifact不能直接证明七个Ubuntu native应用已可运行。宏观内存余量也不能证明并行GUI+编译+音视频可稳定承载。

## 五平台运行契约与实际缺口

| 平台/主候选数 | 官方原生入口与隔离 | 已有证据 | 正式采集前必须补齐 |
|---|---|---|---|
| Web/5 | providers/web/Dockerfile、providers/web/template/run_one.py；Playwright MCP。reference/tests/scorer/root staging对非root agent不可读，network namespace为评分运行强制条件，agent/build无ambient capabilities。 | Web单题CLI、截图与交付历史已见；新5个reference和训练verifier仍0准入。 | 固定独立训练输入、构建和依赖缓存、原生浏览器动作/截图/状态重置；独立训练verifier参考自校验与actor不可读探测；统一模型/图像适配重放。 |
| Ubuntu/7 | providers/linux/Dockerfile及scripts/linux/worker.py/runtime；Xvfb+D-Bus+AT-SPI+Openbox，CUA0.7.3和loopback SSH。Linux runtime接收准备好的Ubuntu目标，官方不负责创建/销毁VM。 | pinned官方native脚本与源码已取得；没有新7题reference/build/AT-SPI准入报告。WSL主机没xvfb-run不等于容器内没Xvfb。 | 独立native Linux镜像/目标；GTK/Qt/KDE6、字体/locale、Xournal++ externals、音频sink和构建缓存；逐应用启动、可访问控件/坐标、文件输出、reset及权限反证。 |
| Windows/5 | providers/windows/template/run_one.py→scripts/windows/worker.py/stages/recreation.py；有交互desktop的Windows10/11/Server SSH宿主，Python3.12、Node、CLI、CUA0.7.3/UIA。rbagent+ACL强制隔离reference binary；默认network隔离用Windows Firewall，正常结束恢复policy。 | 本机是Windows，但系统Python3.11仅供研究读文件，不满足官方目标Python3.12要求；无已准备独立Windows SSH/desktop目标验收报告。 | 准备独立Windows VM或远端Windows宿主与快照、有效GUI session/OpenSSH/UIA截图；MSVC/.NET/NuGet/WebView2、WinMerge externals、Rust/Qt/Electron缓存；actor ACL反证、firewall备份恢复和中断回收验证。不要在用户研究工作站上把当前会话、D:/skillloop或共享firewall直接当训练sandbox。 |
| macOS/3 | providers/macos/template/run_one.py，用户拥有目标生命周期；macOS14.7.5、Xcode15.4/CLT、SSH管理员、活跃GUI/Accessibility/ScreenRecording权限；Python3.9+pyobjc、Node22/npm10、CUA0.7.3；devagent必须非admin。 | 三个fixed源已归档；未见可连接macOS原生宿主及readiness/AX权限验收。Windows/WSL不能替代AppKit/AX。 | 提供/准备真实macOS宿主（本地Mac或受控远端Mac）；登录GUI、TCC授权、devagent/source边界，固定Xcode和Swift/Qt等逐源要求。To-Day2.0所需更现代Xcode须与官方Xcode15.4baseline比较；若不兼容，单独版本准入/保留失败，不悄然换源或跨平台复刻冒充macOS。 |
| Android/6 | providers/android：官方列x86_64Ubuntu22.04/KVM宿主，Docker emulator API35 Google APIs x86_64与worker；UiAutomator/MobileMCP0.1.5。可信准备构建source APK，agent启动前删除source checkout和磁盘APK，只留可交互reference。 | /dev/kvm存在但当前用户不能读写；没有adb/emulator命令或活跃emulator证据，新6题SDK/Gradle准入0。 | 独立KVM host或确认可用的隔离嵌套虚拟化/权限；API35 emulator snapshot、每题独立state reset/package身份；JDK17/21、Gradle/AGP/SDK/NDK与离线seed；包名匹配、UiAutomator/截图及隐藏source/APK反证。官方建议32vCPU/128GiB/200GiB不是实测硬性最低线，本机低于建议且共享负载，不能先承诺六任务并行或纯软件模拟可比。 |

reference与candidate不必机械分为两台机器：官方契约是在同一受控平台宿主里由可信准备/评测主体保护源码、binary/APK、tests等，仅让低权限actor看到可运行GUI和独立workspace。必须保留同平台真实启动与程序状态；Web页面截图或手写交互故事不能替代Windows/macOS/Android原生准入。

## 建议采用的路径（尚未执行）

1. 保持Docker Desktop停止。优先在与其他聊天账本/挂载/网络明确分开的user-managed Linux/Docker或独立Ubuntu SSH目标做Web与Ubuntu训练runtime准入；每题一个干净sandbox，固定镜像digest与依赖。FC Agent Sandbox也是官方可用替代，但需要用户账户、API key、区域endpoint和镜像registry/template；现在不能假称已有该账户，不为采集擅自申请/付费。
2. Windows、macOS、Android分别排队准入上述原生宿主，缺宿主则保留waiting_host，不把排队记失败/0。正式起跑资格按平台逐项判断，不能把拥有26份源码直接当26题能同时采集。
3. 新演化base应以218 pinned官方vendor/原生CLI为出发点，只引用必要且有重放证据的模型协议、图像传输与请求等待适配，并冻结统一派生配置、版本、角色与依赖。不得默认继承267/v17的corravale专用fidelity hints、route/content guides或observation guard作为所有26题的共同原生baseline；这17版历史如单独复用须注明暴露/指导差异。
4. 来源池task registry尚未是runtime bundle。先在新目录生成独立training instance/reference launch recipe/公开合成fixtures/训练verifier，保留published250原tasks和hidden tests。Android默认providers/android/run-bench.sh:9使用tasks/android.jsonl并拒绝不在表内的APP_ID；TASKS_FILE可独立覆盖，故应使用独立训练allowlist与验证器输入，不修改原250名单或借用同领域benchmark tests冒充训练verifier。
5. 先做无模型的reference准入、actor不能读源码/裁判反证、训练verifier参考自校验和“损坏/空candidate应失败”校验。再做每个ready平台一条真实完整canary，验证CLI→模型→GUI/编码→build/launch→自查→轨迹与artifact落盘，而不是只测一次API图像就全量启动。并发先1；容量与quota未实测前不宣称速度倍数。

## 时间、轮次与传输预算事实

官方scripts/core/agent_invocation.py:31–32明确 `DEFAULT_AGENT_TIMEOUT_SEC=72_000`、`DEFAULT_REQUEST_TIMEOUT_MS=1_800_000`；:113的`max_turns=None`，:195–196只在显式配置时追加CLI `--max-turns`。create入口有`--timeout`/`--request-timeout-ms`参数。macOS scaffold声明默认turns不限；Linux、Windows、macOS和Android平台明确72000秒单完整run。Web scripts/web/runner/run_agent.py:413–414区分：模型单请求30分钟、浏览器动作3分钟、完整agent run20小时。Web入口有`--skip-eval`用于只recreation，不需要为了采轨迹启动官方250评分。

建议沿官方单rollout20h上限与最多3完整attempts（含首次），不增加更短的默认截断；最多60h/应用、26全准入上界1560agent-hours是极端预算上界，不是耗时预测。未用完的轮次不为凑样本补跑；首轮已达预先阈值即可停止，三轮未达即保留负结果。多次工具调用、内部探索→实现→自查不是每步单算一次attempt。用户三轮约束作用于同source_family/task，不得以换版本、换宿主或多个workflow重置。

单个API不能被旧240秒传输表意外截断；继承30min正常请求边界、真实完成/错误/取消与SSE心跳证据。健康检查和外部服务轮询可短超时，不能因此杀正常模型请求或整个轨迹。基础设施失败如未进入actor前host/API联通拒绝独立登记为preflight/infra事件；已有模型执行但被打断的片段必须保留、计成本和家族尝试 ledger，不利用“基础设施重试”无限续刷。是否恢复同session、如何计入3次必须在freeze前明确，而不是运行后按分数决定。

## 下一阶段可交付证据与研究边界

每个准入task先有固定source/build/toolchain/host digest、public behavior admission、reset protocol和独立training-verifier manifest；完整attempt保存原生trajectory.jsonl/session、task请求与后续工具回执、按序截图manifest/SHA、workspace source/build.sh/launch.sh或APK/exe/应用包、原生自查/裁判反馈、exit reason、真实模型/传输使用账本和family attempt counter。agent看到的是公开请求、GUI与自己的实现，不见参考源码、benchmark gold或训练verifier源码；本轮仅研究人员静态读源，不等于授权actor照抄。

因此合理预期是最多26个完整任务家族；全26准入时26–78个完整尝试位置，否则仅采集已准入任务，以及其真实成功/失败轨迹素材；没有保证成功率、技能条数或250题增益。failed/unknown/missing artifact/transport failure分别标注，不能按高分挑轨迹或把预想skills手写为学习产物。后续AutoSkill是否抽取出技能和embedding/维护/消费效果，须在真实轨迹进入既定原生学习入口后再验收，本报告不提前宣布skills_ready。

本轮证据均为本地pinned官方源码、现存状态/metrics与只读宿主查询；未运行任何provision/setup脚本。官方文档位置：218/vendor/RecreationWorld/docs/providers/{linux,web,windows,macos,android,sandbox}.md，providers/*/README.md及scripts/{linux,windows,macos,android}/README.md。源码要点：scripts/core/agent_invocation.py，scripts/windows/stages/recreation.py，scripts/macos/runtime_assets/prepare_sandbox.sh，providers/android/run-bench.sh。以上路径均相对research/experiments；旧source/freeze/分数/失败原样保留。
