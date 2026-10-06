#!/usr/bin/env python3
"""Build AutoSkill trajectory input from the collection results, TOOL EVENTS KEPT.

Learner-visible only: user utterances, assistant public text, native tool calls
and their official environment results (including errors). Hidden simulator
notes / evaluator gold never appear. One text record per task plus a manifest.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs" / "collect" / "evolution.json"
OUT_DIR = ROOT / "autoskill_input" / "trajectories"


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    sims = data.get("simulations", [])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    order = []
    for sim in sims:
        task_id = sim.get("task_id")
        lines = []
        for message in sim.get("messages", []):
            role = message.get("role")
            content = (message.get("content") or "").strip()
            if role == "user" and content:
                lines.append(f"USER: {content}")
            elif role == "assistant":
                if content:
                    lines.append(f"AGENT: {content}")
                for call in message.get("tool_calls") or []:
                    lines.append(
                        "AGENT_TOOL_CALL: "
                        + json.dumps(
                            {"name": call.get("name"), "arguments": call.get("arguments")},
                            ensure_ascii=False,
                        )
                    )
            elif role == "tool":
                tag = "TOOL_RESULT_ERROR" if message.get("error") else "TOOL_RESULT"
                body = (message.get("content") or "")[:4000]
                lines.append(f"{tag}: {body}")
        text = "\n".join(lines)
        safe = (re.sub(r"[^A-Za-z0-9_.\-]", "_", str(task_id))[:100]
                + "_" + hashlib.sha1(str(task_id).encode()).hexdigest()[:6])
        (OUT_DIR / f"task_{safe}.txt").write_text(text, encoding="utf-8")
        order.append(
            {
                "task_id": task_id,
                "termination": sim.get("termination_reason"),
                "reward": (sim.get("reward_info") or {}).get("reward"),
                "chars": len(text),
            }
        )
    (OUT_DIR / "manifest.json").write_text(
        json.dumps({"source": str(SOURCE), "records": order}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(order)} trajectory records to {OUT_DIR}")


if __name__ == "__main__":
    main()
