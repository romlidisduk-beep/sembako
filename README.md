# Pelacak Harga Sembako Gresik–Lamongan

Skrip Python tanpa dependensi eksternal untuk:

- mengambil harga per pasar dari SISKAPERBAPO Jawa Timur;
- mencari lokasi dengan harga termurah;
- menyimpan riwayat harga harian;
- mendeteksi sinyal `MURAH` dan `WASPADA NAIK`;
- membandingkan harga tambahan dari toko, koperasi, atau swalayan melalui CSV.

## Menjalankan di komputer

Gunakan Python 3.10 atau yang lebih baru. Tidak perlu menjalankan `pip install`.

```bash
python track_prices.py
```

Contoh:

```bash
python track_prices.py --areas=gresik,lamongan
python track_prices.py --areas=lamongan --commodities=gula,cabai-rawit
python track_prices.py --transport=10000
python track_prices.py --retail=data/retail-prices.csv
```

File hasil:

- `data/price-history.csv` — riwayat harga;
- `data/latest-price-report.json` — laporan lengkap untuk dipakai aplikasi lain.
- `web/` — website statis untuk menampilkan laporan dengan pencarian, filter,
  perbandingan harga per satuan, dan urutan termurah.

Untuk mencoba website di komputer:

```bash
python -m http.server 8080
```

Buka `http://localhost:8080/web/` setelah laporan JSON tersedia. Website
membaca `data/latest-price-report.json` secara langsung.

## Notifikasi Telegram

Pelacak dapat mengirim daftar harga secara otomatis dari yang termurah. Setiap
baris berisi produk, merek, harga per satuan, jenis tempat, nama lokasi, dan
wilayah.

Atur dua environment secret berikut:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Lalu jalankan:

```bash
python track_prices.py --telegram
```

Pesan akan dipecah otomatis jika daftar terlalu panjang untuk satu pesan
Telegram. Jangan menaruh token bot di repository atau di file CSV. Workflow
GitHub Actions akan mengirim notifikasi bila kedua secret tersedia; tambahkan pada
**Settings → Secrets and variables → Actions → New repository secret**.

Website statis tidak mengirim Telegram secara langsung. Notifikasi dikirim oleh
workflow GitHub Actions agar token dan chat ID tetap berada di environment
server dan tidak pernah dikirim ke browser.

### Format notifikasi harian

Workflow berjalan otomatis **satu kali sehari pada pukul 14.00 WIB**. Jika
Telegram atau WhatsApp aktif, setiap kanal menerima beberapa pesan terpisah
agar tidak menjadi satu pesan panjang:

1. `🌾 Update harga sembako` — tanggal, jumlah harga, lokasi, pasar, dan retail;
2. `🛒 Harga sembako termurah` — daftar harga termurah berdasarkan harga per
   satuan;
3. `⚠️ Waspada kenaikan harga` — hanya komoditas dengan sinyal kenaikan kuat;
4. `💚 Peluang harga murah` — komoditas yang dekat titik terendah;
5. `🌾 Referensi nasional & produsen` — Panel Bapanas, PIHPS, BPS, HPP, dan
   input pengepul manual jika tersedia;
6. `🚧 Catatan sumber data` — hanya muncul bila ada sumber yang gagal dibaca.

## Notifikasi WhatsApp (gratis, lewat CallMeBot)

Ada juga opsi kirim daftar harga termurah ke WhatsApp memakai **CallMeBot**,
layanan gratis pihak ketiga (bukan WhatsApp Cloud API resmi dari Meta).
Catatan penting: API gratis ini **untuk pemakaian personal**, ada rate limit,
dan bergantung pada layanan pihak ketiga kecil yang bisa berubah/berhenti
sewaktu-waktu — kalau butuh yang lebih stabil untuk skala lebih besar,
pertimbangkan WhatsApp Cloud API resmi.

Cara mendapatkan API key (sekali saja, manual lewat HP kamu):

1. Simpan nomor bot CallMeBot sebagai kontak di WhatsApp — cek nomor
   terbaru di https://www.callmebot.com/blog/free-api-whatsapp-messages/
   (nomornya bisa berubah).
2. Kirim pesan **"I allow callmebot to send me messages"** ke kontak itu.
3. Tunggu balasan berisi API key (bisa sampai beberapa menit).

Atur dua environment secret berikut (isi `WHATSAPP_PHONE` dengan nomor kamu
sendiri dalam format internasional, contoh `6281234567890`):

```text
WHATSAPP_PHONE
WHATSAPP_APIKEY
```

Lalu jalankan:

```bash
python track_prices.py --whatsapp
python track_prices.py --whatsapp --whatsapp-limit=10
```

Untuk mengirim ke beberapa orang, gunakan satu secret tambahan bernama
`WHATSAPP_RECIPIENTS`. Isinya satu penerima per baris dengan format
`nomor=APIKEY`; setiap nomor perlu API key CallMeBot miliknya sendiri:

```text
6281234567890=apikey-orang-pertama
6289876543210=apikey-orang-kedua
```

Nomor boleh ditulis dengan tanda `+`, spasi, tanda kurung, atau tanda hubung;
skrip akan menormalkannya ke format internasional. Penerima duplikat hanya
dikirimi sekali. Jika satu penerima gagal, skrip tetap melanjutkan ke penerima
lain lalu melaporkan kegagalan tersebut dan membuat workflow berstatus gagal,
sehingga masalahnya tidak diam-diam terlewat. Konfigurasi lama
`WHATSAPP_PHONE` + `WHATSAPP_APIKEY` tetap didukung untuk satu orang.

Workflow GitHub Actions otomatis mengirim WhatsApp bila konfigurasi
`WHATSAPP_RECIPIENTS` atau pasangan secret lama tersedia (tambahkan lewat
**Settings → Secrets and variables → Actions**),
berjalan berdampingan dengan Telegram — bisa aktifkan salah satu atau
keduanya sekaligus. Karena rate limit CallMeBot ketat, pesan WhatsApp
dipecah lebih pendek dan diberi jeda antar pesan dibanding Telegram.

## Menambahkan harga toko, koperasi, dan swalayan

Salin contoh berikut:

```bash
cp data/retail-prices.example.csv data/retail-prices.csv
```

Lalu ganti data contoh dengan harga nyata. Kolom wajib:

```csv
date,area,marketId,location,sourceType,commodityKey,commodity,unit,price,address,sourceUrl
2026-09-21,gresik,retail:toko-edi,Toko Edi,toko,beras-medium,Beras medium,kg,12500,"Alamat toko, Gresik",https://contoh.com
```

Nilai `sourceType` dapat berupa `toko`, `koperasi`, atau `swalayan`.
`price` adalah harga total untuk ukuran pada kolom `size`; dashboard otomatis
menghitung ekuivalen per `unit` saat membandingkan paket berbeda, misalnya
`62500` untuk `5 kg` dibandingkan sebagai `12500/kg`.
Laporan JSON menuliskan hasil normalisasi tersebut pada field `unitPrice`.

Commodity key yang tersedia:

```text
beras-premium, beras-medium, gula, minyak-curah, minyakita, ayam,
telur, sapi, cabai-keriting, cabai-besar, cabai-rawit, bawang-merah,
bawang-putih, lpg
```

## Referensi gabah nasional & daerah (di luar SISKAPERBAPO)

Selain harga konsumen per pasar, skrip juga mengambil referensi harga
GABAH/beras tingkat produsen setiap kali dijalankan (aktif secara default):

- **Panel Harga Bapanas** (`panelharga.badanpangan.go.id`) — pusat, harian
- **PIHPS Nasional / BI** (`hargapangan.id`) — pusat, harian
- **BPS Kabupaten Gresik & Lamongan** — repost rilis NTP + harga gabah
  Provinsi Jawa Timur, **bulanan** (dicek otomatis tiap tanggal 1–5 saja
  supaya tidak boros request di hari lain)
- **HPP Bulog/KDMP** — bukan hasil scraping, angka acuan tetap. Ganti lewat
  `--hpp-kdmp` kalau ada Perbadan/SK baru
- **Harga pengepul/tengkulak** — **tidak ada sumber publik** untuk ini (itu
  transaksi langsung di lapangan). Isi manual lewat `--pengepul-price` kalau
  sudah dicek sendiri

Hasilnya masuk ke `data/national-reference-history.csv` dan ke field
`nationalReferences` pada `data/latest-price-report.json`. Karena situs BPS
merender sebagian isinya lewat JavaScript, hasil scraping BPS bisa berupa
"Cek manual: <link>" — itu tanda kamu perlu membuka link tersebut sendiri.

Nonaktifkan bagian ini dengan `--no-national` kalau hanya perlu harga pasar:

```bash
python track_prices.py --no-national
python track_prices.py --hpp-kdmp=6600 --pengepul-price=7200
```

## Menjalankan otomatis lewat GitHub

Salin isi folder ini ke root repository GitHub. Workflow di
`.github/workflows/track-prices.yml` dapat dijalankan manual atau otomatis
setiap hari. Workflow akan menyimpan riwayat dan laporan terbaru kembali ke
repository, lalu menerbitkan folder `web/` bersama laporan JSON ke GitHub
Pages.

Jalankan manual melalui menu **Actions → Pelacak Harga Sembako → Run workflow**.

Pada repository GitHub, buka **Settings → Pages** dan pilih **GitHub Actions**
sebagai source jika belum otomatis aktif.

Catatan: harga pasar adalah data survei. Harga yang sangat rendah harus
dikonfirmasi kepada pasar sebelum melakukan perjalanan atau pembelian besar.