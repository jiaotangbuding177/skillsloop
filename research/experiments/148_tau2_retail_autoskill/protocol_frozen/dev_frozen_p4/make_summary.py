#!/usr/bin/env python3
"""Emit reports/summary.json and reports/experiment_report.md for experiment 148."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "runs" / "test" / name).read_text(encoding="utf-8"))["simulations"]


def stats(sims):
    vals = [((s.get("reward_info") or {}).get("reward")) for s in sims]
    vals = [v for v in vals if v is not None]
    per = defaultdict(list)
    for s in sims:
        r = (s.get("reward_info") or {}).get("reward")
        per[s["task_id"]].append(r)
    return {
        "runs": len(sims),
        "evaluable": len(vals),
        "avg_reward": round(sum(vals) / len(vals), 4),
        "pass_1": round(sum(1 for v in vals if v == 1.0) / len(vals), 4),
        "pass_4_tasks": sum(1 for rs in per.values() if len(rs) == 4 and all(r == 1.0 for r in rs)),
        "tasks": len(per),
        "non_zero_runs": sum(1 for v in vals if v and v > 0),
        "terminations": dict(Counter(s["termination_reason"] for s in sims)),
        "avg_user_turns": round(sum(sum(1 for m in s["messages"] if m["role"] == "user") for s in sims) / len(sims), 2),
        "avg_tool_calls": round(sum(sum(len(m.get("tool_calls") or []) for m in s["messages"] if m["role"] == "assistant") for s in sims) / len(sims), 2),
    }


def main() -> None:
    b0, b1 = load("no_skill.json"), load("autoskill_library.json")
    s0, s1 = stats(b0), stats(b1)
    r0 = {(s["task_id"], s.get("trial")): (s.get("reward_info") or {}).get("reward") for s in b0}
    r1 = {(s["task_id"], s.get("trial")): (s.get("reward_info") or {}).get("reward") for s in b1}
    pairs = [k for k in r0 if k in r1 and r0[k] is not None and r1[k] is not None]
    win = sum(1 for k in pairs if r1[k] > r0[k])
    loss = sum(1 for k in pairs if r0[k] > r1[k])
    summary = {
        "experiment": "148_tau2_retail_autoskill",
        "benchmark": "tau2-bench v1.0.1 retail text (tau3-era revisions; not tau2-paper comparable)",
        "models": {"consumer": "glm-4-flash", "user_simulator": "glm-4-flash", "judge": "glm-4-flash", "embeddings": "ecnu-embedding-small (dim 1024)"},
        "materials": {"evolution": 70, "test_tasks": 40, "trials": 4, "frozen_skills": 5},
        "B0_no_skill": s0,
        "B1_autoskill_library": s1,
        "paired": {"pairs": len(pairs), "B1_better": win, "B0_better": loss, "ties": len(pairs) - win - loss,
                    "mean_diff_B1_minus_B0": round(sum(r1[k] - r0[k] for k in pairs) / len(pairs), 4),
                    "sign_test_two_sided_p": 0.824},
        "skill_read_evidence": {"sessions_scanned": 162, "sessions_with_skill_read": 0,
                                 "exposure": "skills listed in system prompt (160/160); workspace copies match manifest (810/810 sha256)"},
        "content_review": {
            "B0": {"ideal": 12, "partial": 27, "wrong": 101, "abnormal": 20, "ideal_vs_nonideal": "1:10.7"},
            "B1": {"ideal": 17, "partial": 48, "wrong": 80, "abnormal": 15, "ideal_vs_nonideal": "1:7.5"},
            "reports": ["reports/final_review_b0.md", "reports/final_review_b1.md"],
        },
        "conclusion": ("No detectable skill benefit (and no harm): the B1 arm never read any skill "
                        "(0/160); the comparison therefore tests exposure only. Differences are within noise."),
    }
    (ROOT / "reports" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# 148 实验报告（AutoSkill x tau2-bench Retail，v1.0.1）

- 结论：**未检出技能收益（也未检出损害）**——B1 组 0/160 场读取过任何技能（技能仅被列出、从未使用），B0/B1 差异不可归因于技能；配对胜利 11:9、p=0.824。
- 材料：演化 70 场采集（55 user_stop / 10 timeout / 5 too_many_errors，基建错误 0）；测试 40 题 x 4 trials x 2 组 = 320 场（两组均无基建错误）；技能库 5 个（frozen_skills/，sha256 manifest）。
- 分数：B0 平均 reward {s0['avg_reward']} / pass^1 {s0['pass_1']}；B1 平均 reward {s1['avg_reward']} / pass^1 {s1['pass_1']}；pass^4 两组均为 0。
- 内容口径（逐题读完）：B0 理想12/部分27/错误101/异常20（理想:非理想 1:10.7）；B1 理想17/部分48/错误80/异常15（1:7.5）。
- 限制（不可跨比）：消费者/模拟器/判分均为 GLM-4-Flash；τ³ 修订版任务；本地 OpenClaw harness；单套 trial seed；模拟器占位符噪声（两组同等）。
- 明细：reports/final_review_b0.md、reports/final_review_b1.md、reports/summary.json、ledger/requests.jsonl、runs/ 与 frozen_skills_manifest.json。
"""
    (ROOT / "reports" / "experiment_report.md").write_text(report, encoding="utf-8")
    print("wrote reports/summary.json and reports/experiment_report.md")


if __name__ == "__main__":
    main()
