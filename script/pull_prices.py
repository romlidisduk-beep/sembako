#!/usr/bin/env python3
"""Collect official producer prices and publish a browser-readable snapshot.

The Panel Harga endpoint has changed shape in the past and can temporarily
return an HTML maintenance page. This script treats both cases as normal
failures, keeps the last successful snapshot, and never deletes local field
records.

Run from the repository root:
    python script/pull_prices.py
"""

from __future__ import annotations

import csv
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OFFICIAL_CSV = DATA_DIR / "harga_resmi.csv"
OFFICIAL_JSON = DATA_DIR / "official-prices.json"

ENDPOINTS = [
    "https://panelharga.badanpangan.go.id/api/harga/harian-provinsi?provinsi_id=11",
    "https://panelharga.badanpangan.go.id/api/harga/pasar-modern?provinsi_id=11",
]

SOURCE_CATALOG = [
    {
        "name": "Panel Harga Badan Pangan",
        "url": "https://panelharga.badanpangan.go.id",
        "role": "Harga gabah dan beras tingkat petani",
    },
    {
        "name": "SISKAPERBAPO Jawa Timur",
        "url": "https://siskaperbapo.indagjatim.com/display/show",
        "role": "Harga konsumen dan pasar Jawa Timur",
    },
    {
        "name": "PIHPS Nasional · Bank Indonesia",
        "url": "https://www.bi.go.id/hargapangan",
        "role": "Harga rata-rata dan perubahan antar daerah",
    },
]

OFFICIAL_HEADER = ["Tgl", "Sumber", "Komoditas", "Harga", "Satuan"]
COMMODITY_KEYWORDS = ("gabah", "jagung", "beras")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not OFFICIAL_CSV.exists():
        with OFFICIAL_CSV.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(OFFICIAL_HEADER)


def parse_number(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(value)
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def first_value(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def extract_items(value: Any) -> list[dict[str, Any]]:
    """Find record-like dictionaries in several common API envelopes."""
    if isinstance(value, list):
        records: list[dict[str, Any]] = []
        for child in value:
            records.extend(extract_items(child))
        return records
    if not isinstance(value, dict):
        return []

    record_keys = {
        "name",
        "komoditas",
        "commodity",
        "harga",
        "rata_rata",
        "price",
    }
    if record_keys.intersection(value):
        return [value]

    records = []
    for child in value.values():
        records.extend(extract_items(child))
    return records


def normalise_record(item: dict[str, Any], fetched_at: str) -> dict[str, Any] | None:
    name = first_value(item, ("name", "komoditas", "commodity", "nama_komoditas"))
    if not name:
        return None

    commodity = str(name).strip()
    if not any(keyword in commodity.lower() for keyword in COMMODITY_KEYWORDS):
        return None

    price = parse_number(first_value(item, ("harga", "rata_rata", "price", "harga_rata_rata")))
    if price is None or price <= 0:
        return None

    raw_date = first_value(item, ("tanggal", "tgl", "date", "tanggal_update"))
    return {
        "tanggal": str(raw_date or fetched_at[:10]),
        "sumber": "Panel Harga Badan Pangan",
        "komoditas": commodity,
        "harga": price,
        "satuan": str(first_value(item, ("satuan", "unit")) or "kg"),
        "level": "petani",
        "wilayah": "Jawa Timur",
    }


def fetch_endpoint(url: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PelacakHarga/1.0 (+local-price-dashboard)",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        body = response.read().decode("utf-8", errors="replace")
        if "json" not in content_type:
            raise ValueError(f"respons bukan JSON ({content_type or 'content-type kosong'})")
        payload = json.loads(body)
    return extract_items(payload)


def read_existing_snapshot() -> dict[str, Any]:
    if not OFFICIAL_JSON.exists():
        return {}
    try:
        with OFFICIAL_JSON.open(encoding="utf-8") as file:
            payload = json.load(file)
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_snapshot(payload: dict[str, Any]) -> None:
    temporary = OFFICIAL_JSON.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temporary.replace(OFFICIAL_JSON)


def append_csv_records(records: list[dict[str, Any]]) -> None:
    existing: set[tuple[str, str, str, str]] = set()
    if OFFICIAL_CSV.exists():
        with OFFICIAL_CSV.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                existing.add((row["Tgl"], row["Komoditas"], row["Harga"], row["Satuan"]))

    with OFFICIAL_CSV.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for record in records:
            key = (
                record["tanggal"],
                record["komoditas"],
                str(record["harga"]),
                record["satuan"],
            )
            if key in existing:
                continue
            writer.writerow(
                [
                    record["tanggal"],
                    record["sumber"],
                    record["komoditas"],
                    record["harga"],
                    record["satuan"],
                ]
            )
            existing.add(key)


def tarik_panel_harga() -> dict[str, Any]:
    fetched_at = now_iso()
    errors: list[str] = []
    records: list[dict[str, Any]] = []

    for url in ENDPOINTS:
        print(f"Mencoba: {url}")
        try:
            for item in fetch_endpoint(url):
                record = normalise_record(item, fetched_at)
                if record:
                    records.append(record)
        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
            urllib.error.URLError,
        ) as error:
            message = f"{url}: {error}"
            errors.append(message)
            print(f"  Lewati: {error}")

    unique_records = list(
        {
            (record["tanggal"], record["komoditas"], record["harga"], record["satuan"]): record
            for record in records
        }.values()
    )

    if unique_records:
        append_csv_records(unique_records)
        snapshot = {
            "version": 1,
            "status": "ok",
            "source": "Panel Harga Badan Pangan",
            "sources": SOURCE_CATALOG,
            "fetchedAt": fetched_at,
            "lastSuccessfulFetch": fetched_at,
            "records": unique_records,
            "errors": errors,
        }
        print(f"Berhasil: {len(unique_records)} harga resmi")
    else:
        previous = read_existing_snapshot()
        snapshot = {
            **previous,
            "version": 1,
            "status": "stale" if previous.get("records") else "unavailable",
            "source": previous.get("source", "Panel Harga Badan Pangan"),
            "sources": previous.get("sources", SOURCE_CATALOG),
            "lastAttemptAt": fetched_at,
            "records": previous.get("records", []),
            "errors": errors or ["Tidak ada record harga yang dikenali dari endpoint."],
        }
        print("Tidak ada data baru. Snapshot terakhir dipertahankan.")

    write_snapshot(snapshot)
    return snapshot


if __name__ == "__main__":
    init_files()
    result = tarik_panel_harga()
    print(f"Snapshot: {result['status']} -> {OFFICIAL_JSON}")