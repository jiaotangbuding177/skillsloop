#!/usr/bin/env python3
"""Split and coverage audit for tau2-bench telecom (pinned v1.0.1), experiment 268.

Telecom task ids encode structure: [<category>]<sub-issue path>[PERSONA:<difficulty>]
e.g. [mms_issue]bad_network_preference|break_apn_mms_setting[PERSONA:Hard].
Categories: mms_issue / mobile_data_issue / service_issue; personas: None/Easy/Hard.

Inputs (frozen copies, see versions.json):
  inputs/telecom_tasks_full.json   (2285 tasks; base 114 selected by split)
  inputs/telecom_split.json        (small 20 / train 74 / test 40 / full 2285 / base 114)

Outputs:
  split_manifest.json                     (public summary + frozen selection)
  private/telecom_coverage_detail.json    (per-task category detail)
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

ID_RE = re.compile(r"^\[(?P<cat>[^\]]+)\](?P<sub>.*?)\[PERSONA:(?P<persona>[^\]]+)\]$")
# Round-robin priority for dev selection: largest train category first.
CATEGORY_PRIORITY = ["mms_issue", "mobile_data_issue", "service_issue"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def parse_id(tid: str):
    m = ID_RE.match(tid)
    if not m:
        return {"category": "unparsed", "persona": "unparsed", "components": []}
    return {
        "category": m.group("cat"),
        "persona": m.group("persona"),
        "components": sorted(m.group("sub").split("|")),
    }


def main() -> None:
    tasks = json.loads((INPUTS / "telecom_tasks_full.json").read_text(encoding="utf-8"))
    split = json.loads((INPUTS / "telecom_split.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in tasks}
    base, train, test = list(split["base"]), list(split["train"]), list(split["test"])
    small = list(split.get("small", []))

    checks = {
        "task_ids_all_valid": all(i in by_id for i in train + test),
        "train_test_disjoint": not (set(train) & set(test)),
        "base_equals_union": set(base) == (set(train) | set(test)),
        "counts": {"train": len(train), "test": len(test), "base": len(base), "small": len(small)},
        "small_subset_of_base": set(small) <= set(base),
    }
    assert checks["task_ids_all_valid"] and checks["train_test_disjoint"]
    assert checks["base_equals_union"]

    detail = {}
    for tid in base:
        task = by_id[tid]
        parsed = parse_id(tid)
        ec = task.get("evaluation_criteria") or {}
        names = [a.get("name") for a in ec.get("actions") or [] if isinstance(a, dict)]
        detail[tid] = {
            "split": "train" if tid in train else ("test" if tid in test else "base_only"),
            "category": parsed["category"],
            "persona": parsed["persona"],
            "components": parsed["components"],
            "tool_names": names,
            "reward_basis": list(ec.get("reward_basis") or []),
        }

    cat_counts = {
        "train": dict(Counter(detail[t]["category"] for t in train)),
        "test": dict(Counter(detail[t]["category"] for t in test)),
    }
    persona_counts = {
        "train": dict(Counter(detail[t]["persona"] for t in train)),
        "test": dict(Counter(detail[t]["persona"] for t in test)),
    }

    # ---- dev selection: one per category (seed 42), then round-robin ----
    rng = random.Random(DEV_SEED)
    shuffled = {}
    for cat in CATEGORY_PRIORITY:
        candidates = sorted(t for t in train if detail[t]["category"] == cat)
        rng.shuffle(candidates)
        shuffled[cat] = candidates
    dev_ids, dev_detail = [], {}
    order = [c for c in CATEGORY_PRIORITY]
    round_i = 0
    while len(dev_ids) < DEV_COUNT and any(shuffled[c] for c in order):
        cat = order[round_i % len(order)]
        round_i += 1
        if not shuffled[cat]:
            continue
        chosen = shuffled[cat].pop(0)
        dev_ids.append(chosen)
        dev_detail[chosen] = {"category": cat, "persona": detail[chosen]["persona"]}
    evolve_ids = [t for t in train if t not in set(dev_ids)]

    # ---- relatedness ---------------------------------------------------
    tr_comp, te_comp = Counter(), Counter()
    for t in train:
        tr_comp.update(detail[t]["components"])
    for t in test:
        te_comp.update(detail[t]["components"])
    shared_components = sorted(set(tr_comp) & set(te_comp))

    def instruction(tid: str) -> str:
        scenario = by_id[tid].get("user_scenario") or {}
        inst = scenario.get("instructions")
        if isinstance(inst, dict):
            return json.dumps(inst, sort_keys=True, ensure_ascii=False)
        return str(inst or "")

    # Instruction strings are category-level templates (same reason_for_call /
    # known_info per category). Verify template structure instead of similarity
    # pairs: count distinct instruction strings per category per split.
    templates = {}
    for split_name, ids in (("train", train), ("test", test)):
        per_cat = defaultdict(set)
        for t in ids:
            per_cat[detail[t]["category"]].add(instruction(t))
        templates[split_name] = {c: len(s) for c, s in per_cat.items()}

    evolve_cats = set(detail[t]["category"] for t in evolve_ids)
    test_needs = {
        t: {"category": detail[t]["category"],
            "covered_by_evolve_category": detail[t]["category"] in evolve_cats}
        for t in sorted(test)
    }

    manifest = {
        "domain": "telecom",
        "tau2_version": "v1.0.1",
        "inputs": {
            "tasks_full_sha256": sha256(INPUTS / "telecom_tasks_full.json"),
            "split_sha256": sha256(INPUTS / "telecom_split.json"),
            "main_policy_sha256": sha256(INPUTS / "telecom_main_policy.md"),
            "tech_support_manual_sha256": sha256(INPUTS / "telecom_tech_support_manual.md"),
            "db_sha256": sha256(INPUTS / "telecom_db.toml"),
            "user_db_sha256": sha256(INPUTS / "telecom_user_db.toml"),
        },
        "checks": checks,
        "counts": {"train": len(train), "test": len(test),
                    "dev": len(dev_ids), "evolution": len(evolve_ids)},
        "dev_selection": {
            "rule": "one task per category in priority [mms_issue,mobile_data_issue,service_issue], "
                    "each category's sorted train ids shuffled with random.Random(42); then continue "
                    "round-robin over categories until 4 dev tasks. No test data consulted.",
            "seed": DEV_SEED,
            "dev_ids": dev_ids,
            "dev_categories": dev_detail,
        },
        "train_ids": sorted(train),
        "test_ids": sorted(test),
        "evolution_ids": sorted(evolve_ids),
        "category_counts": cat_counts,
        "persona_counts": persona_counts,
        "relatedness": {
            "shared_subissue_components": shared_components,
            "shared_component_count": len(shared_components),
            "instruction_templates_distinct_per_category": templates,
            "templates_note": "user_scenario.instructions are identical templates within a "
                              "category (verified); task identity = issue-combination path + persona.",
        },
        "test_primary_coverage": test_needs,
        "exposure_notes": [
            "Gold action names/ids used only for this researcher-facing audit; "
            "no gold content flows into Collector/AutoSkill/Consumer inputs.",
            "Telecom reward_basis is [ENV_ASSERTION] (2253 tasks) or [ENV_ASSERTION, ACTION] (32); "
            "state-checked, no judge model for the main reward.",
        ],
    }
    (ROOT / "split_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "private" / "telecom_coverage_detail.json").write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding="utf-8")

    print("counts:", manifest["counts"])
    print("dev:", dev_ids, dev_detail)
    print("train categories:", cat_counts["train"])
    print("test categories:", cat_counts["test"])
    print("persona counts:", persona_counts)
    print("shared components:", len(shared_components), shared_components[:10])
    print("instruction templates per category:", templates)
    print("test tasks w/o evolve-category coverage:",
          [t for t, v in test_needs.items() if not v["covered_by_evolve_category"]])


if __name__ == "__main__":
    main()
