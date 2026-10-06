#!/usr/bin/env bash
# Resilient loop for 268 telecom dev smoke: 4 dev tasks x 1 trial.
set -u
cd /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill
export TAU2_RETAIL_DOMAIN=telecom
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill/runs
export TAU2_RETAIL_RELAY_PORT=8181
export TAU2_RETAIL_RELAY_BASE=http://127.0.0.1:8181/tau2_retail/consumer/v1
export TAU2_RETAIL_USER_MODEL=openai/deepseek-flash
export TAU2_RETAIL_USER_BASE=http://127.0.0.1:8181/tau2_retail/user/v1
export TAU2_RETAIL_JUDGE_BASE=http://127.0.0.1:8181/tau2_retail/judge/v1
export TAU2_RETAIL_MAX_REQUESTS=60000

RESULT=runs/dev/no_skill.json
TARGET=4

completed() {
  [ -f "$RESULT" ] || { echo 0; return; }
  ./runtime_py/bin/python - "$RESULT" <<'PYEOF'
import json, sys
try:
    d = json.loads(open(sys.argv[1]).read())
    print(len([s for s in d.get("simulations", []) if (s.get("reward_info") or {}).get("reward") is not None]))
except Exception:
    print(0)
PYEOF
}

for attempt in $(seq 1 200); do
  n=$(completed)
  if [ "$n" -ge "$TARGET" ]; then
    echo "DEV COMPLETE ($n/$TARGET) attempt=$attempt $(date -Is)" >> /var/tmp/skillsloop268_phase.status
    exit 0
  fi
  if ! curl -s --max-time 3 http://127.0.0.1:8181/health 2>/dev/null | grep -q "requests_reserved"; then
    setsid nohup ./runtime_py/bin/python scripts/model_relay.py > /var/tmp/skillsloop268_relay.log 2>&1 < /dev/null &
    sleep 6
  fi
  echo "=== attempt $attempt: $n/$TARGET done $(date -Is)" >> /var/tmp/skillsloop268_dev.log
  ./runtime_py/bin/python scripts/run_wrapper.py --phase dev --group no_skill \
    --tasks dev --num-trials 1 --concurrency 4 \
    --result "$RESULT" >> /var/tmp/skillsloop268_dev.log 2>&1
  sleep 20
done
echo "DEV LOOP EXHAUSTED $(date -Is)" >> /var/tmp/skillsloop268_phase.status
