#!/usr/bin/env bash
# Echo the number of scored simulations in a result JSON (arg 1 = path).
set -u
cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill
./runtime_py/bin/python - "$1" <<'PYEOF'
import json
import sys
try:
    d = json.loads(open(sys.argv[1]).read())
    print(len([s for s in d.get("simulations", []) if (s.get("reward_info") or {}).get("reward") is not None]))
except Exception:
    print(0)
PYEOF
