export type Area = 'Gresik' | 'Lamongan';

export type SembakoRecord = {
  date: string; area: Area; marketId: string; location: string; sourceType: string;
  commodityKey: string; commodity: string; brand: string; productName: string;
  size: string; unit: string; price: number; unitPrice: number; priceType: string;
  stockStatus: 'Tersedia' | 'Terbatas'; confidence: 'Tinggi' | 'Sedang';
  observedAt: string; address: string; sourceUrl: string;
};

export type PanenRecord = {
  tanggal: string; kabupaten: Area; kecamatan: string; desaKelurahan: string;
  lokasi: string; komoditas: string; kualitas: string; hargaPerKg: number; catatan: string;
};

export type PanenSummary = {
  komoditas: string; kualitas: string; hargaTerakhir: number; tanggalTerakhir: string;
  lokasiTerakhir: string; kabupaten: Area; rataRata: number; jumlahCatatan: number;
};

export type OfficialPriceRecord = {
  tanggal: string; sumber: string; komoditas: string; harga: number;
  satuan: string; level: string; wilayah: string;
};

export type OfficialSnapshotStatus = 'ok' | 'stale' | 'unavailable';

export type PriceData = {
  sembako: SembakoRecord[]; panen: PanenRecord[]; official: OfficialPriceRecord[];
  origin: 'demo' | 'official'; officialStatus: OfficialSnapshotStatus;
  officialFetchedAt: string | null;
};

let sourceCounter = 100;
const base = (item: Partial<SembakoRecord> & Pick<SembakoRecord, 'area' | 'location' | 'commodityKey' | 'commodity' | 'productName' | 'price' | 'unitPrice'>): SembakoRecord => ({
  date: '2024-06-18', marketId: `${sourceCounter++}`, sourceType: 'Survei lapangan',
  brand: 'Umum', size: '1', unit: 'kg', priceType: 'Harga eceran',
  stockStatus: 'Tersedia', confidence: 'Tinggi', observedAt: '18 Jun 2024, 07.40',
  address: `Jl. ${sourceCounter % 2 ? 'Panglima Sudirman' : 'KH. Abdul Karim'}, ${item.area}`,
  sourceUrl: '#', ...item,
});

export const demoSembako: SembakoRecord[] = [
  base({ area: 'Gresik', location: 'Pasar Baru Gresik', commodityKey: 'beras', commodity: 'Beras', productName: 'Beras medium', price: 14500, unitPrice: 14500, size: '1', unit: 'kg' }),
  base({ area: 'Lamongan', location: 'Pasar Sidoharjo', commodityKey: 'beras', commodity: 'Beras', productName: 'Beras medium', price: 14200, unitPrice: 14200, size: '1', unit: 'kg' }),
  base({ area: 'Gresik', location: 'Pasar Sentolang', commodityKey: 'beras', commodity: 'Beras', productName: 'Beras premium', price: 15800, unitPrice: 15800, size: '1', unit: 'kg', brand: 'Lumbung Kita' }),
  base({ area: 'Lamongan', location: 'Pasar Blimbing', commodityKey: 'beras', commodity: 'Beras', productName: 'Beras premium', price: 16000, unitPrice: 16000, size: '1', unit: 'kg', brand: 'Lumbung Kita', stockStatus: 'Terbatas' }),
  base({ area: 'Gresik', location: 'Pasar Baru Gresik', commodityKey: 'gula', commodity: 'Gula pasir', productName: 'Gula pasir putih', price: 17800, unitPrice: 17800, size: '1', unit: 'kg' }),
  base({ area: 'Lamongan', location: 'Pasar Sidoharjo', commodityKey: 'gula', commodity: 'Gula pasir', productName: 'Gula pasir putih', price: 17600, unitPrice: 17600, size: '1', unit: 'kg' }),
  base({ area: 'Gresik', location: 'Pasar Sentolang', commodityKey: 'minyak', commodity: 'Minyak goreng', productName: 'Minyak goreng sawit', price: 17500, unitPrice: 17500, size: '1', unit: 'liter', brand: 'Bimoli' }),
  base({ area: 'Lamongan', location: 'Pasar Blimbing', commodityKey: 'minyak', commodity: 'Minyak goreng', productName: 'Minyak goreng sawit', price: 16800, unitPrice: 16800, size: '1', unit: 'liter', brand: 'Fortune' }),
  base({ area: 'Gresik', location: 'Pasar Baru Gresik', commodityKey: 'telur', commodity: 'Telur ayam', productName: 'Telur ayam ras', price: 28500, unitPrice: 28500, size: '1', unit: 'kg' }),
  base({ area: 'Lamongan', location: 'Pasar Sidoharjo', commodityKey: 'telur', commodity: 'Telur ayam', productName: 'Telur ayam ras', price: 27900, unitPrice: 27900, size: '1', unit: 'kg' }),
  base({ area: 'Gresik', location: 'Pasar Sentolang', commodityKey: 'cabai', commodity: 'Cabai merah', productName: 'Cabai merah keriting', price: 52000, unitPrice: 52000, size: '1', unit: 'kg', confidence: 'Sedang' }),
  base({ area: 'Lamongan', location: 'Pasar Blimbing', commodityKey: 'cabai', commodity: 'Cabai merah', productName: 'Cabai merah keriting', price: 48500, unitPrice: 48500, size: '1', unit: 'kg', confidence: 'Sedang' }),
  base({ area: 'Gresik', location: 'Pasar Baru Gresik', commodityKey: 'tepung', commodity: 'Tepung terigu', productName: 'Tepung terigu serbaguna', price: 13500, unitPrice: 13500, size: '1', unit: 'kg', brand: 'Segitiga Biru' }),
  base({ area: 'Lamongan', location: 'Pasar Sidoharjo', commodityKey: 'tepung', commodity: 'Tepung terigu', productName: 'Tepung terigu serbaguna', price: 13200, unitPrice: 13200, size: '1', unit: 'kg', brand: 'Segitiga Biru' }),
];

export const demoPanen: PanenRecord[] = [
  { tanggal: '2024-06-17', kabupaten: 'Lamongan', kecamatan: 'Tikung', desaKelurahan: 'Jatirejo', lokasi: 'Kelompok Tani Jatirejo', komoditas: 'Gabah kering panen', kualitas: 'Medium', hargaPerKg: 6800, catatan: 'Kadar air 24%; panen raya mulai masuk.' },
  { tanggal: '2024-06-14', kabupaten: 'Lamongan', kecamatan: 'Sekaran', desaKelurahan: 'Kalen', lokasi: 'Lumbung Desa Kalen', komoditas: 'Gabah kering panen', kualitas: 'Premium', hargaPerKg: 7450, catatan: 'Bulir padat, kadar air 20%.' },
  { tanggal: '2024-06-16', kabupaten: 'Gresik', kecamatan: 'Duduksampeyan', desaKelurahan: 'Sumengko', lokasi: 'Gapoktan Sumengko', komoditas: 'Gabah kering panen', kualitas: 'Medium', hargaPerKg: 6950, catatan: 'Serapan penggilingan stabil.' },
  { tanggal: '2024-06-13', kabupaten: 'Gresik', kecamatan: 'Dukun', desaKelurahan: 'Mentaras', lokasi: 'Kios Tani Mentaras', komoditas: 'Jagung pipilan', kualitas: 'Kering', hargaPerKg: 5200, catatan: 'Kadar air sekitar 15%.' },
  { tanggal: '2024-06-09', kabupaten: 'Lamongan', kecamatan: 'Brondong', desaKelurahan: 'Sidomukti', lokasi: 'TPI Brondong', komoditas: 'Kedelai', kualitas: 'Lokal', hargaPerKg: 11200, catatan: 'Pasokan dari panen tumpangsari.' },
  { tanggal: '2024-06-08', kabupaten: 'Gresik', kecamatan: 'Manyar', desaKelurahan: 'Sembayat', lokasi: 'Pasar Sembayat', komoditas: 'Kedelai', kualitas: 'Lokal', hargaPerKg: 11000, catatan: 'Harga menguat karena permintaan tahu-tempe.' },
];

const fallbackData: PriceData = {
  sembako: demoSembako, panen: demoPanen, official: [], origin: 'demo',
  officialStatus: 'unavailable', officialFetchedAt: null,
};

const officialDataUrl = `${import.meta.env.BASE_URL}data/official-prices.json`;

export const loadPriceData = async (): Promise<PriceData> => {
  await new Promise((resolve) => window.setTimeout(resolve, 280));
  try {
    const response = await fetch(officialDataUrl, { cache: 'no-store' });
    if (!response.ok) return fallbackData;
    const payload = await response.json() as {
      status?: string; fetchedAt?: string | null; records?: Array<Partial<OfficialPriceRecord>>;
    };
    const official = (payload.records ?? []).flatMap((record) => {
      const harga = Number(record.harga);
      if (!record.komoditas || !Number.isFinite(harga) || harga <= 0) return [];
      return [{
        tanggal: String(record.tanggal ?? ''),
        sumber: String(record.sumber ?? 'Panel Harga Badan Pangan'),
        komoditas: String(record.komoditas),
        harga, satuan: String(record.satuan ?? 'kg'),
        level: String(record.level ?? 'petani'),
        wilayah: String(record.wilayah ?? 'Jawa Timur'),
      }];
    });
    if (!['ok', 'stale'].includes(payload.status ?? '') || official.length === 0) return fallbackData;
    return {
      ...fallbackData,
      official,
      origin: 'official',
      officialStatus: payload.status as 'ok' | 'stale',
      officialFetchedAt: payload.fetchedAt ?? null,
    };
  } catch {
    return fallbackData;
  }
};

export const loadDemoData = loadPriceData;

export const summarizePanen = (rows: PanenRecord[]): PanenSummary[] => {
  const buckets = new Map<string, PanenRecord[]>();
  rows.forEach((row) => {
    const key = `${row.komoditas}::${row.kualitas}`;
    buckets.set(key, [...(buckets.get(key) ?? []), row]);
  });
  return [...buckets.values()].map((items) => {
    const latest = [...items].sort((a, b) => b.tanggal.localeCompare(a.tanggal))[0];
    return {
      komoditas: latest.komoditas, kualitas: latest.kualitas, hargaTerakhir: latest.hargaPerKg,
      tanggalTerakhir: latest.tanggal, lokasiTerakhir: latest.lokasi, kabupaten: latest.kabupaten,
      rataRata: Math.round(items.reduce((sum, item) => sum + item.hargaPerKg, 0) / items.length),
      jumlahCatatan: items.length,
    };
  });
};