# Asupan Merek dan Standar Rumah

> Lahir dari satu kegagalan yang diukur: sebuah deck 19 slide selesai dirender, lolos
> semua pagar teks, lalu ditolak penjualnya sendiri dengan kalimat "ini deck paling
> jelek buatan AI". Cacatnya bukan di satu slide. Cacatnya: **tidak ada satu pun fase
> yang pernah menanyakan seperti apa deck perusahaan ini biasanya**.

## Kenapa berkas ini ada

`b2b-visual-contract.md` menyebut palet, font, dan logo sebagai **runtime input**.
Itu benar dan tetap benar. Tapi selama ini tidak ada fase yang **mengambil** runtime
input itu. Akibatnya `catalog-visual` berjalan dengan `[RUNTIME PLACEHOLDER]` yang
tidak pernah terisi, model gambar memakai defaultnya sendiri, dan hasilnya adalah
tampilan generik yang persis terbaca sebagai "buatan AI".

Placeholder yang tidak terisi bukan netral. Ia adalah keputusan desain yang
diserahkan ke model gambar.

## Aturan tertinggi — standar rumah mengalahkan default plugin

**Kalau penjual sudah punya deck, katalog, atau company profile yang dipakai selama
ini, berkas itu ADALAH spesifikasi visualnya.** Bukan referensi, bukan inspirasi —
spesifikasi.

Baca berkasnya, bongkar sistem tata letaknya, tulis hasilnya ke `brand.md`, dan
pakai itu. Setiap default di `b2b-visual-contract.md` yang bertabrakan dengan standar
rumah **kalah**, dan tabrakannya dicatat di `brand.md` supaya terlihat disengaja.

Alasannya sederhana: deck penawaran beredar bersama materi perusahaan yang lain. Deck
yang tampilannya beda sendiri terbaca sebagai dokumen pihak ketiga, bukan dokumen
perusahaan yang mengirimnya.

Cara membongkarnya, per halaman contoh:
- di mana penanda babak diletakkan, dan bentuknya apa — pita tegak, lencana kotak,
  atau chip
- ada pita bawah atau tidak; kalau ada, isinya apa saja dan urutannya bagaimana
- nomor halaman ada di mana
- bidang visualnya foto, render 3D, diagram, atau ikon garis
- alasnya terang atau gelap, dan slide mana yang membalik
- berapa warna yang benar-benar dipakai, dan tiap warna tugasnya apa

## Yang wajib dikumpulkan

| # | Isi | Kalau kosong |
|---|---|---|
| 1 | **Berkas standar rumah** — deck/katalog yang sudah ada, format apa pun | Tanya apakah benar-benar tidak ada. Kalau memang tidak ada, catat `TIDAK ADA` dan pakai default kontrak visual — tapi katakan ke pengguna bahwa deck ini akan jadi standar rumah yang pertama |
| 2 | **Palet** — tiap warna beserta tugasnya | STOP. Ini tidak boleh ditebak |
| 3 | **Font** — judul dan badan | Boleh fallback ke keluarga generik, dicatat sebagai fallback |
| 4 | **Berkas logo penjual** — path, versi terang dan gelap | Slot kosong, tempel manual |
| 5 | **Berkas logo prospek** | Slot kosong, tempel manual |
| 6 | **Nada visual** — sinematik/foto, editorial/diagram, atau ikon datar | Ikut standar rumah. Tanpa standar rumah, tanya — jangan pilih sendiri |
| 7 | **Foto bukti milik prospek atau penjual** — foto survei, tangkapan layar sistem lama, foto lokasi | Tidak ada bukti visual = babak MASALAH kehilangan senjata terkuatnya |
| 8 | **Wajah** — ada portret pendiri/tim yang memang mau dipakai? Path berkasnya? | Nol wajah (lihat kontrak visual) |

## Keputusan visual yang bukan milik plugin

Empat hal ini pernah diputuskan sendiri oleh plugin dan ditolak keras oleh penjualnya.
Semuanya **wajib ditanyakan**, jawabannya dicatat di `brand.md`:

1. **Wajah manusia** — default nol wajah. Tapi slide perusahaan dengan portret
   pendiri adalah pilihan sah yang sering dipakai penjual. Tanya, jangan larang.
2. **Menyebut nama vendor lama** — default anonim. Sebagian penjual justru ingin
   menyebutnya terang-terangan karena di situ letak seluruh argumennya. Tanya.
3. **Mengakui bagian yang belum pernah dibangun** — lihat pagar kejujuran #12. Ada
   bentuk yang jujur tanpa terdengar seperti mengumumkan kelemahan sendiri. Tanya
   bentuk mana yang dipakai.
4. **Pilot satu lokasi dulu, atau serentak** — lihat `b2b-phased-sale.md`. Pilot
   menurunkan risiko pembeli, tapi juga menurunkan ukuran transaksi dan bisa terbaca
   sebagai penjual yang ragu pada produknya sendiri. Ini keputusan komersial penjual,
   bukan default plugin.

## Bentuk `brand.md`

```
# Merek dan Standar Rumah — <penjual>

## Standar rumah
sumber: <nama berkas> | TIDAK ADA
sistem tata letak yang dibongkar dari berkas itu:
  - penanda babak: <bentuk + posisi>
  - pita bawah: <ada/tidak> · isi: <kiri | tengah | kanan>
  - nomor halaman: <posisi>
  - bidang visual: <foto | render 3D | diagram | ikon garis>
  - alas: <terang | gelap> · slide yang membalik: <daftar>

## Palet — satu warna, satu tugas
| peran | nilai | dipakai di |

## Font
judul: <...> · badan: <...> · (fallback? y/t)

## Berkas aset (path, untuk ref-conditioning dan tempel-sesudah-render)
logo penjual terang/gelap · logo prospek · foto bukti · portret

## Empat keputusan
wajah: <nol | slide mana, berkas apa>
vendor lama: <anonim | disebut sebagai "...">
pengakuan kematangan: <bentuk yang dipilih>
model penggelaran: <pilot satu lokasi | serentak> — alasan komersialnya

## Tabrakan dengan default kontrak visual
| default plugin | standar rumah | yang dipakai |
```

## Gerbang

`catalog-visual` **berhenti** kalau `brand.md` tidak ada, atau kalau masih ada
`[RUNTIME PLACEHOLDER]` yang belum terisi di dalamnya. Merender dengan placeholder
kosong adalah cara termahal untuk mengetahui bahwa palet belum ditanyakan.
