export type PriceSource = {
  name: string;
  description: string;
  url?: string;
};

export type ReferencePrice = {
  label: string;
  price: number;
  unit: string;
  note: string;
};

export const officialSources: PriceSource[] = [
  {
    name: 'Data Pangan Bapanas',
    description: 'Portal data & publikasi pangan nasional',
    url: 'https://data.badanpangan.go.id/',
  },
  {
    name: 'PIHPS Nasional · Bank Indonesia',
    description: 'Harga produsen dan perubahan antar daerah',
    url: 'https://www.bi.go.id/hargapangan',
  },
  {
    name: 'Panel Harga Badan Pangan',
    description: 'Harga gabah dan beras tingkat petani',
    url: 'https://panelharga.badanpangan.go.id/beranda',
  },
  {
    name: 'SISKAPERBAPO Jawa Timur',
    description: 'Harga konsumen dan pasar Jawa Timur',
    url: 'https://siskaperbapo.jatimprov.go.id/',
  },
  {
    name: 'SIMHARGA Kementerian Pertanian',
    description: 'Rekap harga gabah petani dan penggilingan',
    url: 'https://bdsp2.pertanian.go.id/simharga/index_harga.php',
  },
  {
    name: 'SIJAGUNG Kementerian Pertanian',
    description: 'Data pembelian dan harga jagung/gabah',
    url: 'https://simpakan.ditjenpkh.pertanian.go.id/sijagung/backend/web/site/data-pembelian',
  },
  {
    name: 'BPS Jawa Timur · Harga-harga',
    description: 'Tabel statistik harga Jawa Timur',
    url: 'https://jatim.bps.go.id/id/statistics-table?subject=536',
  },
  {
    name: 'BPS Jawa Timur · Statistik Harga Produsen Gabah',
    description: 'Publikasi harga produsen gabah Jatim 2024',
    url: 'https://jatim.bps.go.id/id/publication/2025/02/17/28bd96a8b5e9c3751f7981b8/statistik-harga-produsen-gabah-provinsi-jawa-timur-2024.html',
  },
];

export const fieldSources = [
  'KTNA Gresik',
  'KTNA Lamongan',
  'Info Harga Gabah Jatim',
  'Pengepul Babat · Brondong · Dukun · Menganti',
  'Toko benih lokal',
];

export const verificationContacts = [
  'Bulog Divre Jatim Mojokerto',
  'Penggilingan Babat Lamongan',
  'Koperasi Merah Putih desa setempat',
];

export const referencePrices: ReferencePrice[] = [
  { label: 'GKP petani', price: 6500, unit: 'kg', note: 'Patokan bawah KDMP' },
  { label: 'GKG penggilingan', price: 8682, unit: 'kg', note: 'Patokan KDMP' },
  { label: 'GKP pasar bebas', price: 7850, unit: 'kg', note: 'Patokan pembanding' },
  { label: 'Jagung kering KA15%', price: 6400, unit: 'kg', note: 'Patokan bawah KDMP' },
];

export const googleSheetFormula =
  '=IMPORTHTML("https://siskaperbapo.indagjatim.com/display/show";"table";1)';

// --- Kontak admin & interaksi WhatsApp (tanpa backend, gratis) ------------
export const ADMIN_PHONE = '6282244756231'; // format internasional tanpa +
export const ADMIN_DISPLAY = '0822-4475-6231';

export const waLink = (message: string) =>
  `https://wa.me/${ADMIN_PHONE}?text=${encodeURIComponent(message)}`;

export const waAdminMessage =
  'Halo Admin Pelacak Harga Sembako Gresik-Lamongan, saya ingin bertanya tentang harga.';

export const waLaporHarga = (input: {
  lokasi: string; komoditas: string; harga: string; catatan?: string;
}) =>
  [
    '*LAPOR HARGA SEMBAKO*',
    `Lokasi: ${input.lokasi || '-'}`,
    `Komoditas: ${input.komoditas || '-'}`,
    `Harga: Rp${input.harga || '-'}`,
    input.catatan ? `Catatan: ${input.catatan}` : '',
    '',
    `Dikirim: ${new Date().toLocaleString('id-ID')}`,
  ].filter(Boolean).join('\n');