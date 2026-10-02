import { useMemo, useState } from 'react';
import { MessageCircle, Send, User } from 'lucide-react';
import { ADMIN_DISPLAY, waAdminMessage, waLaporHarga, waLink } from '@/sources';

/** Kartu interaksi: hubungi admin + form lapor harga via WhatsApp.
 *  Tanpa backend: pesan disusun lokal lalu dibuka di wa.me. */
export function AdminContact() {
  return <a
    href={waLink(waAdminMessage)}
    target="_blank"
    rel="noreferrer"
    data-testid="admin-contact"
    className="flex items-center gap-3 rounded-[14px] border border-[#cae1d2] bg-[#edf7ef] px-4 py-3 text-sm font-semibold text-[#22453b] shadow-sm transition hover:bg-[#e0f2e4]"
  >
    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#25d366] text-white"><MessageCircle size={17} /></span>
    <span>
      Hubungi Admin
      <span className="block text-[11px] font-normal text-[#5f7a6c]">WhatsApp {ADMIN_DISPLAY}</span>
    </span>
  </a>;
}

export function LaporHargaCard() {
  const [lokasi, setLokasi] = useState('');
  const [komoditas, setKomoditas] = useState('');
  const [harga, setHarga] = useState('');
  const [catatan, setCatatan] = useState('');

  const ready = lokasi.trim() && komoditas.trim() && harga.trim();
  const link = useMemo(
    () => waLink(waLaporHarga({ lokasi, komoditas, harga, catatan })),
    [lokasi, komoditas, harga, catatan],
  );

  const field = "w-full rounded-[10px] border border-[#ddd2c0] bg-[#fffaf1] px-3 py-2 text-sm text-[#29463e] outline-none placeholder:text-[#a9a294] focus:border-[#6fa26d]";

  return <section id="lapor-harga" className="rise mt-12 rounded-[18px] border border-[#e1d5c3] bg-[#fdf7ec] p-5 shadow-sm">
    <div className="mb-4 flex items-center gap-2">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8b84d] text-[#263f3b]"><Send size={16} /></span>
      <div>
        <h3 className="font-display text-lg font-bold text-[#244a40]">Lapor harga yang kamu lihat</h3>
        <p className="text-xs text-[#718077]">Bantu warga sekitar — kirim harga terbaru lewat WhatsApp admin.</p>
      </div>
    </div>
    <div className="grid gap-3 sm:grid-cols-2">
      <input className={field} placeholder="Lokasi (mis. Pasar Baru Gresik)" value={lokasi} onChange={(e) => setLokasi(e.target.value)} />
      <input className={field} placeholder="Komoditas (mis. Beras medium)" value={komoditas} onChange={(e) => setKomoditas(e.target.value)} />
      <input className={field} inputMode="numeric" placeholder="Harga per kg/liter (mis. 14500)" value={harga} onChange={(e) => setHarga(e.target.value.replace(/[^0-9]/g, ''))} />
      <input className={field} placeholder="Catatan (opsional)" value={catatan} onChange={(e) => setCatatan(e.target.value)} />
    </div>
    <a
      href={ready ? link : undefined}
      target="_blank"
      rel="noreferrer"
      aria-disabled={!ready}
      onClick={(e) => { if (!ready) e.preventDefault(); }}
      className={`mt-4 inline-flex items-center gap-2 rounded-[11px] px-4 py-2.5 text-sm font-semibold transition ${ready
        ? 'bg-[#25d366] text-white shadow hover:bg-[#1fb457]'
        : 'cursor-not-allowed bg-[#d8d2c5] text-[#928b7c]'}`}
    >
      <MessageCircle size={16} /> Kirim ke Admin via WhatsApp
    </a>
    <p className="mt-2 flex items-center gap-1 text-[11px] text-[#899088]"><User size={11} /> Pesan terbuka di WhatsApp kamu — belum terkirim sampai kamu tekan kirim di sana.</p>
  </section>;
}
