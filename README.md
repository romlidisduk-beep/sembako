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

## Pencatatan harga komoditas pertanian

Untuk memasukkan harga berdasarkan kualitas gabah, jagung, dan biji kangkung,
gunakan modul CSV terpisah berikut:

```bash
python harga_gresik_lamongan.py
```

Data disimpan di `data/harga_gresik_lamongan.csv`. Setiap catatan sekarang
memiliki `Kabupaten`, `Kecamatan`, `Desa_Kelurahan`, `Kode_Desa`, komoditas,
kualitas, harga per kilogram, dan catatan. Daftar wilayah lengkap tersimpan di
`data/administrative-areas.json`, mencakup 18 kecamatan Gresik dan 27
kecamatan Lamongan beserta seluruh desa/kelurahannya: Gresik memiliki 330
desa dan 26 kelurahan; Lamongan memiliki 462 desa dan 12 kelurahan.

Modul ini menyediakan menu untuk memilih kabupaten → kecamatan →
desa/kelurahan, menambah harga, melihat semua catatan, dan melihat ringkasan
terbaru beserta rata-rata riwayat. Aksi tertentu juga dapat dijalankan langsung:

```bash
python harga_gresik_lamongan.py lihat
python harga_gresik_lamongan.py ringkasan
python harga_gresik_lamongan.py --file=/tmp/harga.csv ringkasan
```

Data pertanian sengaja disimpan terpisah dari laporan sembako utama karena
kualitas produk, lokasi, dan makna harga per kilogramnya berbeda.

Master wilayah diambil dari API Wilayah Indonesia 2025 yang mencantumkan
Kepmendagri No. 300.2.2-2138 Tahun 2025 sebagai sumber:
`https://wilayah.web.id`.

Commodity key yang tersedia:

```text
beras-premium, beras-medium, gula, minyak-curah, minyakita, ayam,
telur, sapi, cabai-keriting, cabai-besar, cabai-rawit, bawang-merah,
bawang-putih, lpg
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