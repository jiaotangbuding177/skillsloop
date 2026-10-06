#!/usr/bin/env bash
# 267 airline dev smoke: ensure relay on 8180, run dev 4 tasks x 1 trial.
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
export TAU2_RETAIL_MAX_REQUESTS=60000

# our relay identifies itself with requests_reserved; anything else on the port is a conflict
if curl -s --max-time 3 http://127.0.0.1:8180/health 2>/dev/null | grep -q "requests_reserved"; then
  echo "267 relay already up"
else
  echo "starting 267 relay on 8180"
  setsid nohup runtime_py/bin/python scripts/model_relay.py > /var/tmp/skillsloop267_relay.log 2>&1 < /dev/null &
  sleep 6
fi
curl -s --max-time 5 http://127.0.0.1:8180/health; echo

echo "=== dev smoke start $(date -Is)"
runtime_py/bin/python scripts/run_wrapper.py --phase dev --group no_skill \
  --tasks dev --num-trials 1 --concurrency 4 \
  --result runs/dev/no_skill.json > /var/tmp/skillsloop267_dev.log 2>&1
echo "dev smoke finished $(date -Is)" >> /var/tmp/skillsloop267_phase.status
