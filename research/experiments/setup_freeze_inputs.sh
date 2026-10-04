#!/usr/bin/env bash
# One-off: freeze airline inputs into 267; dump telecom purpose/category info.
set -u
cd /mnt/d/skillloop/research/experiments
PY=148_tau2_retail_autoskill/runtime_py/bin/python

# --- 267 airline frozen inputs ---
D=148_tau2_retail_autoskill/vendor/tau2-bench/data/tau2/domains/airline
mkdir -p 267_tau2_airline_autoskill/inputs
cp "$D/tasks.json" 267_tau2_airline_autoskill/inputs/airline_tasks.json
cp "$D/split_tasks.json" 267_tau2_airline_autoskill/inputs/airline_split.json
cp "$D/policy.md" 267_tau2_airline_autoskill/inputs/airline_policy.md
cp "$D/db.json" 267_tau2_airline_autoskill/inputs/airline_db.json
echo "airline inputs:"; ls -la 267_tau2_airline_autoskill/inputs/

# --- 268 telecom frozen inputs ---
D2=148_tau2_retail_autoskill/vendor/tau2-bench/data/tau2/domains/telecom
mkdir -p 268_tau2_telecom_autoskill/inputs
cp "$D2/tasks.json" 268_tau2_telecom_autoskill/inputs/telecom_tasks_full.json
cp "$D2/split_tasks.json" 268_tau2_telecom_autoskill/inputs/telecom_split.json
cp "$D2/main_policy.md" 268_tau2_telecom_autoskill/inputs/telecom_main_policy.md
cp "$D2/tech_support_manual.md" 268_tau2_telecom_autoskill/inputs/telecom_tech_support_manual.md
cp "$D2/db.toml" 268_tau2_telecom_autoskill/inputs/telecom_db.toml
cp "$D2/user_db.toml" 268_tau2_telecom_autoskill/inputs/telecom_user_db.toml
echo "telecom inputs:"; ls -la 268_tau2_telecom_autoskill/inputs/

# --- telecom purpose inspection ---
cd /mnt/d/skillloop/research/experiments
"$PY" - <<'PYEOF'
import json
from collections import Counter
from pathlib import Path
base = Path("148_tau2_retail_autoskill/vendor/tau2-bench/data/tau2/domains/telecom")
tasks = json.loads((base / "tasks.json").read_text())
split = json.loads((base / "split_tasks.json").read_text())
base_ids, train, test = set(split["base"]), set(split["train"]), set(split["test"])
by_id = {t["id"]: t for t in tasks}
found = [i for i in base_ids if i in by_id]
print("base:", len(base_ids), "train:", len(train), "test:", len(test), "found:", len(found))
purposes = Counter()
for i in base_ids:
    t = by_id.get(i)
    if not t:
        continue
    purposes[str((t.get("description") or {}).get("purpose"))[:90]] += 1
print("purposes in base (top 25):")
for p, c in purposes.most_common(25):
    print(f"  {c:4d}  {p}")
# small set purposes
small = set(split.get("small", []))
print("small ids sample:", sorted(small)[:5], "count:", len(small))
PYEOF
