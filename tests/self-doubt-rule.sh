#!/usr/bin/env bash
# Aturan penjual 2026-11-11: deck tidak pernah meremehkan kemampuan penjual. Kekurangan dibahas
# saat interview/rapat, bukan di slide. Uji: aturannya ada di pagar, di gate (BLOCKING), dan di
# skill penulis deck.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0
chk() { grep -q "$2" "$1" || { echo "MISSING self-doubt rule in $1"; fail=1; }; }
chk references/b2b/b2b-honesty-rails.md 'merendahkan kemampuan'
chk references/b2b/b2b-buyer-rubric.md 'merendahkan kemampuan'
chk skills/catalog-master/SKILL.md 'merendahkan kemampuan'
chk skills/catalog-variant/SKILL.md 'merendahkan kemampuan'
grep -q 'These four are \*\*BLOCKING on their own\*\*' references/b2b/b2b-buyer-rubric.md \
  || { echo "rubric: anti-pattern list not four BLOCKING items"; fail=1; }
[ "$fail" -eq 0 ] && echo "self-doubt rule OK"
exit "$fail"
