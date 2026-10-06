"""Index existing topic partitions for baseline preparation. No task inference or LLM."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/datasets/evomind/task_topics_20261006"
OUT = Path(__file__).resolve().parent


def rows(path: Path):
    with path.open(encoding="utf-8-sig") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = OUT / "private"
    if destination.exists():
        raise SystemExit("Frozen registry already exists; do not overwrite it.")
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8-sig"))
    annotations = rows(SOURCE / "private/session_annotations.jsonl")
    candidates = rows(SOURCE / "private/learning_candidates.jsonl")
    assert len(annotations) == 1224 and len(candidates) == 719
    assert len({r["session_id"] for r in annotations}) == 1224
    assert len({r["candidate_id"] for r in candidates}) == 719
    session_map = {row["session_id"]: row for row in annotations}
    indexed, statistics, source_paths = [], [], [
        SOURCE / "summary.json", SOURCE / "topic_statistics.csv",
        SOURCE / "private/session_annotations.jsonl", SOURCE / "private/learning_candidates.jsonl",
        SOURCE / "private/conversations.jsonl", SOURCE / "private/model_inputs.jsonl",
    ]
    for expected in summary["topic_statistics"]:
        code = expected["代码"]
        partition = SOURCE / "private/topics" / code
        partition_candidates = rows(partition / "learning_candidates.jsonl")
        partition_sessions = rows(partition / "conversations.jsonl")
        group = [row for row in candidates if row["research_annotations"]["task_topic"] == code]
        primary = [row for row in annotations if row["session_primary_topic"] == code]
        assert len(group) == expected["具体任务学习片段"] == len(partition_candidates)
        assert len(primary) == expected["可用会话素材"] == len(partition_sessions)
        assert {row["candidate_id"] for row in group} == {row["candidate_id"] for row in partition_candidates}
        states = Counter(row["screening"] for row in primary)
        assert states["KEEP"] == expected["保留学习候选会话"]
        assert states["HOLD"] == expected["暂存待补证会话"]
        member_roles, outcomes = Counter(), Counter()
        message_count = char_count = 0
        for line_number, candidate in enumerate(partition_candidates, 1):
            assert candidate["session_id"] in session_map
            assert candidate["research_annotations"]["task_topic"] == code
            members = candidate["messages"]
            assert all(message["content"].strip() for message in members)
            member_roles.update(message["role"] for message in members)
            message_count += len(members)
            char_count += sum(len(message["content"]) for message in members)
            outcomes[str(candidate["task_success"])] += 1
            indexed.append({
                "topic_code": code, "topic_name": expected["主题"],
                "candidate_id": candidate["candidate_id"], "session_id": candidate["session_id"],
                "existing_task_annotation": candidate["task"],
                "source_partition": str((partition / "learning_candidates.jsonl").relative_to(ROOT)),
                "source_line": line_number,
                "message_group_ids": [message["group_id"] for message in members],
                "source_task_success_metadata": candidate["task_success"],
                "complete_trace_verified": candidate["complete_trace_verified"],
                "chronology_verified": candidate["chronology_verified"],
                "episode_outcome": "NOT_ADJUDICATED_THIS_ROUND",
                "target_skill_family": None,
                "baseline_job_created": False,
            })
        statistics.append({
            "主题": expected["主题"], "代码": code,
            "会话主主题数量": len(primary), "保留": states["KEEP"], "暂存": states["HOLD"],
            "任务片段数量": len(group), "片段来源会话数量": len({row["session_id"] for row in group}),
            "片段消息成员数": message_count, "用户消息成员数": member_roles["user"],
            "AI消息成员数": member_roles["assistant"], "正文字符数": char_count,
            "已生成技能数": 0,
        })
        source_paths.extend([partition / "learning_candidates.jsonl", partition / "conversations.jsonl"])
    assert sum(row["任务片段数量"] for row in statistics) == 719
    assert sum(row["会话主主题数量"] for row in statistics) == 1224
    destination.mkdir(parents=True)
    (destination / "candidate_registry.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in indexed), encoding="utf-8")
    with (OUT / "topic_preparation_statistics.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(statistics[0]))
        writer.writeheader()
        writer.writerows(statistics)
    source_hashes = {str(path.relative_to(ROOT)): digest(path) for path in source_paths}
    mapping = []
    for session_id in ("conv_011570125174", "conv_f586a09e7356"):
        annotation = session_map[session_id]
        mapping.append({"session_id": session_id, "screening": annotation["screening"],
                        "primary_topic": annotation["session_primary_topic"],
                        "candidate_ids": [r["candidate_id"] for r in candidates if r["session_id"] == session_id]})
    manifest = {
        "status": "LOCAL_TOPIC_REGISTRY_PREPARED_NO_BASELINE_EXECUTION",
        "dataset": str(SOURCE.relative_to(ROOT)), "primary_session_count": 1224,
        "keep_sessions": 716, "hold_sessions": 508, "excluded_sessions": 242,
        "existing_candidate_count": 719, "topic_count": 13, "topics_with_candidates": 12,
        "statistics": statistics, "previous_contract_case_mapping": mapping,
        "source_hashes": source_hashes,
        "candidate_registry_sha256": digest(destination / "candidate_registry.jsonl"),
        "statistics_sha256": digest(OUT / "topic_preparation_statistics.csv"),
        "native_baseline_commit": "3d0b52a140f002a512930252b613c49048f7d5ac",
        "new_llm_calls": 0, "new_rollouts": 0, "new_skills": 0,
        "limits": [
            "Topic assignments are existing research annotations, not certified task traces.",
            "Candidate task labels and research conclusions are not raw agent history or parametric seed inputs.",
            "No outcome adjudication, automatic task-family clustering, recovery, or skill generation occurred.",
            "Message counts are candidate membership occurrences, not necessarily globally unique messages.",
            "Separate baseline jobs per predeclared task family are an outer experimental configuration.",
            "Preserve all native analysis/patch/merge/translation/apply/validation mechanisms in the chosen faithful migration.",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "sessions": 1224, "candidates": 719,
                      "topics": 13, "model_calls": 0, "skills_generated": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
