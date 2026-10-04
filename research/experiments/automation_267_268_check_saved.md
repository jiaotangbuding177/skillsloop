# 定时任务存档：每30分钟巡检267/268双域实验（已于 2026-10-05 07:0x 暂停/移除）

- 原 automationId：automation-5969ec2e-5993-492f-a61a-43cbb56720f2
- 原计划：每 30 分钟（intervalUnit=minute, interval=30, cron=\"* * * * *\"），ACTIVE
- 状态：**用户要求暂停**；三域实验已全部收官（148/267/268），该巡检只剩重复确认静态完成状态。
- 恢复方法：用同内容重建自动化即可（见下 prompt）。

## 原 prompt（存档）

巡检实验 267（τ²-bench Airline × AutoSkill）与 268（Telecom）的采集/dev 进度；只读为主，必要时幂等重拉阶段循环。禁止：修改任何结果/配置文件、动 Docker、执行 wsl --shutdown、干预其他实验线进程。

1) 进度：
   wsl.exe -d Ubuntu -- bash -c \"grep 'Status:' /var/tmp/skillsloop267_collect.log | tail -1; echo ---; grep 'Status:' /var/tmp/skillsloop268_dev.log | tail -1\"
   完成数以结果文件为准（267: runs/collect/evolution.json 已完成条数/26；268: runs/dev/no_skill.json 已完成条数/4）。

2) 运行状态：
   wsl.exe -d Ubuntu -- bash -c \"ps aux | grep -E '[r]un_wrapper|[r]un_collect_loop|[r]un_dev_loop' | wc -l; curl -s --max-time 4 http://127.0.0.1:8180/health; echo; curl -s --max-time 4 http://127.0.0.1:8181/health; echo; ps -o lstart= -p 1\"
   期望：≥2 个运行进程；8180/8181 均返回 requests_reserved；PID1 启动时间不早于 2026-10-04 17:35。

3) 自愈重拉（仅当对应阶段未完成且循环进程缺失时执行；幂等）：
   - 267 采集未满 26 且无 run_collect_loop：wsl.exe -d Ubuntu -- bash -c \"cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill && setsid nohup bash scripts/run_collect_loop.sh > /var/tmp/skillsloop267_collect_loop.log 2>&1 < /dev/null &\"
   - 268 dev 未满 4 且无 run_dev_loop：wsl.exe -d Ubuntu -- bash -c \"cd /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill && setsid nohup bash scripts/run_dev_loop.sh > /var/tmp/skillsloop268_dev_loop.log 2>&1 < /dev/null &\"
   - Windows 守护缺失时重启：powershell.exe -NoProfile -Command \"Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'wsl_supervisor_267'} | Measure-Object | Select-Object -ExpandProperty Count\" 若为 0 则 Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','D:\\skillloop\\research\\experiments\\wsl_supervisor_267.ps1' -WindowStyle Hidden；268 同理（wsl_supervisor_268.ps1）。

4) 向用户汇报（中文、简短）：267 采集 n/26（含均分）；268 dev n/4；进程/中继/PID1 状态；异常：无/具体说明；某线完成时明确写\"可进入学习阶段\"。未知项不猜测、不填 0。
