"""Uji cache cadangan: baris riwayat valid dibaca, tanggal terakhir dikenali."""
from __future__ import annotations

import csv
from pathlib import Path

import track_prices

FIELDS = ["date", "area", "marketId", "location", "sourceType", "commodityKey",
          "commodity", "brand", "productName", "size", "unit", "price",
          "priceType", "stockStatus", "confidence", "observedAt", "address", "sourceUrl"]


def test_riwayat_dibaca_dan_tanggal_terakhir_dikenali(tmp_path: Path) -> None:
    history = tmp_path / "price-history.csv"
    with history.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({
            "date": "2026-09-30", "area": "gresik", "marketId": "45",
            "location": "Pasar Baru", "sourceType": "toko",
            "commodityKey": "beras-premium", "commodity": "Beras premium",
            "brand": "", "productName": "Beras premium", "size": "5 kg",
            "unit": "kg", "price": "15000", "priceType": "normal",
            "stockStatus": "tersedia", "confidence": "Tinggi",
            "observedAt": "2026-09-30 07:00", "address": "", "sourceUrl": "",
        })
    rows = track_prices.read_csv_records(history)
    assert rows, "riwayat valid harus terbaca"
    last_date = max(row["date"] for row in rows if row.get("date"))
    assert last_date == "2026-09-30"
