#!/usr/bin/env bash
# TEMPLATE (rb_unify) — review before use.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)/site"; PORT="${RB_PORT:-8080}"
[ -d "$D" ] || { echo "ERROR: $D missing; extract reference.tar.gz first" >&2; exit 1; }
CFG=(); [ -f "$D/serve.json" ] && CFG=(--config "$D/serve.json")
npx --yes serve "${CFG[@]}" --listen "$PORT" "$D" >/dev/null 2>&1 &
echo "RB_BASE_URL=http://127.0.0.1:$PORT"
