# 技能公布说明与源码可安装性核查

会话：conv_6cccc27c6040；候选：conv_6cccc27c6040:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：README宣称发布数量不等实际目录，核官方版本与目录并实测安装；仅镜像安装说明无内容不能声称安装成功，有源码的另一个候选独立安装

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 原筛选种子 · 用户

u_fce8cb0732429042e2

查一个skill，higgsfield-game-generation

## 原筛选种子 · 用户

u_88911e37015446b7ad

game-developer呢

## 原筛选种子 · 用户

u_a98bdb5e11ad64c8c4

两个都帮我装一下看看

## 原筛选种子 · 用户

u_88f6ca8528b2e31867

没事儿，先试试game-developer，告诉我杂用

## 原筛选种子 · AI

a_4307ae90cf8d7cfcd0

Higgsfield 那边官方仓库确实还没放出文件（llmbase 等镜像站也只有安装说明没有内容）。我实测一下 npx 能不能装上，同时找官方博客的 Game Studio skill 备用方案。

## 原筛选种子 · AI

a_943ad8a7ceb56dfbc7

装完了，汇报结果：

## ✅ game-developer — 装好了

- **位置**：`/workspace/skills/game-developer/`
- **内容**：SKILL.md 主文件 + 5 个 references（unity-patterns、unreal-cpp、ecs-patterns、performance-optimization、multiplayer-networking），共 54KB，来自 Jeffallan/claude-skills（11.3k stars 仓库）
- 新技能一般**下个会话/重启 gateway 后生效**，之后聊 Unity/Unreal/Godot 开发就会自动触发，也可手动 `/game-developer` 调用

## ❌ higgsfield-game-generation — 装不了，原因实锤

我做了几重验证，结论明确：**官方仓库里根本没有这个文件，只有"预告"**：
- `higgsfield-ai/skills`（当前 v0.12.0）实际只发布 8 个 skill 目录，game-generation 不在其中（README/INSTALL.md 写着"9 个技能"，但目录没推送）
- `npx skills add higgsfield-ai/skills --skill higgsfield-game-generation` 实测失败——工具只能列出那 8 个
- 第三方镜像站（llmbase/mcpservers）也只有安装说明、没有内容；官方博客的 Game Studio skill 下载链接也无法直接抓取（动态页面）

**现在想玩 Higgsfield 游戏生成，只有两条路**：
1. **网页端 Supercomputer → Games**（higgsfield.ai/games-intro）：一句话 prompt 出游戏，自动部署，无需等 skill
2. **Higgsfield MCP**：在 OpenClaw/Claude 里接 MCP connector 后生成素材+托管

官方一旦把 game-generation 目录推上线，`npx skills add higgsfield-ai/skills --skill higgsfield-game-generation` 一条命令就能装，我可以帮你盯着仓库。要我现在设个定时检查（比如每天一次），上线就通知你吗？
