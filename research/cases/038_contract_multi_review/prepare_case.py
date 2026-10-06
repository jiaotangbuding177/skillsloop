"""Prepare a local, source-linked contract-review case without model calls.

The private output copies selected enterprise messages verbatim. Keep it local.
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


TRAIN = ("conv_f586a09e7356", "conv_011570125174")
HOLDOUT = "conv_60925fa3f733"
SELECTED = (*TRAIN, HOLDOUT)
SKILL_REQUEST = re.compile(r"请\s*使用\s*技能")
CONTRACT_BUCKET = re.compile(
    r"(合同|协议|NDA|保密协议|条款).*(审|看|查|改|风险|起草)"
    r"|(审|审阅|审查|审核).*(合同|协议|NDA|条款)|补充协议"
)


def digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lines(path, values):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def clean_user(text):
    # Remove the platform language wrapper only. Preserve short feedback verbatim.
    return re.sub(r"^请使用中文回复，除非用户明确使用其他语言。\s*", "", text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mining", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    private = output / "private"
    private.mkdir(parents=True, exist_ok=True)

    user = json.loads((args.mining / "user_messages.json").read_text(encoding="utf-8"))
    cleaned = json.loads((args.mining / "messages_clean.json").read_text(encoding="utf-8"))
    sessions = {x["id"]: x for x in json.loads((args.mining / "sessions.json").read_text(encoding="utf-8"))}
    all_user_by_id = {x["id"]: x for x in user}
    excluded_sessions = {x["session_id"] for x in user if SKILL_REQUEST.search(x["content"])}
    bucket_hits = [x for x in cleaned if CONTRACT_BUCKET.search(x["content"])]
    eligible_hits = [x for x in bucket_hits if x["session_id"] not in excluded_sessions]
    lines(private / "eligible_contract_user_messages.jsonl", [all_user_by_id[x["id"]] for x in eligible_hits])
    cohort = {
        "definition": "original analyze.mjs contract regex on messages_clean, followed by whole-session skill-request exclusion",
        "rawKeywordHits": len(bucket_hits),
        "rawKeywordSessions": len({x["session_id"] for x in bucket_hits}),
        "eligibleKeywordHits": len(eligible_hits),
        "eligibleSessions": len({x["session_id"] for x in eligible_hits}),
        "eligibleStableUsers": len({sessions[x["session_id"]]["user_id"] for x in eligible_hits}),
        "excludedHitSessions": len({x["session_id"] for x in bucket_hits if x["session_id"] in excluded_sessions}),
        "hitMessageIdsBySession": {
            sid: [x["id"] for x in eligible_hits if x["session_id"] == sid]
            for sid in sorted({x["session_id"] for x in eligible_hits})
        },
    }
    dump(output / "cohort_index.json", cohort)
    user_by_id = {x["id"]: x for x in user if x["session_id"] in SELECTED}
    users_by_session = defaultdict(list)
    for x in user_by_id.values():
        users_by_session[x["session_id"]].append(x)
    owner_ids = {sessions[sid]["user_id"] for sid in SELECTED}
    assert len(owner_ids) == 1, "selected sessions must belong to one member"
    for sid in SELECTED:
        assert all(not SKILL_REQUEST.search(x["content"]) for x in users_by_session[sid]), sid

    records = defaultdict(list)
    exact_raw_lines = []
    with (args.raw / "zclaw_messages.jsonl").open("rb") as f:
        for source_line, raw in enumerate(f, 1):
            item = json.loads(raw)
            if item["sessionId"] not in SELECTED:
                continue
            assert item["role"] in ("user", "assistant", "system")
            if item["role"] == "user":
                assert item["id"] in user_by_id, f"user timestamp absent: {item['id']}"
            records[item["sessionId"]].append((source_line, item, raw))
            exact_raw_lines.append(raw)

    assert all(records[sid] for sid in SELECTED)
    assert {x["id"] for sid in SELECTED for _, x, _ in records[sid] if x["role"] == "user"} == set(user_by_id)
    assert all(not SKILL_REQUEST.search(x["content"]) for sid in SELECTED for _, x, _ in records[sid] if x["role"] == "user")
    # Local byte copy of selected JSONL rows, preserving the original export line.
    with (private / "raw_messages.jsonl").open("wb") as f:
        for raw in exact_raw_lines:
            f.write(raw if raw.endswith(b"\n") else raw + b"\n")
    lines(private / "user_messages_with_dates.jsonl", sorted(user_by_id.values(), key=lambda x: x["created_at"]))

    source_index = []
    traces = []
    import_train = []
    import_compat = []
    holdout_request = None
    for sid in SELECTED:
        rows = records[sid]
        source_users = [x for _, x, _ in rows if x["role"] == "user"]
        assert len(source_users) == len(users_by_session[sid])
        user_dates = [user_by_id[x["id"]]["created_at"] for x in source_users]
        assert user_dates == sorted(user_dates), f"source order and user dates conflict in {sid}"
        assert all(x["status"] == "done" for _, x, _ in rows)

        turns = []
        current = None
        for source_line, item, raw in rows:
            source_index.append({
                "messageId": item["id"], "sessionId": sid, "sourceLine": source_line,
                "role": item["role"], "status": item["status"],
                "userCreatedAt": user_by_id[item["id"]]["created_at"] if item["role"] == "user" else None,
                "rawLineSha256": hashlib.sha256(raw.rstrip(b"\r\n")).hexdigest(),
                "contentSha256": hashlib.sha256(item["content"].encode("utf-8")).hexdigest(),
                "rawPayloadKeys": list((item.get("rawPayload") or {}).keys()),
            })
            if item["role"] == "user":
                current = {"user": item, "assistant": [], "userSourceLine": source_line}
                turns.append(current)
            elif item["role"] == "assistant":
                assert current is not None, f"assistant before first user: {sid}"
                current["assistant"].append(item)

        trace_turns = []
        initial_import_id = None
        for number, turn in enumerate(turns, 1):
            original = turn["user"]
            in_scope = not (sid == HOLDOUT and number == len(turns))  # later price query
            request_id = "src-" + original["id"].split(":")[-1]
            import_session = "038-" + sid
            import_id = "import-" + digest(["alice", import_session, request_id])[:24]
            if initial_import_id is None:
                initial_import_id = import_id
            trace_turns.append({
                "turn": number,
                "task": "contract_review" if in_scope else "out_of_scope_market_price",
                "userMessageId": original["id"],
                "userTimestampUtc": user_by_id[original["id"]]["created_at"],
                "assistantMessageIds": [x["id"] for x in turn["assistant"]],
                "assistantTiming": "unknown",
                "sourceOrderBasis": "source JSONL line order, checked against increasing user timestamps and semantic continuity",
                "technicalStatus": "COMPLETED" if turn["assistant"] else "DISCONNECTED",
                "businessOutcome": "UNKNOWN",
                "sourceUserLine": turn["userSourceLine"],
                "importTurnId": import_id if sid in TRAIN else None,
            })
            if sid in TRAIN:
                assert turn["assistant"], f"train turn missing assistant: {sid} / {number}"
                imported = {
                    "session": import_session,
                    "requestId": request_id,
                    "user": clean_user(original["content"]),
                    "assistant": "\n\n".join(x["content"] for x in turn["assistant"]),
                    "status": "COMPLETED",
                }
                if number > 1:
                    imported["replyTo"] = initial_import_id
                assert len(imported["user"]) + len(imported["assistant"]) <= 60000
                import_train.append(imported)
                compatibility_view = dict(imported)
                if sid == "conv_011570125174" and number == 1:
                    # The current demo's REQUEST rule misses a request beginning
                    # with “从委托方...”. This view is only an interface shim.
                    compatibility_view["user"] = "请" + compatibility_view["user"]
                import_compat.append(compatibility_view)
            elif number == 1:
                holdout_request = {
                    "sessionId": sid,
                    "sourceMessageId": original["id"],
                    "createdAtUtc": user_by_id[original["id"]]["created_at"],
                    "request": clean_user(original["content"]),
                    "referenceAnswerFile": "private/raw_messages.jsonl",
                    "referenceAnswerVisibility": "withheld from skill generation",
                    "inputLimitation": "contract DOCX attachment bytes absent from both exports",
                }
        traces.append({
            "sessionId": sid,
            "memberAlias": "member-01",
            "split": "generation" if sid in TRAIN else "later_holdout",
            "userTimeRangeUtc": [user_dates[0], user_dates[-1]],
            "sourceMessageCount": len(rows),
            "turns": trace_turns,
            "sourceStatus": "all selected rows done; not a business success label",
            "attachmentBytesAvailable": False,
        })

    dump(output / "source_index.json", source_index)
    dump(output / "recovered_trajectories.json", traces)
    lines(private / "demo_generation_import.jsonl", import_train)
    lines(private / "demo_generation_import_compat.jsonl", import_compat)
    dump(output / "holdout_request.json", holdout_request)
    dump(output / "package_manifest.json", {
        "caseId": "038_contract_multi_review",
        "source": {"mining": str(args.mining), "raw": str(args.raw)},
        "selectedSessions": list(SELECTED),
        "generationSessions": list(TRAIN),
        "laterHoldoutSession": HOLDOUT,
        "memberAlias": "member-01",
        "messageCounts": {sid: len(records[sid]) for sid in SELECTED},
        "eligibleContractKeywordHits": len(eligible_hits),
        "generationTurnCount": len(import_train),
        "compatibilityViewChange": "prepend 请 to the first request of conv_011570125174 only; original view retained",
        "evidenceState": "raw text and assistant claims; contract attachments and output files not exported",
        "historicalBusinessOutcome": "UNKNOWN",
        "modelCallsMade": 0,
    })
    print(json.dumps({"sessions": list(SELECTED), "sourceMessages": len(exact_raw_lines),
                      "generationTurns": len(import_train), "holdoutPrepared": bool(holdout_request)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
