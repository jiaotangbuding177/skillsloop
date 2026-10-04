#!/usr/bin/env python3
"""Read-only progress snapshot for experiment 148 (tau2 retail x AutoSkill).

Counts completed simulation runs against the planned schedule:
dev 4 + evolution collection 70 + paired test 320 = 394 runs; AutoSkill
freezing is reported as a separate milestone. Also reports relay request
usage and captured native tool calls. Writes reports/progress.md.
"""
from __future__ import annotations

import glob
import json
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = {"dev": 4, "collect": 70, "test": 320}
REQUEST_CAP = 60000


def runs_done(phase: str) -> int:
    count = 0
    _cand = (phase + "_v4") if (ROOT / "runs" / (phase + "_v4")).exists() else ((phase + "_v2") if (ROOT / "runs" / (phase + "_v2")).exists() else phase)
    for path in sorted((ROOT / "runs" / _cand).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        count += len(data.get("simulations", []) or [])
    return count


def main() -> None:
    done = {phase: runs_done(phase) for phase in PLAN}
    total_plan = sum(PLAN.values())
    total_done = sum(done.values())
    lines = [f"# 148 进度快照 {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    for phase in ("dev", "collect", "test"):
        pct = 100 * done[phase] / PLAN[phase]
        lines.append(f"- {phase}: {done[phase]}/{PLAN[phase]} ({pct:.1f}%)")
    lines.append(f"- 总场次: {total_done}/{total_plan} ({100 * total_done / total_plan:.2f}%)")
    ledger = ROOT / "ledger" / "requests.jsonl"
    if ledger.exists():
        rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
        roles = Counter(r.get("role") for r in rows)
        lines.append(f"- 模型请求: {len(rows)}/{REQUEST_CAP} {dict(roles)}")
    lines.append(f"- 技能冻结: {'完成' if (ROOT / 'frozen_skills').exists() else '未开始'}")
    bridges = sum(
        1
        for pattern in (str(ROOT / "runs/*/*/*/bridge_calls.jsonl"),)
        for f in glob.glob(pattern)
        for l in open(f, encoding="utf-8")
        if l.strip()
    )
    lines.append(f"- 原生工具调用(捕获): {bridges}")
    text = "\n".join(lines)
    print(text)
    out = ROOT / "reports" / "progress.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
