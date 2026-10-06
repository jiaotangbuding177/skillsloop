---
name: AutoEvoSkillCreate
description: OpenClaw-compatible skill for creating or upgrading skills with a five-step method: add good/bad examples as context, write natural-language triggers, add pass/fail evals, add memory for real feedback, and use a skill-doctor loop to remove stale, vague, duplicate, or AI-like instructions. Use when the user asks to create a new skill, improve an existing skill, turn a repeated workflow into a skill, or standardize a team's skill-building process.
---

# AutoEvoSkillCreate

Use this skill to create new skills or upgrade existing skills into reusable, maintainable capabilities.

## Trigger

Use when the user asks to:

- create a skill from a repeated workflow;
- improve an existing skill;
- convert prompts, SOPs, articles, or examples into a skill;
- add examples, evals, memory, or trigger descriptions to skills;
- build a reusable skill system for a person, team, or organization.

## Five-Step Method

### Step 1: Give Context

Define what good output looks like before writing rules.

Add:

- 3 good examples;
- 1 bad example;
- a short explanation of why the good examples work and why the bad example fails.

Put these in `references/examples.md` when the skill is more than a tiny one-file instruction.

### Step 2: Simplify Triggering

Make the skill trigger from natural user language.

Use this description pattern:

```text
Use when the user wants to <do this task>, especially when they mention <common natural phrases>, <target artifacts>, or <workflow contexts>.
```

Avoid command-only triggers such as `/skill_name --flag=value`.

### Step 3: Add Evals

Add 10 concrete pass/fail checks for common output errors.

Put them in `references/evals.md`. Each check should be objective enough that an agent can inspect the output and decide pass or fail.

### Step 4: Add Memory

Add `references/memory.md` to record one-sentence learnings from real user feedback.

Do not invent memory. If there is no history yet, write:

```text
- No stored preference yet.
```

### Step 5: Add a Skill-Doctor Loop

Create or use a maintenance skill to periodically inspect the skill for:

- duplicate rules;
- stale instructions;
- vague words such as "appropriate", "usually", or "high quality" without criteria;
- contradictions between `SKILL.md`, `OPENCLAW.md`, references, and metadata;
- AI-like filler or over-explaining.

For this repository, use `paper-skill-doctor` for paper-writing skills or adapt the same pattern for other domains.

## Output Package

For OpenClaw-compatible skills, create:

```text
<skill-name>/
  SKILL.md
  skill.yaml
  OPENCLAW.md
  security.json
  references/
    examples.md
    evals.md
    memory.md
```

For Codex-compatible skills, `SKILL.md` is required; references are optional but recommended for non-trivial skills.

## Final Response

When creating or improving a skill, report:

```text
Part 1 [Created or Updated Files]
<file list>

Part 2 [Five-Step Coverage]
Context examples: yes/no
Natural trigger: yes/no
Pass/fail evals: yes/no
Memory: yes/no
Skill-doctor loop: yes/no

Part 3 [Validation]
<what was checked>
```
