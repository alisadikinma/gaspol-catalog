# B2B Visual Contract and Render Guards

> Sumber pola: standar deck penawaran B2B internal, §2 (nol wajah), §3 (palet
> ko-branding), §4 (kontrak visual 60/40), §5.4 (pita babak), §8 (distribusi PDF),
> §9 (logo klien), §10.1–10.2 (rasio dan nada), plus tiga batch temuan render:
> §0b, §0c-C, §0d. Digenerikkan: nol hex, nol nama font merek, nol nama klien.

Berkas ini memberi makan **lapis render** `catalog-gate` — fase pemblokir tersendiri.

## Nol wajah manusia

**Tidak ada wajah manusia di slide mana pun.** Ini membatalkan default sebagian
pembangkit carousel yang mewajibkan wajah kreator di hook dan CTA.

Alasannya: wajah pendiri di halaman pertama membuat manajemen prospek menilai
**konsultan perorangan**, bukan perusahaan yang bisa dikontrak, ditagih, dan dituntut.
Covernya objek dan bukti, bukan orang.

Turunannya: **tidak ada sapaan personal** di teks yang dirender. Yang memutuskan
pembelian sebesar ini bukan satu orang — sebut institusinya.

## Kontrak visual 60/40

Pengendali paling menentukan seluruh tampilan: kira-kira 60% kanvas untuk bidang
visual (diagram, pita, bagan), 40% untuk teks. Slide yang melewati ambang itu ke arah
teks berhenti terbaca dalam lima detik dan gagal cek `5-Second Rule` di lapis (a).

## Palet ko-branding — satu warna, satu tugas

Palet runtime, bukan bawaan plugin. Aturannya struktural:

- satu warna struktur (pita babak ISSUES, header)
- satu warna aksen (SOLUTIONS, sorotan, glyph)
- netral untuk badan
- **satu warna, satu tugas.** Warna yang dipakai untuk dua hal berbeda di deck yang
  sama menghapus artinya.

Palet dan font spesifik merek adalah **runtime input**. Berkas ini tidak menyebut satu
pun nilai warna atau nama font — kalau ia menyebutnya, ia berhenti jadi kanon.

## Rasio dan nada

- **16:9, bukan 4:5.** Rasionya sendiri sebuah pesan: dokumen rapat, bukan unggahan
  sosial.
- **Terang dan korporat presisi, bukan sinematik gelap.** Deck penawaran dibaca di
  proyektor ruang rapat dan dicetak.

## Pagar render — model gambar mengulang dan mengarang

Ini pola sistemik, bukan kecelakaan. Tiap pagar di bawah lahir dari cacat yang
benar-benar lolos review teks.

### A. Duplikasi teks

Model gambar **mengulang** teks: kartu penuh dirender dua kali, label dicetak di dalam
**dan** di luar wadahnya. Terjadi di hampir separuh slide pada satu deck yang diukur.

Pagar wajib di tiap prompt: sebutkan bahwa tiap blok teks muncul **tepat satu kali**,
dan sebut wadahnya secara eksplisit ("label di dalam kartu, tidak diulang di luarnya").

### B. Angka dan frasa karangan

Model gambar **mengarang**: memunculkan angka yang tidak ada di naskah, dan mencetak
label dwibahasa yang tidak diminta.

Pagar: bake angka persis dari naskah, larang angka lain muncul di kanvas, dan larang
bahasa kedua kecuali diminta.

### C. Tiga kebocoran diam yang lolos review teks

Cacatnya lahir di **prompt**, bukan di naskah — jadi tidak ada pemeriksaan teks yang
bisa menangkapnya:

1. Instruksi "nol teks lain" menghapus headline yang seharusnya tercetak.
2. Kualifikasi terpotong (mis. "berdasarkan kompilasi sekunder" hilang separuh).
3. Disclaimer hilang saat prompt di-upgrade.

Pagar: setelah render, **bandingkan teks di gambar terhadap naskah baris per baris**.
Itu isi lapis render.

### D. Logo dan lockup

**Logo prospek tidak pernah digambar model gambar.** Sisakan slot kosong di prompt,
tempel berkasnya sesudah render. Wordmark prospek hasil render selalu salah bentuk,
dan wordmark yang salah di halaman pertama adalah cacat termahal di seluruh deck.

Kotak logo yang diminta ke model gagal hampir di semua slide pada satu deck yang
diukur — itu asal aturan ini.

Menempel logo di pojok kanan atas juga gagal berulang, karena panjang headline tidak
bisa dijamin dari prompt. Yang bekerja: taruh lockup **di dalam pita bawah** (versi
reversed, rata kiri), dan tabrakan jadi mustahil.

### E. Pita babak dan full-bleed

- Pita tepi babak **ditempel, tidak pernah digenerate**.
- Lebar pita sekitar 1,7% kanvas; ukuran font pita diskalakan ke lebar kanvas, bukan
  ditulis dalam piksel absolut — teks kecil tidak terbaca dari tiga meter.
- Deteksi tinggi pita saat QA memakai **proporsi piksel gelap**, bukan rata-rata
  luminansi.
- Frasa full-bleed yang bekerja menyebut **kolom piksel pertama dan terakhir**, bukan
  "edge to edge".

## Distribusi PDF

- **Watermark miring berulang menutupi seluruh halaman**, bukan satu cap di pojok. Cap
  pojok hilang begitu orang memotret satu bagian slide.
- Warna watermark mengikuti terang-gelap tiap halaman.
- Opasitas rendah, sekitar 5%. Lebih pekat dari itu ia bertarung dengan isinya.
- Baris kerahasiaan ditaruh di pita **di luar bidang slide** — halaman ditambah sedikit
  ke bawah. Di dalam, ia menabrak elemen lain sekarang atau di revisi berikutnya.

## Review render adalah fase tersendiri

Sebuah deck pernah **PASS di review teks dan BLOCKING di review render pada hari yang
sama**. Itu bukan anomali, itu strukturnya: naskahnya benar, promptnya yang salah.

Karena itu lapis render `catalog-gate` berjalan setelah PNG ada, memeriksa gambar
terhadap naskahnya, dan memblokir sendiri. Tanpa PNG ia melapor `NOT RUN` — **tidak
pernah** PASS.
