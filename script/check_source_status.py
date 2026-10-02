#!/usr/bin/env python3
"""Cek status tiap sumber resmi (aktif/pemeliharaan/blokir) -> data/source-status.json.

Dipanggil workflow harian. Fail-soft: selalu exit 0.
"""
from __future__ import annotations
import json, ssl, urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCES = [
    ("bapanas-panel", "Panel Harga Badan Pangan", "https://panelharga.badanpangan.go.id/beranda"),
    ("bapanas-data", "Data Pangan Bapanas", "https://data.badanpangan.go.id/"),
    ("pihps", "PIHPS Bank Indonesia", "https://www.bi.go.id/hargapangan/TabelHarga/ProdusenDaerah"),
    ("siskaperbapo", "SISKAPERBAPO Jawa Timur", "https://siskaperbapo.jatimprov.go.id/"),
    ("simharga", "SIMHARGA Kementan", "https://bdsp2.pertanian.go.id/simharga/index_harga.php"),
    ("sijagung", "SIJAGUNG Kementan", "https://simpakan.ditjenpkh.pertanian.go.id/sijagung/backend/web/site/data-pembelian"),
    ("bps-jatim", "BPS Jawa Timur", "https://jatim.bps.go.id/id/statistics-table?subject=536"),
]
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def cek(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126"})
        body = urllib.request.urlopen(req, timeout=20, context=CTX).read().decode(errors="ignore")
        low = body.lower()
        if "pemeliharaan" in low or "maintenance" in low:
            return {"status": "pemeliharaan"}
        if len(body) < 2000:  # halaman kosong / shell saja
            return {"status": "terbatas"}
        return {"status": "aktif"}
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code in (403, 503):  # Cloudflare / blokir mesin
            return {"status": "blokir-otomatis"}
        return {"status": "tidak-dijangkau"}


def main() -> int:
    items = []
    for key, nama, url in SOURCES:
        hasil = cek(url)
        hasil.update({"id": key, "nama": nama, "url": url})
        items.append(hasil)
        print(f"{nama}: {hasil['status']}")
    out = {
        "generatedAt": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
        "items": items,
    }
    path = Path(__file__).resolve().parents[1] / "data" / "source-status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"source-status: {len(items)} sumber -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
