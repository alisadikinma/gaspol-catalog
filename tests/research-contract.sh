#!/usr/bin/env bash
# CAT-1 Phase B — riset pembeli wajib punya bentuk yang bisa dikonsumsi rubrik.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0

for f in research/buyer-brain.md research/sources.md; do
  [ -f "$f" ] || { echo "MISSING: $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1

# Enam bagian wajib — ini yang dikonsumsi b2b-buyer-rubric.md (Phase F)
for h in "## Pemicu keputusan" "## Keberatan" "## Bahasa pembeli" \
         "## Bukti yang dipercaya" "## Pola pengadaan" "## Anti-pola"; do
  grep -qF "$h" research/buyer-brain.md \
    || { echo "MISSING heading: $h"; fail=1; }
done

# Tiap klaim wajib punya penanda sumber [S<n>]; nol penanda = riset tak tertelusur
claims=$(grep -cE '^\- ' research/buyer-brain.md || echo 0)
sourced=$(grep -cE '^\- .*\[S[0-9]+\]' research/buyer-brain.md || echo 0)
if [ "$claims" -ne "$sourced" ]; then
  echo "UNSOURCED: $((claims - sourced)) dari $claims klaim tanpa penanda [S<n>]"
  fail=1
fi

# Tiap [S<n>] yang dipakai wajib terdaftar di sources.md
for n in $(grep -oE '\[S[0-9]+\]' research/buyer-brain.md | sort -u | tr -d '[]S'); do
  grep -qE "^S${n}\b" research/sources.md \
    || { echo "DANGLING: [S${n}] tidak ada di sources.md"; fail=1; }
done

[ "$fail" -eq 0 ] && echo "research contract OK — $claims klaim, semua tertelusur"
exit "$fail"
