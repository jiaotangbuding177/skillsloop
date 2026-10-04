#!/usr/bin/env bash
# 268 telecom learning chain: canonicalize -> AutoSkill trajectory build -> freeze.
set -u
cd /mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill
export TAU2_RETAIL_RELAY=http://127.0.0.1:8181
LOG=/var/tmp/skillsloop268_learn.log

echo "LEARN CHAIN START $(date -Is)" >> /var/tmp/skillsloop268_phase.status
runtime_py/bin/python scripts/canonicalize_trajectory.py >> "$LOG" 2>&1
echo "canonicalize rc=$? $(date -Is)" >> "$LOG"
runtime_py/bin/python scripts/autoskill_build_trajectory.py >> "$LOG" 2>&1
echo "autoskill rc=$? $(date -Is)" >> "$LOG"
runtime_py/bin/python scripts/freeze_skills.py >> "$LOG" 2>&1
echo "freeze rc=$? $(date -Is)" >> "$LOG"
echo "LEARN CHAIN DONE $(date -Is)" >> /var/tmp/skillsloop268_phase.status
