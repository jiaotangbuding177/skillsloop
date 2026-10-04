#!/usr/bin/env bash
# One-off setup: copy 148 pipeline scripts/tests into 267 (airline) and 268 (telecom).
set -u
cd /mnt/d/skillloop/research/experiments
SRC=148_tau2_retail_autoskill
for dst in 267_tau2_airline_autoskill 268_tau2_telecom_autoskill; do
  cp "$SRC"/scripts/*.py "$dst"/scripts/
  cp "$SRC"/scripts/*.sh "$dst"/scripts/
  cp -r "$SRC"/tests "$dst"/
  rm -rf "$dst"/tests/__pycache__
  cp "$SRC"/.gitignore "$dst"/
  cp "$SRC"/source_audit.md "$dst"/
done
echo "copied to 267: $(ls 267_tau2_airline_autoskill/scripts | wc -l) files"
echo "copied to 268: $(ls 268_tau2_telecom_autoskill/scripts | wc -l) files"
