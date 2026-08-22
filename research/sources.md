# Sumber riset pembeli — CAT-1 Phase B

Format: `S<n> | judul | lokasi | tanggal akses | kedalaman`

**Kedalaman** menandai seberapa jauh sumber benar-benar dibaca, dan ini bagian dari
pagar kejujuran — bukan basa-basi:

- `penuh` — halaman diambil utuh dan dibaca; angka di dalamnya boleh dikutip.
- `cuplikan` — hanya ringkasan hasil pencarian yang terbaca. Boleh dipakai untuk
  arah dan keberadaan isu, **tidak boleh** jadi sumber angka.
- `arsip` — dokumen internal, dibaca langsung dari disk.

Klaim di `buyer-brain.md` yang membawa angka wajib bersandar pada sumber `penuh`
atau `arsip`. Klaim yang hanya bersandar pada `cuplikan` ditulis tanpa angka.

## Eksternal

S1 | Akibat Solar Langka, Pengusaha Logistik di Surabaya Rugi Rp 1 Juta Per Truk Per Hari (DPC Aptrindo Surabaya, I Wayan Sumadita) | https://aptrindo.id/akibat-solar-langka-pengusaha-logistik-di-surabaya-rugi-rp-1-juta-per-truk-per-hari/ | 2026-08-22 | penuh
S2 | Margin Tergerus, Operator Logistik Tak Mampu Lagi Tahan Lonjakan Biaya (ALFI Trismawan Sanjaya; MTI Raja Oloan Saut Gurning), Bisnis.com 13 Juli 2026 | https://ekonomi.bisnis.com/read/20260713/98/1987519/margin-tergerus-operator-logistik-tak-mampu-lagi-tahan-lonjakan-biaya | 2026-08-22 | penuh
S3 | Biaya Logistik Naik, Asosiasi Pengusaha Truk Minta Evaluasi Kebijakan Pelabuhan, Kontan | https://industri.kontan.co.id/news/biaya-logistik-naik-asosiasi-pengusaha-truk-minta-evaluasi-kebijakan-pelabuhan | 2026-08-22 | cuplikan
S4 | Aptrindo keberatan atas pengaturan pembatasan — risiko kongesti pelabuhan + denda penumpukan, Kontan (via arsip sosial) | https://www.facebook.com/KontanNews/posts/1213446160450685/ | 2026-08-22 | cuplikan
S5 | Gemilang Tarigan (Ketua Umum DPP Aptrindo) — evaluasi tarif OPP/OPT kargo di pelabuhan, DPW ALFI Jakarta | http://www.alfijakarta.com/wp/tag/gemilang-tarigan/ | 2026-08-22 | cuplikan
S6 | 4 Kendala Umum Fleet Management di Indonesia dan Cara Mengatasinya, Cartrack Indonesia | https://www.cartrack.id/id/4-kendala-umum-fleet-management-di-indonesia-dan-cara-mengatasinya | 2026-08-22 | cuplikan
S7 | Pencurian Truk: Ancaman bagi Industri Logistik, Cartrack Indonesia | https://cartrack.id/id/pencurian-truk-ancaman-bagi-industri-logistik | 2026-08-22 | cuplikan
S8 | Jasa Pembuatan Sistem Fleet Management & Tracking Cargo — "admin harus bertanya kepada driver satu per satu" | https://masuk-ptn.com/artikel/detail/jasa-pembuatan-sistem-fleet-management-dan-tracking-cargo | 2026-08-22 | cuplikan
S9 | Cara Menghitung Biaya Ritase, Mobitech | https://mobitech.id/cara-menghitung-biaya-ritase/ | 2026-08-22 | cuplikan
S10 | Diskusi biaya angkutan darat — struktur biaya operasional kendaraan, milis Supply Chain Indonesia | https://groups.google.com/g/supplychainindonesia/c/1L4YwJ0pCgY | 2026-08-22 | cuplikan
S11 | Penentuan Tarif Pengiriman Barang Berdasarkan Biaya Operasional Kendaraan (studi kasus operator truk), ResearchGate | https://www.researchgate.net/publication/393476449 | 2026-08-22 | cuplikan
S12 | Demurrage: Pahami Denda Saat Akan Ekspor-Impor Barang, Transcon Indonesia | https://www.transcon-indonesia.com/id/blog/demurrage-pahami-denda-saat-akan-ekspor-impor-barang | 2026-08-22 | cuplikan
S13 | National Logistics Ecosystem — Terobosan Dorong Performa Logistik, Kementerian Keuangan RI | https://www.kemenkeu.go.id/informasi-publik/publikasi/berita-utama/National-Logistics-Ecosystem | 2026-08-22 | cuplikan
S14 | Penerapan Teknologi Digital di Pelabuhan Indonesia untuk Menurunkan Biaya Logistik Nasional, Jurnal Manajemen Transportasi & Logistik ITL Trisakti | https://journal.itltrisakti.ac.id/index.php/jmtranslog/article/download/738/pdf | 2026-08-22 | cuplikan

## Internal (arsip sendiri)

S15 | Playbook Cargo Logistics — pelajaran operasional lintas gelombang build | vault `30-Knowledge/playbook-cargo-logistics.md` | 2026-08-22 | arsip
S16 | Standar Deck Penawaran B2B — §6 pagar kejujuran, §7 harga & kit urgensi, §11 asumsi & penjualan berfase, §12 menu modular | vault `30-Knowledge/deck-b2b-standard.md` | 2026-08-22 | arsip
S17 | IRN-Logistik README — posisi platform, skala terverifikasi, batas klaim | vault `20-Projects/IRN-Logistik/README.md` | 2026-08-22 | arsip
S18 | Kontrak konten publik operator referensi — cakupan layanan yang disetujui dan daftar larangan publikasi | repo `indusia-ai-logistics/docs/content/irn-public-content-contract.md` | 2026-08-22 | arsip

## Catatan NotebookLM

Notebook dibuat: `19929772-160a-4103-a08b-fd29aebe1932` — "CAT-1 riset pembeli
logistik Indonesia". Sumber eksternal dimasukkan ke sana supaya tim marketing bisa
menanyainya ulang belakangan.

NotebookLM **tidak dipakai sebagai penulis** riset ini. Alasannya tercatat di vault
(2026-08-08): NotebookLM pernah mengarang — mengklaim sebuah dokumen 111 halaman
padahal aslinya 22, dan salah memetakan struktur sebuah bagan. Setiap angka di
`buyer-brain.md` diambil dari halaman aslinya yang dibaca langsung, bukan dari
ringkasan NotebookLM.
