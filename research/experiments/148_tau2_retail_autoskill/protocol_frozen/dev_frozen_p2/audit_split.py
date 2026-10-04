#!/usr/bin/env python3
"""Split and workflow-coverage audit for tau2-bench retail (pinned v1.0.1).

Researcher-facing audit only. Nothing produced here is fed to the Collector,
AutoSkill, or the Consumer. Gold action *names*/ids are used for coverage
statistics; raw hidden instructions and reference answers stay in the
evaluation data and are not copied into any manifest consumed by the pipeline.

Inputs (frozen, see versions.json):
  inputs/retail_tasks_v1.0.1.json         (114 retail tasks)
  inputs/split_v1.0.1_from_vendor.json    (train 74 / test 40 / base 114)

Outputs:
  split_manifest.json                     (public summary + frozen selection)
  private/workflow_coverage_detail.json   (per-task category detail)
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
    "cancel_pending_order",
    "exchange_delivered_order_items",
    "return_delivered_order_items",
    "modify_pending_order_items",
    "modify_pending_order_address",
    "modify_user_address",
    "modify_pending_order_payment",
]
CATEGORY = {
    "cancel_pending_order": "cancel",
    "exchange_delivered_order_items": "exchange",
    "return_delivered_order_items": "return",
    "modify_pending_order_items": "modify_items",
    "modify_pending_order_address": "modify_address",
    "modify_user_address": "modify_address",
    "modify_pending_order_payment": "modify_payment",
    "transfer_to_human_agents": "escalate",
}
# Primary-operation priority: most consequential mutation first.
PRIORITY = ["cancel", "return", "exchange", "modify_payment", "modify_items", "modify_address"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def iter_arg_values(obj):
    """Yield all string leaf values of a JSON-ish structure."""
    if isinstance(obj, dict):
        for value in obj.values():
            yield from iter_arg_values(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_arg_values(value)
    elif isinstance(obj, str):
        yield obj


def main() -> None:
    tasks = json.loads((INPUTS / "retail_tasks_v1.0.1.json").read_text(encoding="utf-8"))
    split = json.loads((INPUTS / "split_v1.0.1_from_vendor.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in tasks}

    # ---- 1. structural validation -------------------------------------
    train, test = split["train"], split["test"]
    base = split.get("base", [])
    checks = {
        "task_ids_all_valid": all(i in by_id for i in train + test),
        "train_test_disjoint": not (set(train) & set(test)),
        "base_equals_union": set(base) == (set(train) | set(test)),
        "base_equals_all_tasks": set(base) == set(by_id),
        "counts": {"train": len(train), "test": len(test), "base": len(base)},
        "test_contains_task_9": "9" in test,
    }
    assert checks["task_ids_all_valid"]
    assert checks["train_test_disjoint"]
    assert checks["base_equals_union"] and checks["base_equals_all_tasks"]

    # ---- 2. per-task operation categories ------------------------------
    detail = {}
    for tid, task in by_id.items():
        ec = task.get("evaluation_criteria") or {}
        actions = ec.get("actions") or []
        names = [a.get("name") for a in actions if isinstance(a, dict)]
        cats = [CATEGORY[n] for n in names if n in CATEGORY]
        primary = next((c for c in PRIORITY if c in cats), "escalate" if "transfer_to_human_agents" in names else "read_only")
        user_keys, order_keys = set(), set()
        for a in actions:
            if not isinstance(a, dict):
                continue
            for value in iter_arg_values(a.get("arguments") or {}):
                if re.fullmatch(r"user_\w+", value, re.I):
                    user_keys.add(value.lower())
                if re.fullmatch(r"#W\d+", value):
                    order_keys.add(value.upper())
        detail[tid] = {
            "split": "train" if tid in train else "test",
            "primary": primary,
            "categories": sorted(set(cats)),
            "tool_names": names,
            "user_keys": sorted(user_keys),
            "order_keys": sorted(order_keys),
        }

    cat_counts = {
        "train": dict(Counter(detail[t]["primary"] for t in train)),
        "test": dict(Counter(detail[t]["primary"] for t in test)),
    }

    # ---- 3. dev selection (deterministic, seed=42) ---------------------
    rng = random.Random(DEV_SEED)
    dev_ids, dev_detail = [], {}
    for cat in PRIORITY:
        if len(dev_ids) >= DEV_COUNT:
            break
        candidates = sorted(t for t in train if detail[t]["primary"] == cat)
        if not candidates:
            continue
        rng.shuffle(candidates)
        chosen = candidates[0]
        dev_ids.append(chosen)
        dev_detail[chosen] = cat
    evolve_ids = [t for t in train if t not in set(dev_ids)]

    # ---- 4. light relatedness audit ------------------------------------
    def group_map(key: str):
        groups = defaultdict(list)
        for tid in base:
            for v in detail[tid][key]:
                groups[v].append(tid)
        return groups

    shared = {"users": [], "orders": []}
    for key in ("user_keys", "order_keys"):
        groups = group_map(key)
        for value, ids in groups.items():
            tr = [i for i in ids if i in train]
            te = [i for i in ids if i in test]
            if tr and te:
                shared["users" if key == "user_keys" else "orders"].append(
                    {"key": value, "train": sorted(tr, key=int), "test": sorted(te, key=int)}
                )

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
        for t in sorted(test, key=int)
    }

    # ---- 5. outputs -----------------------------------------------------
    manifest = {
        "domain": "retail",
        "tau2_version": "v1.0.1",
        "inputs": {
            "tasks_sha256": sha256(INPUTS / "retail_tasks_v1.0.1.json"),
            "split_sha256": sha256(INPUTS / "split_v1.0.1_from_vendor.json"),
            "policy_sha256": sha256(INPUTS / "retail_policy_v1.0.1.md"),
            "db_sha256": sha256(INPUTS / "retail_db_v1.0.1.json"),
        },
        "checks": checks,
        "counts": {"train": len(train), "test": len(test),
                    "dev": len(dev_ids), "evolution": len(evolve_ids)},
        "dev_selection": {
            "rule": "primary-operation buckets ranked by priority "
                    "[cancel,return,exchange,modify_payment,modify_items,modify_address]; "
                    "per bucket shuffle sorted train ids with random.Random(42), take first; "
                    "stop at 4 dev tasks. Deterministic; no test data consulted.",
            "seed": DEV_SEED,
            "dev_ids": dev_ids,
            "dev_categories": dev_detail,
        },
        "train_ids": sorted(train, key=int),
        "test_ids": sorted(test, key=int),
        "evolution_ids": sorted(evolve_ids, key=int),
        "category_counts": cat_counts,
        "relatedness": {
            "train_test_shared_users": shared["users"],
            "train_test_shared_orders": shared["orders"],
            "same_action_signature_train_test_pairs": near_dupes,
        },
        "test_primary_coverage": test_needs,
        "exposure_notes": [
            "test task 9 must not be used for prompt tuning, demos, or skill generation; "
            "disclose if it is ever touched.",
            "Gold action names were used only for this researcher-facing coverage audit; "
            "no gold action content flows into Collector/AutoSkill/Consumer inputs.",
        ],
    }
    out = ROOT / "split_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    detail_out = ROOT / "private" / "workflow_coverage_detail.json"
    detail_out.write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")

    print("counts:", manifest["counts"])
    print("dev:", dev_ids, dev_detail)
    print("train primary:", cat_counts["train"])
    print("test primary:", cat_counts["test"])
    print("shared users:", len(shared["users"]), "shared orders:", len(shared["orders"]))
    print("same-signature pairs:", near_dupes)
    print("test tasks w/o evolve-category coverage:",
          [t for t, v in test_needs.items() if not v["covered_by_evolve_category"]])
    print("wrote:", out, "and", detail_out)


if __name__ == "__main__":
    main()
