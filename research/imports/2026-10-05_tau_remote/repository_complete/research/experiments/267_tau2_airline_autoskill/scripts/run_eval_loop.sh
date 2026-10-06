#!/usr/bin/env bash
# Resilient 267 airline paired evaluation: B0 + B1 in parallel (6+6), test 20 x 4 trials.
set -u
cd /mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill
export TAU2_RETAIL_DOMAIN=airline
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/runs
export TAU2_RETAIL_RELAY_PORT=8180
export TAU2_RETAIL_RELAY_BASE=http://127.0.0.1:8180/tau2_retail/consumer/v1
export TAU2_RETAIL_USER_MODEL=openai/deepseek-flash
export TAU2_RETAIL_USER_BASE=http://127.0.0.1:8180/tau2_retail/user/v1
export TAU2_RETAIL_JUDGE_BASE=http://127.0.0.1:8180/tau2_retail/judge/v1
export TAU2_RETAIL_MAX_REQUESTS=60000
export TAU2_RETAIL_FROZEN_DIR=/mnt/d/skillloop/research/experiments/267_tau2_airline_autoskill/frozen_skills

B0=runs/test/no_skill.json
B1=runs/test/autoskill_library.json
TARGET=80
COUNT=scripts/completed_count.sh

for attempt in $(seq 1 300); do
  if ! curl -s --max-time 3 http://127.0.0.1:8180/health 2>/dev/null | grep -q "requests_reserved"; then
    setsid nohup ./runtime_py/bin/python scripts/model_relay.py > /var/tmp/skillsloop267_relay.log 2>&1 < /dev/null &
    sleep 6
  fi
  n0=$(./$COUNT "$B0"); n1=$(./$COUNT "$B1")
  if [ "$n0" -ge "$TARGET" ] && [ "$n1" -ge "$TARGET" ]; then
    echo "EVAL COMPLETE B0=$n0 B1=$n1 $(date -Is)" >> /var/tmp/skillsloop267_phase.status
    exit 0
  fi
  echo "=== eval attempt $attempt: B0=$n0/80 B1=$n1/80 $(date -Is)" >> /var/tmp/skillsloop267_eval.log
  if [ "$n0" -lt "$TARGET" ]; then
    TAU2_RETAIL_GROUP=no_skill ./runtime_py/bin/python scripts/run_wrapper.py --phase evaluate \
      --group no_skill --tasks test --num-trials 4 --concurrency 6 \
      --result "$B0" >> /var/tmp/skillsloop267_eval.log 2>&1 &
    P0=$!
  fi
  if [ "$n1" -lt "$TARGET" ]; then
    TAU2_RETAIL_GROUP=autoskill_library ./runtime_py/bin/python scripts/run_wrapper.py --phase evaluate \
      --group autoskill_library --tasks test --num-trials 4 --concurrency 6 \
      --result "$B1" >> /var/tmp/skillsloop267_eval.log 2>&1 &
    P1=$!
  fi
  [ -n "${P0:-}" ] && wait $P0
  [ -n "${P1:-}" ] && wait $P1
  unset P0 P1
  sleep 20
done
echo "EVAL LOOP EXHAUSTED $(date -Is)" >> /var/tmp/skillsloop267_phase.status
