#!/usr/bin/env python3
"""Penarik harga produsen beras dari PIHPS Bank Indonesia.

Mengisi bagian "laporan panen" website dengan harga indikatif tingkat
produsen (penggilingan) dari PIHPS BI -- sumber resmi yang masih terbuka.
Sengaja diberi label jelas "BI PIHPS - Harga Produsen" supaya tidak
tertukar dengan harga acuan pemerintah (HPP/KDMP) atau transaksi pasar.

Dipanggil otomatis oleh workflow .github/workflows/track-prices.yml
sebelum build website, jadi gagal di sini tidak boleh menggagalkan
pelacakan harga pasar (exit code selalu 0).
"""
from __future__ import annotations

import argparse
import json
import time
import http.cookiejar
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://www.bi.go.id/hargapangan"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# com_1..com_6 = varian beras produsen PIHPS (cat_1)
BERAS_IDS = ["com_1"]  # satu respons berisi semua 6 varian (level 2)
JAKARTA = ZoneInfo("Asia/Jakarta")


def _session():
    """Session dengan cookie anti-forgery BI (wajib sebelum AJAX)."""
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA), ("X-Requested-With", "XMLHttpRequest")]
    op.open(f"{BASE}/TabelHarga/ProdusenDaerah", timeout=30).read()
    return op


def _grid(op, comid: str, day: str) -> dict:
    params = urllib.parse.urlencode({
        "price_type_id": "1",      # produsen
        "comcat_id": comid,
        "province_id": "16",       # Jawa Timur
        "regency_id": "",
        "market_id": "",
        "tipe_laporan": "1",       # harian
        "start_date": day,
        "end_date": day,
    })
    url = f"{BASE}/WebSite/TabelHarga/GetGridDataDaerah?{params}"
    return json.loads(op.open(url, timeout=40).read())


def _to_number(raw) -> float | None:
    try:
        n = float(str(raw).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _day_key(day_iso: str) -> str:
    d = date.fromisoformat(day_iso)
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def collect(target_date: str) -> list[dict]:
    """Ambil semua varian beras produsen utk satu tanggal. [] kalau gagal."""
    try:
        op = _session()
    except Exception as exc:
        print(f"PIHPS: gagal buka sesi: {exc}")
        return []
    key = _day_key(target_date)
    records = []
    for comid in BERAS_IDS:
        try:
            payload = _grid(op, comid, target_date)
        except Exception as exc:
            print(f"PIHPS {comid}: gagal ({exc}), lewati")
            continue
        for row in payload.get("data", []):
            if row.get("level") != 2:
                continue  # level 2 = varian spesifik; level 1 = agregat "Beras" (duplikat)
            harga = _to_number(row.get(key))
            if harga is None:
                continue
            records.append({
                "tanggal": target_date,
                "kabupaten": "Jawa Timur (tingkat produsen)",
                "kecamatan": "-",
                "desaKelurahan": "-",
                "lokasi": "BI PIHPS - Harga Produsen",
                "komoditas": str(row.get("name", "")).strip(),
                "kualitas": "produsen",
                "hargaPerKg": harga,
                "catatan": (
                    "Harga indikatif tingkat produsen dari PIHPS Bank Indonesia "
                    "(sumber resmi, bukan transaksi pasar/kios). Dipublikasi harian."
                ),
            })
        time.sleep(1)  # jaga-jaga rate limit BI
    return records


def merge_into_report(records: list[dict], report_path: Path) -> bool:
    """Gabungkan ke harga-panen-report.json TANPA menimpa record acuan HPP."""
    if not records:
        return False
    data = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    existing = data.get("records", [])
    seen = {
        (r.get("tanggal"), r.get("komoditas"), r.get("lokasi"))
        for r in existing
    }
    added = 0
    for r in records:
        key = (r["tanggal"], r["komoditas"], r["lokasi"])
        if key not in seen:
            existing.append(r)
            seen.add(key)
            added += 1
    if not added:
        print("PIHPS: tidak ada record baru.")
        return False
    data["records"] = existing
    data["generatedAt"] = datetime.now(JAKARTA).isoformat()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PIHPS: +{added} record laporan panen -> {report_path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="YYYY-MM-DD (default: hari ini, waktu Jakarta)")
    ap.add_argument("--root", default=".", help="root proyek")
    args = ap.parse_args()

    target = args.date or datetime.now(JAKARTA).date().isoformat()
    # PIHPS kadang telat publikasi: coba H-1 kalau hari ini kosong
    fallback = (date.fromisoformat(target) - timedelta(days=1)).isoformat()

    records = collect(target)
    if not records:
        print("PIHPS: data kosong, coba H-1...")
        records = collect(fallback)
    if not records:
        print("PIHPS: tetap kosong, dilewati (fail-soft).")
        return 0

    report = Path(args.root) / "data" / "harga-panen-report.json"
    merge_into_report(records, report)
    return 0  # selalu sukses: bagian panen tidak boleh mematikan workflow


if __name__ == "__main__":
    raise SystemExit(main())
