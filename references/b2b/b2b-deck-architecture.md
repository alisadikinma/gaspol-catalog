# B2B Offer-Deck Architecture

> Sumber pola: standar deck penawaran B2B internal, §5 (arsitektur), §5.1 (cover),
> §5.2 (pasangan cover-penutup), §5.3 (slide dampak), §5.4 (pita tepi babak),
> §5.5 (cliffhanger glyph), §1 (ciri pembaca). Digenerikkan: nol nama klien, nol
> nama kota, nol angka nyata.

## Kapan arsitektur ini berlaku

Dokumen penawaran komersial ke **manajemen perusahaan operasi**. Bukan carousel
sosial, bukan deck galang dana, bukan materi pelatihan.

Tiga ciri pembacanya menentukan seluruh aturan di bawah:

1. **Dokumen beredar tanpa penyajinya.** Dibuka di rapat oleh orang yang tidak hadir.
   Setiap slide berdiri sendiri.
2. **Ada yang menghitung.** Selalu ada satu orang keuangan yang membagi angka di
   kalkulator saat kita bicara.
3. **Yang dijual perusahaan, bukan orang.** Deck ini menjual badan usaha, bukan
   pendirinya.

## Delapan babak

```
1        COVER      ringkasan penawaran + durasi + tenggat
2 … n    ISSUES     temuan dari dokumen PROSPEK, satu temuan per slide
n+1 … m  SOLUTIONS  mekanisme, lalu satu slide DAMPAK sebelum/sesudah
m+1      LINIMASA   sumbu bulan, kaki "di luar lingkup"
m+2      NEXT       yang belum dibeli, berlencana
m+3      CTA        kuotasi + hitung mundur + harga sesudah tenggat
m+4      PENUTUP    gema cover + satu perintah
```

Sasaran ≤ 16 slide. Babak ISSUES tidak boleh kosong: penawaran tanpa temuan milik
prospek adalah brosur, bukan penawaran.

## Cover

Halaman pertama menjawab *"ini penawaran apa"* dalam lima detik. Aturan curiosity gap
milik konten, **bukan** milik penawaran.

Wajib memuat: kicker · headline masalah↔sistem · **durasi proyek** · **tenggat
harga**.

**Cover tidak memuat harga.** Rupiah di halaman pertama membuat pembaca menilai harga
sebelum melihat satu pun temuan.

Simetri N masalah → N sistem bercerita sendiri sebelum satu huruf dibaca.

## Cover dan penutup adalah satu pasangan berkas

Keduanya satu-satunya slide yang pasti dilihat semua orang. Gema antar keduanya yang
membuat deck terasa satu argumen, bukan tumpukan kartu.

**Ganti cover → penutup wajib diperiksa.** Cover dirombak sementara penutup masih
menggemakan slide lama langsung terbaca "tidak nyambung" tanpa pembacanya bisa
menunjuk sebabnya.

Tapi bukan salinan persis — headline penutup yang identik terbaca seperti deck
mengulang. Polanya: **bingkai sama kata per kata, klausa terakhir diganti jadi hal
yang berubah sepanjang deck.**

> `DUA MASALAH — DUA SISTEM YANG MENJAWABNYA`
> → `DUA MASALAH — DUA SISTEM — SATU KEPUTUSAN`

Penutup memuat **satu perintah saja**. Dua pilihan menghasilkan penundaan; satu
pilihan menghasilkan jawaban. Dilarang menaruh peta jalan atau chip fase di penutup —
itu mengembalikan pembaca ke mode berpikir jangka panjang persis di detik kita
meminta keputusan.

## Slide DAMPAK sebelum/sesudah

Slide yang paling sering hilang. Deck teknis menjelaskan mekanisme dengan sempurna
lalu tidak pernah memperlihatkan apa yang berubah. Manajemen tidak membeli
arsitektur, mereka membeli selisih hari kerja.

Bentuknya: dua pita bertumpuk, kiri kelabu berantakan → panah → kanan terang rapi.
Satu pita per masalah.

**Slide ini WAJIB nol rupiah dan nol persen.** Ia hanya membandingkan tiga hal proses:
**kapan** informasi datang, **bentuknya** apa, **tindakan** apa yang masih mungkin.
Satu angka penghematan di sana membatalkan baris "di luar lingkup".

## Pita tepi babak

Pita tegak setinggi kanvas di **tepi kiri**, teks diputar 90°. Satu warna untuk
ISSUES, warna aksen untuk SOLUTIONS. Hanya di slide isi; cover, linimasa, next, CTA,
dan penutup tanpa pita — babaknya memang sudah selesai.

**Kenapa tepi kiri, bukan pojok:** ketiga pojok yang naluriah selalu terisi di
sebagian slide (kiri-atas headline, kiri-bawah wordmark, kanan-atas chip). Tepi kiri
satu-satunya zona kosong di semua slide isi.

Pita **ditempel setelah render, tidak pernah digenerate** — lihat
`b2b-visual-contract.md`.

## Cliffhanger antar-slide

Kalau sebuah slide sengaja **menahan** satu angka supaya slide berikutnya bisa
menjawabnya sebagai payoff, tandai penahanannya dengan **satu glyph grafis besar**
(tanda tanya, panah) — bukan kalimat. Taruh bersebelahan dengan angka yang ditahan,
warna aksen, kontras rendah supaya terbaca dekorasi bukan fokus utama.

⚠️ **Jangan menjelaskan maksud glyph di prompt render yang sama.** Model gambar akan
mencetak kalimat penjelasnya literal sebagai teks di kanvas. Pisahkan: satu kalimat
maksud-desain di catatan operator, satu instruksi render yang murni menyebut bentuk
grafisnya.
