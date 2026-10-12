"""Initialize explicit IMA time/library inputs into fresh real API objects."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
from pathlib import Path

from source_ima_cli import api, parse_time


def now(): return dt.datetime.now(dt.timezone.utc).isoformat()


def initialize_ima(source_context, artifacts, session_id, attempt_id, credentials):
    """Return mapped_context, source_runtime_plan, remote_checks for root initializer."""
    source = copy.deepcopy(source_context)
    cfg = credentials["ima"]
    temporal = source["temporal_view"]
    if parse_time(temporal["reference_time"]) > parse_time(temporal["snapshot_time"]):
        raise ValueError("Reference time must not follow snapshot")
    libs = {lib["library_id"]: lib for lib in source["libraries"]}
    notes, checks = [], []
    for template in source["notes"]:
        if parse_time(template["updated_at"]) > parse_time(temporal["snapshot_time"]):
            raise ValueError("Future experiment update was included in the input snapshot")
        if any(l not in libs for l in template["library_ids"]):
            raise ValueError("Unknown library membership")
        artifact = next(a for a in artifacts if a["mount"] == template["input_mount"])
        raw = Path(artifact["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise ValueError("IMA fixture input SHA changed")
        content = raw.decode("utf-8-sig")
        started = now()
        imported = api("/openapi/note/v1/import_doc", {"content_format": 1, "content": content}, cfg)
        completed = now()
        note_id = imported.get("note_id", imported.get("doc_id"))
        if not note_id:
            raise RuntimeError("IMA did not return a fresh note ID")
        readback = api("/openapi/note/v1/get_doc_content", {"note_id": note_id, "target_content_format": 0}, cfg)
        actual = readback["content"]
        if session_id not in actual:
            raise RuntimeError("Fresh IMA note readback did not preserve source marker")
        note = {**template, "note_id": str(note_id), "actual_created_at_utc": completed,
            "actual_import_observation_interval_utc": {"start": started, "end": completed},
            "actual_remote_created_at_utc": imported.get("created_at_utc"),
            "actual_remote_updated_at_utc": readback.get("updated_at_utc"),
            "real_remote_timestamp_availability": "API UTC timestamp fields retained if present; host import observation is not the remote created/updated timestamp",
            "input_body_sha256": artifact["sha256"], "actual_readback_body_sha256": hashlib.sha256(actual.encode()).hexdigest(),
            "attempt_id": attempt_id}
        if template.get("knowledge_item_required"):
            item = api("/openapi/wiki/v1/add_knowledge", {"media_type": 11, "title": template["title"],
                "knowledge_base_id": source["knowledge_base_id"], "note_info": {"content_id": str(note_id)}}, cfg)
            note["knowledge_item"] = {"code": 0, "data": item}
        notes.append(note)
        checks.append({"service": "ima", "fixture_key": note["fixture_key"], "fresh_note_id": str(note_id),
            "fresh_content_readback_passed": True, "readback_body_sha256": note["actual_readback_body_sha256"],
            "declared_library_ids": note["library_ids"], "real_wiki_add_passed": bool(note.get("knowledge_item")),
            "experiment_updated_at": note["updated_at"], "real_remote_timestamp_not_replaced": True})
    source.update({"notes": notes, "session_id": session_id, "attempt_id": attempt_id, "fresh_initialization_required": False})
    runtime = {"schema": "source-ima-temporal-library-runtime-v7", "session_id": session_id,
        "attempt_id": attempt_id, "notes": notes, "knowledge_base_id": source["knowledge_base_id"],
        "libraries": source["libraries"], "temporal_view": temporal,
        "scope": "only declared current source/attempt IDs; logical public/private memberships are experimental; never scan unrelated personal note bodies"}
    return source, runtime, checks
