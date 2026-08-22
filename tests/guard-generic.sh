#!/usr/bin/env bash
# CAT-1 Phase C — references/ hanya boleh memuat pengetahuan GENERIK.
# Nama klien, kota sasaran, warna merek, dan identitas pribadi adalah
# runtime input — lihat gaspol-pitch/CLAUDE.md aturan keras #2 dan #3.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

[ -d references ] || { echo "GUARD ERROR: references/ tidak ada"; exit 1; }
[ -d skills ] || { echo "GUARD ERROR: skills/ tidak ada"; exit 1; }

# Nama klien, kota, identitas pribadi.
PAT='indusia|irn[ -]?cargo|indrajaya|yafindo|ekaputra|tranzporter|global pratama|hub71|alisadikin|0F59B6|batam|pekanbaru|makassar'
hits=$(grep -rniE "$PAT" references/ skills/ 2>/dev/null || true)
if [ -n "$hits" ]; then
  echo "GUARD FAIL — isi spesifik-klien di references/ atau skills/:"
  echo "$hits"
  exit 1
fi

# Alamat basis-pengetahuan. catalog-brainstorm BOLEH menyuruh mencari second brain;
# ia TIDAK BOLEH memuat alamatnya. Path absolut dan nama vault adalah runtime input.
ADDR='/Users/|/home/[a-z]|C:\\Users|Drive-D|Obsidian-Vault|obsidian-vault|20-Projects|10-Identity|90-Inbox'
addr_hits=$(grep -rniE "$ADDR" references/ skills/ 2>/dev/null || true)
if [ -n "$addr_hits" ]; then
  echo "GUARD FAIL — alamat basis-pengetahuan ter-hardcode (harus runtime input):"
  echo "$addr_hits"
  exit 1
fi

echo "guard OK — references/ + skills/ generik, nol alamat ter-hardcode"
