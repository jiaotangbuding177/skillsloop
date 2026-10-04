"""v4 paired analysis: B0 (no_skill) vs B1 (frozen_skills_v2, native $skill refs).

Inputs:
  runs/test_v4/no_skill.json
  runs/test_v4/autoskill_library.json
  reports/skill_read_audit_v4.json  (optional; from scripts/scan_skill_reads.py)

Outputs:
  reports/v4_paired_summary.json
  reports/v4_paired_report.md
"""
from __future__ import annotations

import argparse
import json
import math
import re
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_sims(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("simulations") or []


def reward_of(sim: dict):
    return (sim.get("reward_info") or {}).get("reward")


def stats(sims: list[dict]) -> dict:
    vals = [reward_of(s) for s in sims]
    vals = [v for v in vals if v is not None]
    per_task = defaultdict(list)
    for s in sims:
        r = reward_of(s)
        if r is not None:
            per_task[s["task_id"]].append(r)
    durations = [s.get("duration") for s in sims if s.get("duration")]
    return {
        "runs": len(sims),
        "evaluable": len(vals),
        "avg_reward": round(sum(vals) / len(vals), 4) if vals else None,
        "pass_1": round(sum(1 for v in vals if v == 1.0) / len(vals), 4) if vals else None,
        "tasks": len(per_task),
        "task_avg_mean": round(sum(sum(rs) / len(rs) for rs in per_task.values()) / len(per_task), 4) if per_task else None,
        "tasks_all_trials_1": sum(1 for rs in per_task.values() if len(rs) == 4 and all(r == 1.0 for r in rs)),
        "tasks_all_trials_0": sum(1 for rs in per_task.values() if len(rs) == 4 and all(r == 0.0 for r in rs)),
        "non_zero_runs": sum(1 for v in vals if v and v > 0),
        "terminations": dict(Counter(s.get("termination_reason") for s in sims)),
        "avg_duration_s": round(sum(durations) / len(durations), 1) if durations else None,
    }


def exact_sign_test(wins: int, losses: int) -> float | None:
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 6)


def bootstrap_ci(deltas: list[float], iterations: int = 10000, seed: int = 42) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(iterations):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * iterations)]
    hi = means[int(0.975 * iterations) - 1]
    return round(lo, 4), round(hi, 4)


def hour_offset_bucket(sims_path: Path) -> str:
    ts = datetime.fromtimestamp(sims_path.stat().st_mtime).isoformat(timespec="seconds")
    return f"results file mtime {ts}"


def match_sessions_to_sims(sims: list[dict], group_dir: Path, audit: dict | None):
    """Match each completed sim to the session dir whose first prompt is nearest."""
    session_records = []
    if audit is None:
        for prompt in sorted(group_dir.glob("task_*/[0-9a-f]*/turn_000_prompt.txt")):
            session_records.append({
                "task": prompt.parent.parent.name,
                "session": prompt.parent.name,
                "first_prompt_epoch": prompt.stat().st_mtime,
                "triggered_skills": [],
                "has_evidence": False,
            })
    else:
        for rec in audit.get("sessions", []):
            session = group_dir / rec["task"] / rec["session"] / "turn_000_prompt.txt"
            if not session.exists():
                continue
            session_records.append({
                "task": rec["task"],
                "session": rec["session"],
                "first_prompt_epoch": session.stat().st_mtime,
                "triggered_skills": rec.get("triggered_skills") or [],
                "has_evidence": True,
            })
    by_task = defaultdict(list)
    for rec in session_records:
        by_task[rec["task"]].append(rec)
    for recs in by_task.values():
        recs.sort(key=lambda r: r["first_prompt_epoch"])

    matches = []
    for sim in sims:
        safe = re.sub(r"[^A-Za-z0-9_.\-]", "_", str(sim['task_id']))[:120]
        task = f"task_{safe}"
        try:
            start = datetime.fromisoformat(sim["start_time"]).timestamp()
        except (KeyError, ValueError):
            matches.append({"task": task, "trial": sim.get("trial"), "session": None,
                            "reason": "no start_time"})
            continue
        candidates = [r for r in by_task.get(task, []) if abs(r["first_prompt_epoch"] - start) <= 300]
        best = min(candidates, key=lambda r: abs(r["first_prompt_epoch"] - start)) if candidates else None
        matches.append({
            "task": task,
            "trial": sim.get("trial"),
            "reward": reward_of(sim),
            "session": best["session"] if best else None,
            "triggered_skills": best["triggered_skills"] if best else [],
        })
    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b0", default=str(ROOT / "runs" / "test_v4" / "no_skill.json"))
    parser.add_argument("--b1", default=str(ROOT / "runs" / "test_v4" / "autoskill_library.json"))
    parser.add_argument("--audit", default=str(ROOT / "reports" / "skill_read_audit_v4.json"))
    parser.add_argument("--json-out", default=str(ROOT / "reports" / "v4_paired_summary.json"))
    parser.add_argument("--md-out", default=str(ROOT / "reports" / "v4_paired_report.md"))
    args = parser.parse_args()

    b0_path, b1_path = Path(args.b0), Path(args.b1)
    b0, b1 = load_sims(b0_path), load_sims(b1_path)
    s0, s1 = stats(b0), stats(b1)

    r0 = {(s["task_id"], s.get("trial")): reward_of(s) for s in b0}
    r1 = {(s["task_id"], s.get("trial")): reward_of(s) for s in b1}
    pairs = [k for k in r0 if k in r1 and r0[k] is not None and r1[k] is not None]
    wins = sum(1 for k in pairs if r1[k] > r0[k])
    losses = sum(1 for k in pairs if r0[k] > r1[k])
    ties = len(pairs) - wins - losses
    mean_diff = sum(r1[k] - r0[k] for k in pairs) / len(pairs) if pairs else None

    per_task_delta = defaultdict(list)
    for k in pairs:
        per_task_delta[k[0]].append(r1[k] - r0[k])
    task_deltas = [sum(v) / len(v) for v in per_task_delta.values()]
    ci = bootstrap_ci(task_deltas) if len(task_deltas) >= 2 else (None, None)

    audit = None
    audit_path = Path(args.audit)
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    matches = match_sessions_to_sims(b1, ROOT / "runs" / "autoskill_library", audit)
    matched = [m for m in matches if m["session"]]
    read_sims = [m for m in matched if m.get("triggered_skills")]
    skill_counts = Counter()
    for rec in read_sims:
        for sk in rec["triggered_skills"]:
            skill_counts[sk] += 1

    # per-task table data
    task_ids = sorted({s["task_id"] for s in b0} | {s["task_id"] for s in b1})
    task_rows = []
    per0 = defaultdict(list)
    per1 = defaultdict(list)
    for s in b0:
        r = reward_of(s)
        if r is not None:
            per0[s["task_id"]].append(r)
    for s in b1:
        r = reward_of(s)
        if r is not None:
            per1[s["task_id"]].append(r)
    for tid in task_ids:
        a0 = per0.get(tid, [])
        a1 = per1.get(tid, [])
        task_rows.append({
            "task_id": tid,
            "b0_mean": round(sum(a0) / len(a0), 3) if a0 else None,
            "b1_mean": round(sum(a1) / len(a1), 3) if a1 else None,
            "b1_minus_b0": round((sum(a1) / len(a1)) - (sum(a0) / len(a0)), 3) if a0 and a1 else None,
            "b0_n": len(a0), "b1_n": len(a1),
        })

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "b0_file": str(b0_path), "b1_file": str(b1_path),
        "b1_file_note": hour_offset_bucket(b1_path),
        "B0_no_skill": s0,
        "B1_frozen_skills_v2": s1,
        "paired": {
            "pairs": len(pairs), "B1_better": wins, "B0_better": losses, "ties": ties,
            "mean_diff_B1_minus_B0": round(mean_diff, 4) if mean_diff is not None else None,
            "sign_test_two_sided_p": exact_sign_test(wins, losses),
            "bootstrap_ci95_task_level": list(ci),
            "bootstrap_note": "10k resamples over task-level mean deltas",
        },
        "skill_read": {
            "completed_b1_sims": len(b1),
            "matched_to_sessions": len(matched),
            "unmatched": len(matches) - len(matched),
            "sessions_with_real_skill_read": len(read_sims),
            "skill_read_rate_matched": round(len(read_sims) / len(matched), 4) if matched else None,
            "skill_counts": dict(skill_counts),
            "audit_source": str(audit_path) if audit else "audit json missing (sessions unmapped)",
        },
        "per_task": task_rows,
    }
    Path(args.json_out).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# v4 配对评测报告：B0（无技能）vs B1（frozen_skills_v2 + 原生 $技能引用）",
        "",
        f"- 生成时间：{summary['generated_at']}",
        f"- B0 文件：`{b0_path}`；B1 文件：`{b1_path}`（{summary['b1_file_note']}）",
        "",
        "## 组统计",
        "",
        "| 指标 | B0 无技能 | B1 有技能 |",
        "|---|---|---|",
        f"| 完成场次 | {s0['runs']} | {s1['runs']} |",
        f"| 平均奖励 | {s0['avg_reward']} | {s1['avg_reward']} |",
        f"| pass@1（单场=1.0 比例） | {s0['pass_1']} | {s1['pass_1']} |",
        f"| 任务数 | {s0['tasks']} | {s1['tasks']} |",
        f"| 任务均值（先平均再汇总） | {s0['task_avg_mean']} | {s1['task_avg_mean']} |",
        f"| 全 4 场全过任务 | {s0['tasks_all_trials_1']} | {s1['tasks_all_trials_1']} |",
        f"| 全 4 场全 0 任务 | {s0['tasks_all_trials_0']} | {s1['tasks_all_trials_0']} |",
        f"| 平均时长(s) | {s0['avg_duration_s']} | {s1['avg_duration_s']} |",
        "",
        "## 配对（同 task 同 trial）",
        "",
        f"- 配对数：{len(pairs)}；B1 更好 {wins}；B0 更好 {losses}；持平 {ties}",
        f"- 平均差（B1−B0）：{summary['paired']['mean_diff_B1_minus_B0']}",
        f"- 精确符号检验双侧 p：{summary['paired']['sign_test_two_sided_p']}",
        f"- 任务级 bootstrap 95% CI：{ci[0]} ~ {ci[1]}",
        "",
        "## 技能读取（真实原生 read 调用）",
        "",
        f"- B1 完成场次：{len(b1)}；匹配到会话：{len(matched)}（未匹配 {len(matches) - len(matched)}）",
        f"- 其中真实读取技能的会话：{len(read_sims)}（匹配口径 {summary['skill_read']['skill_read_rate_matched']}）",
        f"- 读写技能次数（会话口径）：{dict(skill_counts)}",
        "",
        "## 逐任务",
        "",
        "| task | B0 均值 | B1 均值 | Δ(B1−B0) | B0 n | B1 n |",
        "|---|---|---|---|---|---|",
    ]
    for row in task_rows:
        md.append(f"| {row['task_id']} | {row['b0_mean']} | {row['b1_mean']} | {row['b1_minus_b0']} | {row['b0_n']} | {row['b1_n']} |")
    Path(args.md_out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["B0_no_skill", "B1_frozen_skills_v2", "paired", "skill_read"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
