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
    name: 'Panel Harga Badan Pangan',
    description: 'Harga gabah dan beras tingkat petani Jawa Timur',
    url: 'https://panelharga.badanpangan.go.id',
  },
  {
    name: 'SISKAPERBAPO Jawa Timur',
    description: 'Harga konsumen dan pasar Jawa Timur',
    url: 'https://siskaperbapo.indagjatim.com/display/show',
  },
  {
    name: 'PIHPS Nasional · Bank Indonesia',
    description: 'Harga rata-rata dan perubahan antar daerah',
    url: 'https://www.bi.go.id/hargapangan',
  },
  {
    name: 'SIMHARGA Kementerian Pertanian',
    description: 'Rekap harga gabah tingkat petani dan penggilingan',
    url: 'https://datanonkom.pertanian.go.id/simharga/dashboard.php?page=harga_gabah_provinsi',
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