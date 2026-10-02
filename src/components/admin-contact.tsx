import { MessageCircle } from 'lucide-react';
import { ADMIN_DISPLAY, waAdminMessage, waLink } from '@/sources';

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

