#!/usr/bin/env bash
# CAT-1 — gerbang uji gaspol-catalog. Nol dependensi selain bash + grep + awk.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
rc=0
for t in deps-present.sh research-contract.sh guard-generic.sh \
         frontmatter.sh refs-present.sh fixture-shape.sh; do
  [ -f "$t" ] || { echo "SKIP $t (belum ada)"; continue; }
  echo "=== $t"
  bash "$t" || rc=1
done
PY="$HOME/.gaspol-video/venv/bin/python"
if [ -x "$PY" ]; then
  echo "=== python unittest"
  (cd .. && "$PY" -m unittest discover -s tests/py -t .) || rc=1
else
  echo "SKIP python (venv absent)"
fi
[ "$rc" -eq 0 ] && echo "ALL GREEN" || echo "SOME RED"
exit "$rc"
