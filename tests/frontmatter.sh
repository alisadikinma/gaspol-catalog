#!/usr/bin/env bash
# CAT-1 Phase C — SKILL.md frontmatter hanya boleh punya name + description.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0
found=0

for f in skills/*/SKILL.md; do
  [ -f "$f" ] || continue
  found=$((found + 1))
  head -1 "$f" | grep -qx -- '---' || { echo "$f: baris 1 bukan ---"; fail=1; continue; }
  keys=$(awk 'NR>1{ if ($0 == "---") exit; if ($0 ~ /^[A-Za-z_-]+:/) { sub(/:.*/, ""); print } }' "$f")
  [ -n "$keys" ] || { echo "$f: frontmatter kosong"; fail=1; }
  for k in $keys; do
    case "$k" in
      name|description) ;;
      *) echo "$f: kunci frontmatter terlarang '$k'"; fail=1 ;;
    esac
  done
  for req in name description; do
    printf '%s\n' "$keys" | grep -qx -- "$req" || { echo "$f: '$req' hilang"; fail=1; }
  done
done

[ "$found" -eq 0 ] && { echo "frontmatter: nol SKILL.md ditemukan"; exit 1; }
[ "$fail" -eq 0 ] && echo "frontmatter OK — $found skill"
exit "$fail"
