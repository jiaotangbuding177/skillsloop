# conv_40eb4affb7fd

清理版：移除空AI正文24条，合并疑似短时完全重发0条。保留原文及原始顺序冲突标记，未证明卡顿成因或修复全部回复归属。

[清理前完整原文](../../../full_063/private/conversations/conv_40eb4affb7fd.md)

原始标题：帮我安装 superpower skil

共3条保留记录：用户1、AI 2、系统／其他0。

**未发现规则可见冲突；顺序未独立核验**

- 回合仅为展示分组；连续用户发言不单独判为混乱或缺回复。


正文保持导出原样；编号、状态及来源行可回查。未核验回复归属和任务边界。


## 清理后保留顺序


### 展示回合 1


**用户** · conv_40eb4affb7fd:b016a777 · 原文件第1917行 · 状态done · 2026-05-25T21:42:23.559Z

````text
[Tue 2026-05-26 13:42 GMT+8] 帮我安装 superpower skills
````


**AI** · conv_40eb4affb7fd:f2adf0e1 · 原文件第1926行 · 状态done · 无可用消息时间

````text
找到了！**openclaw-superpowers** 是一个包含 56 个即用型技能的插件库，能让你的 AI 代理具备自主运行、自我修复和自我改进的能力。

**安装步骤：**

1. 克隆仓库到 extensions 目录
2. 运行安装脚本
3. 重启 OpenClaw

让我帮你安装：
````


**AI** · conv_40eb4affb7fd:66e0547e · 原文件第1943行 · 状态done · 无可用消息时间

````text
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
````
