#!/usr/bin/env bash
# CAT-1 Phase A — 19 skill prasyarat harus bisa dirouting Claude Code.
set -uo pipefail
missing=0

# getagentseal/founder-playbook — 12 dipakai (dari 16 terpasang)
for s in mom-test lean-startup storybrand made-to-stick influence \
         obviously-awesome 100m-offers monetizing-innovation traction \
         blue-ocean-strategy spin-selling crossing-the-chasm; do
  [ -e "$HOME/.claude/skills/$s/SKILL.md" ] \
    || { echo "MISSING founder-playbook: $s"; missing=1; }
done

# guia-matthieu/clawfu-skills — 7 (spin-selling SENGAJA tidak diambil, lihat gotcha)
for s in challenger-sale meddic-scorecard sandler-system \
         never-split-difference sales-narrative positioning pricing-strategy; do
  [ -e "$HOME/.claude/skills/$s/SKILL.md" ] \
    || { echo "MISSING clawfu: $s"; missing=1; }
done

[ "$missing" -eq 0 ] && echo "deps OK — 19/19"
exit "$missing"
