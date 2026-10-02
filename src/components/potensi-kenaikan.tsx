import { useEffect, useState } from 'react';
import { TrendingUp, ShieldCheck } from 'lucide-react';

type OutlookItem = {
  komoditas: string; hargaProdusen: number; perubahan14HariPct: number;
  naikTigaHari: boolean; proyeksi7Hari: number; proyeksiPct: number;
  sinyal: string; sumber: string;
};
type Outlook = {
  generatedAt: string; tanggalAnalisis: string; periode: string;
  metodologi: string; totalDipantau: number; totalWaspadaNaik: number;
  items: OutlookItem[];
};

const rupiah = (n: number) => `Rp${Math.round(n).toLocaleString('id-ID')}`;

/** Kartu "Potensi Kenaikan" — data dari data/price-outlook.json (BI PIHPS produsen). */
export function PotensiKenaikan() {
  const [data, setData] = useState<Outlook | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/price-outlook.json?ts=${Date.now()}`, { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setData)
      .catch(() => setData(null));
  }, []);

  if (!data) return null;
  const naik = data.items.filter((i) => i.sinyal === 'WASPADA NAIK');
  const pantau = data.items.filter((i) => i.sinyal === 'PANTAU');
  const stabil = data.items.filter((i) => i.sinyal === 'STABIL');
  const rows = showAll ? data.items : [...naik, ...pantau].slice(0, 8);

  return <section id="potensi-kenaikan" className="rise mt-12 rounded-[18px] border border-[#f0d9c8] bg-[#fdf3e7] p-5 shadow-sm">
    <div className="mb-4 flex items-center gap-2">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#d27855] text-white"><TrendingUp size={17} /></span>
      <div>
        <h3 className="font-display text-lg font-bold text-[#5a3320]">Potensi Kenaikan Harga</h3>
        <p className="text-xs text-[#8a6d55]">
          Deteksi dini dari harga produsen (BI PIHPS) · periode {data.periode} · {data.totalWaspadaNaik} dari {data.totalDipantau} komoditas waspada
        </p>
      </div>
    </div>

    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-wider text-[#a3795c]">
            <th className="py-2 pr-3">Komoditas</th>
            <th className="py-2 pr-3">Harga produsen</th>
            <th className="py-2 pr-3">14 hari</th>
            <th className="py-2 pr-3">Proyeksi 7 hari</th>
            <th className="py-2">Sinyal</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((i) => (
            <tr key={i.komoditas} className="border-t border-[#efe0cf]">
              <td className="py-2 pr-3 font-semibold text-[#4a2e1d]">{i.komoditas}{i.naikTigaHari && <span className="ml-1 rounded bg-[#f7ddca] px-1 text-[9px] text-[#a05a2c]">3 hari naik</span>}</td>
              <td className="py-2 pr-3">{rupiah(i.hargaProdusen)}</td>
              <td className={`py-2 pr-3 ${i.perubahan14HariPct > 0 ? 'text-[#b34a2b]' : 'text-[#3a7d54]'}`}>{i.perubahan14HariPct > 0 ? '+' : ''}{i.perubahan14HariPct}%</td>
              <td className={`py-2 pr-3 font-semibold ${i.proyeksiPct > 0 ? 'text-[#b34a2b]' : 'text-[#3a7d54]'}`}>
                {rupiah(i.proyeksi7Hari)} ({i.proyeksiPct > 0 ? '+' : ''}{i.proyeksiPct}%)
              </td>
              <td className="py-2">
                <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                  i.sinyal === 'WASPADA NAIK' ? 'bg-[#f8d7cf] text-[#a33a1c]'
                  : i.sinyal === 'PANTAU' ? 'bg-[#f5e6bd] text-[#8a6d1a]'
                  : 'bg-[#dcefe0] text-[#3a7d54]'}`}>{i.sinyal}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    {stabil.length > 0 && <p className="mt-3 text-[11px] text-[#8a6d55]">
      Stabil ({stabil.length}): {stabil.map((s) => s.komoditas).join(', ')}
    </p>}

    {data.items.length > 8 && <button onClick={() => setShowAll(!showAll)} className="mt-3 text-xs font-semibold text-[#bd654e] underline underline-offset-2">
      {showAll ? 'Sembunyikan' : `Tampilkan semua ${data.items.length} komoditas`}
    </button>}

    <p className="mt-3 flex items-start gap-1 text-[11px] leading-relaxed text-[#9a7a5f]">
      <ShieldCheck size={12} className="mt-0.5 shrink-0" /> {data.metodologi} Sumber: {data.items[0]?.sumber}.
    </p>
  </section>;
}
