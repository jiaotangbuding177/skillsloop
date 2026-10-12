#!/usr/bin/env bash
set -euo pipefail
# Usage:
#   URL1=... URL2=... SHA256=... OUTPUT=package.zip EXTRACT_DIR=package bash bootstrap.sh
: "${URL1:?Set URL1}"
OUTPUT="${OUTPUT:-package.zip}"
EXTRACT_DIR="${EXTRACT_DIR:-package}"
ARGS=(--url "$URL1" --output "$OUTPUT" --extract "$EXTRACT_DIR")
if [ -n "${URL2:-}" ]; then ARGS+=(--fallback "$URL2"); fi
if [ -n "${URL3:-}" ]; then ARGS+=(--fallback "$URL3"); fi
if [ -n "${SHA256:-}" ]; then ARGS+=(--sha256 "$SHA256"); fi
python3 "$(dirname "$0")/scripts/fetch_artifact.py" "${ARGS[@]}"
