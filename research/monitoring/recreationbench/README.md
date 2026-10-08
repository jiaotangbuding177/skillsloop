# RecreationBench每30分钟本机进度巡检

**当前已停用（2026-10-05 17:07）：** 用户要求监控和进程全部停止，任务Disabled/enabled=false、残留巡检进程0；相关RW专用relay/参考容器也已停止，collection private/STOP已写。等待用户明确恢复，不执行下面历史启动命令。[停用记忆](../../memory/299_2026-10-05_rw_user_stop_monitor_and_processes.md)、[Windows实核](299_windows_stop_verification.json)、[进程/容器复核](299_linux_stop_verification.json)。下文为建立时配置与历史，不表示继续监控。

2026-10-05用户要求设置。原生Codex automation_update不在当前会话可调用工具清单中，未声称创建Codex聊天heartbeat；采用Windows计划任务本地回退。

- 任务名称：`Skillloop-RecreationBench-30min`，当前用户交互登录、有限权限、隐藏窗口；每30分钟、实例重叠忽略、单次最多5分钟。
- 首次计划任务真实执行：2026-10-05 11:28:14，LastTaskResult=0；首次预定下一次11:58:13。配置见[task.xml](task.xml)。无需更改电源设置，电脑关机或用户未登录时不能保证按时运行，StartWhenAvailable可补检查。
- 只读观察`research/experiments/*_rw_*collection`中的状态、准入与评分文件；按boot/PID/start_ticks实查记录的controller以及容器状态。没有启动actor、调用模型、评分、终止/恢复任务或修改freeze，不追加第四轮。
- 每次写`snapshot_<时间>.json`和[latest.json](latest.json)。文件/状态变化或巡检错误写`changes.jsonl`，无变化只留快照。属于机械本地变化检测，不能单凭hash判断效果或成功；时间字段变化也可能改变hash。
- 目前没有自动回发当前聊天或推送通知的能力。此任务不是自动推进下一应用的监督器，Vite GUI/verifier仍待人工科研工作接续。计划任务是否触发不等于采集推进。
- 初次手动预演因WSL stderr警告被PowerShell当错误而退出；原错误快照保留。已改为独立元数据probe、捕获stderr/直接exec，第二次预演及首次计划任务均0错误/退出0。旧Squoosh首轮OOMKilled=true为历史容器事实，不当新故障。

查看配置及下一次：`Get-ScheduledTaskInfo -TaskName 'Skillloop-RecreationBench-30min'`；手动检查：`Start-ScheduledTask -TaskName 'Skillloop-RecreationBench-30min'`；停用：`Disable-ScheduledTask -TaskName 'Skillloop-RecreationBench-30min'`。只读巡检可继续覆盖后续新collection目录；用户主动暂停或完成26应用采集后应停用。

参考：[官方定时任务说明](https://learn.chatgpt.com/docs/automations?surface=app)描述本地项目运行条件；本Windows回退实现来自本机任务配置与实际执行证据，不声称官方自动注册Codex聊天任务。
