# The Five-Part Sales Enablement Kit

> Kerangka lima bagian diadaptasi dari pola sales-handoff enablement kit yang lazim di
> praktik GTM. Yang dipakai di sini kerangkanya; isinya diikat ke pagar kejujuran
> `b2b-honesty-rails.md` dan ke temuan `research/buyer-brain.md`.

Ini bentuk baku keluaran `catalog-master`. Tanpa kelimanya, yang dihasilkan adalah
deck, bukan kit — dan tim penjualan tetap harus memanggil pembuatnya tiap kali.

## 1. Context Brief

Untuk siapa kit ini, dan apa yang sudah diketahui.

- Profil pembeli ideal: jenis operasi, ukuran armada atau volume, peran yang memutuskan
- Masalah yang dialamatkan, dalam kalimat yang pembelinya sendiri pakai
- Yang **tidak** dijual — batas cakupan, ditulis eksplisit
- Kematangan tiap modul: berjalan di produksi / rakitan pertama / belum dibangun
- Pelanggan referensi dan **apa yang boleh disebut tentang mereka**, mengikuti kontrak
  kontennya

Berkas: `catalog/context-brief.md`

## 2. Talk Tracks & Scripts

Kata-kata yang benar-benar diucapkan, bukan poin pembicaraan.

- Pembuka WhatsApp dan telepon — pendek, satu pertanyaan, nol lampiran di pesan pertama
- Pertanyaan penggalian, disusun dari situasi → masalah → implikasi → nilai
- **Penanganan keberatan diambil dari `research/buyer-brain.md` bagian
  `## Keberatan`** — keberatannya nyata, dan jawabannya struktural, bukan
  menenangkan
- Kosakata: istilah yang dipakai pembeli, dan daftar istilah vendor yang membunuh
  percakapan
- Kalimat penutup untuk meminta pertemuan berikutnya, satu permintaan saja

Berkas: `catalog/talk-tracks.md`

## 3. Collateral Pack

Barang yang dikirim atau ditinggal.

| Barang | Kapan dipakai |
|---|---|
| Katalog master (12–16 slide) | dikirim sebelum pertemuan pertama |
| One-pager satu halaman | ditinggal setelah pertemuan, atau dikirim lewat pesan |
| Deck varian per-prospek | dikirim setelah temuan prospek terkumpul |
| Dasbor demo yang bisa diklik | diperlihatkan saat pertemuan, bukan dikirim |
| Kalkulator ROI | dipakai **bersama** prospek, angkanya milik mereka |

Aturan yang mengikat semuanya: **cover tanpa harga**, dan tiap angka yang muncul punya
pemilik yang disebut.

Berkas: `catalog/collateral/`

## 4. System Instructions

Cara memakai kit, untuk orang yang bukan pembuatnya.

- Kapan menjalankan `catalog-variant`, dan apa minimum masukannya (dokumen prospek —
  tanpa itu, berhenti)
- Bagaimana penilaian kelayakan deal dibaca, dan apa artinya kalau hasilnya tidak layak
- Alur persetujuan: nol materi dikirim sebelum `catalog-gate` memberi PASS
- Cara memilih varian referensi pelanggan berdasarkan wilayah prospek
- Di mana harga hidup, siapa yang boleh mengubahnya, dan apa yang terjadi pada tenggat
  saat tanggal kirim berubah (slide CTA digenerate ulang)

Berkas: `catalog/system-instructions.md`

## 5. Feedback Loop

Kanal masuk balik dari lapangan ke kit.

- Keberatan baru yang belum ada di `research/buyer-brain.md` — dicatat dengan kalimat
  aslinya, bukan diparafrase
- Pertanyaan yang tidak bisa dijawab tim penjualan
- Alasan menang dan alasan kalah, per deal
- Ambang: keberatan yang sama muncul tiga kali → masuk ke riset pembeli, dan rubriknya
  ikut diperbarui

Berkas: `catalog/feedback-log.md`

Tanpa bagian ini kit membeku pada hari ia dibuat. Bagian ini juga satu-satunya jalan
data primer — wawancara nyata dengan pembeli nyata — akhirnya masuk ke riset yang saat
ini baru berisi hipotesis berbukti.
