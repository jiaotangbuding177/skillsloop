#!/usr/bin/env bash
# v2 paired evaluation, both groups in PARALLEL (B0 8 + B1 8 = 16 concurrent).
# auto_resume keeps any runs already completed in runs/test_v2/.
set -u
cd /mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs

export TAU2_RETAIL_GROUP=no_skill
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group no_skill \
  --tasks test --num-trials 4 --concurrency 8 \
  --result runs/test_v2/no_skill.json > /var/tmp/skillsloop148_v2_b0.log 2>&1 &
P0=$!

export TAU2_RETAIL_GROUP=autoskill_library
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group autoskill_library \
  --tasks test --num-trials 4 --concurrency 8 \
  --result runs/test_v2/autoskill_library.json > /var/tmp/skillsloop148_v2_b1.log 2>&1 &
P1=$!

wait $P0 $P1
echo "v2 test phase complete $(date -Is)" >> /var/tmp/skillsloop148_v2_phase.status
