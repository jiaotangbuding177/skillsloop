# 第299轮：用户停止RW监控和相关进程

日期：2026-10-05，北京时间17:05—17:08。接续读取README、CHARTER、STATE及[298记忆](298_2026-10-05_rw_monitor_healthy_collection_idle.md)。

## 用户已确认要求与当前边界

用户明确“先停止吧，监控和进程都停止”。已停止当前RecreationBench工作及半小时监控，禁止自动恢复、新启动参考准备/采集/模型调用或后续学习评测；等待用户明确恢复。其他聊天的Co-Gym/三域工作不属于本次停止对象，未操作其进程或公共WSL/Docker服务。旧三轮上限、corravale STOP、所有历史评分与负结果保持。

## 证据支持的执行与验收

- Windows计划任务`Skillloop-RecreationBench-30min`已Disable并请求Stop；[Windows实核](../monitoring/recreationbench/299_windows_stop_verification.json)于17:07:51确认Disabled、enabled=false、残留巡检PowerShell进程0。任务定义保留、不删除；末次运行16:58:15为停用前历史，不能当继续调度。
- 采集worker/supervisor/observer已在此前自然结束。实际发现两条仍活跃的RW专用relay：285 PID46842/start_ticks828303/8190，288 PID84417/start_ticks1319647/8193，同boot255b5570-fab4-46e1-a9ff-c307b0bbb76a。逐一校验boot/PID/start_ticks及完整script路径后SIGTERM停止，均未需SIGKILL；身份不再存活、两端口均关闭。
- 唯一仍运行RW容器`rw285-minipaint-admission`，完整container_id及image_id与原runtime_identity匹配后docker stop，现exited、不删除。已有agent/build容器此前已退出，未重跑或更改其结果。
- 在285、288、293三个collection的`private/STOP`创建用户停用标记，原worker/supervisor已有该门禁；没有热改任何冻结执行文件。停止动作见[299_stop_execution.json](../monitoring/recreationbench/299_stop_execution.json)。
- [独立Linux/Docker复核](../monitoring/recreationbench/299_linux_stop_verification.json)：RW归属的脚本进程剩余0、运行中的RW候选容器0。没有全局kill、WSL shutdown或Docker服务停用，未影响其他实验。

## 研究状态与产物保留

本轮无新增效果实证发现。停在2/26应用准入、两应用共6正式执行结束/成功0；miniPaint最后0.4228、Squoosh0.5246，Vite参考构建成功但GUI/verifier未准入。RW技能学习与250正式评测未启动。

所有raw轨迹、评分、日志、checkpoint、freeze、参考构建产物和监控快照完整保留，没有删除数据或覆盖旧失败。监控脚本和任务配置只作为停用后的历史产物，不自动启动。下一步为等待用户明确恢复；恢复时先读研究记忆、核对STOP和身份，并保持三轮预算不可重置。
