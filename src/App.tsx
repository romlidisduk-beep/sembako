import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ArrowUpRight, ChevronDown, ChevronUp, CircleHelp, Database, Layers3, MapPin, Search, SlidersHorizontal, Sprout, Store, Wheat, Wifi, X } from 'lucide-react';
import { Route, Switch, Link, useLocation, useRoute, Router as WouterRouter } from 'wouter';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import NotFound from '@/pages/not-found';
import { loadPriceData, summarizePanen, type OfficialPriceRecord, type PanenRecord, type PanenSummary, type PriceData, type PriceHistoryRecord, type SembakoRecord } from './data';
import { fieldSources, googleSheetFormula, officialSources, referencePrices, verificationContacts } from './sources';

const queryClient = new QueryClient();
const money = (value: number) => `Rp${value.toLocaleString('id-ID')}`;
const shortDate = (value: string) => new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value));

function AppMark() {
  return <div className="flex items-center gap-3" data-testid="brand-pelacak-harga">
    <div className="relative flex h-10 w-10 items-center justify-center rounded-[14px] bg-[#e8b84d] text-[#263f3b] shadow-[3px_3px_0_#193b36]">
      <span className="font-display text-2xl leading-none">p</span>
      <span className="absolute bottom-[7px] right-[7px] h-1.5 w-1.5 rounded-full bg-[#e86c4f]" />
    </div>
    <div>
      <div className="font-display text-[21px] font-bold leading-none tracking-[-.03em] text-[#f9f1df]">Pelacak Harga</div>
      <div className="mt-1 font-data text-[9px] uppercase tracking-[.14em] text-[#b9cbc0]">Gresik · Lamongan</div>
    </div>
  </div>;
}

function StatusBand({ count, panenCount, origin, officialStatus, officialCount, reportDate, source }: { count: number; panenCount: number; origin: PriceData['origin']; officialStatus: PriceData['officialStatus']; officialCount: number; reportDate: string | null; source: string }) {
  const hasSnapshot = origin === 'snapshot';
  const officialIsFresh = officialStatus === 'ok';
  const statusTitle = hasSnapshot ? 'Snapshot pasar aktif' : 'Data contoh aktif';
  const statusBadge = hasSnapshot ? (officialIsFresh ? 'Terbaru' : 'Tersimpan') : 'Demo';
  const statusDescription = hasSnapshot
    ? `${source} · laporan ${reportDate ? shortDate(reportDate) : 'terakhir tersedia'}. Jika sumber resmi gagal, snapshot sebelumnya tetap dipertahankan.`
    : 'Snapshot laporan belum terbaca, jadi data contoh lokal dipakai sementara.';
  return <div className="flex flex-col gap-3 rounded-[18px] border border-[#cae1d2] bg-[#edf7ef] px-4 py-3.5 text-[#22453b] shadow-sm sm:flex-row sm:items-center sm:justify-between">
    <div className="flex items-start gap-3">
      <div className="pulse-dot mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#d3ebd5] text-[#328252]"><Wifi size={14} /></div>
      <div>
        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold"><span data-testid="status-data">{statusTitle}</span><span className="rounded-full bg-[#d1ead8] px-2 py-0.5 font-data text-[10px] uppercase tracking-wide text-[#3d7851]">{statusBadge}</span></div>
        <p className="mt-0.5 text-xs leading-relaxed text-[#567267]">{statusDescription}</p>
      </div>
    </div>
    <div className="flex shrink-0 gap-4 border-t border-[#d2e7d8] pt-2 font-data text-[10px] uppercase tracking-wide text-[#638276] sm:border-l sm:border-t-0 sm:pl-4 sm:pt-0">
      <span><strong className="block text-base font-medium text-[#234f42]">{count}</strong> catatan sembako</span>
       <span><strong className="block text-base font-medium text-[#234f42]">{panenCount}</strong> laporan panen</span><span><strong className="block text-base font-medium text-[#234f42]">{officialCount}</strong> harga resmi</span>
    </div>
  </div>;
}

function SegmentedTabs({ mode, setMode }: { mode: 'sembako' | 'panen'; setMode: (mode: 'sembako' | 'panen') => void }) {
  return <div className="inline-flex rounded-[14px] border border-[#d7cdbd] bg-[#eee7d9] p-1" role="tablist" aria-label="Pilih jenis harga">
    <button data-testid="tab-sembako" role="tab" aria-selected={mode === 'sembako'} onClick={() => setMode('sembako')} className={`flex items-center gap-2 rounded-[10px] px-4 py-2 text-sm font-semibold transition-all ${mode === 'sembako' ? 'bg-[#fffaf1] text-[#254c42] shadow-sm' : 'text-[#7b796d] hover:text-[#254c42]'}`}><Store size={15} /> Sembako</button>
    <button data-testid="tab-panen" role="tab" aria-selected={mode === 'panen'} onClick={() => setMode('panen')} className={`flex items-center gap-2 rounded-[10px] px-4 py-2 text-sm font-semibold transition-all ${mode === 'panen' ? 'bg-[#fffaf1] text-[#254c42] shadow-sm' : 'text-[#7b796d] hover:text-[#254c42]'}`}><Sprout size={15} /> Harga Panen</button>
  </div>;
}

function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <label className="relative block w-full sm:w-[280px]">
    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7e857d]" size={17} />
    <input data-testid="input-search" value={value} onChange={(event) => onChange(event.target.value)} placeholder="Cari komoditas atau lokasi..." className="h-11 w-full rounded-[12px] border border-[#d7cdbd] bg-[#fffaf1] pl-10 pr-9 text-sm text-[#29463e] outline-none transition focus:border-[#d48a57] focus:ring-2 focus:ring-[#e8b84d]/30" />
    {value && <button data-testid="button-clear-search" onClick={() => onChange('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9a9688] hover:text-[#274c42]" aria-label="Hapus pencarian"><X size={15} /></button>}
  </label>;
}

function AreaFilter({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <label className="flex h-11 items-center gap-2 rounded-[12px] border border-[#d7cdbd] bg-[#fffaf1] px-3 text-sm text-[#52645d]">
    <MapPin size={15} className="text-[#d27855]" />
    <select data-testid="select-area" value={value} onChange={(event) => onChange(event.target.value)} className="w-full bg-transparent font-medium outline-none"><option value="Semua area">Semua area</option><option value="Gresik">Gresik</option><option value="Lamongan">Lamongan</option></select>
  </label>;
}

type CategoryKey = 'semua' | 'pokok' | 'protein' | 'bumbu' | 'kebutuhan';
const categoryOptions: Array<{ key: CategoryKey; label: string; description: string; keys: string[] }> = [
  { key: 'semua', label: 'Semua komoditas', description: '14 jenis', keys: [] },
  { key: 'pokok', label: 'Bahan pokok', description: 'beras & gula', keys: ['beras', 'gula'] },
  { key: 'protein', label: 'Protein', description: 'ayam, telur & sapi', keys: ['ayam', 'telur', 'sapi'] },
  { key: 'bumbu', label: 'Bumbu & sayur', description: 'cabai & bawang', keys: ['cabai', 'bawang'] },
  { key: 'kebutuhan', label: 'Kebutuhan dapur', description: 'minyak, tepung & LPG', keys: ['minyak', 'tepung', 'lpg'] },
];

function CategoryNav({ records, value, onChange }: { records: SembakoRecord[]; value: CategoryKey; onChange: (value: CategoryKey) => void }) {
  return <div className="category-scroll" role="tablist" aria-label="Kelompok komoditas">
    {categoryOptions.map((category) => {
      const count = new Set(records.filter((record) => category.keys.length === 0 || category.keys.some((key) => record.commodityKey.includes(key))).map((record) => record.commodityKey)).size;
      return <button key={category.key} role="tab" aria-selected={value === category.key} onClick={() => onChange(category.key)} className={`category-tab ${value === category.key ? 'category-tab-active' : ''}`}>
        <span className="category-icon"><Wheat size={16} /></span>
        <span className="min-w-0 text-left"><strong>{category.label}</strong><small>{count} komoditas · {category.description}</small></span>
      </button>;
    })}
  </div>;
}

function OverviewStats({ data }: { data: PriceData }) {
  const commodities = new Set(data.sembako.map((record) => record.commodityKey)).size;
  const locations = new Set(data.sembako.map((record) => `${record.area}-${record.location}`)).size;
  const warnings = data.trends.filter((trend) => trend.signal === 'WASPADA NAIK').length;
  return <div className="overview-stats">
    <div><span className="stat-kicker">Harga terpantau</span><strong>{data.sembako.length}</strong><small>catatan pasar</small></div>
    <div><span className="stat-kicker">Komoditas</span><strong>{commodities}</strong><small>jenis kebutuhan</small></div>
    <div><span className="stat-kicker">Lokasi aktif</span><strong>{locations}</strong><small>pasar Gresik–Lamongan</small></div>
    <div className={warnings > 0 ? 'stat-alert' : ''}><span className="stat-kicker">Sinyal naik</span><strong>{warnings}</strong><small>{warnings > 0 ? 'perlu dipantau' : 'belum terdeteksi'}</small></div>
  </div>;
}

function usePriceData() {
  const [data, setData] = useState<PriceData | null>(null);
  useEffect(() => { loadPriceData().then(setData); }, []);
  return data;
}

function PriceTrendChart({ history, area, commodityKey, commodity }: { history: PriceHistoryRecord[]; area: string; commodityKey: string; commodity: string }) {
  const points = useMemo(() => {
    const grouped = new Map<string, number[]>();
    history.filter((item) => item.area === area && item.commodityKey === commodityKey).forEach((item) => {
      grouped.set(item.date, [...(grouped.get(item.date) ?? []), item.price]);
    });
    return [...grouped.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([date, prices]) => ({
      date, label: shortDate(date), price: Math.round(prices.reduce((sum, price) => sum + price, 0) / prices.length),
    }));
  }, [history, area, commodityKey]);

  return <div className="rounded-[16px] border border-[#dfd5c4] bg-[#fffaf1] p-4 sm:p-5">
    <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
      <div><div className="font-data text-[10px] uppercase tracking-[.12em] text-[#a06e55]">Riwayat harga</div><h3 className="font-display text-lg font-bold text-[#2e5045]">{commodity} · {area}</h3></div>
      <span className="text-xs text-[#7b8379]">Rata-rata seluruh pasar pada area terpilih</span>
    </div>
    {points.length < 2 ? <div className="flex min-h-[190px] items-center justify-center rounded-[12px] border border-dashed border-[#d9cdbb] bg-[#fbf5e9] px-6 text-center text-sm leading-relaxed text-[#7c8379]">Riwayat belum cukup untuk membentuk tren. Grafik akan terisi otomatis setelah minimal dua tanggal laporan tersimpan.</div> : <div className="h-[230px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#eadfce" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#7b8379', fontSize: 10 }} tickLine={false} axisLine={false} />
          <YAxis tickFormatter={(value) => `Rp${Math.round(Number(value) / 1000)}k`} tick={{ fill: '#7b8379', fontSize: 10 }} tickLine={false} axisLine={false} width={48} />
          <Tooltip formatter={(value) => [money(Number(value)), 'Rata-rata']} labelFormatter={(label) => `Tanggal ${label}`} contentStyle={{ borderRadius: 10, borderColor: '#dfd5c4', background: '#fffaf1', fontSize: 12 }} />
          <Line type="monotone" dataKey="price" stroke="#d27855" strokeWidth={3} dot={{ r: 3, fill: '#d27855', strokeWidth: 0 }} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>}
  </div>;
}

function SelectFilter({ label, value, options, onChange, testId }: { label: string; value: string; options: string[]; onChange: (value: string) => void; testId: string }) {
  return <label className="min-w-[136px] flex-1"><span className="mb-1.5 block font-data text-[10px] uppercase tracking-[.11em] text-[#7d857d]">{label}</span><select data-testid={testId} value={value} onChange={(event) => onChange(event.target.value)} className="h-10 w-full rounded-[10px] border border-[#d7cdbd] bg-[#fffaf1] px-2.5 text-xs font-semibold text-[#35584b] outline-none focus:border-[#d48a57]"><option value="Semua">Semua</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
}

function SkeletonCards() {
  return <div className="space-y-2">{[1, 2, 3, 4].map((item) => <div key={item} className="h-[82px] animate-pulse rounded-[14px] border border-[#e5ddce] bg-[#f3ecdf]" />)}</div>;
}

function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return <div className="rounded-[16px] border border-dashed border-[#d5c8b6] bg-[#fbf5e9] px-6 py-12 text-center">
    <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-[14px] bg-[#eee0c6] text-[#a77a3c]"><Layers3 size={20} /></div>
    <h3 className="font-display text-lg font-bold text-[#2e5045]">{title}</h3><p className="mx-auto mt-1 max-w-sm text-sm leading-relaxed text-[#7c8379]">{body}</p>{action}
  </div>;
}

function CommodityCard({ commodity, records, expanded, onExpand }: { commodity: string; records: SembakoRecord[]; expanded: boolean; onExpand: () => void }) {
  const cheapest = [...records].sort((a, b) => a.unitPrice - b.unitPrice)[0];
  const areas = [...new Set(records.map((record) => record.area))].join(' + ');
  return <div className={`overflow-hidden rounded-[16px] border bg-[#fffaf1] transition-all ${expanded ? 'border-[#d79a58] shadow-[0_8px_22px_rgba(74,73,45,.08)]' : 'border-[#dfd5c4] hover:border-[#caaa76]'}`}>
    <button data-testid={`button-expand-${commodity}`} onClick={onExpand} className="flex w-full items-center gap-3 p-4 text-left sm:p-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] bg-[#edf0dc] font-display text-xl font-bold text-[#486c55]">{commodity.slice(0, 1)}</div>
      <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="font-display text-lg font-bold text-[#2b4c42]">{commodity}</h3><span className="rounded-full bg-[#f0e4c9] px-2 py-0.5 font-data text-[10px] text-[#897047]">{records.length} sumber</span></div><p className="mt-1 truncate text-xs text-[#7b8379]">{areas} <span className="mx-1 text-[#c1b4a2]">·</span> termurah hari ini</p></div>
      <div className="text-right"><div className="font-data text-base font-medium text-[#d3674e]">{money(cheapest.unitPrice)}<span className="text-[10px] text-[#908679]">/{cheapest.unit}</span></div><div className="mt-1 flex items-center justify-end gap-1 text-[10px] text-[#85897e]">{expanded ? 'Tutup' : 'Lihat sumber'} {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}</div></div>
    </button>
    {expanded && <div className="border-t border-[#eadfce] bg-[#f8f0e2] px-4 py-3 sm:px-5">
       {records.sort((a, b) => a.unitPrice - b.unitPrice).map((record) => <div data-testid={`source-row-${record.marketId}`} key={record.marketId} className="flex flex-col gap-2 border-b border-[#e8ddcc] py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2 text-sm font-semibold text-[#35584b]"><MapPin size={13} className="text-[#d27855]" /><Link href={`/pasar/${encodeURIComponent(record.marketId)}`} className="underline decoration-[#c9b898] underline-offset-2 hover:text-[#bd654e]">{record.location}</Link><span className="rounded bg-[#e7f1e3] px-1.5 py-0.5 font-data text-[9px] font-normal text-[#528056]">{record.area}</span></div><div className="mt-1 text-xs text-[#81867d]">{record.productName} · {record.brand} · {record.stockStatus.toLowerCase()}</div></div><div className="flex items-center justify-between gap-4 sm:justify-end"><span className="font-data text-sm text-[#2e5045]">{money(record.unitPrice)}/{record.unit}</span><span className={`text-[10px] ${record.confidence === 'Tinggi' ? 'text-[#528056]' : 'text-[#a77a3c]'}`}>Kepercayaan {record.confidence.toLowerCase()}</span></div></div>)}
       <Link href={`/komoditas/${encodeURIComponent(records[0].commodityKey)}`} className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-[#ba654d] underline decoration-[#d5a17e] underline-offset-4">Lihat tren komoditas <ArrowUpRight size={13} /></Link>
    </div>}
  </div>;
}

function SembakoPanel({ records, search, area, category, reportDate, detailView, setDetailView }: { records: SembakoRecord[]; search: string; area: string; category: CategoryKey; reportDate: string | null; detailView: boolean; setDetailView: (value: boolean) => void }) {
  const [sort, setSort] = useState('Harga terendah');
  const [expanded, setExpanded] = useState<string | null>(null);
  const categoryKeys = categoryOptions.find((item) => item.key === category)?.keys ?? [];
  const filtered = useMemo(() => records.filter((record) => (area === 'Semua area' || record.area === area) && (categoryKeys.length === 0 || categoryKeys.some((key) => record.commodityKey.includes(key))) && `${record.commodity} ${record.productName} ${record.location}`.toLowerCase().includes(search.toLowerCase())), [records, area, search, categoryKeys]);
  const groups = useMemo(() => [...new Map(filtered.map((record) => [record.commodityKey, filtered.filter((item) => item.commodityKey === record.commodityKey)])).values()].sort((a, b) => {
    if (sort === 'A–Z') return a[0].commodity.localeCompare(b[0].commodity);
    return Math.min(...a.map((item) => item.unitPrice)) - Math.min(...b.map((item) => item.unitPrice));
  }), [filtered, sort]);
  return <section className="rise rise-delay-1">
     <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#d27855]" /><h2 className="font-display text-[22px] font-bold text-[#2a4e43]">Bandingkan harga</h2></div><p className="mt-1 text-sm text-[#78827b]">Pilih folder komoditas untuk melihat harga terbaik tanpa menjejalkan semua data dalam satu layar.</p></div><div className="flex items-center gap-2"><button data-testid="button-toggle-source-view" onClick={() => setDetailView(!detailView)} className={`flex items-center gap-2 rounded-[10px] border px-3 py-2 text-xs font-semibold transition ${detailView ? 'border-[#d27855] bg-[#fff0e8] text-[#b65c43]' : 'border-[#d7cdbd] bg-[#fffaf1] text-[#567066]'}`}><SlidersHorizontal size={14} /> {detailView ? 'Tampilan ringkas' : 'Lihat per sumber'}</button><select data-testid="select-sort-sembako" value={sort} onChange={(event) => setSort(event.target.value)} className="h-9 rounded-[10px] border border-[#d7cdbd] bg-[#fffaf1] px-2 text-xs font-semibold text-[#567066] outline-none"><option>Harga terendah</option><option>A–Z</option></select></div></div>
     {filtered.length === 0 ? <EmptyState title="Belum ada harga yang cocok" body="Coba hapus kata pencarian atau pilih area yang lain." action={<button data-testid="button-reset-sembako" onClick={() => { setExpanded(null); setSort('Harga terendah'); }} className="mt-4 text-xs font-bold text-[#ba654d] underline underline-offset-4">Atur ulang tampilan</button>} /> : detailView ? <div className="space-y-2">{filtered.sort((a, b) => a.unitPrice - b.unitPrice).map((record) => <div key={record.marketId} data-testid={`detail-card-${record.marketId}`} className="flex flex-col gap-3 rounded-[14px] border border-[#dfd5c4] bg-[#fffaf1] p-4 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2 font-semibold text-[#35584b]"><MapPin size={14} className="text-[#d27855]" /><Link href={`/pasar/${encodeURIComponent(record.marketId)}`} className="underline decoration-[#c9b898] underline-offset-2 hover:text-[#bd654e]">{record.location}</Link><span className="rounded-full bg-[#e9f0df] px-2 py-0.5 font-data text-[9px] text-[#5c7b5d]">{record.area}</span></div><div className="mt-1 text-xs text-[#7c8379]">{record.commodity} · {record.productName} · {record.size} {record.unit}</div></div><div className="flex items-center justify-between gap-5"><span className="font-data text-base text-[#d3674e]">{money(record.unitPrice)}<span className="text-[10px] text-[#908679]">/{record.unit}</span></span><span className="text-[10px] text-[#6e8177]">{record.observedAt}</span></div></div>)}</div> : <div className="space-y-2">{groups.map((group) => <CommodityCard key={group[0].commodityKey} commodity={group[0].commodity} records={group} expanded={expanded === group[0].commodityKey} onExpand={() => setExpanded(expanded === group[0].commodityKey ? null : group[0].commodityKey)} />)}</div>}
     <div className="mt-3 flex items-center justify-between font-data text-[10px] uppercase tracking-[.1em] text-[#8a8c82]"><span>Menampilkan {detailView ? filtered.length : groups.length} {detailView ? 'sumber' : 'komoditas'}</span><span>Terakhir dipantau {reportDate ? shortDate(reportDate) : '—'}</span></div>
  </section>;
}

function PanenFilters({ rows, kabupaten, setKabupaten, commodity, setCommodity, quality, setQuality }: { rows: PanenRecord[]; kabupaten: string; setKabupaten: (value: string) => void; commodity: string; setCommodity: (value: string) => void; quality: string; setQuality: (value: string) => void }) {
  return <div className="flex flex-col gap-2 rounded-[14px] border border-[#dfd5c4] bg-[#f8f0e1] p-3 sm:flex-row"><SelectFilter label="Kabupaten" value={kabupaten} options={[...new Set(rows.map((row) => row.kabupaten))]} onChange={setKabupaten} testId="select-panen-area" /><SelectFilter label="Komoditas" value={commodity} options={[...new Set(rows.map((row) => row.komoditas))]} onChange={setCommodity} testId="select-panen-commodity" /><SelectFilter label="Kualitas" value={quality} options={[...new Set(rows.map((row) => row.kualitas))]} onChange={setQuality} testId="select-panen-quality" /></div>;
}

function OfficialPriceBand({ records, status }: { records: OfficialPriceRecord[]; status: PriceData['officialStatus'] }) {
  if (records.length === 0) return null;
  const sources = [...new Set(records.map((record) => record.sumber))].join(' · ');
  return <div className="mb-4 rounded-[14px] border border-[#cfe1cd] bg-[#eef7ee] p-3">
    <div className="mb-2 flex items-center justify-between gap-3"><div><div className="text-sm font-semibold text-[#315b49]">Harga resmi tingkat petani</div><div className="text-xs text-[#6b8073]">{sources}</div></div><span className="rounded-full bg-[#d4ead5] px-2 py-1 font-data text-[9px] uppercase tracking-wide text-[#4d7a55]">{status === 'stale' ? 'Snapshot terakhir' : 'Sumber resmi'}</span></div>
    <div className="grid gap-2 sm:grid-cols-3">{records.slice(0, 3).map((record) => <div key={`${record.sumber}-${record.wilayah}-${record.komoditas}-${record.harga}`} className="flex items-center justify-between rounded-[10px] border border-[#d7e9d5] bg-[#f8fcf6] px-3 py-2"><div><div className="text-xs font-semibold text-[#3b6250]">{record.komoditas}</div><div className="text-[10px] text-[#7b8e81]">{record.level} · {record.wilayah}</div></div><span className="font-data text-sm text-[#c9664e]">{money(record.harga)}<small className="text-[9px] text-[#7e8a80]">/{record.satuan}</small></span></div>)}</div>
  </div>;
}

function ReferencePriceBand() {
  return <div className="mb-4 rounded-[14px] border border-[#e7d5a9] bg-[#fff8e8] p-3">
    <div className="mb-2 flex items-start justify-between gap-3"><div><div className="text-sm font-semibold text-[#725c31]">Patokan bawah KDMP Merah Putih</div><div className="text-xs text-[#8c7b59]">Pembanding harga, bukan pengganti harga aktual lapangan</div></div><span className="rounded-full bg-[#f1e2b8] px-2 py-1 font-data text-[9px] uppercase tracking-wide text-[#876d34]">Referensi</span></div>
    <div className="grid gap-2 sm:grid-cols-4">{referencePrices.map((reference) => <div key={reference.label} className="rounded-[10px] border border-[#eddfbc] bg-[#fffdf6] px-3 py-2"><div className="text-xs font-semibold text-[#6b5a37]">{reference.label}</div><div className="mt-1 font-data text-base text-[#c9664e]">{money(reference.price)}<small className="text-[9px] text-[#8c7b59]">/{reference.unit}</small></div><div className="mt-0.5 text-[10px] text-[#9a8965]">{reference.note}</div></div>)}</div>
  </div>;
}

function SourceGuide() {
  return <div className="mt-5 rounded-[14px] border border-[#dfd5c4] bg-[#f8f0e1] p-4">
    <div className="mb-3 flex items-center justify-between gap-3"><div><div className="text-sm font-semibold text-[#35584b]">Sumber pelacak Gresik–Lamongan</div><div className="text-xs text-[#7d857d]">Gunakan minimal satu sumber resmi dan satu konfirmasi lapangan.</div></div><span className="rounded-full bg-[#e6efd9] px-2 py-1 font-data text-[9px] uppercase tracking-wide text-[#628252]">3 lapis verifikasi</span></div>
    <div className="grid gap-4 text-xs sm:grid-cols-3">
      <div><div className="mb-1.5 font-data text-[10px] uppercase tracking-wider text-[#8a806d]">Aplikasi resmi</div><div className="space-y-1.5">{officialSources.map((source) => <a key={source.name} href={source.url} target="_blank" rel="noreferrer" className="block font-semibold text-[#466858] underline decoration-[#b9c9a5] underline-offset-2 hover:text-[#bd654e]">{source.name}<span className="mt-0.5 block font-normal no-underline text-[#879087]">{source.description}</span></a>)}</div></div>
      <div><div className="mb-1.5 font-data text-[10px] uppercase tracking-wider text-[#8a806d]">Real-time lapangan</div><div className="space-y-1 text-[#687a70]">{fieldSources.map((source) => <div key={source}>• {source}</div>)}</div></div>
      <div><div className="mb-1.5 font-data text-[10px] uppercase tracking-wider text-[#8a806d]">Konfirmasi langsung</div><div className="space-y-1 text-[#687a70]">{verificationContacts.map((source) => <div key={source}>• {source}</div>)}</div></div>
    </div>
    <div className="mt-3 flex flex-col gap-1 rounded-[10px] border border-[#dfd5c4] bg-[#fffaf1] px-3 py-2"><span className="font-data text-[9px] uppercase tracking-wider text-[#8a806d]">Formula Google Sheet opsional</span><code className="break-all text-[11px] text-[#536c5e]">{googleSheetFormula}</code><span className="text-[10px] text-[#9a9688]">Jika halaman sumber sedang maintenance atau tabel dirender oleh JavaScript, gunakan collector Python dan verifikasi manual.</span></div>
  </div>;
}

function PanenPanel({ rows, official, officialStatus, active }: { rows: PanenRecord[]; official: OfficialPriceRecord[]; officialStatus: PriceData['officialStatus']; active: boolean }) {
  const [kabupaten, setKabupaten] = useState('Semua');
  const [commodity, setCommodity] = useState('Semua');
  const [quality, setQuality] = useState('Semua');
  const [sort, setSort] = useState('Terbaru');
  const [expanded, setExpanded] = useState<string | null>(null);
  const summaries = useMemo(() => summarizePanen(rows.filter((row) => (kabupaten === 'Semua' || row.kabupaten === kabupaten) && (commodity === 'Semua' || row.komoditas === commodity) && (quality === 'Semua' || row.kualitas === quality))).sort((a, b) => sort === 'Harga tertinggi' ? b.hargaTerakhir - a.hargaTerakhir : b.tanggalTerakhir.localeCompare(a.tanggalTerakhir)), [rows, kabupaten, commodity, quality, sort]);
  return <section className={`rise rise-delay-2 mt-12 border-t border-[#dccfbd] pt-8 ${active ? 'scroll-mt-4' : ''}`} id="harga-panen">
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#7a9b57]" /><h2 className="font-display text-[22px] font-bold text-[#2a4e43]">Harga panen</h2><span className="rounded-full bg-[#e6efd9] px-2 py-0.5 font-data text-[10px] text-[#628252]">Laporan warga</span></div><p className="mt-1 text-sm text-[#78827b]">Harga dari kebun dan lumbung terakhir yang dilaporkan.</p></div><select data-testid="select-sort-panen" value={sort} onChange={(event) => setSort(event.target.value)} className="h-9 rounded-[10px] border border-[#d7cdbd] bg-[#fffaf1] px-2 text-xs font-semibold text-[#567066] outline-none"><option>Terbaru</option><option>Harga tertinggi</option></select></div>
      <OfficialPriceBand records={official} status={officialStatus} /><ReferencePriceBand /><PanenFilters rows={rows} kabupaten={kabupaten} setKabupaten={setKabupaten} commodity={commodity} setCommodity={setCommodity} quality={quality} setQuality={setQuality} />
    {summaries.length === 0 ? <div className="mt-3"><EmptyState title="Belum ada laporan panen" body="Belum ada catatan yang cocok dengan filter ini. Data panen akan tetap tampil di sini saat laporan baru masuk." action={<button data-testid="button-reset-panen" onClick={() => { setKabupaten('Semua'); setCommodity('Semua'); setQuality('Semua'); }} className="mt-4 text-xs font-bold text-[#ba654d] underline underline-offset-4">Bersihkan filter</button>} /></div> : <div className="mt-3 space-y-2">{summaries.map((summary) => <PanenRow key={`${summary.komoditas}-${summary.kualitas}`} summary={summary} expanded={expanded === `${summary.komoditas}-${summary.kualitas}`} onExpand={() => setExpanded(expanded === `${summary.komoditas}-${summary.kualitas}` ? null : `${summary.komoditas}-${summary.kualitas}`)} />)}</div>}
     <SourceGuide />
  </section>;
}

function PanenRow({ summary, expanded, onExpand }: { summary: PanenSummary; expanded: boolean; onExpand: () => void }) {
  return <div className={`overflow-hidden rounded-[14px] border bg-[#fffaf1] ${expanded ? 'border-[#91a86b]' : 'border-[#dfd5c4]'}`}><button data-testid={`button-expand-panen-${summary.komoditas}`} onClick={onExpand} className="flex w-full flex-col gap-3 p-4 text-left sm:grid sm:grid-cols-[1.6fr_1fr_1fr_1.3fr_auto] sm:items-center sm:gap-4"><div><div className="font-semibold text-[#35584b]">{summary.komoditas}</div><div className="mt-1 text-xs text-[#81867d]">{summary.kualitas} <span className="mx-1 text-[#b5aa99]">·</span> {summary.jumlahCatatan} catatan</div></div><div><span className="block font-data text-[9px] uppercase tracking-wider text-[#8b8f84]">Terakhir</span><span className="font-data text-base text-[#d3674e]">{money(summary.hargaTerakhir)}<small className="text-[10px] text-[#8b8f84]">/kg</small></span></div><div><span className="block font-data text-[9px] uppercase tracking-wider text-[#8b8f84]">Rata-rata</span><span className="font-data text-sm text-[#35584b]">{money(summary.rataRata)}</span></div><div className="flex items-center gap-1.5 text-xs text-[#64796f]"><MapPin size={13} className="shrink-0 text-[#7a9b57]" />{summary.lokasiTerakhir}, {summary.kabupaten}</div><div className="flex items-center gap-2 text-[10px] text-[#8b8f84]">{shortDate(summary.tanggalTerakhir)} {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</div></button>{expanded && <div className="border-t border-[#dce6cf] bg-[#f3f6e9] px-4 py-3 text-xs leading-relaxed text-[#617467]">Catatan terakhir berasal dari <strong>{summary.lokasiTerakhir}</strong>. Rata-rata dihitung dari {summary.jumlahCatatan} laporan yang tersedia pada area terpilih.</div>}</div>;
}

function MarketDetail() {
  const [, params] = useRoute<{ marketId: string }>('/pasar/:marketId');
  const data = usePriceData();
  const marketId = params?.marketId ? decodeURIComponent(params.marketId) : '';
  const marketRecords = useMemo(() => data?.sembako.filter((record) => record.marketId === marketId) ?? [], [data, marketId]);
  const [selectedCommodity, setSelectedCommodity] = useState('');
  useEffect(() => {
    if (!selectedCommodity && marketRecords[0]) setSelectedCommodity(marketRecords[0].commodityKey);
  }, [marketRecords, selectedCommodity]);
  const selectedRecord = marketRecords.find((record) => record.commodityKey === selectedCommodity) ?? marketRecords[0];

  if (!data) return <div className="grain flex min-h-[100dvh] items-center justify-center market-shell"><SkeletonCards /></div>;
  if (!marketRecords.length) return <div className="grain min-h-[100dvh] market-shell px-5 py-8"><div className="mx-auto max-w-[760px]"><Link href="/" className="text-sm font-semibold text-[#557567]">← Kembali ke ringkasan</Link><div className="mt-8"><EmptyState title="Pasar tidak ditemukan" body="Lokasi ini tidak ada di snapshot harga yang sedang aktif." action={<Link href="/" className="mt-4 inline-block text-xs font-bold text-[#ba654d] underline underline-offset-4">Kembali ke daftar harga</Link>} /></div></div></div>;

  const market = marketRecords[0];
  return <div className="grain min-h-[100dvh] market-shell text-[#29463e]">
    <main className="mx-auto max-w-[1000px] px-5 pb-16 pt-7 sm:px-8 lg:pt-10">
      <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#557567] transition hover:text-[#bd654e]">← Kembali ke ringkasan</Link>
      <div className="mt-7 flex flex-col justify-between gap-5 border-b border-[#ddd2c0] pb-7 sm:flex-row sm:items-end">
        <div><div className="mb-2 font-data text-[10px] uppercase tracking-[.16em] text-[#a06e55]">Detail pasar</div><h1 className="font-display text-[clamp(2.2rem,5vw,4rem)] font-bold leading-none tracking-[-.045em] text-[#244a40]">{market.location}</h1><p className="mt-3 flex items-center gap-2 text-sm text-[#718077]"><MapPin size={15} className="text-[#d27855]" />{market.area} · {market.address}</p></div>
        <div className="rounded-[14px] border border-[#d9e5d6] bg-[#eef7ee] px-4 py-3 text-sm text-[#527064]"><strong className="block font-data text-lg text-[#2e6b4d]">{marketRecords.length}</strong>komoditas tercatat</div>
      </div>
      <div className="mt-7 grid gap-7 lg:grid-cols-[.8fr_1.5fr]">
        <section><div className="mb-3"><div className="font-data text-[10px] uppercase tracking-[.12em] text-[#a06e55]">Komoditas di lokasi ini</div><p className="mt-1 text-sm text-[#78827b]">Pilih komoditas untuk melihat trennya.</p></div><div className="space-y-2">{marketRecords.sort((left, right) => left.unitPrice - right.unitPrice).map((record) => <button key={record.commodityKey} onClick={() => setSelectedCommodity(record.commodityKey)} className={`flex w-full items-center justify-between rounded-[13px] border p-3 text-left transition ${selectedRecord?.commodityKey === record.commodityKey ? 'border-[#d79a58] bg-[#fff3e7] shadow-sm' : 'border-[#dfd5c4] bg-[#fffaf1] hover:border-[#caaa76]'}`}><span><strong className="block text-sm text-[#35584b]">{record.commodity}</strong><small className="mt-1 block text-xs text-[#81867d]">{record.productName} · {record.unit}</small></span><span className="font-data text-sm text-[#d3674e]">{money(record.unitPrice)}</span></button>)}</div></section>
        <section className="space-y-4">{selectedRecord && <><PriceTrendChart history={data.history} area={selectedRecord.area} commodityKey={selectedRecord.commodityKey} commodity={selectedRecord.commodity} /><div className="rounded-[16px] border border-[#dfd5c4] bg-[#f8f0e2] p-4 text-sm text-[#617467]"><div className="mb-2 flex items-center justify-between gap-3"><strong className="text-[#35584b]">Sumber pencatatan</strong><span className="rounded-full bg-[#e7f1e3] px-2 py-1 font-data text-[9px] uppercase tracking-wide text-[#528056]">{selectedRecord.confidence}</span></div><p>{selectedRecord.productName} · {selectedRecord.size} · dipantau {selectedRecord.observedAt}.</p>{selectedRecord.sourceUrl && <a href={selectedRecord.sourceUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 font-semibold text-[#bd654e] underline underline-offset-2">Buka sumber resmi <ArrowUpRight size={13} /></a>}</div></>}</section>
      </div>
    </main>
  </div>;
}

function CommodityDetail() {
  const [, params] = useRoute<{ commodityKey: string }>('/komoditas/:commodityKey');
  const data = usePriceData();
  const commodityKey = params?.commodityKey ? decodeURIComponent(params.commodityKey) : '';
  const records = useMemo(() => data?.sembako.filter((record) => record.commodityKey === commodityKey) ?? [], [data, commodityKey]);
  const areas = [...new Set(records.map((record) => record.area))];
  const areaLeaders = areas.map((area) => {
    const areaRecords = records.filter((record) => record.area === area);
    return { area, record: [...areaRecords].sort((left, right) => left.unitPrice - right.unitPrice)[0] };
  });

  if (!data) return <div className="grain flex min-h-[100dvh] items-center justify-center market-shell"><SkeletonCards /></div>;
  if (!records.length) return <div className="grain min-h-[100dvh] market-shell px-5 py-8"><div className="mx-auto max-w-[760px]"><Link href="/" className="text-sm font-semibold text-[#557567]">← Kembali ke ringkasan</Link><div className="mt-8"><EmptyState title="Komoditas tidak ditemukan" body="Komoditas ini tidak ada di snapshot harga yang sedang aktif." action={<Link href="/" className="mt-4 inline-block text-xs font-bold text-[#ba654d] underline underline-offset-4">Kembali ke daftar harga</Link>} /></div></div></div>;

  const commodity = records[0];
  return <div className="grain min-h-[100dvh] market-shell text-[#29463e]">
    <main className="mx-auto max-w-[1180px] px-5 pb-16 pt-7 sm:px-8 lg:pt-10">
      <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#557567] transition hover:text-[#bd654e]">← Kembali ke ringkasan</Link>
      <div className="mt-7 flex flex-col justify-between gap-5 border-b border-[#ddd2c0] pb-7 sm:flex-row sm:items-end">
        <div><div className="mb-2 font-data text-[10px] uppercase tracking-[.16em] text-[#a06e55]">Detail komoditas</div><h1 className="font-display text-[clamp(2.2rem,5vw,4rem)] font-bold leading-none tracking-[-.045em] text-[#244a40]">{commodity.commodity}</h1><p className="mt-3 text-sm text-[#718077]">Perbandingan harga terbaru dan riwayat rata-rata per wilayah.</p></div>
        <div className="rounded-[14px] border border-[#d9e5d6] bg-[#eef7ee] px-4 py-3 text-sm text-[#527064]"><strong className="block font-data text-lg text-[#2e6b4d]">{records.length}</strong>sumber harga aktif</div>
      </div>
      <section className="mt-7">
        <div className="mb-3"><div className="font-data text-[10px] uppercase tracking-[.12em] text-[#a06e55]">Harga terbaru</div><p className="mt-1 text-sm text-[#78827b]">Harga terendah per wilayah pada snapshot {data.reportDate ? shortDate(data.reportDate) : 'terakhir tersedia'}.</p></div>
        <div className="grid gap-3 sm:grid-cols-2">{areaLeaders.map(({ area, record }) => <div key={area} className="rounded-[16px] border border-[#dfd5c4] bg-[#fffaf1] p-4"><div className="flex items-center justify-between gap-3"><div><div className="flex items-center gap-2 text-sm font-semibold text-[#35584b]"><MapPin size={14} className="text-[#d27855]" />{area}</div><div className="mt-1 text-xs text-[#81867d]">{record.location} · {record.size}</div></div><div className="text-right font-data text-lg text-[#d3674e]">{money(record.unitPrice)}<small className="text-[10px] text-[#908679]">/{record.unit}</small></div></div><Link href={`/pasar/${encodeURIComponent(record.marketId)}`} className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#ba654d] underline underline-offset-2">Buka detail pasar <ArrowUpRight size={12} /></Link></div>)}</div>
      </section>
      <section className="mt-8">
        <div className="mb-3"><div className="font-data text-[10px] uppercase tracking-[.12em] text-[#a06e55]">Pergerakan antarwilayah</div><p className="mt-1 text-sm text-[#78827b]">Gunakan grafik untuk melihat apakah harga bergerak searah atau berbeda antarwilayah.</p></div>
        <div className="grid gap-4 lg:grid-cols-2">{areas.map((area) => <PriceTrendChart key={area} history={data.history} area={area} commodityKey={commodityKey} commodity={commodity.commodity} />)}</div>
      </section>
    </main>
  </div>;
}

function Home() {
  const [mode, setMode] = useState<'sembako' | 'panen'>('sembako');
  const data = usePriceData();
  const [search, setSearch] = useState('');
  const [area, setArea] = useState('Semua area');
  const [category, setCategory] = useState<CategoryKey>('semua');
  const [detailView, setDetailView] = useState(false);
  const panenSummary = useMemo(() => data ? summarizePanen(data.panen) : [], [data]);
  const setProductMode = (next: 'sembako' | 'panen') => { setMode(next); if (next === 'panen') window.setTimeout(() => document.getElementById('harga-panen')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50); };
  return <div className="grain flex min-h-[100dvh] market-shell text-[#29463e]">
    <aside className="hidden min-h-[100dvh] w-[238px] shrink-0 flex-col justify-between bg-[#1d403a] px-5 py-6 lg:flex"><div><AppMark /><div className="mt-14"><span className="font-data text-[10px] uppercase tracking-[.16em] text-[#88a79b]">Navigasi</span><nav className="mt-3 space-y-1"><button data-testid="nav-overview" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex w-full items-center gap-3 rounded-[11px] bg-[#31574e] px-3 py-2.5 text-left text-sm font-semibold text-[#f6eddb]"><Layers3 size={16} /> Ringkasan harga</button><button data-testid="nav-panen" onClick={() => setProductMode('panen')} className="flex w-full items-center gap-3 rounded-[11px] px-3 py-2.5 text-left text-sm text-[#bdd0c5] transition hover:bg-[#294d46] hover:text-[#f6eddb]"><Sprout size={16} /> Pantau harga panen</button></nav></div></div><div className="rounded-[14px] border border-[#49665d] bg-[#294d46] p-3 text-xs leading-relaxed text-[#b8cdc2]"><CircleHelp size={15} className="mb-2 text-[#e8b84d]" /><strong className="block text-[#f3ead9]">Butuh konteks?</strong>Harga terbaik berarti harga per satuan yang paling rendah dari sumber yang tersedia.</div></aside>
    <main className="min-w-0 flex-1"><header className="flex items-center justify-between border-b border-[#ddd2c0] bg-[#f5eddf]/90 px-5 py-4 backdrop-blur sm:px-8 lg:hidden"><AppMark /><button data-testid="mobile-nav-panen" onClick={() => setProductMode('panen')} className="rounded-[9px] border border-[#d5c7b3] bg-[#fffaf1] p-2 text-[#527064]" aria-label="Buka harga panen"><Sprout size={17} /></button></header><div className="mx-auto max-w-[1180px] px-5 pb-16 pt-7 sm:px-8 lg:px-12 lg:pt-10">
       <div className="rise flex flex-col justify-between gap-6 sm:flex-row sm:items-end"><div><div className="mb-3 flex items-center gap-2 font-data text-[10px] uppercase tracking-[.16em] text-[#a06e55]"><span className="h-1.5 w-1.5 rounded-full bg-[#d27855]" />Laporan {data?.reportDate ? shortDate(data.reportDate) : 'menunggu pembaruan'}</div><h1 className="max-w-[580px] font-display text-[clamp(2.2rem,5vw,4.15rem)] font-bold leading-[.98] tracking-[-.045em] text-[#244a40]">Harga hari ini,<br /><em className="font-normal text-[#cf7052]">tanpa berkeliling.</em></h1><p className="mt-4 max-w-[510px] text-[15px] leading-relaxed text-[#6d7d74]">Bandingkan kebutuhan dapur dan hasil panen dari titik-titik lokal Gresik–Lamongan dalam satu pandangan.</p></div><div className="flex shrink-0 items-center gap-2 rounded-[12px] border border-[#e1d5c3] bg-[#f9f3e8] px-3 py-2 text-xs text-[#718077]"><span className="h-2 w-2 rounded-full bg-[#6fa26d]" />Pantauan lokal · pembaruan otomatis</div></div>
       <div className="mt-8"><StatusBand count={data?.sembako.length ?? 0} panenCount={panenSummary.length} origin={data?.origin ?? 'demo'} officialStatus={data?.officialStatus ?? 'unavailable'} officialCount={data?.official.length ?? 0} reportDate={data?.reportDate ?? null} source={data?.marketSource ?? 'SISKAPERBAPO Jawa Timur'} /></div>
       {data && <OverviewStats data={data} />}
      <div className="mt-8 flex flex-col gap-4 border-b border-[#ddd2c0] pb-4 sm:flex-row sm:items-center sm:justify-between"><SegmentedTabs mode={mode} setMode={setProductMode} /><div className="flex flex-col gap-2 sm:flex-row"><SearchBox value={search} onChange={setSearch} /><AreaFilter value={area} onChange={setArea} /></div></div>
       <div className="mt-7">{!data ? <SkeletonCards /> : mode === 'sembako' ? <><CategoryNav records={data.sembako} value={category} onChange={setCategory} /><div className="mt-7"><SembakoPanel records={data.sembako} search={search} area={area} category={category} reportDate={data.reportDate} detailView={detailView} setDetailView={setDetailView} /></div></> : <PanenPanel rows={data.panen} official={data.official} officialStatus={data.officialStatus} active={mode === 'panen'} />}</div>
       <footer className="mt-14 flex flex-col gap-2 border-t border-[#ddd2c0] pt-5 text-[11px] text-[#899088] sm:flex-row sm:items-center sm:justify-between"><span>Pelacak Harga · dibuat untuk warga dan pedagang kecil</span><span className="flex items-center gap-1 font-data uppercase tracking-wider"><Database size={12} />{data?.marketSource ?? 'Snapshot lokal'} <ArrowUpRight size={12} /></span></footer>
    </div></main>
  </div>;
}

function Router() {
  return <Switch><Route path="/" component={Home} /><Route path="/pasar/:marketId" component={MarketDetail} /><Route path="/komoditas/:commodityKey" component={CommodityDetail} /><Route component={NotFound} /></Switch>;
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

export default function App() {
  return <QueryClientProvider client={queryClient}><TooltipProvider><WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}><RoutedErrorBoundary><Router /></RoutedErrorBoundary></WouterRouter><Toaster /></TooltipProvider></QueryClientProvider>;
}