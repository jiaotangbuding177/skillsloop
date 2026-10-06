#!/usr/bin/env python3
"""Build tau_retail_pool_v2 skills from the collection trajectories using the
official AutoSkill agentic-trajectory extractor (tool events included)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOSKILL = Path("/mnt/d/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill")
sys.path.insert(0, str(AUTOSKILL))

from autoskill import AutoSkill, AutoSkillConfig  # noqa: E402
from autoskill.offline.trajectory.extract import extract_from_agentic_trajectory  # noqa: E402

RELAY = os.environ.get("TAU2_RETAIL_RELAY", "http://127.0.0.1:8141")
LLM_URL = f"{RELAY}/tau2_retail/user/v1"          # DeepSeek route (kept as-is; ledger label noted)
EMBED_URL = f"{RELAY}/tau2_retail/embed/v1"       # ECNU embeddings
STORE = ROOT / "autoskill_state" / "skillbank_trajectory"
INPUT = ROOT / "autoskill_input" / "trajectories"

HINT = (
    "Retail customer-service workflows: identity lookup (name+zip / email), order checks, "
    "policy-grounded eligibility (pending vs delivered), confirmation with the customer before "
    "any write, the write itself, and the follow-up reply. Also capture failure-avoidance "
    "lessons: never fabricate order ids; never claim completion before a tool success; if "
    "identity lookup fails, ask for an alternative identifier."
)


def main() -> None:
    sdk = AutoSkill(
        AutoSkillConfig(
            llm={"provider": "generic", "model": "deepseek-flash", "base_url": LLM_URL,
                 "api_key": "local", "timeout_s": 180},
            embeddings={"provider": "generic", "model": "ecnu-embedding-small",
                        "base_url": EMBED_URL, "api_key": "local", "timeout_s": 180},
            store={"provider": "local", "path": str(STORE)},
        )
    )
    user_id = "tau_retail_pool_v2"
    files = sorted(INPUT.glob("task_*.txt"))
    processed = failed = 0
    for f in files:
        try:
            r = extract_from_agentic_trajectory(
                sdk=sdk, user_id=user_id, file_path=str(f), hint=HINT,
                include_tool_events=True, success_only=False, continue_on_error=True,
            )
            print("OK", f.name, "->", json.dumps(r, ensure_ascii=False, default=str)[:200], flush=True)
            processed += 1
        except Exception as error:  # fall back to inline data form
            try:
                r = extract_from_agentic_trajectory(
                    sdk=sdk, user_id=user_id,
                    data={"task": f.stem, "trajectory": f.read_text(encoding="utf-8")},
                    hint=HINT, include_tool_events=True, success_only=False,
                    continue_on_error=True,
                )
                print("OK(inline)", f.name, "->", json.dumps(r, ensure_ascii=False, default=str)[:200], flush=True)
                processed += 1
            except Exception as error2:
                print("FAIL", f.name, type(error).__name__, str(error)[:120],
                      "|", type(error2).__name__, str(error2)[:120], flush=True)
                failed += 1
    print(json.dumps({"processed": processed, "failed": failed, "total_files": len(files)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
