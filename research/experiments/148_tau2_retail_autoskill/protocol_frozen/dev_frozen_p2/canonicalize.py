#!/usr/bin/env python3
"""Build the AutoSkill learning input from the collection results.

Learner-visible only: user utterances (primary evidence) and assistant public
text (context). Tool calls / tool results / errors are agent-visible state
changes and are kept in a SEPARATE reference view (canonical/evolve/) for
audit; they are never dressed up as user speech. Hidden simulator
instructions and evaluator data are not read at all.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "collect" / "evolution.json"


def qr_view(sim: dict) -> list[dict]:
    """OpenAI-format conversation: user / assistant text only."""
    messages = []
    for message in sim.get("messages", []):
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    return messages


def reference_view(sim: dict) -> list[dict]:
    """Tool-augmented view for audits (assistant-side artifacts only)."""
    out = []
    for message in sim.get("messages", []):
        role = message.get("role")
        if role == "assistant":
            text = (message.get("content") or "").strip()
            if text:
                out.append({"role": "assistant", "content": text})
            for call in message.get("tool_calls") or []:
                out.append(
                    {
                        "role": "assistant",
                        "content": "[tool_call] {} {}".format(
                            call.get("name"),
                            json.dumps(call.get("arguments"), ensure_ascii=False),
                        ),
                    }
                )
        elif role == "tool":
            out.append(
                {
                    "role": "assistant",
                    "content": "[tool_result error={}] {}".format(
                        bool(message.get("error")), message.get("content")
                    ),
                }
            )
        elif role == "user" and (message.get("content") or "").strip():
            out.append({"role": "user", "content": message["content"]})
    return out


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    sims = data.get("simulations", [])
    input_dir = ROOT / "autoskill_input"
    input_dir.mkdir(exist_ok=True)
    reference_dir = ROOT / "canonical" / "evolve"
    reference_dir.mkdir(parents=True, exist_ok=True)

    order, skipped = [], []
    with (input_dir / "tau_retail_pool.jsonl").open("w", encoding="utf-8") as handle:
        for sim in sims:
            task_id = sim.get("task_id")
            messages = qr_view(sim)
            if not any(m["role"] == "user" for m in messages):
                skipped.append(task_id)
                continue
            handle.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            order.append(task_id)
            (reference_dir / f"task_{task_id}.json").write_text(
                json.dumps(
                    {
                        "task_id": task_id,
                        "termination": sim.get("termination_reason"),
                        "messages": reference_view(sim),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    manifest = {
        "source": "runs/collect/evolution.json",
        "conversations": len(order),
        "skipped_no_user": skipped,
        "line_to_task_id": order,
        "format": "JSONL, one OpenAI-style {'messages': [...]} per line; user/assistant text only",
        "reference_view": "canonical/evolve/task_<id>.json (tool calls/results; audit only)",
    }
    (input_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(order)} conversations; skipped: {skipped}")


if __name__ == "__main__":
    main()
