#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bend PROOF.bend
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
bend examples/export.bend -o "$build_dir/export"
bend examples/export.bend -o "$build_dir/export.js"
python3 scripts/check_x11.py "$build_dir/export"
