# AutoEvoSkillCreate

AutoEvoSkillCreate is an OpenClaw-compatible skill for creating and upgrading reusable skills with a practical five-step method. It turns repeated workflows, prompts, SOPs, article methods, or existing agent routines into maintainable skill packages.

### Inspiration

This skill is inspired by Peter Yang's discussion of a practical five-step approach to creating reusable AI skills. The implementation here adapts that idea into an OpenClaw-compatible skill package for repeatable, auditable skill creation.

### 5-Step Skill Create Method

1. **Give context**: add good and bad examples so the agent knows what quality looks like.
2. **Simplify triggering**: write natural-language trigger descriptions instead of command-only usage.
3. **Add evals**: define 10 pass/fail checks for common output errors.
4. **Add memory**: record one-sentence learnings from real user feedback.
5. **Add a skill-doctor loop**: periodically remove stale, vague, duplicate, or AI-like instructions.

### Package Structure

```text
SKILL.md
skill.yaml
OPENCLAW.md
security.json
references/
  examples.md
  evals.md
  memory-policy.md
```

### Recommended Prompt

```text
Use AutoEvoSkillCreate to turn this repeated workflow into an OpenClaw skill.

Workflow or source material:
<paste content or provide path>

Target users:
<who will use the skill>

Expected output:
OpenClaw skill / Codex skill / both
```

### What It Produces

The skill helps generate or improve a skill package with:

- clear scope and trigger description;
- good and bad examples;
- objective pass/fail evals;
- a memory policy based only on real feedback;
- minimal permissions and security notes;
- a final validation summary.

AutoEvoSkillCreate 是一个兼容 OpenClaw 的 skill，用于通过实用的“五步法”创建和升级可复用 skill。它可以把重复工作流、Prompt、SOP、文章方法论或已有 agent 流程整理成可维护的 skill 包。

### 灵感来源

这个 skill 的方法灵感来自 Roblox 产品经理 Peter Yang 关于如何创建可复用 AI Skills 的五步法讲解。本仓库在这个思路基础上，将其整理成一个兼容 OpenClaw 的 skill 包，用于可重复、可评估、可维护地创建 skills。

### 5 步 Skill 创建法

1. **给上下文**：加入好示例和坏示例，让 agent 知道什么叫高质量输出。
2. **简化触发**：使用自然语言触发描述，而不是只依赖命令式调用。
3. **加评估**：定义 10 条 pass/fail 检查项，用来捕捉常见输出错误。
4. **加记忆**：只记录来自真实用户反馈的一句话经验。
5. **加 Skill 体检循环**：定期清理过时、模糊、重复或 AI 味过重的说明。

### 包结构

```text
SKILL.md
skill.yaml
OPENCLAW.md
security.json
references/
  examples.md
  evals.md
  memory-policy.md
```

### 推荐提示词

```text
使用 AutoEvoSkillCreate，把下面这个重复工作流整理成一个 skill。

工作流或来源材料：
<粘贴内容或提供路径>

目标用户：
<谁会使用这个 skill>

期望输出：
OpenClaw skill / Codex skill / 两者都要
```

### 它会产出什么

这个 skill 会帮助生成或改进一个 skill 包，包括：

- 清晰的任务边界和触发描述；
- 好示例和坏示例；
- 客观的 pass/fail 评估清单；
- 只基于真实反馈的 memory 策略；
- 最小必要权限和安全说明；
- 最终验证摘要。
