"""Freeze six observable EvoMind sessions. No network, models, or command execution.

Only the source-input release and its referenced tool-snapshot export are read.
This exporter does not construct turns, task labels, success labels, or chronology.
Every output is opened with mode 'x'; an existing artifact is never overwritten.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parent
REPO = EXPERIMENT.parents[2]
PRIVATE = EXPERIMENT / "private"
SOURCE = REPO / "research/datasets/evomind/task_topics_20261006/private/model_inputs.jsonl"
TOOLS = REPO / "research/datasets/evomind/enriched_20261006/private/tools.jsonl"
RELEASE_BUILDER = REPO / "research/datasets/evomind/task_topics_20261006/build_release.py"
SESSION_IDS = [
    "conv_9b78a49bd169", "conv_7f5a1845d742", "conv_d2c84054d91a",
    "conv_e6fdd2e394f4", "conv_ee979d0d59fb", "conv_b5e6f3d3bab9",
]
OUTPUT_NAMES = ("frozen_source.json", "ecv_input.json", "input_manifest.json")
TOOL_FIELDS = (
    "session_id", "message_id", "group_id", "origin", "tool_call_id", "name",
    "status", "args", "output", "error", "started_at", "source_refs",
    "snapshot_statuses", "record_id", "record_index",
)
EXCLUDED_TOOL_FIELDS = ("evidence_scope", "historical_command_executed")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def relative(path):
    return path.relative_to(REPO).as_posix()


def source_file(path):
    data = path.read_bytes()
    return {"path": relative(path), "sha256": sha(data), "bytes": len(data)}


def read_selected(path, key, accepted):
    found = {}
    locations = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            ident = row.get(key)
            if ident in accepted:
                if ident in found:
                    raise ValueError("Duplicate source identifier: " + ident)
                found[ident] = row
                locations[ident] = {"sourceLine": line_number, "canonicalJsonSha256": sha(canonical(row)),
                                    "jsonlLineUtf8Sha256": sha(line.encode("utf-8"))}
    if set(found) != set(accepted):
        raise ValueError("Missing sources: " + repr(set(accepted) - set(found)))
    return found, locations


def build():
    sessions, session_locations = read_selected(SOURCE, "session_id", SESSION_IDS)
    ordered = [sessions[sid] for sid in SESSION_IDS]
    for row in ordered:
        if row.get("annotation_labels_included") is not False or row.get("selected_task_or_lesson_included") is not False:
            raise ValueError("Source input is not explicitly annotation-free")
        if row.get("chronology_verified") is not False:
            raise ValueError("This frozen projection expects explicitly unverified chronology")
        if {"research_annotations", "accepted_content_correspondences", "unverified_correspondence_candidates", "skill_evidence"} & set(row):
            raise ValueError("Unexpected annotation fields in blind source input")
    wanted_tools = [tid for row in ordered for tid in row.get("tool_record_ids", [])]
    if len(set(wanted_tools)) != len(wanted_tools):
        raise ValueError("Repeated tool-record ID in selected source references")
    raw_tools, tool_locations = read_selected(TOOLS, "record_id", wanted_tools)
    tools = []
    for tid in wanted_tools:
        raw = raw_tools[tid]
        unknown = set(raw) - set(TOOL_FIELDS) - set(EXCLUDED_TOOL_FIELDS)
        if unknown:
            raise ValueError("Unreviewed tool-export fields: " + repr(unknown))
        tool = {key: deepcopy(raw[key]) for key in TOOL_FIELDS if key in raw}
        if tool["session_id"] not in sessions or tid not in sessions[tool["session_id"]]["tool_record_ids"]:
            raise ValueError("Tool source does not match its session reference")
        tools.append(tool)
    message_count = sum(len(row["messages"]) for row in ordered)
    content_characters = sum(len(message["content"]) for row in ordered for message in row["messages"])
    file_count = sum(len(row.get("file_references", [])) for row in ordered)
    if (message_count, content_characters, file_count, len(tools)) != (129, 30603, 20, 11):
        raise ValueError("Frozen six-session coverage differs from the authorized source selection")
    provenance = {"model_inputs": source_file(SOURCE), "tools": source_file(TOOLS),
                  "release_builder": source_file(RELEASE_BUILDER)}
    frozen = {
        "schema": "trace2skill-frozen-source-v1",
        "session_ids": SESSION_IDS,
        "source_provenance": provenance,
        "sessions": deepcopy(ordered),
        "tool_records": tools,
        "export_boundaries": {
            "source_conversation_messages_unchanged": True,
            "tool_snapshots_preserved_separately": True,
            "tool_export_annotation_fields_excluded": list(EXCLUDED_TOOL_FIELDS),
            "chronology_verified": False,
            "attachments_restored": False,
            "business_outcome": "UNKNOWN",
            "historical_commands_executed_by_exporter": False,
            "model_calls_by_exporter": 0,
        },
    }
    events = []
    contexts = [{
        "id": "evomind-import-boundary", "kind": "PUBLIC_CONTEXT",
        "text": "This is a source-preserving observation bag. sourceOrder is the source display or snapshot-export position, not verified temporal order. Message arrays were role-grouped in the release. No responseTo, runId, task relation, user/assistant pairing, success/failure outcome, or evaluation has been inferred. Tool records are historical snapshots and may repeat a call across origins; recorded completed/done statuses do not certify task or business success. Attachment metadata is visible but attachment bytes are unavailable. Preserve uncertainty and source IDs.",
        "source": {"release": "task_topics_20261006", "adapter": "observation-bag-export-v1"},
    }]
    coverage = []
    for source in ordered:
        sid = source["session_id"]
        aliases = []
        for position, message in enumerate(source["messages"], 1):
            linked_files = [deepcopy(ref) for ref in source.get("file_references", [])
                            if ref.get("group_id") in [message["group_id"], *message.get("source_group_ids", [])]]
            event = {
                "id": message["group_id"], "sessionId": sid,
                "role": message["role"], "content": message["content"],
                "sourceOrder": position, "orderBasis": "ROLE_GROUPED_SOURCE_DISPLAY_POSITION_UNVERIFIED",
                "source_group_ids": deepcopy(message.get("source_group_ids", [])),
                "source_occurrences": deepcopy(message.get("source_occurrences", [])),
                "cleaned_content_fingerprint": message.get("cleaned_content_fingerprint"),
                "source_file_references": linked_files,
            }
            events.append(event)
            aliases.append({"event_id": event["id"], "source_group_ids": event["source_group_ids"],
                            "source_message_ids": [occ["id"] for occ in event["source_occurrences"]],
                            "content_utf8_sha256": sha(message["content"].encode("utf-8")),
                            "content_characters": len(message["content"])})
        session_tools = [tool for tool in tools if tool["session_id"] == sid]
        for position, tool in enumerate(session_tools, len(source["messages"]) + 1):
            events.append({
                "id": tool["record_id"], "sessionId": sid, "role": "tool", "content": None,
                "sourceOrder": position, "orderBasis": "TOOL_SNAPSHOT_EXPORT_POSITION_UNVERIFIED",
                "sourceTimestamp": tool.get("started_at"), "callId": tool.get("tool_call_id"),
                "name": tool.get("name"), "arguments": deepcopy(tool.get("args")),
                "result": deepcopy(tool.get("output")), "error": deepcopy(tool.get("error")),
                "status": tool.get("status"), "executionStatus": tool.get("status"),
                "eventType": "HISTORICAL_BUNDLED_SNAPSHOT", "actor": "UNKNOWN", "requestor": "UNKNOWN",
                "source_aliases": {key: deepcopy(value) for key, value in tool.items()
                                   if key not in ("args", "output", "error")},
            })
        metadata = {"session_id": sid, "chronology_verified": source["chronology_verified"],
                    "presentation": source["presentation"],
                    "dated_session_metadata": source.get("dated_session_metadata"),
                    "file_references": source.get("file_references", []),
                    "tool_record_ids": source.get("tool_record_ids", [])}
        contexts.append({"id": sid + ":source-metadata", "kind": "PUBLIC_CONTEXT",
                         "text": json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
                         "source": {"path": relative(SOURCE), "session_id": sid}})
        coverage.append({
            "session_id": sid, **session_locations[sid],
            "frozen_source_session_sha256": sha(canonical(source)),
            "message_count": len(source["messages"]),
            "content_characters": sum(len(m["content"]) for m in source["messages"]),
            "file_reference_count": len(source.get("file_references", [])),
            "tool_record_ids": source.get("tool_record_ids", []),
            "ecv_event_count": len(source["messages"]) + len(session_tools),
            "message_alias_and_coverage": aliases,
            "tool_coverage": [{"record_id": tool["record_id"], **tool_locations[tool["record_id"]],
                               "frozen_payload_sha256": sha(canonical(tool))} for tool in session_tools],
            "chronology_verified": False, "business_outcome": "UNKNOWN",
        })
    ecv = {"E": events, "C": contexts, "V": []}
    encoded = {name: (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
               for name, value in (("frozen_source.json", frozen), ("ecv_input.json", ecv))}
    manifest = {
        "schema": "trace2skill-input-manifest-v1", "session_ids": SESSION_IDS,
        "source_provenance": provenance, "six_source_coverage": coverage,
        "totals": {"sessions": len(ordered), "message_observations": message_count,
                   "message_content_characters": content_characters, "tool_snapshots": len(tools),
                   "ecv_events": len(events), "file_metadata_references": file_count,
                   "restored_attachment_files": 0, "evaluations": 0, "export_model_calls": 0},
        "projection": {"root_keys": ["E", "C", "V"], "messages": "Exact original content; stable group IDs and all source occurrences retained",
                       "tools": "Exact args/output/error retained for all 11 referenced snapshots; no snapshot merged, no historical command run",
                       "excluded_annotations": ["research_annotations", "accepted_content_correspondences", "unverified_correspondence_candidates", "skill_evidence", *EXCLUDED_TOOL_FIELDS],
                       "pairing_inferred": False, "chronology_inferred": False, "task_or_method_answers_included": False,
                       "success_or_failure_labels_inferred": False},
        "unknowns": ["Verified temporal order", "Which assistant observation responds to which user observation",
                     "Which tool snapshot belongs to which user/task", "Attachment file contents", "Business outcome", "Method correctness"],
        "existing_recovery_adapter_warning": "Do not pass this role-grouped observation bag through prepare_events/prepare_batches as a factual turn sequence. intake.assemble uses adjacency when explicit responseTo/runId are absent. An observation-bag adapter must expose source-order uncertainty rather than import its inferred pairs as evidence.",
        "outputs": {name: {"sha256": sha(data), "bytes": len(data)} for name, data in encoded.items()},
        "exporter": {"path": relative(Path(__file__)), "sha256": sha(Path(__file__).read_bytes())},
    }
    encoded["input_manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return encoded, manifest


def main():
    if any((PRIVATE / name).exists() for name in OUTPUT_NAMES):
        raise FileExistsError("Frozen output already exists; nothing overwritten")
    encoded, manifest = build()
    PRIVATE.mkdir(parents=True, exist_ok=True)
    for name, data in encoded.items():
        with (PRIVATE / name).open("xb") as handle:
            handle.write(data)
    print(json.dumps({"created": [relative(PRIVATE / name) for name in encoded],
                      "totals": manifest["totals"], "output_sha256": {name: meta["sha256"] for name, meta in manifest["outputs"].items()}}, ensure_ascii=True))


if __name__ == "__main__":
    main()
