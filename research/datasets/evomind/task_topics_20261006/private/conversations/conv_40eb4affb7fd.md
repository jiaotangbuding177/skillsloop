# conv_40eb4affb7fd

会话主主题：助手配置与技能管理；状态：暂存待补证
其他主题：无

说明：下面保留来源正文展示次序；内容对应关系另存，不据此保证真实时间顺序。

## 用户 · u_c107f69e98e83e5401

帮我安装 superpower skills

## AI · a_19f7249f3409514420

找到了！**openclaw-superpowers** 是一个包含 56 个即用型技能的插件库，能让你的 AI 代理具备自主运行、自我修复和自我改进的能力。

**安装步骤：**

1. 克隆仓库到 extensions 目录
2. 运行安装脚本
3. 重启 OpenClaw

让我帮你安装：

## AI · a_d87a0b0e652952addc

✅ **openclaw-superpowers 安装完成！**

## 已安装内容

| 项目 | 数量 |
|------|------|
| 技能总数 | 56 个 |
| └─ Core 核心技能 | 17 个 |
| └─ OpenClaw-Native 技能 | 38 个 |
| └─ Community 社区技能 | 1 个 |
| 状态目录 | 38 个 |
| Cron 定时任务 | 18 个 |

## 技能亮点

**核心技能**：`using-superpowers`, `brainstorming`, `create-skill`, `systematic-debugging`, `skill-vetting` 等

**自主运行技能**：
- `long-running-ta***KEY***` — 每 15 分钟检查长任务进度
- `morning-briefing` — 工作日早 7 点每日简报
- `daily-review` — 工作日下午 6 点每日总结
- `memory-dag-compactor` — 每晚 11 点记忆压缩
- `spend-circuit-breaker` — 每 4 小时 API 预算检查
- `community-skill-radar` — 每 3 天扫描社区新技能

**安全技能**：
- `prompt-injection-guard` — 提示注入检测
- `dangerous-action-guard` — 危险操作确认
- `secrets-hygiene` — 凭证审计
- `config-encryption-auditor` — 配置加密检查

## ⚠️ 最后一步：重启 OpenClaw

由于我在沙盒环境中无法直接重启 Gateway，请你在主机上执行：

```bash
openclaw gateway restart
```

重启后，再运行：

```bash
cd ~/.openclaw/extensions/openclaw-superpowers && ./register-cron-jobs.sh
```

这将注册所有 18 个定时任务。

## 验证安装

重启后，在新会话中输入：
> "使用 superpowers 技能"

或者检查技能列表：
```bash
openclaw skills list --eligible
```

安装位置：`~/.openclaw/extensions/superpowers`

需要我帮你做什么吗？🦎
