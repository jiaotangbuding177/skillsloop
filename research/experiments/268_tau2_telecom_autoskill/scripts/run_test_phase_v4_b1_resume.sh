#!/usr/bin/env bash
# v4-B1 resume after disk-full crash (2026-10-04 ~00:50).
# Same environment as run_test_phase_v4.sh B1 branch, plus frozen_skills_v2
# and auto_resume from runs/test_v4/autoskill_library.json (96/160 done).
# Consumer & user simulator = DeepSeek (deepseek-flash); native $skill refs active.
set -u
cd /mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill
export TAU2_RETAIL_RUN_ROOT=/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/runs
export TAU2_RETAIL_USER_MODEL=openai/deepseek-flash
export TAU2_RETAIL_USER_BASE=http://127.0.0.1:8141/tau2_retail/user/v1
export TAU2_RETAIL_GROUP=autoskill_library
export TAU2_RETAIL_FROZEN_DIR=/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2

runtime_py/bin/python scripts/run_wrapper.py --phase evaluate --group autoskill_library \
  --tasks test --num-trials 4 --concurrency 12 \
  --result runs/test_v4/autoskill_library.json > /var/tmp/skillsloop148_v4_b1v2d.log 2>&1
echo "v4-B1 resume finished $(date -Is)" >> /var/tmp/skillsloop148_v4_phase.status
