import { useState } from "react";
import { MessageCircle, X } from "lucide-react";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-[9998] bg-black/40" onClick={() => setOpen(false)} />
      )}
      {open ? (
        <div className="fixed bottom-0 right-0 z-[9999] h-[80dvh] w-full max-w-md overflow-hidden rounded-t-2xl border border-[#e1d5c3] bg-[#fdf7ec] shadow-2xl sm:bottom-20 sm:right-5 sm:h-[70dvh] sm:rounded-2xl">
          <div className="flex items-center justify-between bg-[#244a40] px-4 py-2 text-white">
            <span className="text-sm font-semibold">Chat AI — Nana</span>
            <button onClick={() => setOpen(false)} aria-label="Tutup chat" className="rounded-full p-1 hover:bg-white/10"><X size={18} /></button>
          </div>
          <iframe src="https://romlidisduk-beep.github.io/nana/" title="Chat AI Nana" className="h-[calc(80dvh-40px)] w-full sm:h-[calc(70dvh-40px)]" />
        </div>
      ) : (
        <button onClick={() => setOpen(true)} aria-label="Buka chat AI" className="fixed bottom-5 right-5 z-[9999] flex items-center gap-2 rounded-full bg-[#244a40] px-4 py-3 text-sm font-semibold text-white shadow-xl transition hover:bg-[#1d3a33]">
          <MessageCircle size={18} /> Chat AI
        </button>
      )}
    </>
  );
}
