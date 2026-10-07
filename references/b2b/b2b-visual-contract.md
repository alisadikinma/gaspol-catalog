# B2B Visual Contract and Render Guards

> Sumber pola: standar deck penawaran B2B internal, §2, §3, §4, §5.4, §8, §9,
> §10.1–10.2, plus empat batch temuan render: §0b, §0c-C, §0d, dan **§0e — batch dari
> satu deck 19 slide yang lolos seluruh pagar teks lalu ditolak penjualnya sendiri.**
> Digenerikkan: nol hex, nol nama font merek, nol nama klien.

Berkas ini memberi makan **lapis render** `catalog-gate` — fase pemblokir tersendiri.

---

## §0. Standar rumah menang atas seluruh berkas ini

Sebelum satu prompt pun ditulis, `brand.md` harus ada — lihat `b2b-brand-intake.md`.

Semua yang ada di bawah judul **DEFAULT** adalah nilai bawaan yang dipakai **hanya
kalau `brand.md` tidak menyebut yang lain**. Yang ada di bawah judul **KANON** berlaku
selalu, karena melanggarnya menghasilkan gambar yang rusak, bukan gambar yang beda
selera.

Membedakan keduanya adalah inti perbaikan ini. Berkas versi lama menulis selera
sebagai hukum, jadi ia menimpa standar rumah penjualnya sendiri dan hasilnya adalah
deck yang tidak dikenali perusahaan yang mengirimnya.

| | DEFAULT (boleh ditimpa `brand.md`) | KANON (tidak pernah boleh ditimpa) |
|---|---|---|
| wajah | nol wajah manusia | — |
| nada | terang dan korporat presisi | — |
| bidang visual | diagram dan bukti | — |
| penanda babak | pita tegak tepi kiri | penanda babak **ditempel**, tidak digenerate |
| logo | di dalam pita bawah, reversed | logo **tidak pernah digambar model** |
| rasio | — | 16:9, full-bleed kolom piksel pertama–terakhir |
| teks | — | tiap blok muncul tepat satu kali |
| angka | — | nol angka yang tidak ada di naskah |
| bahasa | — | satu bahasa, bahasa naskah |

---

## Nol wajah manusia — DEFAULT

Alasannya: wajah pendiri di halaman pertama membuat manajemen prospek menilai
**konsultan perorangan**, bukan perusahaan yang bisa dikontrak, ditagih, dan dituntut.

Tapi ini default, bukan hukum. Sebagian penjual memang memakai portret pendiri di
slide perusahaan, dan itu pilihan sah. Yang tidak boleh: plugin memutuskannya sendiri.
`b2b-brand-intake.md` menanyakannya; `brand.md` mencatat jawabannya beserta slide
mana dan berkas portret mana.

**KANON yang tetap berlaku walau wajah diizinkan:** wajah tertentu **wajib**
dikondisikan dari berkas foto lewat `refs` — lihat §Ref-conditioning. Wajah yang
dideskripsikan lewat kata selalu menghasilkan orang yang berbeda, dan portret orang
yang salah di slide perusahaan lebih buruk daripada tidak ada portret sama sekali.

Turunan yang tetap KANON: **tidak ada sapaan personal** di teks yang dirender. Yang
memutuskan pembelian sebesar ini bukan satu orang — sebut institusinya.

## Kontrak visual 60/40 — DEFAULT

Kira-kira 60% kanvas untuk bidang visual, 40% untuk teks. Slide yang melewati ambang
itu ke arah teks berhenti terbaca dalam lima detik.

## Palet ko-branding — satu warna, satu tugas

Palet runtime, diambil `b2b-brand-intake.md`, dicatat di `brand.md`. Aturannya
struktural: satu warna struktur, satu warna aksen, netral untuk badan, dan **satu
warna satu tugas** — warna yang dipakai untuk dua hal berbeda di deck yang sama
menghapus artinya.

Berkas ini tidak menyebut satu pun nilai warna atau nama font. Kalau ia menyebutnya,
ia berhenti jadi kanon dan mulai jadi merek.

## Rasio dan nada

- **16:9, bukan 4:5** — KANON. Rasionya sendiri sebuah pesan: dokumen rapat.
- **Terang dan korporat presisi** — DEFAULT. Deck penawaran dibaca di proyektor dan
  dicetak. Tapi kalau standar rumah penjualnya foto sinematik beralas gelap, standar
  rumah yang menang, dan keterbacaan cetak dijaga lewat kontras teks, bukan lewat
  memaksa alas terang.

---

## Pagar render — model gambar mengulang, mengarang, dan membocorkan

Tiap pagar di bawah lahir dari cacat yang benar-benar lolos review teks. Semuanya
KANON.

### A. Duplikasi teks
Model mengulang teks: kartu penuh dirender dua kali, label dicetak di dalam **dan**
di luar wadahnya. Terjadi di hampir separuh slide pada satu deck yang diukur.

Pagar: tiap blok teks muncul **tepat satu kali**, dan wadahnya disebut eksplisit
("label di dalam kartu, tidak diulang di luarnya").

### B. Angka dan frasa karangan
Pagar: bake angka persis dari naskah, larang angka lain muncul di kanvas.

### C. Tiga kebocoran diam
1. Instruksi "nol teks lain" menghapus headline yang seharusnya tercetak.
2. Kualifikasi terpotong separuh.
3. Disclaimer hilang saat prompt di-upgrade.

Pagar: sesudah render, bandingkan teks di gambar terhadap naskah baris per baris.

### D. Logo dan lockup
**Logo tidak pernah digambar model gambar** — milik prospek maupun milik penjual.
Sisakan slot kosong, tempel berkasnya sesudah render. Wordmark hasil render selalu
salah bentuk, dan wordmark salah di halaman pertama adalah cacat termahal di deck.

Menempel di pojok kanan atas gagal berulang karena panjang headline tidak bisa
dijamin. Yang bekerja: lockup **di dalam pita bawah**.

Perkecualian tunggal: logo yang muncul sebagai **objek di dalam adegan** — papan nama
toko, header aplikasi di layar ponsel — tidak bisa ditempel belakangan tanpa merusak
perspektif. Itu dikerjakan lewat `refs`, bukan lewat deskripsi. Lihat §Ref-conditioning.

### E. Pita babak dan full-bleed
- Penanda babak **ditempel, tidak pernah digenerate** — KANON.
- Bentuk dan posisinya DEFAULT: pita tegak tepi kiri, teks diputar 90°. Standar rumah
  boleh menggantinya dengan lencana kotak kiri-atas atau chip.
- Lebar pita sekitar 1,7% kanvas; ukuran font diskalakan ke lebar kanvas, bukan piksel
  absolut — teks kecil tidak terbaca dari tiga meter.
- Deteksi tinggi pita saat QA memakai **proporsi piksel gelap**, bukan rata-rata
  luminansi.
- Full-bleed disebut sebagai **kolom piksel pertama dan terakhir**, bukan "edge to
  edge".

### F. Model gambar tidak bisa berhitung
Diminta menggambar 31 mesin kasir, ia menggambar 34, lalu 36. Diminta 96 garis, ia
menggambar entah berapa. Tidak ada jumlah yang bisa dijamin lewat prompt.

**Pagar: jangan pernah menyuruh model menggambar sekumpulan benda yang jumlahnya
harus tepat.** Kalau angkanya penting — dan di deck penawaran angka selalu penting —
**cetak angkanya besar-besar sebagai teks**, dan biarkan gambarnya menyampaikan jenis
bendanya saja, bukan jumlahnya.

Ini juga menyelamatkan pagar B: kumpulan benda yang jumlahnya meleset adalah angka
karangan yang terbaca sebagai gambar.

**Batas pagar ini, yang sering salah dibaca.** F melarang *menyuruh model menghitung*.
Ia TIDAK mewajibkan tiap kartu memakai angka besar. Angka besar dipakai kalau angkanya
berarti bagi pembelinya. Kalau angkanya cuma berarti bagi orang teknis — batas ukuran
berkas, jumlah lisensi, nomor versi — angka besar justru membuat kartu terbaca kosong,
dan pemilik perusahaan melewatinya. Di kasus itu **ikon yang memimpin kartu, bukan
digit**, dan angkanya turun jadi satu kalimat di badan teks atau hilang sama sekali.
Diukur: satu deck memakai `0` dan `2 GB` sebagai angka besar di dua kartu; pemiliknya
bilang dia tidak mengerti maksud keduanya. Kartu yang sama dengan ikon memimpin lolos
tanpa pertanyaan.

### G. Kata tata letak tercetak sebagai teks
Prompt menulis `HEADLINE`, `PRODUCT LOGO`, `SUBTITLE`, `CAPTION` sebagai penanda
posisi. Model mencetak kata-kata itu apa adanya di kanvas.

**Pagar: nol kata tata letak di dalam prompt.** Sebut posisinya lewat geometri
("sepertiga atas, rata kiri"), bukan lewat nama peran.

### H. Deskripsi ikon tercetak sebagai teks
Prompt menulis "ikon bom waktu, sistem yang tinggal menunggu meledak". Model mencetak
**"a system just waiting to go off"** di sebelah ikonnya, sebagai teks, di kanvas.

**Pagar: bentuk grafis disebut, maknanya tidak.** Satu kalimat maksud-desain boleh ada
di catatan operator; prompt render hanya menyebut bentuknya. Kalimat yang bukan bagian
dari daftar teks tidak boleh muncul di prompt sama sekali — model tidak bisa
membedakan instruksi dari isi.

Ini kasus umum dari peringatan cliffhanger glyph di `b2b-deck-architecture.md`, dan
berlaku untuk **setiap** ikon, bukan hanya glyph cliffhanger.

### I. Daftar putih teks — satu-satunya cara menahan karangan
Melarang satu per satu tidak pernah cukup; model selalu menemukan satu frasa yang
belum dilarang. Sebuah cover pernah mendapat strapline berbahasa Inggris yang tidak
ada di naskah mana pun.

**Pagar: tiap prompt memuat satu blok berjudul "DAFTAR LENGKAP TEKS DI KANVAS INI"**,
berisi tiap string dalam tanda kutip, diakhiri kalimat *"tidak ada teks lain yang
boleh muncul di kanvas ini"*.

Bedanya dengan larangan "nol teks lain" yang menghapus headline (pagar C-1): daftar
putih **menyebut dulu apa yang dicetak**, baru menutup sisanya. Urutan itu yang
membedakan.

### J. Prompt berbahasa Inggris membocorkan bahasa Inggris
Naskah berbahasa Indonesia, prompt ditulis berbahasa Inggris, dan model menerjemahkan
seluruh slide ke bahasa Inggris. Terjadi utuh, satu slide penuh.

**Pagar:** tiap string yang dicetak dikutip **dalam bahasa naskah, apa adanya**, dan
prompt memuat blok `ATURAN BAHASA — KRITIS` yang menyebut bahasanya dan melarang
terjemahan atau bahasa kedua. Aman menulis instruksi prompt dalam bahasa Inggris
selama seluruh string yang dikutip tetap dalam bahasa naskah dan blok bahasa ada.

### K. Angka ilustrasi tanpa capnya
Pagar kejujuran #3 mewajibkan cap `ILUSTRASI` menempel di angka hasil ilustrasi. Cap
itu hilang saat render lebih sering daripada elemen lain mana pun.

**Pagar:** cap masuk ke daftar putih §I sebagai string tersendiri, dengan posisinya,
dan lapis render memeriksanya per slide. Satu cap per slide sudah cukup — cap di tiap
angka membuat slide terlihat kotor dan justru dihapus orang.

### L. Dasbor yang mengarang isinya
Diminta menggambar dasbor, model mengisinya dengan nama kota, nama produk, dan angka
karangan — semuanya terbaca oleh pembaca sebagai data prospek.

**Pagar:** tiap label di dalam dasbor, bagan, atau tangkapan layar palsu masuk ke
daftar putih §I sebagai string yang dikutip. Isi dasbor adalah teks slide, bukan
dekorasi, dan lapis render memperlakukannya begitu.

### M. Kata penanda slot tercetak sebagai teks
Prompt menulis "slot logo kosong" atau "placeholder logo di kanan atas". Model
mencetak kata **LOGO** di dalam kotak itu. Kotaknya benar, isinya salah, dan kata
`LOGO` di halaman yang dikirim ke prospek terbaca sebagai deck yang belum jadi.

**Pagar: slot kosong disebut sebagai BENTUK, bukan sebagai peran.** Tulis "satu
persegi panjang membulat abu muda yang benar-benar kosong — tanpa teks, tanpa huruf,
tanpa ikon di dalamnya", lalu tambahkan larangan eksplisit: kata `LOGO` tidak boleh
muncul di kanvas. Ini pagar G yang menyerang lewat pintu lain: G melarang kata peran
di posisi teks, M melarangnya di posisi slot.

### N. Merek liar menempel di benda dalam adegan
Adegan berisi laptop, ponsel, monitor, atau kemasan. Model menempelkan logo merek
terkenal di tutup laptop tanpa diminta — pernah terjadi berupa logo produsen laptop
di slide yang membicarakan sistem milik pihak lain. Itu klaim merek yang tidak pernah
ditulis siapa pun, di dokumen komersial.

**Pagar: tiap benda bermerek yang digambar disebut POLOS secara eksplisit** — "tutup
laptopnya benar-benar kosong, tanpa logo dan tanpa tanda merek apa pun". Menyebutkan
bendanya saja tidak cukup; kekosongannya harus diminta.

### O. Wajah menyelinap lewat properti adegan
Aturan nol wajah dijaga di tokoh utama, lalu wajah muncul di **benda kecil di dalam
adegan**: foto di kartu identitas yang dipegang, potret di layar, orang di poster
latar. Diukur: satu kartu yang dioper antar-karakter dirender sebagai kartu identitas
lengkap dengan pasfoto.

**Pagar: nol wajah berlaku sampai ke isi properti.** Tiap benda yang bisa memuat
gambar orang — kartu, layar, poster, bingkai, kemasan — disebut isinya secara
eksplisit ("kartu putih polos dengan dua garis, tanpa foto, tanpa wajah").

### P. Kata merek dicetak dua kali di sebelah lambangnya
Naskah menyebut satu nama perusahaan dan promptnya meminta lambang perusahaan itu
sejajar dengan namanya. Model mencetak lambangnya, lalu namanya, lalu **mengulang
namanya lagi** di baris berikutnya.

**Pagar: kalau sebuah lambang dipasang sebaris dengan namanya, sebutkan jumlah
kemunculan kata itu.** Contoh kalimat pagar: "kata <nama> ditulis PERSIS SEKALI di
seluruh kanvas, tepat sesudah lambangnya." Ini kasus khusus pagar A yang tidak
tertangkap oleh aturan umumnya, karena yang diulang adalah satu kata, bukan satu blok.

### Q. Ejaan bahasa naskah rontok di render
Model membuang akhiran, menyambung kata, atau menukar huruf pada bahasa non-Inggris —
sering pada kata terakhir sebuah kalimat panjang. Diukur: sebuah kata kehilangan dua
huruf terakhirnya di kaki slide, dan render terpasang dua jam sebelum ada yang sadar.

**Pagar: sesudah render, tiap string di daftar putih §I dibaca ULANG HURUF PER HURUF
terhadap naskah**, bukan sekadar "ada/tidak ada". Untuk kalimat panjang, prompt boleh
mengeja bagian rawannya: "kata terakhir adalah <kata>, dieja <e-j-a-a-n>".

Ini sebabnya lapis render tidak bisa diwakili pemeriksaan sekilas: kalimatnya ada,
posisinya benar, dan tetap salah.

---

## Prompt hidup di berkas, bukan di percakapan

Cacat paling mahal di plugin ini bukan salah satu pagar di atas. Cacatnya: **prompt
render yang tidak pernah ditulis ke berkas.**

Yang terjadi kalau prompt hanya ada di percakapan: revisi berikutnya mengetik ulang
promptnya dari ingatan. Yang ikut hilang tiap kali mengetik ulang bukan bagian yang
diingat orang — headline dan angka selalu selamat — melainkan **blok pagarnya**,
karena blok itu panjang, membosankan, dan tidak terlihat di hasil sampai ia gagal.
Hasilnya deck yang dirender lima kali dan mendapat cacat berbeda tiap kali, dan tiap
cacat adalah pagar yang sudah tertulis di berkas ini bertahun-tahun.

Aturannya:

- Tiap slide punya **satu berkas prompt**. Render selalu dijalankan dari berkas itu.
- Revisi = **menyunting berkas prompt**, lalu render ulang. Tidak pernah mengetik
  ulang prompt di percakapan.
- Berkas prompt menyimpan riwayatnya: satu baris per revisi, apa yang diubah dan
  cacat apa yang memicunya. Tanpa baris itu, pagar yang sama dihapus lagi bulan depan.
- Render yang ditolak disimpan dengan **nama yang menyebut cacatnya**, bukan `_v2`,
  `_v3`, `_buang`. Nama versi menyimpan urutan; hanya nama cacat yang menyimpan
  alasan.

---

## Ref-conditioning — yang tidak bisa dicapai lewat kata

Tiga hal tidak pernah berhasil dideskripsikan dan selalu berhasil dikondisikan dari
berkas gambar, kalau pembangkitnya menerima gambar rujukan:

| Yang dikondisikan | Kenapa kata gagal |
|---|---|
| **Wajah tertentu** | Deskripsi menghasilkan orang yang berbeda tiap render |
| **Logo sebagai objek di dalam adegan** (papan nama, header aplikasi) | Wordmark hasil render selalu salah bentuk, dan di dalam adegan ia tidak bisa ditempel belakangan tanpa merusak perspektif |
| **Foto bukti milik prospek** | Bukti yang digambar ulang berhenti jadi bukti |

Aturannya:
- Berkasnya diambil di fase asupan dan pathnya tercatat di `brand.md`.
- **Rujukan tidak membatalkan satu pun pagar.** Prompt tetap memuat daftar putih §I,
  blok bahasa §J, dan larangan menghitung §F.
- Logo yang **bukan** bagian dari adegan tetap slot kosong yang ditempel belakangan
  (pagar D). Rujukan bukan izin untuk menggambar wordmark di sudut slide.
- Kalau pembangkitnya tidak menerima gambar rujukan, ketiga hal di atas **turun jadi
  slot tempel-sesudah-render**, bukan dipaksakan lewat deskripsi.

## Kebersihan pemanggilan pembangkit gambar

- Konfirmasi id model lewat tool daftar-model milik server itu sendiri, jangan
  diasumsikan.
- **Batas tunggu default terlalu pendek untuk slide padat.** Satu render pernah
  melewati batas 420 detik dan berhasil di 540. Naikkan batasnya sebelum render, jangan
  sesudah gagal — render yang timeout tetap menghabiskan kuotanya.
- Simpan render yang ditolak ke folder terpisah, jangan ditimpa. Tanpa berkas
  tertolaknya, cacat yang sama akan diperdebatkan lagi di revisi berikutnya.

## Distribusi PDF

- **Watermark miring berulang menutupi seluruh halaman**, bukan satu cap di pojok. Cap
  pojok hilang begitu orang memotret satu bagian slide.
- Ukuran tiap tulisan **sekitar 10–14% lebar kanvas**, diulang jadi kira-kira tiga
  kolom kali empat baris, miring 30°, baris ganjil digeser setengah kolom. Diukur:
  satu tulisan selebar 58% kanvas terbaca sebagai cacat cetak, bukan sebagai
  watermark, dan ujungnya terpotong sesudah diputar — lebar sesudah rotasi yang
  dihitung, bukan lebar sebelum rotasi.
- Opasitas **8–12%**. Angka 5% yang tertulis di versi lama berkas ini tidak terlihat
  sama sekali di alas gelap dan hilang saat dicetak.
- **Warna watermark ditentukan per halaman** dari luminansi **pita tengah** kanvas
  (kira-kira 15–85% lebar, 20–80% tinggi), bukan dari rata-rata seluruh halaman:
  putih di halaman gelap, warna struktur di halaman terang. Halaman gelap yang
  memakai warna gelap kehilangan watermarknya sepenuhnya.
- Baris kerahasiaan di pita **di luar bidang slide** — halaman ditambah sedikit ke
  bawah. Di dalam, ia menabrak elemen lain sekarang atau di revisi berikutnya.

## Review render adalah fase tersendiri

Sebuah deck pernah **PASS di review teks dan BLOCKING di review render pada hari yang
sama**. Itu bukan anomali, itu strukturnya: naskahnya benar, promptnya yang salah.

Lapis render `catalog-gate` berjalan setelah PNG ada, memeriksa gambar terhadap
naskahnya, dan memblokir sendiri. Tanpa PNG ia melapor `NOT RUN` — **tidak pernah**
PASS.

## Putaran revisi — tempat aturan paling sering dilanggar

Putaran pertama dijaga oleh fase-fasenya. Putaran revisi tidak: orang yang punya deck
mengirim daftar perubahan per halaman, dan pekerjaan langsung melompat ke prompt dan
render. Semua butir di bawah terjadi dalam **satu** putaran revisi sebuah deck 21
halaman, dan hampir semuanya sudah tertulis sebagai aturan sebelum dilanggar.

**Putaran revisi tetap lewat fase.** Daftar perubahan diterapkan ke `deck.md` dulu,
lapis teks `catalog-gate` dijalankan pada naskah yang sudah berubah, baru render.
Reviewer yang dijalankan sesudah render menemukan cacat naskah yang memaksa render
ulang berbayar.

### Naskah

- **Ganti istilah = ganti di semua halaman.** Nama modul, sebutan sistem prospek, kata
  untuk integrasi: sebelum render, cari istilah lama di seluruh `deck.md` dan tulis
  daftar halaman yang ikut berubah. Halaman yang tidak dirender ulang menyimpan istilah
  lama, dan pembaca melihat dua nama untuk satu barang.
- **Menggabung halaman membuang batasan.** Sebelum halaman gabungan dirender, kumpulkan
  semua baris "wajib tercetak" dari halaman asalnya dan centang satu per satu. Yang
  hilang lebih dulu selalu kalimat batas, bukan kalimat manfaat.
- **Janji yang dinaikkan ke halaman depan memakai kalimat halaman syaratnya, kata demi
  kata.** Versi ringkas di halaman depan selalu lebih luas daripada syaratnya, dan
  pembeli memegang versi yang lebih luas.
- **Klaim "lebih murah" dihitung terhadap semua paket.** Tulis selisihnya dalam rupiah
  dan persen di catatan, lalu uji terhadap tiap paket lain di deck. Bundel yang lebih
  murah dari jumlah satuannya bisa sekaligus lebih mahal dari kombinasi satuan lain.
  Kata "jauh" tidak dicetak untuk selisih satu digit persen.
- **Rumus dan contoh hitungnya harus satu.** Contoh memakai setiap suku rumus yang
  dicetak di atasnya, atau menulis terang suku mana yang nol. Suku yang ditambahkan
  penyusun sendiri ditandai sebagai turunan, bukan sebagai kutipan sumber.
- **Kalimat yang tidak dimengerti pemilik deck tidak akan dimengerti pembeli.** Kalau
  pemilik bertanya "ini artinya apa?", kalimatnya ditulis ulang, bukan dijelaskan.

### Render

- **Benda dinamai dari bentuknya, bukan dari jenis dokumennya.** "Invoice sheet"
  menghasilkan kata INVOICE di kertas, "RFID tag" menghasilkan RFID di tag, "ticket
  booth" menghasilkan tulisan di loket. Tulis "selembar kertas putih kosong bergaris
  abu-abu, tanpa kata", "kotak gelap polos tanpa huruf". Ini pagar N diperluas dari
  merek ke kata benda.
- **Logo penjual muncul sendiri di pojok atas.** Gambar acuan wordmark yang dilampirkan
  untuk layar aplikasi ikut dicetak sebagai kop halaman. Tiap prompt menutupnya: "tidak
  ada wordmark di kiri-atas; eyebrow adalah baris pertama."
- **Bidang tempel diminta sebagai ruang putih, bukan sebagai kotak.** "Seperempat
  kiri-atas kartu adalah bidang putih kosong" memberi ruang bersih. "Satu kotak kosong"
  memberi kotak abu-abu yang harus dihapus lagi.
- **Kemiripan wajah butuh kata, bukan hanya gambar acuan.** Ciri yang paling dikenali
  ditulis sebagai larangan terang: "kepala botak bersih, tanpa rambut sama sekali,
  termasuk di samping." Dengan acuan saja, model menambahkan rambut di pelipis.
- **Bendera, logo, dan foto asli ditempel dari berkas aslinya.** Logo prospek di layar
  monitor atau sisi kendaraan ditempel sesudah render dengan dimiringkan mengikuti
  bidangnya. Bendera diambil dari berkas resmi. Model tidak diminta menggambar keduanya.
- **Cacat kecil ditambal, tidak dirender ulang.** Satu kata nyasar, satu baris teks
  polos, satu huruf tambahan di judul: tutup atau salin dari piksel halaman itu sendiri.
  Render ulang membayar lagi dan membawa cacat baru. Syaratnya dua: tambalan ditulis
  sebagai skrip yang bisa dijalankan ulang, dan render mentahnya tetap disimpan.
- **Nomor berkas render tidak sama dengan nomor halaman.** Begitu satu halaman digabung
  atau dipindah, nomor berkas dibiarkan dan urutan halaman dipegang satu daftar pilih.
  Mengganti nama berkas memutus semua rujukan pemilik deck ke render lama.

### Tempel sesudah render — bidang warna, bukan kotak kosong

Semua butir di bawah datang dari satu putaran revisi sebuah deck 19 halaman yang
memuat belasan logo, foto wajah, bendera, dan satu lencana.

- **Tempat tempelan diminta sebagai bidang satu warna polos yang tidak dipakai di
  mana pun di palet deck.** Model menggambar bidang itu di tempat dan kemiringan yang
  benar; skrip mencari kelompok piksel berwarna itu dan menempel berkas aslinya. Ini
  menggantikan "kotak kosong" dan "ruang putih" untuk tempelan yang berada **di dalam
  adegan**: layar monitor, sisi kendaraan, papan nama, kop aplikasi di ponsel.
- **Jumlah bidang per halaman ditulis sebagai angka yang diharapkan, dan skrip berhenti
  kalau jumlahnya lain.** Model kadang menggambar logonya sendiri dan tidak menyisakan
  bidang, atau memecah satu bidang jadi dua karena tertutup sosok. Tanpa hitungan itu,
  logo masuk ke bidang yang salah tanpa ada yang tahu.
- **Urutan bidang dipetakan terang.** "Bidang paling kiri = logo A, bidang di bawah
  perisai = logo B." Urutan bawaan dari kiri ke kanan pernah menaruh logo perusahaan
  keamanan di sisi truk.
- **Bidang yang tertutup sebagian oleh sosok diisi per piksel, bukan dengan pelat.**
  Pelat persegi menutup kepala atau lengan orang yang berdiri di depannya. Ganti hanya
  piksel berwarna bidang itu; sosok di depannya tetap utuh.
- **Kalau model tetap menggambar logonya sendiri, timpa di titik tetap.** Koordinatnya
  ditulis di skrip dengan catatan render mana yang ia maksud. Render ulang menghapus
  koordinat itu, jadi catatannya wajib.
- **Sesudah tempel, hitung sisa piksel warna bidang. Angkanya harus nol.** Sisa tipis
  di tepi bidang terlihat sebagai garis mencolok di PDF.
- **Tambahan kecil dikerjakan skrip, tidak dirender ulang.** Bendera negara, lencana
  jaminan, kartu ulasan contoh, satu baris teks yang pudar: semuanya digambar atau
  ditempel skrip di atas render yang sudah lolos. Bendera sederhana digambar dari
  bentuk dasarnya pada ukuran berlipat lalu dikecilkan, supaya tepinya halus.
- **Bendera dan lencana berdiri di samping logo, tidak di atasnya.** Tanda yang
  menumpang di pojok logo menutup huruf terakhirnya. Kecilkan logonya sedikit dan beri
  tanda itu tempat sendiri di bidang yang sama.
- **Logo yang harus terbaca boleh lebih besar dari bidangnya.** Bidang dari model hampir
  selalu terlalu kecil untuk logo yang pemilik deck minta "jelas". Skrip memperbesar
  kotaknya dengan faktor tertulis, lalu hasilnya dilihat lagi.
- **Bukti contoh ditulis sebagai contoh di gambarnya.** Kartu ulasan bintang lima,
  tangkapan layar pesan, sertifikat: kalau bukan milik nyata, kata "contoh" tercetak di
  kartunya sendiri, bukan di catatan kaki.

### Tokoh, wajah, dan jumlah gambar acuan

- **Tokoh yang muncul di banyak halaman dibuat dulu sebagai satu lembar tokoh.** Badan
  penuh dan close-up dalam satu gambar, dirender sekali, disetujui pemilik deck, lalu
  dilampirkan sebagai acuan di tiap halaman tempat tokoh itu muncul. Tokoh yang hanya
  dideskripsikan berganti wajah dan kostum di tiap halaman.
- **Tokoh AI harus terbaca sebagai AI dari jarak baca slide.** Lencana kecil
  bertulisan "AI" tidak cukup; pemilik deck melihat perempuan biasa. Yang terbaca:
  chip hologram, cincin cahaya, ikon data yang melayang, cahaya di tepi badan. Tanda
  itu ditulis di prompt tiap halaman, bukan hanya di lembar tokoh.
- **Kostum dan nama tokoh adalah keputusan pemilik deck.** Tanyakan di asupan merek.
  Kostum yang dipilih penyusun diganti di putaran berikutnya, dan tiap halaman yang
  memuat tokoh itu ikut dirender ulang.
- **Wajah orang nyata: tanyakan foto asli atau kartun.** Untuk halaman tim, pemilik
  deck bisa meminta sosok kartun bergaya deck; berkas fotonya lalu hanya jadi acuan
  kemiripan. Jawabannya dicatat di `brand.md`.
- **Pembangkit gambar membatasi jumlah gambar acuan, dan menolak dengan galat umum.**
  Satu panggilan dengan tujuh acuan ditolak tanpa penjelasan. Gabungkan wajah-wajah
  ke satu gambar berjajar, dengan urutan yang disebut di prompt ("dari kiri: ...").
- **Jumlah orang di teks dan di gambar dicocokkan.** Ini pagar F: model tidak bisa
  berhitung. Kalau teks menulis lima orang dan gambar menunjukkan empat, laporkan ke
  pemilik deck; jangan diam.
- **Jabatan orang di pihak pembeli dikonfirmasi sebelum render.** "Direktur" yang
  ternyata "Owner" memaksa halaman penutup dirender ulang.

### Mutu render dan halaman review

- **Halaman padat teks dirender di mutu lebih tinggi sejak awal.** Di mutu terendah,
  satu halaman dengan banyak baris teks gagal ejaan tiga kali berturut-turut; di mutu
  satu tingkat di atasnya ia lolos sekali jalan. Mengulang di mutu rendah lebih mahal.
- **Halaman review memuat daftar "yang berubah di putaran ini" di paling atas**, dan
  daftar itu ditulis ulang tiap putaran, bukan ditambah. Di bawahnya cacat yang sudah
  diketahui penyusun tetapi belum diperbaiki. Pemilik deck tidak perlu menemukannya
  sendiri.
- **Permintaan "slide N" merujuk ke nomor di halaman review, bukan nomor berkas
  render.** Kalau dua nomor itu berbeda, sebut dua-duanya saat melapor, dan tanyakan
  kalau permintaannya bisa berarti dua halaman.

### Serah

- **"Sudah" berarti berkas yang dibuka orang itu sudah berubah.** Tambalan yang baru
  ada di folder render, atau baru diuji di satu halaman, belum selesai. Perubahan yang
  berlaku untuk semua halaman (pita bawah, alamat situs) dipasang ke semua halaman
  sebelum dilaporkan.
- **Gambar untuk review tidak bernomor halaman, dan PDF tidak dibuat.** Dua-duanya
  menunggu kata dari pemilik deck. Selama review, urutan berubah berkali-kali; nomor
  yang sudah tercetak dan PDF yang sudah jadi sama-sama basi di perubahan pertama.
- **Ukuran berkas masukan dicek sebelum ditempel.** Logo selebar tiga ratus piksel
  tampak lunak begitu dibesarkan di sampul. Laporkan, dan minta berkas yang lebih besar.

