# Kontrak uji-diri CAT-1

Berkas ini dibaca manusia **dan** agen. Ia memetakan tiap cacat yang ditanam di
`references/b2b/examples/bad-catalog.md` ke lapis yang **wajib** menangkapnya.

Skrip di `tests/` memeriksa bentuk: berkas ada, cacat masih tertanam, frontmatter
sah, referensi lengkap. Skrip **tidak bisa** memeriksa verdict — itu dijalankan agen
dengan menjalankan `catalog-gate` terhadap kedua fixture.

**Plugin dinyatakan benar hanya kalau dua-duanya terpenuhi:**

- `bad-catalog.md` → **BLOCKING**, dengan tiap cacat menyebut lapis penangkapnya
- `good-catalog.md` → **PASS**

## Peta cacat → lapis

| # | Cacat di `bad-catalog.md` | Lokasi | Lapis penangkap |
|---|---|---|---|
| 1 | fluff B2B — `solusi end-to-end terintegrasi`, `world-class`, `tercanggih di kelasnya` | cover, slide 3, slide 4 | (a) Linguistic-Fluff |
| 2 | headline label bukan asersi — `Masalah`, `Solusi`, `Manfaat`, `Harga` | slide 2, 3, 6, 7 | (a) Assertion-vs-Topic |
| 3 | satu slide empat pesan digabung "dan" | slide 5 | (a) One-Message |
| 4 | persen telanjang tanpa baris artinya — `Hemat hingga 40%` | slide 6 | (a) Data-Parsing |
| 5 | harga di cover — `RP 450 JUTA` | cover | (b) arsitektur deck |
| 6 | aritmetika jangkar patah — `450jt × 17% = 373,5jt`, tertulis bayar `380jt` | slide 7 | (d) konsistensi |
| 7 | total rincian tidak cocok harga — `415jt` vs `380jt` | slide 7 vs 9 | (d) konsistensi |
| 8 | wajah manusia di slide | cover | (g) kontrak visual · Lapis 2 |
| 9 | kematangan modul disamakan platform — `sudah terbukti di ratusan perusahaan` untuk modul yang diklaim tercanggih | slide 4 | (e) gerbang bukti-operasi |
| 10 | urgensi tidak berlaku — `PROMO TERBATAS`, `HANYA HARI INI`, `Kuota tinggal 3` | slide 10 | (h) keabsahan kit urgensi |
| 11 | janji penghematan — `Hemat hingga 40%` | slide 6 | (g) pagar kejujuran 1 — **memblokir sendiri** |

Rencana menargetkan 8 cacat; fixture akhirnya membawa **11**, karena dua cacat
aritmetika ternyata independen (jangkar patah *dan* total rincian tidak cocok) dan
`Hemat hingga 40%` kena dua lapis berbeda — Data-Parsing di (a) dan janji penghematan
di (g). Cacat tambahan tidak dihapus: lebih banyak yang tertangkap lebih baik daripada
fixture yang dirapikan supaya cocok dengan rencana.

## Yang WAJIB dipenuhi `good-catalog.md`

| Yang diperiksa | Bukti di fixture | Lapis |
|---|---|---|
| headline asersi, nol label | tiap `##` sebuah klaim | (a) |
| angka berformat, nol angka dieja | `23%`, `412 dari 1.790`, `Rp 298.800.000` | (a) |
| satu pesan per slide | tiap slide satu pekerjaan | (a) |
| cover tanpa rupiah, dengan durasi + tenggat | `4 bulan · selesai 15 Desember · berlaku sampai 30 September` | (b) |
| slide DAMPAK nol rupiah nol persen | tabel kapan/bentuk/tindakan | (b) |
| penutup menggemakan cover, klausa akhir diganti, satu perintah | `DUA MASALAH, DUA SISTEM` → `DUA MASALAH, DUA SISTEM, SATU KEPUTUSAN` | (b) |
| aritmetika jangkar utuh | `360jt × 17% = 61,2jt`; `360 − 61,2 = 298,8` | (d) |
| rincian menjumlah ke headline | `149,4 + 89,64 + 34,86 + 24,9 = 298,8jt` | (d) |
| temuan milik prospek, bersumber | `412 dari 1.790 order`, rekap Januari–Juni | dimensi 1 |
| satuan yang pembeli hitung | order, panggilan per hari, perjalanan | dimensi 2 |
| dua lapis kematangan dipisah di badan slide | Lapis 1 berjalan / Lapis 2 rakitan pertama | (e) |
| jalan keluar risiko bertanggal | kriteria terima ditulis prospek, boleh berhenti tanpa tagihan | dimensi 6 |
| baris di luar lingkup ada | di slide linimasa, atau di kartu harga kalau linimasa tidak dipakai | (g) |
| temuan dibawa sebagai pertanyaan | "apakah selisih ini memang belum pernah ditelusuri?" | (g) |
| urgensi benar-benar berlaku | tenggat 30 Sept terikat tutup kuartal; mulai 1 Okt konsekuensinya; harga sesudah tenggat disebut | (h) |
| termin membayar risiko prospek | angsuran akhir setelah pendampingan | dimensi 9 |
| nol wajah manusia | catatan visual cover eksplisit | Lapis 2 |
| jalan keluar dari vendor dinyatakan | data milik prospek, ekspor terbuka gratis, waktu tanggap 4 jam, dua penyedia yang bisa saling menggantikan | (a) Platform-Risk |

## Aturan saat sebuah cacat lolos

**Perbaiki rubriknya, jangan fixture-nya.** Fixture buruk yang dirapikan supaya lolos
mengubah kontrak ini jadi bohong tanpa ada yang tahu — itulah yang dijaga
`tests/fixture-shape.sh`.

Satu pengecualian, dan arahnya berlawanan: kalau **fixture baik** melanggar sebuah
cek, periksa dulu apakah cek-nya benar. Kalau cek-nya benar, fixture baiknya yang
diperbaiki — ia memang harus mencontohkan praktik yang benar.

Ini sudah terjadi dua kali saat Phase L dijalankan:

1. Headline fixture baik semula berbunyi "Dua puluh tiga persen order…", melanggar
   `Data-Parsing`. Cek-nya benar, jadi headline-nya diubah jadi `23% order…`.
2. Fixture baik nol menyebut kepemilikan data, jalur ekspor, SLA, dan kelanjutan
   layanan — gagal `Platform-Risk`. Cek-nya benar dan justru penting untuk pembeli
   B2B, jadi blok "kalau suatu hari Anda berhenti memakai kami" ditambahkan ke slide
   linimasa.

Dua-duanya bukti kontrak ini bekerja: keduanya lolos pembacaan manusia dan baru
ketahuan saat rubriknya benar-benar dijalankan baris per baris.
