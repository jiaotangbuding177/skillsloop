"""One declared source's later file reference resolves to this trial's new HTML."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE_ID = "conv_a67233b76a8f"
REFERENCE_DISPATCH = 3
REQUESTED_FILENAME = "0627培训技术支持总结汇报.html"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def location(transport, trial_id):
    identity = hashlib.sha256(str(trial_id).encode()).hexdigest()[:24]
    return Path(transport) / "episode_created_outputs" / identity


def html_fingerprints(workspace):
    workspace = Path(workspace).resolve()
    root = workspace / "outputs"
    result = {}
    if not root.is_dir():
        return result
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in (".html", ".htm") or path.is_symlink() or not path.is_file():
            continue
        if not path.resolve().is_relative_to(root):
            continue
        result[path.relative_to(workspace).as_posix()] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
    return result


def handle_turn(context, workspace, transport, trial_id, dispatch_index, phase):
    if not isinstance(context, dict):
        return None
    continuity = context.get("same_episode_output_continuity")
    reference = context.get("same_episode_output_reference")
    declared = continuity if isinstance(continuity, dict) and continuity.get("required") is True else reference
    if not isinstance(declared, dict) or declared.get("required") is not True:
        return None
    if declared.get("session_id") != SOURCE_ID:
        raise ValueError("Current HTML output bridge is restricted to its declared complete source")
    if phase not in ("before_turn", "after_turn"):
        raise ValueError("Unknown episode output phase")
    workspace = Path(workspace).resolve()
    state = location(transport, trial_id)
    common = {
        "schema": "current-episode-HTML-output-reference-v7",
        "session_id": SOURCE_ID,
        "native_trial_id": str(trial_id),
        "dispatch_index": dispatch_index,
        "phase": phase,
        "historical_output_injected": False,
        "static_surrogate_input_injected": False,
        "original_business_answer_injected": False,
    }
    before_path = state / "initial_outputs.json"
    if dispatch_index == 0 and phase == "before_turn":
        if before_path.exists():
            raise ValueError("A current output trial boundary cannot restart silently")
        write_json(before_path, {**common, "before": html_fingerprints(workspace)})
        return {**common, "guide": "本会话按用户需求新生成及修改的文件请实际保存在/workspace/outputs内；后续引用前轮产物时继续操作本次文件。"}
    if phase == "after_turn" and dispatch_index < REFERENCE_DISPATCH:
        if not before_path.exists():
            raise ValueError("Current output initial boundary was not captured")
        before = json.loads(before_path.read_text(encoding="utf-8"))["before"]
        current = html_fingerprints(workspace)
        candidates = {path: item for path, item in current.items() if path not in before}
        receipt = {**common, "current_created_HTML": candidates, "candidate_count": len(candidates)}
        write_json(state / "latest_outputs.json", receipt)
        return receipt
    if dispatch_index != REFERENCE_DISPATCH or phase != "before_turn":
        return None
    if not isinstance(reference, dict) or reference.get("required") is not True:
        return None
    if reference.get("session_id") != SOURCE_ID or reference.get("requested_filename") != REQUESTED_FILENAME:
        raise ValueError("Unexpected source or filename for current HTML reference")
    latest_path = state / "latest_outputs.json"
    candidates = {}
    if latest_path.exists():
        saved = json.loads(latest_path.read_text(encoding="utf-8"))
        if saved.get("native_trial_id") != str(trial_id) or saved.get("dispatch_index") != REFERENCE_DISPATCH - 1:
            raise ValueError("Reference requires the completed previous turn in this trial")
        current = html_fingerprints(workspace)
        candidates = {
            path: item for path, item in saved["current_created_HTML"].items()
            if current.get(path, {}).get("sha256") == item["sha256"]
        }
    exact = [path for path in candidates if Path(path).name == REQUESTED_FILENAME]
    selected = exact[0] if len(exact) == 1 else next(iter(candidates)) if not exact and len(candidates) == 1 else None
    receipt = {**common, "available": selected is not None, "candidate_count": len(candidates)}
    if selected:
        source = workspace / selected
        alias = workspace / "inputs/current_episode" / SOURCE_ID / REQUESTED_FILENAME
        alias.parent.mkdir(parents=True, exist_ok=True)
        if alias.is_symlink():
            if alias.resolve() != source.resolve():
                raise ValueError("Current HTML alias would point to another file")
        elif alias.exists():
            raise ValueError("Current HTML alias would overwrite an existing input")
        else:
            alias.symlink_to(source)
        receipt.update({
            "current_output_path": str(source),
            "read_path": str(alias),
            "current_output_sha256": candidates[selected]["sha256"],
            "producer_dispatch_index": REFERENCE_DISPATCH - 1,
            "output_bytes_modified_by_bridge": False,
            "alias_origin": "current_actor_output_after_canonical_dispatch_2",
            "guide": "用户本轮附加的同名HTML是本次前两轮制作并补充后的页面；未提供旧历史页面作为替代。请原生read完整读取 " + str(alias) + " 后，只按本轮要求修改本次产物。若指定段落在本次页面没有出现，请如实说明，不编造已删除。",
        })
    else:
        receipt.update({
            "reason": "missing_or_ambiguous_actual_current_trial_HTML",
            "guide": "本次前轮尚未留下唯一可映射的HTML；没有预灌旧页面。请从本次已有outputs中明确选出前两轮实际制作的页面并读取；若尚未落盘，请依据本次前轮内容先落盘，不能把静态旧答案当作输入。",
        })
    write_json(state / "turn_0004.current_HTML_mapping.json", receipt)
    return receipt
