"""Freeze already-recovered traces and resolve their full source text. No LLM."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/cases/038_contract_multi_review/private/051-first5-run05"
OUT = Path(__file__).resolve().parent / "private"


def read(name: str):
    return json.loads((SOURCE / name).read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if OUT.exists():
        raise SystemExit("Output already exists; preserve frozen inputs instead of overwriting.")
    document = read("stage-3.json")
    traces = document["traces"]
    events = read("selected-events.json")
    event_by_id = {event["id"]: event for event in events}
    assert len(event_by_id) == len(events), "Duplicate source IDs"
    pairs = {pair["id"]: pair for pair in read("stage-1.json")["pairs"]}
    assert len(traces) == 2
    rows, cards, counts = [], [], Counter()
    for trace in traces:
        ids = trace["sourceMessageIds"]
        assert len(ids) == len(set(ids)), "Duplicate trace member IDs"
        messages = [event_by_id[source_id] for source_id in ids]
        assert all(event["sessionId"] == trace["session"] for event in messages)
        assert all(event["content"].strip() for event in messages)
        assert trace["businessOutcome"] == "UNKNOWN"
        counts.update(event["role"] for event in messages)
        rows.append({
            "schema": "existing-trace-full-text-preflight-v1",
            "trace_id": trace["id"], "session_id": trace["session"],
            "source_message_ids": ids,
            "messages": messages,
            "message_order_basis": "EXISTING_TRACE_SOURCE_MESSAGE_IDS_ARRAY",
            "business_outcome": trace["businessOutcome"],
            "verification": trace["verification"],
            "temporal_order_gold": False,
        })
        seen = set()
        lines = [f"# {trace['goal']}", "", f"会话：{trace['session']}；既有轨迹：{trace['id']}", "",
                 "以下按已经保存的问答对分组，补齐全部来源正文；不是重新恢复，也不是独立时间真值。",
                 "助手声称生成文件仍是自述；业务结果、实际交付文件验收均为未知。", ""]
        for number, pair_id in enumerate(trace["pairIds"], 1):
            pair = pairs[pair_id]
            group_ids = [pair["sourceUserMessageId"]] + [s["sourceId"] for s in pair["assistantSegments"]]
            lines.extend([f"## 已有问答组 {number}", ""])
            for source_id in group_ids:
                if source_id not in ids or source_id in seen:
                    continue
                event = event_by_id[source_id]
                seen.add(source_id)
                role = "用户" if event["role"] == "user" else "AI"
                lines.extend([f"### {role}", "", f"来源：{source_id}；原导出位置：{event['sourceOrder']}",
                              "", event["content"], ""])
        assert seen == set(ids), "Some full source messages were omitted from the readable view"
        cards.append((trace["session"] + ".md", "\n".join(lines)))
    assert counts == {"user": 8, "assistant": 40}, counts
    assert sum(len(row["messages"]) for row in rows) == 48
    OUT.mkdir(parents=True)
    (OUT / "trace_inputs.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    # Keep the existing derived structure separate from the full-text input.
    (OUT / "existing_stage3_snapshot.json").write_bytes((SOURCE / "stage-3.json").read_bytes())
    for name, body in cards:
        (OUT / name).write_text(body, encoding="utf-8")
    files = ["stage-3.json", "stage-1.json", "selected-events.json"]
    manifest = {
        "status": "INPUT_FROZEN_NATIVE_OUTCOME_ROUTING_UNRESOLVED",
        "task_family": "合同多立场审查与修订",
        "model_calls": 0, "new_rollouts": 0, "new_recovery_calls": 0,
        "trace_count": 2, "message_count": 48, "roles": dict(counts),
        "rounds": sum(len(t["turns"]) for t in traces),
        "attempts": sum(len(t["attempts"]) for t in traces),
        "source_hashes": {str((SOURCE / name).relative_to(ROOT)): sha(SOURCE / name) for name in files},
        "outputs": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file()},
        "original_success_or_failure_run_labels_created": False,
        "notes": [
            "Preserve existing task boundaries and full source text; do not feed turns.assistant excerpts as the full log.",
            "SEALED / COMPLETED / STAGE4_PROCESSED are pipeline states, not business SUCCESS.",
            "Both existing business outcomes remain UNKNOWN. No original FAILED/SUCCEED filename is synthesized.",
            "Original released analysis prompts target spreadsheets; a contract-domain run needs an explicit protocol.",
            "No model generation, artifact execution, baseline core modification, or final skill packaging occurred.",
        ],
    }
    write_json(OUT / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "traces": 2, "messages": 48,
                      "roles": dict(counts), "model_calls": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
