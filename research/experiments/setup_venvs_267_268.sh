#!/usr/bin/env bash
# Setup venvs for 267/268 by cloning 148's runtime and re-pointing the editable
# tau2 install at the new per-experiment vendor copy.
set -u
cd /mnt/d/skillloop/research/experiments
SRC=148_tau2_retail_autoskill/runtime_py
for dst in 267_tau2_airline_autoskill 268_tau2_telecom_autoskill; do
  if [ -d "$dst/runtime_py" ]; then
    echo "$dst/runtime_py already exists, skipping copy"
  else
    cp -r "$SRC" "$dst/runtime_py"
  fi
  echo "--- re-pointing editable tau2 for $dst"
  "$dst/runtime_py/bin/python" -m pip install -e "$PWD/$dst/vendor/tau2-bench" --no-deps --no-build-isolation 2>&1 | tail -2
  "$dst/runtime_py/bin/python" -c "import tau2, sys; print('tau2 at:', tau2.__file__)"
done
echo SETUP_DONE
