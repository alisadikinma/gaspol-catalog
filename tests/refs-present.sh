#!/usr/bin/env bash
# CAT-1 — tiap berkas references/b2b yang dimuat skill harus ada dan tidak kosong.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0
for f in b2b-deck-rubric.md b2b-buyer-rubric.md b2b-deck-architecture.md \
         b2b-honesty-rails.md b2b-visual-contract.md b2b-phased-sale.md \
         enablement-kit.md; do
  p="references/b2b/$f"
  if [ ! -f "$p" ]; then echo "MISSING ref: $p"; fail=1; continue; fi
  n=$(wc -l < "$p")
  [ "$n" -ge 20 ] || { echo "TOO THIN: $p ($n baris, minimal 20)"; fail=1; }
done
[ "$fail" -eq 0 ] && echo "refs OK — 7 berkas"
exit "$fail"
