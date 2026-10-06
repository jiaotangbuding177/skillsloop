#!/usr/bin/env bash
# 267 airline collection: 26 evolution tasks x 1 trial (relay 8180 must be up).
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

if ! curl -s --max-time 3 http://127.0.0.1:8180/health 2>/dev/null | grep -q "requests_reserved"; then
  echo "267 relay missing; starting"
  setsid nohup runtime_py/bin/python scripts/model_relay.py > /var/tmp/skillsloop267_relay.log 2>&1 < /dev/null &
  sleep 6
fi

echo "=== collect start $(date -Is)"
runtime_py/bin/python scripts/run_wrapper.py --phase collect --group no_skill \
  --tasks evolution --num-trials 1 --concurrency 12 \
  --result runs/collect/evolution.json > /var/tmp/skillsloop267_collect.log 2>&1
echo "collect finished $(date -Is)" >> /var/tmp/skillsloop267_phase.status
