# Pelacak Harga Sembako & Panen

Dashboard ini membandingkan harga sembako per komoditas dan menampilkan laporan
harga panen lokal. Data resmi tingkat petani dari Panel Harga Badan Pangan
dipublikasikan ke `public/data/official-prices.json` oleh script collector.

## Menarik harga resmi

Jalankan dari root repository:

```bash
python artifacts/pelacak-harga/scripts/pull_prices.py
```

Script hanya memakai library bawaan Python. Jika endpoint sedang maintenance,
respons bukan JSON, atau format API berubah, snapshot resmi terakhir tetap
dipertahankan dan dashboard menggunakan data lokal sebagai fallback.

## Cara membaca sumber

- **Sumber resmi:** Panel Harga Badan Pangan, SISKAPERBAPO Jawa Timur, dan
  harga pengadaan Bulog.
- **Patokan KDMP:** GKP petani Rp6.500/kg, GKG penggilingan Rp8.682/kg, GKP
  pasar bebas Rp7.850/kg, dan jagung kering KA15% Rp6.400/kg. Angka ini hanya
  pembanding harga bawah dan tidak dicampur dengan harga aktual.
- **Verifikasi lapangan:** KTNA, grup informasi harga gabah, pengepul,
  penggilingan, toko benih, Bulog, dan koperasi desa. Catatan lapangan harus
  menyimpan tanggal, lokasi, komoditas, kualitas, harga, dan catatan.

Formula Google Sheet yang dapat dicoba sebagai jalur manual:

```text
=IMPORTHTML("https://panelharga.badanpangan.go.id";"table";1)
```

Formula ini bergantung pada tabel HTML yang tersedia. Jika halaman memakai
rendering JavaScript atau sedang maintenance, gunakan collector Python.

Setelah snapshot berhasil dibuat, jalankan build ulang agar data ikut masuk ke
hasil static build:

```bash
PORT=18822 BASE_PATH=/ pnpm --filter @workspace/pelacak-harga run build
```

Data resmi tingkat provinsi ditampilkan terpisah dari laporan lapangan Gresik
dan Lamongan karena keduanya memiliki cakupan dan makna harga yang berbeda.