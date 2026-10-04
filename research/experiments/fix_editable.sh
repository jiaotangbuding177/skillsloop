#!/usr/bin/env bash
# Fix the editable tau2 path in a cloned venv: point it at the local vendor.
# Usage: fix_editable.sh <experiment_dir>   (relative to experiments root or absolute)
set -u
EXP="$1"
cd "$EXP"
SP="runtime_py/lib/python3.12/site-packages"
VENDOR_ABS="$PWD/vendor/tau2-bench"
PTH="$SP/_editable_impl_tau2.pth"
if [ -f "$PTH" ]; then
  printf '%s\n' "$VENDOR_ABS/src" > "$PTH"
  echo "pth -> $(cat "$PTH")"
else
  echo "pth missing: $PTH"
fi
DU="$SP/tau2-1.0.1.dist-info/direct_url.json"
if [ -f "$DU" ]; then
  printf '{"dir_info": {"editable": true}, "url": "file://%s"}\n' "$VENDOR_ABS" > "$DU"
  echo "direct_url -> $(cat "$DU")"
fi
echo "--- verify import:"
runtime_py/bin/python -c "import tau2; print(tau2.__file__)"
runtime_py/bin/python -c "import tau2.registry; print('registry ok')"
