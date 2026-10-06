# Pass/Fail Checks

1. PASS if the generated skill has a clear task boundary; FAIL if it mixes unrelated workflows.
2. PASS if `description` includes natural user phrasing; FAIL if it depends on command-only triggers.
3. PASS if good and bad examples are included or explicitly judged unnecessary; FAIL if quality is undefined.
4. PASS if the skill has 10 pass/fail checks for common errors; FAIL if evals are vague advice.
5. PASS if memory is based only on real feedback; FAIL if user preferences are invented.
6. PASS if OpenClaw packages include `SKILL.md`, `skill.yaml`, `OPENCLAW.md`, and `security.json`; FAIL if any required file is missing.
7. PASS if references are listed in `skill.yaml`; FAIL if bundled references are undiscoverable.
8. PASS if permissions are minimal; FAIL if broad shell, network, or filesystem access is added without need.
9. PASS if duplicated or stale instructions are removed; FAIL if the skill keeps conflicting rules.
10. PASS if final response reports files, five-step coverage, and validation; FAIL if it only says the skill was created.
