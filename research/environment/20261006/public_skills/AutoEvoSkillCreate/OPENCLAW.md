# OpenClaw Use

## Skill

`AutoEvoSkillCreate`

## Purpose

Use this skill to create or improve skills with a practical five-step method: context examples, natural triggers, pass/fail evals, memory, and a skill-doctor cleanup loop.

## 中文用途

用于把重复任务、Prompt、SOP、文章方法论或已有工作流整理成可复用的 skill。它会按照五步法补齐：上下文示例、自然语言触发、评估清单、记忆沉淀和 Skill 体检机制。

## Install

Copy this whole folder into OpenClaw's skills directory.

## 中文安装说明

将整个 `AutoEvoSkillCreate` 文件夹复制到 OpenClaw 的 skills 目录中。

## Recommended Prompt

```text
Use AutoEvoSkillCreate to turn this repeated workflow into an OpenClaw skill.

Workflow or source material:
<paste content or provide path>

Target users:
<who will use the skill>

Expected output:
OpenClaw skill / Codex skill / both
```

## 中文推荐提示词

```text
使用 AutoEvoSkillCreate，把下面这个重复工作流整理成一个 skill。

工作流或来源材料：
<粘贴内容或提供路径>

目标用户：
<谁会使用这个 skill>

期望输出：
OpenClaw skill / Codex skill / 两者都要
```

## Safety

Do not invent user memory, fake examples, fake eval results, or unsupported tool permissions. Keep generated skills scoped to the user's actual workflow.

## 中文安全说明

不要编造用户记忆、伪造示例、伪造评估结果，也不要添加没有必要的工具权限。生成的 skill 应严格围绕用户真实工作流。
