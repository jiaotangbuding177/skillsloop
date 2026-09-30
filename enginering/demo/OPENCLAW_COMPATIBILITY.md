# OpenClaw Windows 兼容适配（024）

固定版本：OpenClaw 2026.9.5、Node 26.1.0。仅作用于 demo 私有 `.runtime`，不修改全局安装。

## 实际故障与修复

`agent exec` 的 one-shot 生命周期要求 exec 子进程具有可验证的进程树清理回执。此版本的普通 Windows child adapter 没有响应 `ownProcessTree`，导致 Python 命令已执行成功，整个 agent 最终仍返回 `process cleanup cannot confirm owned execution-tree settlement`。

`scripts/patch_openclaw_windows.py` 将这类非交互命令接到 OpenClaw 已自带的 Windows Job Object relay，继续等待真实的树清理承诺；参数以 Base64 编码的数据传入中间 Node 进程，避免把 argv 再拼成用户 shell 语句。明确不支持交互 stdin 和秘密输入通道。

原生 relay 还有一个可复现的关闭竞争：root 已退出，supervisor 请求清理时，anchor 恰好关闭 IPC，产生 EPIPE。适配只在已收到 root-result 的 Windows 分支启动有限清理等待；仍必须收到 closing 回执且 anchor 已退出，否则原有清理失败逻辑继续生效。没有把清理错误统一忽略，没有把原来的失败结果改为成功。

安装脚本自动应用适配。补丁校验原始文件 SHA256、保存原件、验证唯一替换位置，拒绝不认识的版本或额外改动。运行时的临时诊断日志修改已撤销。原始失败保留于 `artifacts/diagnosis-024`、`artifacts/a024` 和 `artifacts/a024b`。

## 复核

```powershell
python scripts/patch_openclaw_windows.py
& .runtime/node-v26.1.0-win-x64/node.exe scripts/check_windows_process.mjs
```

无模型、无网络的检查覆盖中文/引号参数、非零退出、嵌套进程，以及通过真实 supervisor 管理的 PowerShell 成功和失败。`extinction: settled` 表示原生清理承诺已正常完成，不由测试直接赋予运行成功。

Python 适配层关闭 CLI 自动重启，并保留官方 Windows stack-size 参数；超时只清理本次创建的进程树，保存 UNKNOWN，不自动重复任务。设置 `DEMO_NETWORK_MODE=direct` 时只为该 OpenClaw 子进程移除代理变量；默认继承系统网络配置。

该适配解决本地 demo 执行条件，不是论文算法贡献，也不意味着其他平台或后续 OpenClaw 版本已验证。
