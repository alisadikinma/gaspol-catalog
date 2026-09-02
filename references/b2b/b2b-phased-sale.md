# Phased, Proof-First Selling for Capital Equipment

> Sumber pola: standar deck penawaran B2B internal, §11.3 (verifikasi lewat angka
> hidup), §11.6 (model penjualan berfase), §11.7 (struktur konsorsium). Digenerikkan.

Berlaku untuk penggelaran barang modal ke operator: pelacakan armada, akses gerbang,
sensor terpasang, sistem yang menyentuh alur kerja lapangan sehari-hari.

## Model penggelaran adalah keputusan penjual, bukan default plugin

⚠️ **Baca ini sebelum memakai tabel di bawah.** Berkas versi lama menulis pilot satu
lokasi sebagai model penjualan, dan `catalog-brainstorm` memakainya sebagai asumsi
pertanyaan linimasa. Yang dihasilkannya di satu deck nyata: sebuah slide yang meminta
prospek memulai di satu cabang dulu, pada penawaran yang penjualnya memang berniat
menggelar serentak. Penjualnya menghapus slide itu dan menyebutnya pemikiran yang
mengecilkan penawarannya sendiri.

Dua model, dua-duanya sah:

| | Pilot satu lokasi | Serentak |
|---|---|---|
| menurunkan | risiko pembeli | waktu sampai sistem utuh |
| menaikkan | peluang tutup pada pembeli yang berhati-hati | ukuran transaksi dan momentum |
| ongkosnya | pendapatan penuh tertunda; deck bisa terbaca sebagai penjual yang ragu pada produknya sendiri | prospek menanggung risiko yang lebih besar di depan, jadi bukti operasionalnya harus lebih kuat |
| cocok saat | teknologinya asing bagi pembeli, atau lokasinya sangat berbeda satu sama lain | penjual sudah punya penggelaran berjalan yang bisa ditunjuk, dan lokasinya seragam |

**Tanyakan, catat jawabannya di `brand.md`, dan susun linimasa dari jawaban itu.**
Pertanyaan linimasa di `catalog-brainstorm` tidak boleh lagi mengasumsikan salah satu.

Sisa berkas ini menjelaskan model berfase, dan berlaku **hanya kalau model itu yang
dipilih.**

## Survei → Pilot satu titik → Rollout

Bukti-konsep berfase di **satu lokasi** sebelum rollout penuh menurunkan risiko
pembeli dan membangun champion internal.

| Fase | Isi | Yang dibuktikan |
|---|---|---|
| **Survei** | pemetaan lapangan, data induk, integrasi yang ada | apa yang benar-benar ada, bukan apa yang diasumsikan |
| **Pilot** | satu lokasi, satu regu, cakupan sempit | sistemnya bekerja **di tempat mereka**, bukan di demo |
| **Rollout** | armada penuh, pendampingan lapangan | organisasinya sanggup memakainya |

## Kriteria sukses pilot ditandatangani SEBELUM fase berikutnya

Ini pasal yang paling sering dilewat, dan yang paling menentukan.

Kriteria terima **wajib ditandatangani prospek sebelum fase 2 dimulai**. Bentuknya
ambang terukur — laju kecocokan, throughput per jam, nol penolakan salah dalam N
percobaan — dan **prospek yang menulisnya**, bukan kita.

Dua hal terjadi sekaligus:

1. Mencegah penolakan *"tidak memenuhi ekspektasi saya"* yang tidak pernah diungkapkan
   di depan.
2. Memberi manajemen prospek **pelindung internal** untuk keputusan lanjut atau
   berhenti. Mereka membutuhkannya, dan penawaran yang menyediakannya lebih mudah
   disetujui daripada yang menjanjikan lebih banyak.

Kriteria yang **prospek** tulis adalah yang mengubah risiko jadi kredibilitas.
Kriteria yang kita tulis hanyalah janji dengan angka.

## Gerbang keluar bertanggal

Pasangan dari kriteria di atas: satu titik di mana prospek boleh **berhenti tanpa
tagihan** kalau kriteria tidak terpenuhi.

Verifikasi lewat bukti operasional, bukan lewat meyakinkan. Pertanyaan pembeli bukan
*"teknologi ini bisa apa"* melainkan *"angkanya boleh dipercaya tidak"* — dan yang
menjawabnya adalah dasbor yang bisa diklik, di mana tiap klaim punya perhitungan di
belakangnya dan angka di layar bersumber sama dengan angka di uji.

## Struktur konsorsium: satu titik SLA menghadap pembeli

Pengadaan menyukai **satu** kontak vendor untuk SLA dan jaminan layanan, tapi pembeli
juga tidak mau mengurus banyak vendor sendiri.

Bentuk yang bekerja: **pemimpin rekayasa sebagai pemegang SLA tunggal + mitra lokal
sebagai subkontraktor pemasangan**, dengan pembagian lingkupnya di lampiran
administrasi. Ini meringkas kerumitan vendor jadi satu pihak yang bertanggung jawab,
sementara kredibilitas rekayasa dan kapasitas layanan lokal dua-duanya tetap terlihat.

Pelengkapnya di meja: **posisikan kemitraan jangka panjang, bukan eksekusi proyek
pilot semata.** Menonjolkan perencanaan dan kapabilitas jangka panjang menandakan
pendekatan yang matang ke manajemen — menaikkan nilai yang dipersepsikan dan
membenarkan ukuran transaksi di luar keterlibatan transaksional.

## Kematangan platform ≠ kematangan modul

Platform bisa berjalan di produksi sementara modul spesifik-prospek di atasnya baru
dirakit pertama kali. **Dua-duanya wajib dilabeli terpisah di badan slide** — sebagai
penanda kecil yang menempel di modulnya, bukan sebagai slide pengakuan tersendiri
(lihat pagar kejujuran #12, yang direvisi persis di titik ini).

Modul baru tidak pernah dijual sebagai sesuatu yang sudah terbukti di banyak tempat.
Kalau model berfase yang dipilih, ia dijual sebagai **pilot dengan kriteria terima**;
kalau serentak yang dipilih, yang menggantikan perannya adalah kriteria terima per
fase di linimasa dan termin yang menahan angsuran terakhir sampai pendampingan
selesai. Mengaburkan keduanya adalah risiko terbesar deck yang
menyamar sebagai kekuatannya, dan itu memblokir di lapis (h).

## Peran perangkat keras adalah keputusan per-prospek

Perangkat yang sama bisa berperan sebagai **bukti** (dicatat, tidak pernah memicu
transisi) atau sebagai **gerbang** (secara fisik tidak membuka tanpa kecocokan).
Tingkat kepercayaannya berbeda, konsekuensi kegagalannya berbeda, dan pilihannya
mengikuti kebutuhan operasional prospek — bukan diwarisi dari penggelaran sebelumnya.

Jangan mengasumsikan peran dari deployment terakhir berlaku otomatis di prospek
berikutnya. Tanyakan.

## Degradasi anggun pada data induk

Data induk selalu tertinggal dari kenyataan. Sistem yang memblokir keras karena data
induk belum lengkap menciptakan kemacetan baru dan menghasilkan penolakan palsu.

Pola yang bekerja: pengayaan di sisi server + tampilan cadangan + verifikasi asinkron,
mengalahkan tolak-lalu-paksa-ulang. Ini juga jawaban terhadap keberatan *"data kami
belum siap"* — dijawab dengan perilaku sistem, bukan dengan janji bahwa datanya akan
beres.
