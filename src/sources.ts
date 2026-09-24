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
    description: 'Harga pasar Gresik dan Lamongan',
    url: 'https://siskaperbapo.jatimprov.go.id',
  },
  {
    name: 'Harga Pengadaan Bulog',
    description: 'Harga serap Bulog Jawa Timur',
    url: 'https://pengadaan.bulog.co.id/harga',
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
  '=IMPORTHTML("https://panelharga.badanpangan.go.id";"table";1)';