#!/usr/bin/env bash
# CAT-1 Phase D — fixture buruk WAJIB tetap memuat cacat yang ditanam.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
B=references/b2b/examples/bad-catalog.md
G=references/b2b/examples/good-catalog.md
fail=0

for f in "$B" "$G"; do
  [ -f "$f" ] || { echo "MISSING fixture: $f"; fail=1; }
done
[ "$fail" -eq 1 ] && exit 1

# Enam cacat yang ditanam, satu per lapis review (lihat b2b-deck-rubric.md)
grep -qiE 'end-to-end terintegrasi|world-class|solusi menyeluruh' "$B" \
  || { echo "bad fixture kehilangan cacat: fluff B2B (lapis a)"; fail=1; }
grep -qE '^## (Harga|Solusi|Manfaat)[[:space:]]*$' "$B" \
  || { echo "bad fixture kehilangan cacat: headline label (lapis a)"; fail=1; }
awk '/^# COVER/,/^## /' "$B" | grep -qiE 'Rp|IDR|[0-9]+ *(juta|jt|miliar)' \
  || { echo "bad fixture kehilangan cacat: harga di cover (lapis b)"; fail=1; }
grep -qiE 'foto (founder|pendiri)|potret (founder|pendiri)|wajah' "$B" \
  || { echo "bad fixture kehilangan cacat: wajah manusia (lapis g)"; fail=1; }
grep -qiE 'sudah terbukti di ratusan|telah digunakan ribuan' "$B" \
  || { echo "bad fixture kehilangan cacat: klaim kematangan palsu (lapis h)"; fail=1; }
grep -qiE 'promo terbatas|hanya hari ini|kuota tinggal' "$B" \
  || { echo "bad fixture kehilangan cacat: urgensi tak berlaku (lapis i)"; fail=1; }

# Fixture baik WAJIB bersih dari keenamnya
grep -qiE 'world-class|end-to-end terintegrasi' "$G" \
  && { echo "good fixture tercemar fluff"; fail=1; }
awk '/^# COVER/,/^## /' "$G" | grep -qiE 'Rp|IDR' \
  && { echo "good fixture menaruh harga di cover"; fail=1; }

[ "$fail" -eq 0 ] && echo "fixture shape OK"
exit "$fail"
