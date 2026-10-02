#!/usr/bin/env python3
"""Kartu 'Potensi Kenaikan' — analisis momentum harga produsen PIHPS BI.

Mengambil 14 hari harga produsen (Jawa Timur) untuk semua komoditas
sembako, menghitung momentum, lalu menyusun proyeksi konservatif 7 hari.
Hasilnya disimpan ke data/price-outlook.json dan dibaca website.

Dipanggil otomatis oleh workflow (fail-soft: selalu exit 0).
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://www.bi.go.id/hargapangan"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CATEGORIES = {
    "cat_1": "Beras", "cat_2": "Daging Ayam", "cat_3": "Daging Sapi",
    "cat_4": "Telur Ayam", "cat_5": "Bawang Merah", "cat_6": "Bawang Putih",
    "cat_7": "Cabai Merah", "cat_8": "Cabai Rawit",
    "cat_9": "Minyak Goreng", "cat_10": "Gula Pasir",
}
JAKARTA = ZoneInfo("Asia/Jakarta")
LOOKBACK_DAYS = 14


def _session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA), ("X-Requested-With", "XMLHttpRequest")]
    op.open(f"{BASE}/TabelHarga/ProdusenDaerah", timeout=30).read()
    return op


def _grid(op, catid: str, start: str, end: str) -> dict:
    params = urllib.parse.urlencode({
        "price_type_id": "1", "comcat_id": catid, "province_id": "16",
        "regency_id": "", "market_id": "", "tipe_laporan": "1",
        "start_date": start, "end_date": end,
    })
    return json.loads(op.open(
        f"{BASE}/WebSite/TabelHarga/GetGridDataDaerah?{params}", timeout=40).read())


def _num(v):
    try:
        n = float(str(v).replace(",", ""))
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def collect(target: date) -> dict[str, list[tuple[datetime, float]]]:
    """Kumpulkan seri harga per varian produsen selama LOOKBACK_DAYS."""
    start = (target - timedelta(days=LOOKBACK_DAYS)).isoformat()
    end = target.isoformat()
    op = _session()
    series: dict[str, list] = {}
    for catid in CATEGORIES:
        try:
            payload = _grid(op, catid, start, end)
        except Exception as exc:
            print(f"outlook {catid}: gagal ({exc}), lewati")
            continue
        for row in payload.get("data", []):
            if row.get("level") != 2:
                continue
            points = []
            for k, v in row.items():
                if "/2026" not in k and f"/{target.year}" not in k:
                    continue
                try:
                    dt = datetime.strptime(k, "%d/%m/%Y")
                except ValueError:
                    continue
                price = _num(v)
                if price:
                    points.append((dt, price))
            if len(points) >= 3:
                series[row["name"].strip()] = sorted(points, key=lambda x: x[0])
        time.sleep(1)
    return series


def analyze(nama: str, points: list[tuple[datetime, float]]) -> dict | None:
    """Momentum 14 hari -> sinyal + proyeksi 7 hari konservatif (0.5x momentum)."""
    if len(points) < 3:
        return None
    akhir = points[-1][1]
    awal = points[0][1]
    delta14 = (akhir - awal) / awal * 100 if awal else 0.0
    last3 = [p for _, p in points[-3:]]
    naik3 = len(set(last3)) == 3 and last3[0] < last3[1] < last3[2]
    proyeksi = akhir * (1 + delta14 / 100 * 0.5)
    pot_pct = (proyeksi - akhir) / akhir * 100 if akhir else 0.0
    if delta14 >= 1 or naik3:
        sinyal = "WASPADA NAIK"
    elif delta14 > 0:
        sinyal = "PANTAU"
    else:
        sinyal = "STABIL"
    return {
        "komoditas": nama,
        "hargaProdusen": round(akhir),
        "perubahan14HariPct": round(delta14, 2),
        "naikTigaHari": naik3,
        "proyeksi7Hari": round(proyeksi),
        "proyeksiPct": round(pot_pct, 2),
        "sinyal": sinyal,
        "sumber": "BI PIHPS - Harga Produsen Jawa Timur",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="YYYY-MM-DD (default: hari ini Jakarta)")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    target = (date.fromisoformat(args.date) if args.date
              else datetime.now(JAKARTA).date())
    try:
        series = collect(target)
    except Exception as exc:
        print(f"outlook: sesi gagal ({exc}) — dilewati")
        return 0
    if not series:
        print("outlook: tidak ada data — dilewati (fail-soft)")
        return 0

    rows = [r for r in (analyze(n, p) for n, p in series.items()) if r]
    rows.sort(key=lambda r: -r["proyeksiPct"])
    naik = sum(1 for r in rows if r["sinyal"] == "WASPADA NAIK")

    out = {
        "generatedAt": datetime.now(JAKARTA).isoformat(),
        "tanggalAnalisis": target.isoformat(),
        "periode": f"{LOOKBACK_DAYS} hari terakhir",
        "metodologi": (
            "Momentum harga produsen 14 hari (BI PIHPS) diproyeksikan "
            "konservatif 7 hari (setengah kekuatan momentum). Bukan jaminan — "
            "harga konsumen mengikuti dengan jeda 1-2 minggu."
        ),
        "totalDipantau": len(rows),
        "totalWaspadaNaik": naik,
        "items": rows,
    }
    out_path = Path(args.root) / "data" / "price-outlook.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"outlook: {len(rows)} komoditas, {naik} waspada naik -> {out_path}")
    return 0  # selalu sukses


if __name__ == "__main__":
    raise SystemExit(main())
