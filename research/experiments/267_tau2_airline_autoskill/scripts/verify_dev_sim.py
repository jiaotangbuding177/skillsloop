"""Quick quality check of the 267 dev sims."""
import json
from pathlib import Path

p = Path("/mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/runs/dev/no_skill.json")
d = json.loads(p.read_text())
for s in d["simulations"]:
    msgs = s["messages"]
    tool_calls = sum(len(m.get("tool_calls") or []) for m in msgs if m.get("role") == "assistant")
    user_turns = sum(1 for m in msgs if m.get("role") == "user")
    r = s.get("reward_info") or {}
    print("task", s["task_id"], "dur=%.0fs" % s.get("duration", 0), "user_turns=", user_turns,
          "tool_calls=", tool_calls, "term=", s.get("termination_reason"))
    print("   reward=", r.get("reward"), "db=", (r.get("db_check") or {}).get("db_match"),
          "communicate=", (r.get("reward_breakdown") or {}).get("COMMUNICATE"))
