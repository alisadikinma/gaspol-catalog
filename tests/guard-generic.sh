#!/usr/bin/env bash
# CAT-1 Phase C — references/ hanya boleh memuat pengetahuan GENERIK.
# Nama klien, kota sasaran, warna merek, dan identitas pribadi adalah
# runtime input — lihat gaspol-pitch/CLAUDE.md aturan keras #2 dan #3.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

[ -d references ] || { echo "GUARD ERROR: references/ tidak ada"; exit 1; }

PAT='indusia|irn[ -]?cargo|indrajaya|yafindo|ekaputra|tranzporter|global pratama|hub71|alisadikin|0F59B6|batam|pekanbaru|makassar'
hits=$(grep -rniE "$PAT" references/ 2>/dev/null || true)
if [ -n "$hits" ]; then
  echo "GUARD FAIL — isi spesifik-klien di references/:"
  echo "$hits"
  exit 1
fi
echo "guard OK — references/ generik"
