"""Extra task-level cuts for the v4 report: movers, distribution, exact sign test."""
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "runs" / "test_v4" / name).read_text())["simulations"]


def reward(s):
    return (s.get("reward_info") or {}).get("reward")


def exact_sign(w, l):
    n = w + l
    if n == 0:
        return None
    k = min(w, l)
    return round(min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n), 6)


b0, b1 = load("no_skill.json"), load("autoskill_library.json")
per0, per1 = defaultdict(list), defaultdict(list)
for s in b0:
    per0[s["task_id"]].append(reward(s))
for s in b1:
    per1[s["task_id"]].append(reward(s))

rows = []
for tid in sorted(set(per0) | set(per1)):
    a0 = sum(per0[tid]) / len(per0[tid])
    a1 = sum(per1[tid]) / len(per1[tid])
    rows.append((tid, a0, a1, a1 - a0))

improved = [r for r in rows if r[3] > 0]
worsened = [r for r in rows if r[3] < 0]
same = [r for r in rows if r[3] == 0]
print("task-level: improved", len(improved), "worsened", len(worsened), "same", len(same))
print("task-level exact sign p =", exact_sign(len(improved), len(worsened)))
print("biggest improvements:")
for r in sorted(improved, key=lambda x: -x[3])[:8]:
    print("  task", r[0], "B0", round(r[1], 2), "-> B1", round(r[2], 2))
print("biggest regressions:")
for r in sorted(worsened, key=lambda x: x[3])[:8]:
    print("  task", r[0], "B0", round(r[1], 2), "-> B1", round(r[2], 2))
