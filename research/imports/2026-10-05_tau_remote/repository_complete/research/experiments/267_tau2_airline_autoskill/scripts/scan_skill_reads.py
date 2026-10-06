"""Scan v4-B1 (and archived v1/v2) sessions for real skill-read evidence.

Evidence sources per session (read-only):
  1. openclaw_state_archive/agents/main/agent/openclaw-agent.sqlite
     - transcript_events: assistant toolCall parts + toolResult parts
     - trajectory_runtime_events: type='tool.call' rows
  2. turn_000_prompt.txt: v6 native $skill references (format check)

A session counts as "triggered" when the agent actually invoked the native
read tool on a workspace/skills/<name>/SKILL.md path (call or result side),
matching by path substring 'skills/<name>/SKILL.md'.

Outputs: JSON + Markdown under reports/ (never mutates run data).
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import zstandard
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILL_FILE_RE = re.compile(r"skills[/\\]([A-Za-z0-9_\-]+)[/\\]SKILL\.md")


def _load_blob(value):
    if value is None:
        return ""
    if isinstance(value, memoryview | bytes):
        data = bytes(value)
        try:
            return zstandard.ZstdDecompressor().decompress(data).decode("utf-8", "replace")
        except Exception:
            return data.decode("utf-8", "replace")
    return str(value)


def scan_sqlite(db_path: Path) -> dict:
    """Return read-call hits from one openclaw-agent.sqlite."""
    out = {"exists": db_path.exists(), "read_calls": [], "read_results": [], "errors": []}
    if not db_path.exists():
        return out
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error as error:
        out["errors"].append(f"open: {error}")
        return out
    try:
        cur = con.cursor()
        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "transcript_events" in tables:
            cols = [r[1] for r in cur.execute("PRAGMA table_info(transcript_events)")]
            for row in cur.execute("SELECT * FROM transcript_events"):
                rec = dict(zip(cols, row))
                payload = _load_blob(
                    rec.get("event_json") or rec.get("event_zstd") or rec.get("payload")
                )
                if not payload:
                    continue
                for m in re.finditer(r'"type"\s*:\s*"toolCall"', payload):
                    window = payload[m.start(): m.start() + 600]
                    if '"read"' not in window:
                        continue
                    path_match = re.search(r'"path"\s*:\s*"([^"]+)"', window)
                    if path_match:
                        hit = SKILL_FILE_RE.search(path_match.group(1))
                        out["read_calls"].append({
                            "path": path_match.group(1),
                            "skill": hit.group(1) if hit else None,
                        })
                for m in re.finditer(r'"toolName"\s*:\s*"read"', payload):
                    window = payload[m.start(): m.start() + 1200]
                    hit = SKILL_FILE_RE.search(window)
                    if hit:
                        out["read_results"].append({"skill": hit.group(1)})
        if "trajectory_runtime_events" in tables:
            cols = [r[1] for r in cur.execute("PRAGMA table_info(trajectory_runtime_events)")]
            for row in cur.execute("SELECT * FROM trajectory_runtime_events"):
                rec = dict(zip(cols, row))
                payload = _load_blob(
                    rec.get("data_json") or rec.get("data_zstd") or rec.get("data") or rec.get("event_json")
                )
                if not payload or '"read"' not in payload:
                    continue
                path_match = re.search(r'"path"\s*:\s*"([^"]+)"', payload)
                if path_match:
                    hit = SKILL_FILE_RE.search(path_match.group(1))
                    if hit:
                        out["read_calls"].append({
                            "path": path_match.group(1),
                            "skill": hit.group(1),
                            "source": "trajectory",
                        })
    except sqlite3.Error as error:
        out["errors"].append(str(error))
    finally:
        con.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-dir", default=str(ROOT / "runs" / "autoskill_library"))
    parser.add_argument("--skills-dir", default=str(ROOT / "frozen_skills_v2"),
                        help="known skill names to disambiguate $refs from prices")
    parser.add_argument("--json-out", default=str(ROOT / "reports" / "skill_read_audit_v4.json"))
    parser.add_argument("--md-out", default=str(ROOT / "reports" / "skill_read_audit_v4.md"))
    parser.add_argument("--limit", type=int, default=0, help="scan at most N sessions (0=all)")
    args = parser.parse_args()

    known_skills = set()
    skills_dir = Path(args.skills_dir)
    if skills_dir.exists():
        known_skills = {p.parent.name for p in skills_dir.rglob("SKILL.md")}

    group_dir = Path(args.group_dir)
    sessions = []
    for prompt in sorted(group_dir.glob("task_*/[0-9a-f]*/turn_000_prompt.txt")):
        sessions.append(prompt.parent)
    if args.limit:
        sessions = sessions[: args.limit]
    print(f"sessions with turn_000 prompt: {len(sessions)}")

    results = []
    skill_counter = Counter()
    by_task = defaultdict(lambda: {"sessions": 0, "triggered": 0, "skills": Counter()})
    for session in sessions:
        task = session.parent.name
        prompt_text = (session / "turn_000_prompt.txt").read_text(encoding="utf-8", errors="replace")
        refs = sorted(set(re.findall(r"\$([a-z][a-z0-9_\-]{2,})", prompt_text)))
        known = [r for r in refs if not known_skills or r in known_skills]
        db = session / "openclaw_state_archive" / "agents" / "main" / "agent" / "openclaw-agent.sqlite"
        scan = scan_sqlite(db)
        read_skills = {c["skill"] for c in scan["read_calls"] if c.get("skill")}
        read_skills |= {c["skill"] for c in scan["read_results"] if c.get("skill")}
        triggered = bool(read_skills)
        by_task[task]["sessions"] += 1
        if triggered:
            by_task[task]["triggered"] += 1
            for s in read_skills:
                skill_counter[s] += 1
                by_task[task]["skills"][s] += 1
        results.append({
            "task": task,
            "session": session.name,
            "has_db": scan["exists"],
            "prompt_skill_refs": refs,
            "read_calls": scan["read_calls"][:20],
            "read_results": scan["read_results"][:20],
            "triggered_skills": sorted(read_skills),
            "errors": scan["errors"],
        })

    total = len(results)
    with_db = sum(1 for r in results if r["has_db"])
    triggered = sum(1 for r in results if r["triggered_skills"])
    ref_sessions = sum(1 for r in results if r["prompt_skill_refs"])
    summary = {
        "group_dir": str(group_dir),
        "sessions": total,
        "sessions_with_db": with_db,
        "sessions_with_prompt_refs": ref_sessions,
        "triggered_sessions": triggered,
        "refs_and_triggered": sum(1 for r in results if r["prompt_skill_refs"] and r["triggered_skills"]),
        "refs_no_trigger": sum(1 for r in results if r["prompt_skill_refs"] and not r["triggered_skills"]),
        "no_refs_triggered": sum(1 for r in results if not r["prompt_skill_refs"] and r["triggered_skills"]),
        "trigger_rate_all": round(triggered / total, 4) if total else None,
        "trigger_rate_with_db": round(triggered / with_db, 4) if with_db else None,
        "skill_sample_counts": dict(skill_counter),
        "per_task": {k: {"sessions": v["sessions"], "triggered": v["triggered"],
                         "skills": dict(v["skills"])} for k, v in sorted(by_task.items())},
    }
    Path(args.json_out).write_text(json.dumps({"summary": summary, "sessions": results},
                                              ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# v4-B1 技能读取审计（真实原生 read 调用）",
        "",
        f"- 扫描目录：`{group_dir}`",
        f"- 会话数（含 turn_000 prompt）：{total}；其中有 sqlite 归档：{with_db}",
        f"- 首轮 prompt 含 `$技能` 引用（v6）：{ref_sessions}/{total}",
        f"- **真实读取技能的会话：{triggered}/{total} = {summary['trigger_rate_all']}**"
        f"（有归档口径：{triggered}/{with_db} = {summary['trigger_rate_with_db']}）",
        "",
        "## 各技能被读取次数（会话口径）",
        "",
    ]
    for name, count in skill_counter.most_common():
        lines.append(f"- `{name}`: {count}")
    lines += ["", "## 逐任务", "", "| task | sessions | triggered | skills |", "|---|---|---|---|"]
    for task, data in summary["per_task"].items():
        sk = ", ".join(f"{k}×{v}" for k, v in sorted(data["skills"].items())) or "-"
        lines.append(f"| {task} | {data['sessions']} | {data['triggered']} | {sk} |")
    Path(args.md_out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:1500])


if __name__ == "__main__":
    main()
