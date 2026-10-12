"""Source-scoped real IMA reads with declared experiment update-time semantics."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TRANSPORT_EVENTS = []


def zone(name):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        # Windows host runtime has no tzdata package. These modern Shanghai
        # source dates use UTC+8; the Linux container retains its native tzdb.
        if name == "Asia/Shanghai":
            return dt.timezone(dt.timedelta(hours=8), "Asia/Shanghai")
        raise


def api(path, body, cfg):
    request = urllib.request.Request("https://ima.qq.com" + path,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "ima-openapi-clientid": cfg["clientId"],
                 "ima-openapi-apikey": cfg["apiKey"]})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    read_only = path in {"/openapi/note/v1/get_doc_content", "/openapi/wiki/v1/get_knowledge_list", "/openapi/wiki/v1/get_addable_knowledge_base_list"}
    for attempt in range(3):
        try:
            with opener.open(request, timeout=45) as response:
                data = json.load(response)
            break
        except urllib.error.HTTPError as error:
            retry = read_only and error.code in {429, 500, 502, 503, 504} and attempt < 2
            TRANSPORT_EVENTS.append({"path": path, "http_status": error.code, "retry": retry, "attempt": attempt + 1})
            if not retry:
                raise
            time.sleep(2 ** (attempt + 1))
    if data.get("code") != 0:
        raise RuntimeError("IMA API returned code " + str(data.get("code")))
    return data.get("data", {})


def read_note(note_id, cfg):
    return api("/openapi/note/v1/get_doc_content", {"note_id": note_id,
        "target_content_format": 0}, cfg)["content"]


def parse_time(value, timezone="Asia/Shanghai"):
    value = str(value)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=zone(timezone)) if parsed.tzinfo is None else parsed


def safe_name(value):
    name = re.sub(r"[^\w\u4e00-\u9fff .-]", "_", str(value)).strip(" .")
    if name in {"", ".", ".."}:
        raise ValueError("Invalid export path component")
    return name


def execute(args):
    transport_start = len(TRANSPORT_EVENTS)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    cfg = json.loads(Path(args.credentials).read_text(encoding="utf-8-sig"))["ima"]
    libraries = {x["library_id"]: x for x in plan.get("libraries", [])}
    temporal = plan.get("temporal_view", {})
    timezone = temporal.get("timezone", "Asia/Shanghai")
    notes = list(plan["notes"])
    if any(not n.get("note_id") for n in notes):
        raise ValueError("IMA source must be initialized into fresh remote note IDs")
    if len({str(n["note_id"]) for n in notes}) != len(notes):
        raise ValueError("Duplicate scoped remote note IDs")
    if any(any(l not in libraries for l in n.get("library_ids", [])) for n in notes):
        raise ValueError("Undeclared library membership")
    if args.command == "read":
        notes = [n for n in notes if str(n["note_id"]) == str(args.note_id)]
        if not notes:
            raise ValueError("Note ID is outside this source and attempt")
    if args.library and args.library not in libraries:
        raise ValueError("Library ID is outside this source")
    selected_library_ids = {key for key, value in libraries.items()
        if (not args.library or key == args.library)
        and (not args.public_only or (value.get("visibility") == "public_experiment" and value.get("joined_by_user")))}
    if args.library or args.public_only:
        notes = [n for n in notes if set(n.get("library_ids", [])) & selected_library_ids]
    if args.command == "libraries":
        return {"source": plan["session_id"], "attempt_id": plan.get("attempt_id"),
            "libraries": [libraries[l] for l in sorted(selected_library_ids)],
            "count": len(selected_library_ids), "scope": "declared source experiment memberships",
            "real_public_subscription_history_restored": False, "unrelated_personal_note_bodies_read": 0}
    since = parse_time(args.since, timezone) if args.since else None
    until = parse_time(args.until, timezone) if args.until else None
    if args.yesterday:
        reference = parse_time(args.reference_time or temporal["reference_time"], timezone).astimezone(zone(timezone))
        today = dt.datetime.combine(reference.date(), dt.time(), zone(timezone))
        since, until = today - dt.timedelta(days=1), today
    if since and until and since >= until:
        raise ValueError("Expected since < until")
    if (since or until or args.sort_by == "updated_at") and not temporal:
        raise ValueError("Source has no declared experiment update-time view")
    if since or until:
        notes = [n for n in notes if (not since or parse_time(n["updated_at"], timezone) >= since)
            and (not until or parse_time(n["updated_at"], timezone) < until)]
    result = []
    for note in notes:
        item = dict(note)
        item["content"] = read_note(note["note_id"], cfg)
        if args.command == "search" and args.query.lower() not in (item["title"] + "\n" + item["content"]).lower():
            continue
        item["body_sha256"] = hashlib.sha256(item["content"].encode()).hexdigest()
        result.append(item)
    key = args.sort_by or ("updated_at" if temporal else "actual_created_at_utc")
    reverse = args.order == "desc"
    result.sort(key=lambda n: (parse_time(n[key], timezone), n.get("fixture_key", n["title"])), reverse=reverse)
    written = []
    if args.command == "export":
        destination = Path(args.output_dir).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        for item in result:
            members = [libraries[l] for l in item.get("library_ids", [])
                if l in selected_library_ids or not (args.public_only or args.library)]
            if not members:
                members = [{"library_id": "unclassified", "name": "未分类知识库", "category": item.get("category", "未分类")}]
            for library in members:
                parent = destination / safe_name(library["category"]) / safe_name(library["name"]) if args.by_library else destination / safe_name(item.get("category", "未分类"))
                filename = safe_name(item["title"]) + "__" + safe_name(item.get("fixture_key", str(item["note_id"]))) + ".md"
                path = parent / filename
                if destination not in path.resolve().parents:
                    raise ValueError("Export escaped destination")
                path.parent.mkdir(parents=True, exist_ok=True)
                header = ("# " + item["title"] + "\n\n来源：当前完整会话的实验IMA笔记\n"
                    + "真实远端笔记ID：" + str(item["note_id"]) + "\n"
                    + "实验知识库：" + library["name"] + "\n"
                    + "实验最后更新时间：" + item.get("updated_at", "unknown") + "\n"
                    + "真实远端创建时间：" + str(item.get("actual_remote_created_at_utc") or "API未提供") + "\n"
                    + "实际导入观测时间：" + str(item.get("actual_created_at_utc", "unknown")) + "\n"
                    + "时间声明：实验更新时间为授权合成初态，不是原订阅历史或远端修改时间。\n\n")
                path.write_text(header + item["content"] + "\n", encoding="utf-8")
                record = {"path": str(path), "fixture_key": item.get("fixture_key"), "library_id": library["library_id"],
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "body_sha256": item["body_sha256"]}
                item.setdefault("exports", []).append(record)
                written.append(record)
        (destination / "export_manifest.json").write_text(json.dumps({"source": plan["session_id"],
            "attempt_id": plan.get("attempt_id"), "filter": {"since_inclusive": since.isoformat() if since else None,
            "until_exclusive": until.isoformat() if until else None, "public_only": args.public_only},
            "items": written}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"source": plan["session_id"], "attempt_id": plan.get("attempt_id"), "real_ima_body_api_used": True,
        "unrelated_personal_note_bodies_read": 0, "original_private_notes_restored": False,
        "time_basis": "declared_synthetic_experiment_updated_at" if temporal else "actual_import_observation",
        "reference_time": temporal.get("reference_time"), "snapshot_time": temporal.get("snapshot_time"),
        "filter": {"since_inclusive": since.isoformat() if since else None, "until_exclusive": until.isoformat() if until else None,
                   "public_only": args.public_only, "library": args.library},
        "sort": {"by": key, "order": args.order}, "notes": result, "count": len(result),
        "exported_files": len(written), "transport_events": TRANSPORT_EVENTS[transport_start:], "is_end": True}


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="/workspace/services/source_ima.json")
    parser.add_argument("--credentials", default="/run/secrets/services.json")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("libraries", "list", "read", "search", "export"):
        command = commands.add_parser(name)
        command.add_argument("--library")
        command.add_argument("--public-only", action="store_true")
        command.add_argument("--yesterday", action="store_true")
        command.add_argument("--reference-time")
        command.add_argument("--since")
        command.add_argument("--until")
        command.add_argument("--sort-by", choices=["updated_at", "actual_created_at_utc"])
        command.add_argument("--order", choices=["asc", "desc"], default="desc")
        if name == "read": command.add_argument("--note-id", required=True)
        if name == "search": command.add_argument("--query", required=True)
        if name == "export":
            command.add_argument("--output-dir", required=True)
            command.add_argument("--by-library", action="store_true")
    return parser


def main():
    args = make_parser().parse_args()
    try:
        print(json.dumps(execute(args), ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error_type": type(error).__name__, "http_status": error.code if isinstance(error, urllib.error.HTTPError) else None}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
