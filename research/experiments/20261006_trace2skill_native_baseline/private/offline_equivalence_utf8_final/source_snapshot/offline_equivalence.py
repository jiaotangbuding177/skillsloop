"""Synthetic offline controls for unchanged native Trace2Skill mechanisms.

No OpenAI client constructor, credentials, HTTP or LLM is used. Response fixtures
are manufactured controls, never model results or enterprise outcome evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

from profiles import BASELINE, BASELINE_COMMIT, HERE, PROJECT, generation_config_for, load_profile, native_evolver_kwargs

sys.path[:0] = [str(BASELINE / ".runtime/deps"), str(BASELINE), str(BASELINE / "src")]
from src.react_agent.models import OpenAIClient
from skill_evolver.parallel_evolving_agent import ParallelSkillEvolver
from skill_evolver.parallel_success_evolving_agent import CombinedParallelSkillEvolver, normalize_mixed_records
from analysis import run_success_analysis_llm as success_native
from analysis.parse_success_analysis_outputs import parse_report as parse_success
from spreadsheet_agent.agents.cli_skill_preloaded_agent import CLISkillPreloadedAgent

OPENCLAW = PROJECT / "enginering/demo/.runtime/node_modules/openclaw"
CHECKER = OPENCLAW / "skills/skill-creator/scripts/quick_validate.py"
AUTHOR_S0 = BASELINE / "spreadsheet_agent/skills/xlsx"
SYNTHETIC = "SYNTHETIC_OFFLINE_CONTROL_NOT_A_MODEL_RESULT"
MARKERS = {"alpha": "- Synthetic offline control alpha: record a visible check.",
           "beta": "- Synthetic offline control beta: preserve the input structure."}


def sha(value):
    raw = value.read_bytes() if isinstance(value, Path) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def serial(value):
    if is_dataclass(value): return serial(asdict(value))
    if isinstance(value, Path): return str(value)
    if isinstance(value, dict): return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [serial(v) for v in value]
    return value


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serial(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def response(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def edit(which, exact=False):
    return {"file": "SKILL.md", "op": "append_to_section",
            "target_section": "## Overview" if exact else "## Overview (approximate)",
            "content": MARKERS[which]}


def fenced(edits):
    return "```json\n" + json.dumps({"reasoning": SYNTHETIC, "edits": edits,
        "changelog_entries": [SYNTHETIC]}, ensure_ascii=False) + "\n```"


def isolated_skill(folder):
    root = folder / "skill_root"
    shutil.copytree(AUTHOR_S0, root / "xlsx")
    assert len(list(root.glob("*/SKILL.md"))) == 1
    return root / "xlsx"


class FixtureCapture:
    """Native OpenAIClient.chat executes its normal config merge; send is replaced."""
    def __init__(self, profile, replay=None):
        self.profile = profile
        self.rows = []
        self.lock = threading.Lock()
        self.system_stages = {}
        self.replay = replay
        self.client = object.__new__(OpenAIClient)  # Never invokes credential-reading constructor.
        self.client.model = "OFFLINE_SYNTHETIC_NO_MODEL"
        self.client.generation_config = generation_config_for(profile, "evolution")
        self.client._get_from_cache = lambda key: None
        self.client._save_to_cache = lambda *args: None
        self.client._send_request_with_retry = self.send

    def bind(self, evolver):
        self.system_stages = {sha(getattr(evolver, name)): phase for name, phase in (
            ("_map_system_prompt", "map"), ("_merge_system_prompt", "merge"),
            ("_translation_system_prompt", "translation"), ("_verification_system_prompt", "verification"))}

    def send(self, messages, config):
        phase = self.system_stages[sha(messages[0]["content"])]
        last = messages[-1]["content"]
        subphase = "initial"
        if "Your previous response could not be parsed as valid JSON" in last: subphase = "json_self_fix"
        elif len(messages) > 2: subphase = "continuation"
        payload = {"model": self.client.model, "messages": deepcopy(messages), **deepcopy(config)}
        request_sha = sha(canonical(payload))
        if self.replay is not None:
            if request_sha not in self.replay: raise AssertionError("Replay payload changed")
            text = self.replay[request_sha]
        elif phase == "map":
            which = "alpha" if "offline-error-alpha" in messages[1]["content"] else "beta"
            valid = fenced([edit(which)])
            if which == "alpha" and subphase == "initial":
                text = "```json\n" + json.dumps({"reasoning": SYNTHETIC,
                    "edits": "Append " + MARKERS[which] + " to SKILL.md section Overview (approximate).",
                    "changelog_entries": [SYNTHETIC]}) + "\n```"  # Invalid edits type; intended content remains explicit.
            elif which == "beta" and subphase == "initial": text = valid[:-5]
            elif which == "beta" and subphase == "continuation": text = valid[-5:]
            else: text = valid
        elif phase == "merge": text = fenced([edit("alpha"), edit("beta")])
        elif phase == "translation":
            which = "alpha" if MARKERS["alpha"] in messages[1]["content"] else "beta"
            text = fenced([edit(which, exact=True)])
        elif phase == "verification":
            text = fenced([{"file": "SKILL.md", "op": "replace_in_section",
                            "old_text": "name: INVALID NAME", "content": "name: xlsx"}])
        else: raise AssertionError(phase)
        with self.lock:
            self.rows.append({"label": SYNTHETIC, "phase": phase, "subphase": subphase,
                              "request": payload, "request_sha256": request_sha,
                              "response_fixture": text, "response_sha256": sha(text), "http_calls": 0})
        return response(text)


class SuccessFixtureSDK:
    def __init__(self, report):
        self.report = report
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self, **request):
        self.requests.append(deepcopy(request))
        return response(self.report)


def success_control(folder, profile):
    log = folder / "synthetic_success_log.md"
    log.write_text("USER: Preserve the two input columns.\nASSISTANT: Both columns preserved in this manufactured control.\n", encoding="utf-8")
    report = "# Success Memory Item 1\n\n## Title\nPreserve input columns\n\n## Description\nSynthetic control only.\n\n## Content\nPreserve the original columns before writing the output.\n"
    sdk = SuccessFixtureSDK(report)
    messages, text = success_native.analyze_instance(sdk, "OFFLINE_SYNTHETIC_NO_MODEL",
        success_native.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        success_native.USER_PROMPT_PATH.read_text(encoding="utf-8"), log,
        generation_config_for(profile, "success_analysis"))
    report_file = folder / "success_analysis_offline-success-beta.md"
    report_file.write_text(text, encoding="utf-8")
    record = parse_success(report_file, "offline-success-beta")
    assert len(record["items"]) == 1 and record["items"][0]["type"] == "success_memory"
    assert sdk.requests[0]["messages"] == messages and sdk.requests[0]["temperature"] == 1.0
    dump(folder / "success_request_capture.json", {"label": SYNTHETIC, "request": sdk.requests[0],
        "response_fixture": report, "parsed_record": record, "http_calls": 0})
    return record


def error_record(which):
    return {"instance_id": "offline-error-" + which, "source_file": "synthetic_control.md",
            "items": [{"type": "failure_cause", "title": "Synthetic failed check",
                       "content": "Manufactured mechanism control; not a historical task judgment."}]}


def native_run(folder, profile, arm, records, replay=None):
    skill = isolated_skill(folder)
    capture = FixtureCapture(profile, replay)
    cls = ParallelSkillEvolver if arm == "error" else CombinedParallelSkillEvolver
    evolver = cls(client=capture.client, skill_dir=skill, verbose=False,
                  output_dir=folder / "native_intermediates", parse_failure_dir=folder / "parse_failures",
                  **native_evolver_kwargs(profile))
    capture.bind(evolver)
    before_valid, before_msg = evolver._evolver.validate_skill()
    assert before_valid and "skipped" not in before_msg.lower()
    result = evolver.run(records, input_mode="records")
    dump(folder / "response_fixtures_and_requests.json", {"label": SYNTHETIC, "calls": capture.rows})
    dump(folder / "native_result.json", {"label": SYNTHETIC, "result": result})
    assert len(result["patches"]) == 2 and result["final_patch"] is not None
    counts = Counter((row["phase"], row["subphase"]) for row in capture.rows)
    assert counts[("merge", "initial")] == 1
    assert counts[("translation", "initial")] == 2
    assert counts[("map", "json_self_fix")] == 1 and counts[("map", "continuation")] == 1
    final = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert all(final.count(value) == 1 for value in MARKERS.values())
    translated = json.loads((folder / "native_intermediates/translated_final_patch.json").read_text(encoding="utf-8"))
    assert len(translated["edits"]) == 2 and all(e["target_section"] == "## Overview" for e in translated["edits"])
    overview = final.split("## Overview\n", 1)[1].split("\n## ", 1)[0]
    assert all(value in overview for value in MARKERS.values())
    valid, check_message = evolver._evolver.validate_skill()
    assert valid and "skipped" not in check_message.lower()
    assert all(r["request"]["temperature"] == 0.6 for r in capture.rows)
    dump(folder / "response_fixtures_and_requests.json", {"label": SYNTHETIC, "calls": capture.rows})
    dump(folder / "native_result.json", {"label": SYNTHETIC, "result": result})
    summary = {"label": SYNTHETIC, "arm": arm, "map_patches": len(result["patches"]),
               "phase_counts": {str(k): v for k, v in counts.items()}, "skill_sha256": sha(skill / "SKILL.md"),
               "native_parameters": {key: getattr(evolver, key) for key in (
                   "batch_size", "merge_batch_size", "max_workers", "max_merge_levels",
                   "max_verification_rounds", "skip_translation", "enable_json_format_self_fix", "temperature")},
               "checker_valid": valid, "checker_message": check_message, "real_model_calls": 0}
    dump(folder / "summary.json", summary)
    return summary, capture.rows


def checker_negative_and_repair(folder, profile):
    skill = isolated_skill(folder)
    path = skill / "SKILL.md"
    path.write_text(path.read_text(encoding="utf-8").replace("name: xlsx", "name: INVALID NAME", 1), encoding="utf-8")
    capture = FixtureCapture(profile)
    evolver = ParallelSkillEvolver(client=capture.client, skill_dir=skill, verbose=False,
        output_dir=folder / "native_intermediates", parse_failure_dir=folder / "parse_failures",
        **native_evolver_kwargs(profile))
    capture.bind(evolver)
    invalid, failure = evolver._evolver.validate_skill()
    assert not invalid and "skipped" not in failure.lower()
    changelog = evolver.run_verification_phase()  # Native default maximum 3 rounds.
    valid, message = evolver._evolver.validate_skill()
    assert valid and "skipped" not in message.lower() and len(capture.rows) == 1
    result = {"label": SYNTHETIC, "known_bad_rejected": not invalid, "bad_checker_message": failure,
              "native_default_max_fix_rounds": evolver.max_verification_rounds,
              "actual_synthetic_fix_calls": len(capture.rows), "repaired_checker_valid": valid,
              "checker_message": message, "changelog": changelog, "semantic_result": "NOT_EVALUATED"}
    dump(folder / "control_result.json", result)
    dump(folder / "response_fixtures_and_requests.json", {"label": SYNTHETIC, "calls": capture.rows})
    return result


def consumer_control(folder):
    skill = isolated_skill(folder)
    agent = CLISkillPreloadedAgent(client=object(), skills_dir=str(skill.parent), verbose=False)
    native_agent = agent._ensure_agent(str(folder / "work"))
    assert len(agent._skills) == 1
    metadata, content = agent._skills[0]
    source_text = (AUTHOR_S0 / "SKILL.md").read_text(encoding="utf-8")
    source_body = source_text[source_text.index("---", 3) + 3:].lstrip("\n")
    assert content and content == source_body
    template = native_agent.config.system_template
    embedded = template.split("<skill_content>\n", 1)[1].split("\n</skill_content>", 1)[0]
    assert embedded == content and Path(metadata.file_path).resolve() == (skill / "SKILL.md").resolve()
    result = {"label": SYNTHETIC, "discovered_skills": 1, "selected_name": metadata.name,
              "selected_file": metadata.file_path, "selected_file_sha256": sha(skill / "SKILL.md"),
              "loaded_body_sha256": sha(content), "injected_body_sha256": sha(embedded),
              "independent_author_source_body_sha256": sha(source_body),
              "rendered_system_template_sha256": sha(template), "body_exact": embedded == content,
              "consumer_executed": False, "real_model_calls": 0}
    dump(folder / "consumer_injection.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "private/offline_equivalence")
    parser.add_argument("--profile", choices=["both", "release_readme", "paper_v5"], default="both")
    args = parser.parse_args()
    if not sys.flags.utf8_mode:
        raise SystemExit("Native locale-dependent text readers require Python -X utf8; no empty-skill acceptance.")
    if args.output.exists(): raise SystemExit("Preserve existing offline control results; choose a fresh --output.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASELINE, text=True).strip()
    assert commit == BASELINE_COMMIT and CHECKER.is_file()
    assert not subprocess.check_output(["git", "diff", "--name-only"], cwd=BASELINE, text=True).strip()
    args.output.mkdir(parents=True)
    dump(args.output / "control_manifest.json", {"label": SYNTHETIC, "official_commit": commit,
        "scripts_sha256": {p.name: sha(p) for p in (HERE / "profiles.py", HERE / "profiles.json", Path(__file__))},
        "scope": "Native mechanism equivalence control only; not real model results."})
    for source in (HERE / "profiles.py", HERE / "profiles.json", Path(__file__)):
        target = args.output / "source_snapshot" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    old_cwd = Path.cwd()
    results = {}
    try:
        os.chdir(OPENCLAW)  # Resolves the author's unchanged relative checker path.
        with patch("socket.socket.connect", side_effect=AssertionError("Network prohibited in offline controls")):
            for name in (["release_readme", "paper_v5"] if args.profile == "both" else [args.profile]):
                profile = load_profile(name)
                root = args.output / name
                root.mkdir()
                success = success_control(root, profile)
                summaries = {}
                for arm in ("error", "combined"):
                    records = [error_record("alpha"), error_record("beta")] if arm == "error" else normalize_mixed_records([error_record("alpha")], [success])
                    initial, rows = native_run(root / arm / "capture", profile, arm, records)
                    replay_map = {row["request_sha256"]: row["response_fixture"] for row in rows}
                    replay, replay_rows = native_run(root / arm / "replay", profile, arm, records, replay_map)
                    assert initial["skill_sha256"] == replay["skill_sha256"]
                    assert Counter(r["request_sha256"] for r in rows) == Counter(r["request_sha256"] for r in replay_rows)
                    summaries[arm] = {"capture": initial, "replay": replay, "payloads_and_output_exact": True}
                summaries["checker_negative_and_native_repair"] = checker_negative_and_repair(root / "checker_negative", profile)
                summaries["consumer_injection"] = consumer_control(root / "consumer")
                results[name] = summaries
    except Exception as exc:
        dump(args.output / "control_failure.json", {"label": SYNTHETIC,
            "status": "CONTROL_FAILED_PRESERVED", "error_type": type(exc).__name__, "error": str(exc),
            "real_model_calls": 0, "http_calls": 0})
        raise
    finally:
        os.chdir(old_cwd)
    assert not subprocess.check_output(["git", "diff", "--name-only"], cwd=BASELINE, text=True).strip()
    report = {"status": "OFFLINE_MECHANISM_CONTROLS_PASS", "label": SYNTHETIC,
              "official_commit": commit, "checker_path": str(CHECKER), "checker_sha256": sha(CHECKER),
              "real_model_calls": 0, "http_calls": 0, "business_or_semantic_effect": "NOT_EVALUATED",
              "runtime": {"python_utf8_mode": bool(sys.flags.utf8_mode), "python_executable": sys.executable,
                          "native_text_reader_modified": False},
              "coverage_excludes": ["Real model/API behavior and model output quality", "Native Agentic error diagnosis on real artifacts",
                                    "Real consumer task execution", "Train validation/seed selection/held-out effectiveness"],
              "profiles": results, "scripts_sha256": {p.name: sha(p) for p in (HERE / "profiles.py", HERE / "profiles.json", Path(__file__))}}
    dump(args.output / "result.json", report)
    print(json.dumps({"status": report["status"], "profiles": list(results), "real_model_calls": 0,
                      "http_calls": 0, "result": str(args.output / "result.json")}))


if __name__ == "__main__": main()
