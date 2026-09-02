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

## Enam babak wajib

```
1        COVER      hook + ringkasan penawaran + durasi + tenggat
2 … a    MASALAH    temuan dari dokumen PROSPEK, satu temuan per slide
a+1 … b  SOLUSI     mekanisme — cara kerjanya, lalu satu slide DAMPAK sebelum/sesudah
b+1 … c  PRODUK     yang benar-benar mereka pakai sehari-hari, satu modul per slide
c+1      HARGA      tiga kartu paket, satu ditandai disarankan
c+2      PENUTUP    gema cover + satu perintah + kuotasi, tenggat, hitung mundur
```

Urutan ini tidak boleh diubah, dan tidak ada babak yang boleh kosong. Sasaran ≤ 20
slide.

**Kenapa SOLUSI dan PRODUK dipisah.** Versi lama menggabungkannya, dan hasilnya
adalah deretan slide mekanisme yang menjelaskan arsitektur dengan sempurna tanpa
pembaca pernah melihat benda yang akan mereka pakai. SOLUSI menjawab *"kenapa ini
menyelesaikan masalah tadi"*; PRODUK menjawab *"apa yang saya buka besok pagi"*.
Manajemen membeli yang kedua. Satu slide per modul, dan tiap slide memperlihatkan
layarnya, bukan diagramnya.

**Babak MASALAH tidak boleh kosong** — penawaran tanpa temuan milik prospek adalah
brosur, bukan penawaran. Babak PRODUK juga tidak boleh kosong; kalau modulnya belum
ada wujudnya, itu GAP yang dibawa ke `catalog-brainstorm`, bukan slide yang dilewati.

### Tiga sisipan opsional, dan slotnya sudah ditentukan

Ketiganya bukan babak. Boleh tidak ada. Kalau ada, tempatnya tidak boleh geser:

| Sisipan | Slot | Kapan dipakai |
|---|---|---|
| **PERUSAHAAN** | sesudah PRODUK, sebelum HARGA | pembeli belum kenal penjualnya. Isinya portofolio penggelaran yang berjalan — bukan pengakuan kelemahan (lihat pagar kejujuran #12) |
| **PERBANDINGAN** | sesudah PERUSAHAAN, sebelum HARGA | ada sistem lama yang sedang berjalan. Bentuknya hari kerja yang sama di dua sistem, fakta yang bisa diperiksa prospek (pagar #13) |
| **LINIMASA** | sesudah HARGA, sebelum PENUTUP | selalu, kecuali durasinya sudah muat di kartu harga |

**LINIMASA turun dari babak jadi sisipan, tapi isinya tetap wajib ada di suatu
tempat.** Menyebut lama proyek dan tanggal selesai menghapus ketakutan terbesar
pembeli perangkat lunak — bahwa proyeknya tidak akan pernah selesai — dan kaki *"di
luar lingkup"* yang menempel padanya adalah yang menjawab *"jadi hematnya berapa?"*.
Kalau tidak ada slide linimasa, kedua hal itu pindah ke kartu harga, dan lapis (g)
tetap memeriksanya.

**Babak NEXT dihapus.** Slide "yang belum dibeli" mengembalikan pembaca ke mode
berpikir jangka panjang persis di detik kita meminta keputusan. Kalau memang ada
modul fase berikutnya, tempatnya satu baris di kartu harga, bukan slide sendiri.

**Linimasa wajib menyebut apa yang dihitungnya.** Dua belas minggu pembuatan sistem
dan dua belas minggu sampai semua cabang memakainya adalah dua janji yang berbeda,
dan menukar keduanya adalah cara tercepat kehilangan kepercayaan di rapat kedua.

## Cover — hook, bukan teka-teki

Halaman pertama punya dua tugas sekaligus, dan versi lama berkas ini hanya mengakui
satu. Ia menulis bahwa curiosity gap milik konten dan bukan milik penawaran, lalu
menghasilkan cover yang benar, rapi, dan tidak dibaca siapa pun. Penjualnya menyebut
kalimatnya kurang kuat dan arahnya tidak jelas. Ia benar.

Dua tugasnya:

1. **Menahan pembaca** — kalimat pertama harus membuat orang berhenti.
2. **Menjawab "ini penawaran apa"** dalam lima detik.

Yang mendamaikan keduanya: **hook dibuat dari fakta prospek sendiri, bukan dari
informasi yang ditahan.** Teka-teki menahan jawaban dan membuat pembaca merasa
dipermainkan. Hook yang bekerja justru memberi jawabannya di depan — jawaban yang
sudah mereka tahu benar, dan belum pernah mereka lihat ditulis.

Bentuk yang terbukti, dua baris:

> baris 1 — **satu momen yang pasti terjadi malam ini**, disebut dengan angka mereka
> baris 2 — **apa yang sudah terjadi di momen itu tanpa mereka ketahui**

Bedanya dengan judul kapabilitas terlihat langsung. *"Sistem terintegrasi untuk
retail multi-cabang"* menggambarkan kita. *"Malam ini dua belas cabang tutup — tiga
hal sudah terjadi dan Anda belum tahu"* menggambarkan malam mereka, dan yang kedua
yang dibaca sampai habis.

Empat ujian sebelum cover diterima:

- Kalimatnya menyebut **momen**, bukan kemampuan.
- Angkanya **milik prospek**, diambil dari dokumen mereka.
- Tidak ada satu pun jawaban yang ditahan untuk slide berikutnya.
- Dibaca keras-keras, terdengar seperti kalimat orang, bukan judul brosur.

Selain hook, cover wajib memuat: kicker · **durasi proyek** · **tenggat harga**.

**Cover tidak memuat harga.** Rupiah di halaman pertama membuat pembaca menilai harga
sebelum melihat satu pun temuan.

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

### Penutup memikul dua beban sekaligus

Babak CTA yang dulu berdiri sendiri sekarang melebur ke penutup, jadi satu slide ini
harus menutup argumennya **dan** meminta keputusan. Isinya, dalam urutan ini:

1. **Gema cover** — bingkai yang sama, klausa terakhir diganti.
2. **Satu perintah** — satu kalimat, satu tindakan, satu penerima. Bukan "hubungi
   kami untuk diskusi lebih lanjut".
3. **Perangkat urgensi yang benar-benar berlaku** — tenggat harga, harga sesudah
   tenggat, hitung mundur, tanggal mulai yang bergantung tenggat. Semuanya diuji
   `b2b-honesty-rails.md`; yang tidak benar-benar berlaku dibuang, bukan dilunakkan.
4. **Satu jalur kontak, bukan tiga.** Tiga nomor dan dua surel membuat pembaca memilih
   jalur, dan memilih jalur adalah bentuk paling halus dari menunda.

Yang **tidak** boleh ikut: kartu harga diulang, daftar modul, peta jalan fase, atau
ringkasan seluruh deck. Penutup yang meringkas ulang membuat pembaca merasa sudah
selesai membaca dan belum perlu memutuskan.

Kalau CTA-nya terasa lemah, sebabnya hampir selalu satu dari dua: perintahnya bukan
tindakan yang bisa dikerjakan besok pagi, atau urgensinya tidak punya alasan nyata.
Keduanya diperbaiki di naskah, tidak pernah dengan kalimat yang lebih besar.

## Slide DAMPAK sebelum/sesudah

Slide yang paling sering hilang. Deck teknis menjelaskan mekanisme dengan sempurna
lalu tidak pernah memperlihatkan apa yang berubah. Manajemen tidak membeli
arsitektur, mereka membeli selisih hari kerja.

Bentuknya: dua pita bertumpuk, kiri kelabu berantakan → panah → kanan terang rapi.
Satu pita per masalah.

**Slide ini WAJIB nol rupiah dan nol persen.** Ia hanya membandingkan tiga hal proses:
**kapan** informasi datang, **bentuknya** apa, **tindakan** apa yang masih mungkin.
Satu angka penghematan di sana membatalkan baris "di luar lingkup".

## Slide harga: kartu, bukan daftar

Babak HARGA adalah babaknya sendiri, tepat sebelum penutup, dan bentuknya menentukan
apakah ia dibaca atau dilewati.

**Daftar harga bertingkat tidak bekerja.** Deretan baris memaksa pembaca membandingkan
sendiri, dan pembaca yang harus membandingkan sendiri menunda keputusan.

Bentuk yang bekerja: **satu kartu per paket, berdampingan, tiga kartu adalah jumlah
yang paling sering pas.** Tiap kartu memuat nama paket, jangkar yang dicoret, harga
setelah potongan, potongan sebagai nominal rupiah, dan isi paketnya sebagai daftar
pendek. Aritmetikanya mengikuti `b2b-honesty-rails.md` — jangkar dikurangi potongan
harus benar-benar sama dengan harga akhir, di ketiga kartu.

**Satu kartu ditandai sebagai yang disarankan**, dibedakan lewat satu warna aksen dan
satu lencana. Tanpa penanda itu tiga pilihan menghasilkan penundaan; dengan penanda,
pembaca punya titik awal dan menyesuaikan dari situ.

**Perangkat atau biaya yang dibeli sendiri oleh pembeli ditulis di blok terpisah di
bawah kartu, berjudul apa adanya.** Ditaruh di dalam daftar isi paket, ia terbaca
sebagai sesuatu yang kita sediakan, dan salah paham soal siapa yang membeli perangkat
adalah salah paham yang muncul di rapat, bukan di deck.

Aturan turunan yang tetap berlaku: harga tidak pernah ada di cover, dan total seluruh
lokasi tidak dicantumkan (`b2b-honesty-rails.md`, menu modular).

## Kerangka tetap tiap slide

Sebelum bicara isi slide, deck harus punya **satu kerangka yang sama di tiap halaman**.
Kerangka inilah yang membuat 17 halaman terbaca sebagai satu dokumen, bukan sebagai
tujuh belas gambar yang kebetulan dikirim bersama. Tanpa kerangka yang ditulis, tiap
sesi render menyusun ulang tepiannya sendiri, dan itu sumber perombakan yang tidak
pernah selesai.

Dua bentuk kerangka yang terbukti. `brand.md` memilih SATU, dan pilihan itu berlaku
untuk seluruh deck.

**Bentuk 1 — pita tegak tepi kiri.** Lihat bagian berikutnya. Cocok untuk deck yang
bidang visualnya penuh dan tidak menyisakan garis atas.

**Bentuk 2 — lencana atas + pita bawah.** Enam slot tetap, posisinya tidak pernah
berubah antar-halaman:

| slot | posisi | isi |
|---|---|---|
| lencana babak | kiri atas | nama babak, huruf besar, warna mengikuti babaknya |
| baris kerahasiaan | kanan atas | satu kata, huruf renggang, tipis |
| slot logo prospek | kanan atas, di bawah baris kerahasiaan | **kosong**, ditempel sesudah render |
| slot logo penjual | kiri, di dalam pita bawah | **kosong**, ditempel sesudah render |
| kalimat pukulan | tengah, di dalam pita bawah | satu kalimat huruf besar, mengunci maksud halaman |
| nomor halaman | kanan, di dalam pita bawah | angka saja |

Pita bawahnya sekitar **8% tinggi kanvas**, satu warna pekat, teks putih. Kalimat
pukulan di dalamnya bukan hiasan: ia satu-satunya bagian slide yang menjamin halaman
tetap berarti kalau pembacanya cuma melihatnya lima detik. Satu kalimat per halaman,
tidak pernah kosong, tidak pernah sama dengan headline-nya.

Yang membuat bentuk 2 sering dipilih: ia menyisakan seluruh badan kanvas untuk bidang
visual, dan ketiga slot logo/nomor sudah punya rumah tetap — jadi tidak ada slide yang
mendadak butuh tata letak khusus.

**KANON di kedua bentuk:** lencana, pita, logo, dan nomor halaman **ditempel setelah
render, tidak pernah digenerate** — lihat `b2b-visual-contract.md` pagar D, E, dan M.
Nomor halaman ikut ditempel, karena nomor yang digenerate ikut berubah tiap slide
di-render ulang dan deck kehilangan urutannya di tengah revisi.

## Pita tepi babak

Pita tegak setinggi kanvas di **tepi kiri**, teks diputar 90°. Satu warna untuk
MASALAH, warna aksen untuk SOLUSI dan PRODUK. Hanya di slide isi; cover, harga,
linimasa, dan penutup tanpa penanda — babaknya memang sudah selesai.

**Kenapa tepi kiri, bukan pojok:** ketiga pojok yang naluriah selalu terisi di
sebagian slide (kiri-atas headline, kiri-bawah wordmark, kanan-atas chip). Tepi kiri
satu-satunya zona kosong di semua slide isi.

Pita **ditempel setelah render, tidak pernah digenerate** — lihat
`b2b-visual-contract.md`.

Kalau `brand.md` memilih bentuk 2, bagian ini tidak dipakai — lencana kiri-atas
menggantikan seluruh fungsinya, dan memasang keduanya sekaligus membuat slide punya
dua penanda babak yang saling bertengkar.

## Cliffhanger antar-slide

Kalau sebuah slide sengaja **menahan** satu angka supaya slide berikutnya bisa
menjawabnya sebagai payoff, tandai penahanannya dengan **satu glyph grafis besar**
(tanda tanya, panah) — bukan kalimat. Taruh bersebelahan dengan angka yang ditahan,
warna aksen, kontras rendah supaya terbaca dekorasi bukan fokus utama.

⚠️ **Jangan menjelaskan maksud glyph di prompt render yang sama.** Model gambar akan
mencetak kalimat penjelasnya literal sebagai teks di kanvas. Pisahkan: satu kalimat
maksud-desain di catatan operator, satu instruksi render yang murni menyebut bentuk
grafisnya.
