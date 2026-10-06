"""Register the OpenClaw retail agent with tau2 and drive experiment runs.

Usage (WSL venv, from the experiment root):
  runtime_py/bin/python scripts/run_wrapper.py --phase dev --group no_skill \
      --tasks dev --num-trials 1 --result runs/dev/no_skill.json
  runtime_py/bin/python scripts/run_wrapper.py --phase collect \
      --tasks evolution --num-trials 1 --result runs/collect/no_skill.json
  runtime_py/bin/python scripts/run_wrapper.py --phase evaluate \
      --group autoskill_library --tasks test --num-trials 4 \
      --result runs/test/autoskill_library.json

Recorded adaptations (see source_audit.md):
  * NL-assertions judge replaced via TAU2_RETAIL_JUDGE_MODEL / _BASE before
    tau2.evaluator is imported (offline resource), per-call api_base/api_key;
  * user simulator model comes from TAU2_RETAIL_USER_MODEL / _BASE;
  * agent factory 'openclaw_retail' registered from scripts/tau2_openclaw_agent.py.

No vendor file is modified: all patches are runtime, in this process.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# --- runtime adaptations must happen before tau2.evaluator is imported -----
import tau2.config as tau2_config  # noqa: E402

JUDGE_MODEL = os.environ.get("TAU2_RETAIL_JUDGE_MODEL", "openai/glm-4-flash")
JUDGE_BASE = os.environ.get(
    "TAU2_RETAIL_JUDGE_BASE", "http://127.0.0.1:8141/tau2_retail/judge/v1"
)
tau2_config.DEFAULT_LLM_NL_ASSERTIONS = JUDGE_MODEL
tau2_config.DEFAULT_LLM_NL_ASSERTIONS_ARGS = {
    "temperature": 0.0,
    "api_base": JUDGE_BASE,
    "api_key": "local",
}

from tau2.registry import registry  # noqa: E402
from tau2.runner import get_tasks, run_tasks  # noqa: E402
from tau2.data_model.simulation import TextRunConfig  # noqa: E402
from tau2_openclaw_agent import create_openclaw_retail_agent  # noqa: E402


# --- all-roles judge override ---------------------------------------------
# tau2/__init__ imports the evaluator before this module can patch
# tau2.config, so the constants already bound inside evaluator modules must be
# overridden too; otherwise NL-assertion judging calls the official default
# model with no credentials (observed 2026-10-02 on tasks with nl_assertions).
JUDGE_ARGS = dict(tau2_config.DEFAULT_LLM_NL_ASSERTIONS_ARGS)
for _module in list(sys.modules.values()):
    for _attr, _value in (
        ("DEFAULT_LLM_NL_ASSERTIONS", JUDGE_MODEL),
        ("DEFAULT_LLM_ENV_INTERFACE", JUDGE_MODEL),
        ("DEFAULT_LLM_NL_ASSERTIONS_ARGS", JUDGE_ARGS),
        ("DEFAULT_LLM_ENV_INTERFACE_ARGS", JUDGE_ARGS),
    ):
        if hasattr(_module, _attr):
            setattr(_module, _attr, dict(_value) if _attr.endswith("ARGS") else _value)


# --- robust NL-assertions judge -------------------------------------------
# The judge model occasionally returns empty content; a JSONDecodeError in the
# vendor evaluator aborts the whole simulation and triggers tau2's task-level
# retry (observed 2026-10-02: tasks 2/3/4 marked infrastructure_error). Retry
# the judge call in place instead.
try:
    import json as _json

    from tau2.evaluator import evaluator_nl_assertions as _nl_ev

    _orig_nl_reward = _nl_ev.NLAssertionsEvaluator.calculate_reward.__func__

    def _robust_nl_reward(cls, *args, **kwargs):
        last_error = None
        for _attempt in range(6):
            try:
                return _orig_nl_reward(cls, *args, **kwargs)
            except _json.JSONDecodeError as error:  # empty / invalid judge output
                last_error = error
        raise last_error

    _nl_ev.NLAssertionsEvaluator.calculate_reward = classmethod(_robust_nl_reward)
    print("judge retry wrapper active")
except Exception as _patch_error:  # never break the run because of the patch
    print("judge retry wrapper not installed:", _patch_error)


# --- fence-strip judge normalization --------------------------------------
# glm-4-flash wraps the judge verdict in a ```json markdown fence (captured raw
# in ledger/judge_raw on 2026-10-03, content non-empty, finish_reason=stop);
# the vendor judge does a bare json.loads(content) and cannot parse a fence.
# Normalize the fence before parsing (format-only; raw replies stay archived).
try:
    import re as _re

    from tau2.evaluator import evaluator_nl_assertions as _nl_ev2

    _orig_generate = _nl_ev2.generate

    def _fence_strip_generate(*args, **kwargs):
        message = _orig_generate(*args, **kwargs)
        content = getattr(message, "content", None) or ""
        if "```" in content:
            match = _re.search(r"```(?:json)?\s*(.*?)```", content, _re.S)
            if match:
                stripped = match.group(1).strip()
                try:
                    message.content = stripped
                except Exception:
                    if hasattr(message, "model_copy"):
                        message = message.model_copy(update={"content": stripped})
        return message

    _nl_ev2.generate = _fence_strip_generate
    print("judge fence-strip normalization active")
except Exception as _patch_error:
    print("judge fence-strip not installed:", _patch_error)

AGENT_NAME = "openclaw_retail"
DOMAIN = os.environ.get("TAU2_RETAIL_DOMAIN", "telecom")


def register_agent() -> None:
    if registry.get_agent_factory(AGENT_NAME) is None:
        registry.register_agent_factory(create_openclaw_retail_agent, AGENT_NAME)


def load_split_ids() -> dict:
    manifest = json.loads((ROOT / "split_manifest.json").read_text(encoding="utf-8"))
    return {
        "dev": manifest["dev_selection"]["dev_ids"],
        "evolution": manifest["evolution_ids"],
        "test": manifest["test_ids"],
    }


def select_task_ids(selection: str) -> list[str]:
    splits = load_split_ids()
    if selection in splits:
        return [str(i) for i in splits[selection]]
    return [part.strip() for part in selection.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["dev", "collect", "evaluate"], required=True)
    parser.add_argument("--group", choices=["no_skill", "autoskill_library"], required=True)
    parser.add_argument("--tasks", default=None, help="dev|evolution|test|comma-separated ids")
    parser.add_argument("--num-trials", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--result", required=True, help="results JSON path")
    parser.add_argument("--dry-run", action="store_true", help="build env+agent, no simulation")
    args = parser.parse_args()

    task_ids = select_task_ids(args.tasks or ("test" if args.phase == "evaluate" else "evolution"))
    num_trials = args.num_trials if args.num_trials is not None else (4 if args.phase == "evaluate" else 1)

    os.environ["TAU2_RETAIL_GROUP"] = args.group
    os.environ.setdefault("TAU2_RETAIL_RUN_ROOT", str(ROOT / "runs"))
    if args.group == "autoskill_library":
        frozen = Path(os.environ.get("TAU2_RETAIL_FROZEN_DIR", str(ROOT / "frozen_skills")))
        if not frozen.exists():
            raise SystemExit("frozen_skills/ does not exist; refusing B1 before freeze")
        os.environ["TAU2_RETAIL_SKILLS_DIR"] = str(frozen)
    else:
        os.environ.pop("TAU2_RETAIL_SKILLS_DIR", None)

    register_agent()

    tasks = get_tasks(DOMAIN)
    tasks_by_id = {str(t.id): t for t in tasks}
    missing = [i for i in task_ids if i not in tasks_by_id]
    if missing:
        raise SystemExit(f"unknown task ids: {missing}")
    selected = [tasks_by_id[i] for i in task_ids]

    user_model = os.environ.get("TAU2_RETAIL_USER_MODEL", "openai/glm-4-flash")
    user_base = os.environ.get(
        "TAU2_RETAIL_USER_BASE", "http://127.0.0.1:8141/tau2_retail/user/v1"
    )
    config = TextRunConfig(
        domain=DOMAIN,
        agent=AGENT_NAME,
        llm_agent=user_model,  # bookkeeping only; the adapter drives OpenClaw
        llm_args_agent={"temperature": 0.0},
        user="user_simulator",
        llm_user=user_model,
        llm_args_user={"temperature": 0.0, "api_base": user_base, "api_key": "local"},
        num_trials=num_trials,
        max_steps=200,
        max_errors=10,
        max_retries=3,
        retry_delay=1.0,
        timeout=None,  # v2: no wallclock cutoff; bounded by max_steps=200 and per-turn guards
        seed=args.seed,
        task_ids=task_ids,
        auto_resume=True,
        max_concurrency=args.concurrency,
    )

    if args.dry_run:
        from tau2.runner import build_agent, build_environment

        environment = build_environment(DOMAIN)
        agent = build_agent(AGENT_NAME, environment, llm=user_model, llm_args={}, task=selected[0])
        state = agent.get_init_state()
        print(json.dumps({
            "dry_run": True,
            "domain": DOMAIN,
            "tasks": len(selected),
            "tools": len(environment.get_tools()),
            "session_dir": str(state.session_dir),
            "skills_dir": os.environ.get("TAU2_RETAIL_SKILLS_DIR"),
        }, indent=2))
        agent.stop()
        return

    result_path = Path(args.result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    run_tasks(
        config,
        selected,
        save_path=result_path,
        save_dir=result_path.parent / (result_path.stem + "_sims"),
        console_display=True,
    )
    print(f"results written to {result_path}")


if __name__ == "__main__":
    main()
