#!/usr/bin/env python3
"""Build the tau_retail_pool skill library with the official AutoSkill offline
conversation path, using the experiment relay for LLM and embeddings."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOSKILL = Path("/mnt/d/skillloop/research/experiments/115_cogym_spagent_full/vendor/AutoSkill")
sys.path.insert(0, str(AUTOSKILL))

from autoskill import AutoSkill, AutoSkillConfig  # noqa: E402

RELAY = os.environ.get("TAU2_RETAIL_RELAY", "http://127.0.0.1:8141")
LLM_URL = f"{RELAY}/tau2_retail/autoskill/v1"
EMBED_URL = f"{RELAY}/tau2_retail/embed/v1"
STORE = ROOT / "autoskill_state" / "skillbank"
INPUT = ROOT / "autoskill_input" / "tau_retail_pool.jsonl"

def main() -> None:
    sdk = AutoSkill(
        AutoSkillConfig(
            llm={
                "provider": "generic",
                "model": "glm-4-flash",
                "base_url": LLM_URL,
                "api_key": "local",
                "timeout_s": 180,
            },
            embeddings={
                "provider": "generic",
                "model": "ecnu-embedding-small",
                "base_url": EMBED_URL,
                "api_key": "local",
                "timeout_s": 180,
            },
            store={"provider": "local", "path": str(STORE)},
        )
    )
    result = sdk.import_openai_conversations(
        user_id="tau_retail_pool",
        file_path=str(INPUT),
        hint=(
            "Focus on reusable retail customer-service procedures: identity lookup, "
            "order checks, policy-grounded eligibility, confirming with the customer, "
            "and only then performing the business write."
        ),
        continue_on_error=True,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

if __name__ == "__main__":
    main()
