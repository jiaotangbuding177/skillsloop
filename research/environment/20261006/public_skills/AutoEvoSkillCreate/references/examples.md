# Examples

## Example 1: Good Skill From a Repeated Task

Input: "I always ask the agent to turn raw experiment tables into paper-ready LaTeX analysis."

Good skill design:

- Includes examples of strong and weak experiment-analysis paragraphs.
- Triggers on natural phrases such as "analyze these results" and "write the experiment section".
- Adds pass/fail checks for invented numbers, unsupported SOTA claims, and missing negative results.
- Adds memory for real preferences such as preferred paragraph length or venue style.

Why it works: the skill captures quality criteria, not just a prompt.

## Example 2: Good Skill From an SOP

Input: "Here is our internal checklist for reviewing a manuscript."

Good skill design:

- Turns checklist items into a workflow.
- Keeps detailed criteria in references.
- Uses pass/fail evals for required report sections.
- Adds a memory policy that stores only verified user feedback.

Why it works: the skill is auditable and maintainable.

## Example 3: Good Upgrade of an Existing Skill

Input: an existing `SKILL.md` with useful instructions but no examples or evals.

Good upgrade:

- Keeps the original task boundary.
- Adds `references/examples.md`, `references/evals.md`, and `references/memory.md`.
- Improves the description with natural user phrases.
- Adds a doctor-style cleanup pass.

Why it works: it improves reliability without rewriting unrelated content.

## Bad Example

Bad skill design:

- One giant `SKILL.md` with vague rules such as "write high quality output".
- Trigger only works through a command such as `/run_skill --mode=paper`.
- No examples, no evals, and fabricated user preferences.
- Adds broad filesystem or network permissions without need.

Why it fails: the skill is hard to trigger, hard to evaluate, and unsafe to maintain.
