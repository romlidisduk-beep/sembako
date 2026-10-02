import { useEffect, useState } from 'react';
import { MessageSquare, Send } from 'lucide-react';
import { kirimKomentar, subscribeKomentar, type Komentar } from '@/lib/firebase-comments';

const waktu = (c: Komentar) =>
  c.createdAt?.seconds
    ? new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
        .format(new Date(c.createdAt.seconds * 1000))
    : 'baru saja';

/** Komentar live tersimpan di Firestore — real-time, tanpa login. */
export function KomentarLive() {
  const [rows, setRows] = useState<Komentar[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [nama, setNama] = useState('');
  const [isi, setIsi] = useState('');
  const [kirim, setKirim] = useState(false);

  useEffect(() => {
    const unsub = subscribeKomentar(setRows, () =>
      setError('Komentar belum tersedia (Firestore belum diaktifkan).'));
    return () => unsub();
  }, []);

  const submit = async () => {
    if (!nama.trim() || !isi.trim() || kirim) return;
    setKirim(true);
    try {
      await kirimKomentar(nama.trim(), isi.trim());
      setIsi('');
    } catch {
      setError('Gagal mengirim — coba lagi nanti.');
    }
    setKirim(false);
  };

  const field = "w-full rounded-[10px] border border-[#ddd2c0] bg-[#fffaf1] px-3 py-2 text-sm text-[#29463e] outline-none placeholder:text-[#a9a294] focus:border-[#6fa26d]";

  return <section id="komentar" className="rise mt-12 rounded-[18px] border border-[#e1d5c3] bg-[#fdf7ec] p-5 shadow-sm">
    <div className="mb-4 flex items-center gap-2">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#6fa26d] text-white"><MessageSquare size={16} /></span>
      <div>
        <h3 className="font-display text-lg font-bold text-[#244a40]">Komentar warga <span className="ml-1 inline-flex items-center gap-1 rounded-full bg-[#e7f1e3] px-2 py-0.5 text-[9px] font-data uppercase tracking-wide text-[#528056]">live</span></h3>
        <p className="text-xs text-[#718077]">Percakapan tersimpan otomatis & tampil real-time untuk semua pengunjung.</p>
      </div>
    </div>

    <div className="grid gap-2 sm:grid-cols-[180px_1fr]">
      <input className={field} placeholder="Nama kamu" maxLength={40} value={nama} onChange={(e) => setNama(e.target.value)} />
      <textarea className={`${field} min-h-[64px]`} placeholder="Tulis komentar (maks 500 karakter)..." maxLength={500} value={isi} onChange={(e) => setIsi(e.target.value)} />
    </div>
    <button
      onClick={submit}
      disabled={!nama.trim() || !isi.trim() || kirim}
      className={`mt-3 inline-flex items-center gap-2 rounded-[11px] px-4 py-2.5 text-sm font-semibold transition ${nama.trim() && isi.trim() && !kirim
        ? 'bg-[#328252] text-white shadow hover:bg-[#2a6b44]'
        : 'cursor-not-allowed bg-[#d8d2c5] text-[#928b7c]'}`}
    >
      <Send size={15} /> {kirim ? 'Mengirim...' : 'Kirim komentar'}
    </button>

    {error && <p className="mt-3 rounded-[10px] bg-[#fdeeee] px-3 py-2 text-xs text-[#a05548]">{error}</p>}

    <div className="mt-5 space-y-3">
      {rows.length === 0 && !error && <p className="text-xs text-[#899088]">Belum ada komentar — jadilah yang pertama!</p>}
      {rows.map((c) => (
        <div key={c.id} className="rounded-[12px] border border-[#e9e0d1] bg-[#fffaf1] px-3 py-2.5">
          <div className="flex items-center justify-between text-[11px] text-[#899088]">
            <strong className="text-[#35584b]">{c.nama}</strong><span>{waktu(c)}</span>
          </div>
          <p className="mt-1 whitespace-pre-wrap text-sm text-[#29463e]">{c.isi}</p>
        </div>
      ))}
    </div>
  </section>;
}
