#!/usr/bin/env python3
"""Split and coverage audit for tau2-bench airline (pinned v1.0.1), experiment 267.

Researcher-facing audit only. Gold action names/ids are used for coverage
statistics; raw reference answers stay in the evaluation data and are not copied
into any manifest consumed by the pipeline.

Inputs (frozen copies, see versions.json):
  inputs/airline_tasks.json        (50 tasks)
  inputs/airline_split.json        (train 30 / test 20 / base 50)

Outputs:
  split_manifest.json                     (public summary + frozen selection)
  private/airline_coverage_detail.json    (per-task category detail)
"""
import difflib
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
DEV_SEED = 42
DEV_COUNT = 4

WRITE_TOOLS = [
    "book_reservation",
    "cancel_reservation",
    "update_reservation_flights",
    "update_reservation_baggages",
    "update_reservation_passengers",
]
CATEGORY = {
    "book_reservation": "book",
    "cancel_reservation": "cancel",
    "update_reservation_flights": "update_flights",
    "update_reservation_baggages": "update_baggages",
    "update_reservation_passengers": "update_passengers",
    "transfer_to_human_agents": "escalate",
}
# Primary-operation priority: most consequential mutation first (airline).
PRIORITY = ["cancel", "update_flights", "book", "update_baggages", "update_passengers"]

RESERVATION_RE = re.compile(r"^[A-Z0-9]{6}$")
USER_RE = re.compile(r"^[a-z]+_[a-z]+_\d+$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def iter_arg_values(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            yield from iter_arg_values(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_arg_values(value)
    elif isinstance(obj, str):
        yield obj


def main() -> None:
    tasks = json.loads((INPUTS / "airline_tasks.json").read_text(encoding="utf-8"))
    split = json.loads((INPUTS / "airline_split.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in tasks}

    train, test = split["train"], split["test"]
    base = split.get("base", [])
    checks = {
        "task_ids_all_valid": all(i in by_id for i in train + test),
        "train_test_disjoint": not (set(train) & set(test)),
        "base_equals_union": set(base) == (set(train) | set(test)),
        "base_equals_all_tasks": set(base) == set(by_id),
        "counts": {"train": len(train), "test": len(test), "base": len(base)},
    }
    assert checks["task_ids_all_valid"] and checks["train_test_disjoint"]
    assert checks["base_equals_union"] and checks["base_equals_all_tasks"]

    detail = {}
    for tid, task in by_id.items():
        ec = task.get("evaluation_criteria") or {}
        actions = ec.get("actions") or []
        names = [a.get("name") for a in actions if isinstance(a, dict)]
        cats = [CATEGORY[n] for n in names if n in CATEGORY]
        primary = next((c for c in PRIORITY if c in cats),
                       "escalate" if "transfer_to_human_agents" in names else "read_only")
        user_keys, res_keys = set(), set()
        for a in actions:
            if not isinstance(a, dict):
                continue
            for value in iter_arg_values(a.get("arguments") or {}):
                if USER_RE.fullmatch(value.lower()):
                    user_keys.add(value.lower())
                elif RESERVATION_RE.fullmatch(value):
                    res_keys.add(value.upper())
        detail[tid] = {
            "split": "train" if tid in train else "test",
            "primary": primary,
            "categories": sorted(set(cats)),
            "tool_names": names,
            "user_keys": sorted(user_keys),
            "order_keys": sorted(res_keys),  # reservation ids
        }

    cat_counts = {
        "train": dict(Counter(detail[t]["primary"] for t in train)),
        "test": dict(Counter(detail[t]["primary"] for t in test)),
    }

    rng = random.Random(DEV_SEED)
    dev_ids, dev_detail = [], {}
    for cat in PRIORITY:
        if len(dev_ids) >= DEV_COUNT:
            break
        candidates = sorted(t for t in train if detail[t]["primary"] == cat)
        if not candidates:
            continue
        rng.shuffle(candidates)
        dev_ids.append(candidates[0])
        dev_detail[candidates[0]] = cat
    evolve_ids = [t for t in train if t not in set(dev_ids)]

    def group_map(key: str):
        groups = defaultdict(list)
        for tid in base:
            for v in detail[tid][key]:
                groups[v].append(tid)
        return groups

    shared = {"users": [], "orders": []}
    for key in ("user_keys", "order_keys"):
        for value, ids in group_map(key).items():
            tr = [i for i in ids if i in train]
            te = [i for i in ids if i in test]
            if tr and te:
                shared["users" if key == "user_keys" else "orders"].append(
                    {"key": value, "train": sorted(tr), "test": sorted(te)})

    def instruction(tid: str) -> str:
        scenario = by_id[tid].get("user_scenario") or {}
        inst = scenario.get("instructions")
        if isinstance(inst, dict):
            return " ".join(str(v) for v in inst.values())
        return str(inst or "")

    def action_signature(tid: str):
        return tuple(detail[tid]["tool_names"])

    near_dupes = []
    for t_tr in train:
        for t_te in test:
            if action_signature(t_tr) == action_signature(t_te):
                ratio = difflib.SequenceMatcher(None, norm(instruction(t_tr)), norm(instruction(t_te))).ratio()
                if ratio >= 0.5:
                    near_dupes.append({"train": t_tr, "test": t_te, "similarity": round(ratio, 3)})

    evolve_cats = set(detail[t]["primary"] for t in evolve_ids)
    test_needs = {
        t: {"primary": detail[t]["primary"],
            "covered_by_evolve_category": detail[t]["primary"] in evolve_cats}
        for t in sorted(test)
    }

    manifest = {
        "domain": "airline",
        "tau2_version": "v1.0.1",
        "inputs": {
            "tasks_sha256": sha256(INPUTS / "airline_tasks.json"),
            "split_sha256": sha256(INPUTS / "airline_split.json"),
            "policy_sha256": sha256(INPUTS / "airline_policy.md"),
            "db_sha256": sha256(INPUTS / "airline_db.json"),
        },
        "checks": checks,
        "counts": {"train": len(train), "test": len(test),
                    "dev": len(dev_ids), "evolution": len(evolve_ids)},
        "dev_selection": {
            "rule": "primary-operation buckets ranked by priority "
                    "[cancel,update_flights,book,update_baggages,update_passengers]; "
                    "per bucket shuffle sorted train ids with random.Random(42), take first; "
                    "stop at 4 dev tasks. Deterministic; no test data consulted.",
            "seed": DEV_SEED,
            "dev_ids": dev_ids,
            "dev_categories": dev_detail,
        },
        "train_ids": sorted(train),
        "test_ids": sorted(test),
        "evolution_ids": sorted(evolve_ids),
        "category_counts": cat_counts,
        "relatedness": {
            "train_test_shared_users": shared["users"],
            "train_test_shared_reservations": shared["orders"],
            "same_action_signature_train_test_pairs": near_dupes,
        },
        "test_primary_coverage": test_needs,
        "exposure_notes": [
            "Gold action names were used only for this researcher-facing coverage audit; "
            "no gold action content flows into Collector/AutoSkill/Consumer inputs.",
            "Airline reward_basis is [DB, COMMUNICATE] for all 50 tasks; COMMUNICATE checks "
            "are pure string matching in the vendor evaluator (no judge model).",
        ],
    }
    (ROOT / "split_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "private" / "airline_coverage_detail.json").write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")

    print("counts:", manifest["counts"])
    print("dev:", dev_ids, dev_detail)
    print("train primary:", cat_counts["train"])
    print("test primary:", cat_counts["test"])
    print("shared users:", len(shared["users"]), "shared reservations:", len(shared["orders"]))
    print("same-signature pairs:", near_dupes)
    print("test tasks w/o evolve-category coverage:",
          [t for t, v in test_needs.items() if not v["covered_by_evolve_category"]])


if __name__ == "__main__":
    main()
