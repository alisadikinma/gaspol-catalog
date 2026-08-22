# Phased, Proof-First Selling for Capital Equipment

> Sumber pola: standar deck penawaran B2B internal, §11.3 (verifikasi lewat angka
> hidup), §11.6 (model penjualan berfase), §11.7 (struktur konsorsium). Digenerikkan.

Berlaku untuk penggelaran barang modal ke operator: pelacakan armada, akses gerbang,
sensor terpasang, sistem yang menyentuh alur kerja lapangan sehari-hari.

## Survei → Pilot satu titik → Rollout

Bukti-konsep berfase di **satu lokasi** sebelum rollout penuh menurunkan risiko
pembeli dan membangun champion internal. Ini menunda pendapatan penuh tapi menaikkan
peluang tutup — terutama saat pembelinya berhati-hati terhadap teknologi yang asing
baginya.

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
dirakit pertama kali. **Dua-duanya wajib dilabeli terpisah di badan slide.**

Modul baru dijual sebagai **pilot dengan kriteria terima**, tidak pernah sebagai
sesuatu yang sudah terbukti. Mengaburkan keduanya adalah risiko terbesar deck yang
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
