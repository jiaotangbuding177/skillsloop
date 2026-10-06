# conv_b3d8a26f0bb3

会话主主题：助手配置与技能管理；状态：保留学习候选
其他主题：无

说明：下面保留来源正文展示次序；内容对应关系另存，不据此保证真实时间顺序。

## 用户 · u_91312f35645be4f74e

请安装 skill「健身教练」到个人工作区 skills 目录（workspace/skills）：优先平台技能库与市场，没有再从 ClawdHub 或者 GitHub 下载安装

## AI · a_b69d49dabbbfbb5455

收到，我先查看工作区 skills 目录和 skill-creator 技能文件，然后搜索「健身教练」技能的来源。

## AI · a_68a51595385b74e194

skill-creator 的正文已注入，我直接按步骤执行。当前 skills 目录里没有「健身教练」，接下来先检查平台技能市场入口，再搜索 ClawdHub 和 GitHub。

## AI · a_9174692303dac723dc

找到了！ClawHub 社区有一个现成的中文技能 **"AI Fitness Coach (CN)"**（AI健身教练助手），GitHub 上也有镜像仓库 `dvcrn/openclaw-skills-marketplace`。平台技能市场（sim-market 仅为模拟测试用）没有该技能，我从 ClawHub/GitHub 获取。先看仓库结构：

## AI · a_8692a83f318baf3785

技能只有一个 SKILL.md 文件，结构很干净。下载并检查内容：

## AI · a_9ace6b474e2b58d831

下载成功（396 行）。查看完整内容，然后按 EvoMind 个人技能规范调整（中文名称、市场信息部分）：

## AI · a_eabeab4179e48ef4e1

内容质量不错，但需要按 EvoMind 个人技能规范改造：① frontmatter name 改为中文「健身教练」；② 补全触发描述；③ 删除定价/营销等无关内容；④ 末尾补上必填的「市场信息」部分。现在重写：

## AI · a_323e3a714c4cd6e49d

写入完成。现在用 skill-creator 的校验脚本验证：

## AI · a_99afde0c568e19c6d4

脚本不在预期位置，查找一下：

## AI · a_ce27f87c5e8038d456

脚本未同步到 sandbox（注入说明中已注明以工作区文件树与正文为准），我按 SKILL.md 正文规范手工校验：

## AI · a_ab90584d0c1cdea5f5

校验全部通过。提交到工作区 git：

## AI · a_6d2bff8aa3cfd53ce2

✅ 技能「健身教练」安装完成！

**安装来源**
- 平台技能库/市场：未找到该技能（工作区内的 sim-market 仅为测试模拟，非真实市场）
- 已从 **ClawHub 社区**（GitHub 镜像仓库 `dvcrn/openclaw-skills-marketplace`）获取到现成的中文技能 **"AI Fitness Coach (CN)"**，下载后按 EvoMind 个人技能规范改造安装

**安装位置**
`workspace/skills/ai-fitness-coach-cn/SKILL.md`（已在「我的技能」中可被发现）

**规范化改造内容**
- frontmatter `name` 改为中文显示名「健身教练」，`description` 补全触发场景（训练计划、动作指导、饮食方案、减脂增肌、进度追踪等）
- 删除原作者的定价方案与营销文案等无关内容
- 补充了明确的**工作流程指令**（收集信息 → 数据分析 → 生成方案 → 动作指导 → 进度追踪）
- 按规范在文末补全必填的 **「市场信息」** 部分：适合人群、核心亮点、典型输入/需求、输入预填模板、预期输出/成果
- 校验通过：frontmatter 完整、5 个市场字段齐全非空、共 233 行（<500 行规范），目录仅含 SKILL.md 无冗余文件

**技能能力一览**：个性化训练计划（减脂/增肌/塑形/体能）、动作要领详解（含常见错误与替代动作）、每日营养目标与可选食谱、8 周进度追踪报告，并带安全提醒。

现在你可以直接说「帮我制定一份减脂训练计划」来使用它了 💪
