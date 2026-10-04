#!/usr/bin/env bash
# v4 paired evaluation: B0 (no_skill) + B1 (autoskill_library), both groups in
# parallel (8 + 8 = 16 concurrent). Consumer & user simulator = DeepSeek
# (deepseek-flash); native $skill prompt references active for B1; no wallclock
# cutoff; judge unchanged (GLM with fence-strip + retries). Results: runs/test_v4/.
set -u
cd /mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs
export TAU2_RETAIL_USER_MODEL=openai/deepseek-flash
export TAU2_RETAIL_USER_BASE=http://127.0.0.1:8141/tau2_retail/user/v1

export TAU2_RETAIL_GROUP=no_skill
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group no_skill \
  --tasks test --num-trials 4 --concurrency 8 \
  --result runs/test_v4/no_skill.json > /var/tmp/skillsloop148_v4_b0.log 2>&1 &
P0=$!

export TAU2_RETAIL_GROUP=autoskill_library
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group autoskill_library \
  --tasks test --num-trials 4 --concurrency 8 \
  --result runs/test_v4/autoskill_library.json > /var/tmp/skillsloop148_v4_b1.log 2>&1 &
P1=$!

wait $P0 $P1
echo "v4 test phase complete $(date -Is)" >> /var/tmp/skillsloop148_v4_phase.status
