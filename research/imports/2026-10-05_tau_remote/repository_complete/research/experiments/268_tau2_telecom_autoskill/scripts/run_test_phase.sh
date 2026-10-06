#!/usr/bin/env bash
# Paired evaluation: B0 (no_skill) then B1 (autoskill_library), same tasks,
# 4 trials each, identical seeds per trial (seed=42 base in run_wrapper).
set -u
cd /mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs

export TAU2_RETAIL_GROUP=no_skill
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group no_skill \
  --tasks test --num-trials 4 --concurrency 12 \
  --result runs/test/no_skill.json > /var/tmp/skillsloop148_test_b0.log 2>&1

export TAU2_RETAIL_GROUP=autoskill_library
runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group autoskill_library \
  --tasks test --num-trials 4 --concurrency 12 \
  --result runs/test/autoskill_library.json > /var/tmp/skillsloop148_test_b1.log 2>&1

echo "test phase complete $(date -Is)" >> /var/tmp/skillsloop148_test_phase.status
