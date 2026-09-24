#!/usr/bin/env python3
"""Pencatatan harga komoditas pertanian Gresik-Lamongan.

Modul ini melengkapi pelacak harga sembako utama dengan pencatatan manual
berdasarkan kualitas komoditas. Data disimpan sebagai CSV lokal dan tidak
dicampur ke laporan SISKAPERBAPO karena skema serta satuan kualitasnya berbeda.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
DEFAULT_FILE = ROOT / "data" / "harga_gresik_lamongan.csv"
ADMINISTRATIVE_FILE = ROOT / "data" / "administrative-areas.json"
FIELDS = [
    "Tanggal",
    "Kabupaten",
    "Kecamatan",
    "Desa_Kelurahan",
    "Kode_Desa",
    "Lokasi",
    "Komoditas",
    "Kualitas",
    "Harga_per_Kg",
    "Catatan",
]
LEGACY_FIELDS = ["Tanggal", "Lokasi", "Komoditas", "Kualitas", "Harga_per_Kg", "Catatan"]

KUALITAS: dict[str, list[str]] = {
    "GABAH": [
        "GKP Panen (KA 25%)",
        "GKP Penggilingan",
        "GKG (KA 14%)",
        "Gabah Basah",
    ],
    "JAGUNG": [
        "Jagung Basah KA 30%",
        "Jagung Kering KA 15% Pipilan",
        "Jagung Super Kering KA 14%",
    ],
    "BIJI KANGKUNG": ["Bangkok LP-1", "Seriti", "Bika", "Curah Lokal"],
}

def load_administrative_areas(
    path: Path = ADMINISTRATIVE_FILE,
) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        areas = payload["kabupaten"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Daftar wilayah tidak dapat dibaca dari {path}."
        ) from error
    if not isinstance(areas, list) or not areas:
        raise RuntimeError("Daftar kabupaten tidak boleh kosong.")
    return areas


ADMINISTRATIVE_AREAS = load_administrative_areas()


def kabupaten_label(area: dict[str, object]) -> str:
    return str(area["slug"]).capitalize()


def kecamatan_records(area: dict[str, object]) -> list[dict[str, object]]:
    return list(area.get("kecamatan", []))


def desa_records(kecamatan: dict[str, object]) -> list[dict[str, object]]:
    return list(kecamatan.get("desa_kelurahan", []))


def find_location(
    kabupaten: str,
    kecamatan: str,
    desa_kelurahan: str,
    kode_desa: str | int | None = None,
) -> tuple[str, str, str, str]:
    requested_kabupaten = re.sub(
        r"^kabupaten\s+",
        "",
        kabupaten.strip(),
        flags=re.IGNORECASE,
    )
    for area in ADMINISTRATIVE_AREAS:
        area_name = kabupaten_label(area)
        if area_name != requested_kabupaten:
            continue
        for district in kecamatan_records(area):
            if str(district["nama"]) != kecamatan:
                continue
            for village in desa_records(district):
                if (
                    str(village["nama"]) == desa_kelurahan
                    and (kode_desa is None or str(village["kode"]) == str(kode_desa))
                ):
                    return (
                        area_name,
                        str(district["nama"]),
                        str(village["nama"]),
                        str(village["kode"]),
                    )
    raise ValueError(
        "Kombinasi kabupaten, kecamatan, dan desa/kelurahan tidak ditemukan."
    )


def legacy_location_parts(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in value.split(" - ", 1)]
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]


def today_jakarta() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")


def resolve_file(value: str | None) -> Path:
    if not value:
        return DEFAULT_FILE
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def parse_price(value: str) -> int:
    """Parse a whole-rupiah price such as ``7850`` or ``Rp7.850``."""
    text = re.sub(r"\s+", "", str(value).strip().lower())
    if text.startswith("rp"):
        text = text[2:]
    if not text or not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+)", text):
        raise ValueError("Harga harus berupa angka rupiah bulat, misalnya 7850 atau Rp7.850.")
    price = int(text.replace(".", ""))
    if price <= 0:
        raise ValueError("Harga harus lebih besar dari nol.")
    return price


def init_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(FIELDS)
        return

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        fieldnames = next(csv.reader(handle), [])
    if fieldnames != LEGACY_FIELDS:
        return

    # Migrate the original six-column file before appending detailed rows.
    legacy_records = read_records(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(legacy_records)


def read_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        is_legacy = fieldnames == LEGACY_FIELDS
        if not is_legacy and any(field not in fieldnames for field in FIELDS):
            return []
        records: list[dict[str, str]] = []
        for row in reader:
            if not row:
                continue
            if is_legacy:
                lokasi = (row.get("Lokasi") or "").strip()
                kabupaten, kecamatan = legacy_location_parts(lokasi)
                normalized = {
                    "Tanggal": (row.get("Tanggal") or "").strip(),
                    "Kabupaten": kabupaten,
                    "Kecamatan": kecamatan,
                    "Desa_Kelurahan": "",
                    "Kode_Desa": "",
                    "Lokasi": lokasi,
                    "Komoditas": (row.get("Komoditas") or "").strip(),
                    "Kualitas": (row.get("Kualitas") or "").strip(),
                    "Harga_per_Kg": (row.get("Harga_per_Kg") or "").strip(),
                    "Catatan": (row.get("Catatan") or "").strip(),
                }
            else:
                normalized = {field: (row.get(field) or "").strip() for field in FIELDS}
            try:
                parse_price(normalized["Harga_per_Kg"])
                datetime.strptime(normalized["Tanggal"], "%Y-%m-%d")
            except ValueError:
                continue
            if (
                normalized["Komoditas"] not in KUALITAS
                or normalized["Kualitas"] not in KUALITAS[normalized["Komoditas"]]
            ):
                continue
            if is_legacy:
                if not normalized["Kabupaten"] or not normalized["Kecamatan"]:
                    continue
            elif not normalized["Kode_Desa"] and not normalized["Desa_Kelurahan"]:
                # Preserve rows migrated from the original six-column CSV.
                if not normalized["Kabupaten"] or not normalized["Kecamatan"]:
                    continue
            else:
                try:
                    (
                        normalized["Kabupaten"],
                        normalized["Kecamatan"],
                        normalized["Desa_Kelurahan"],
                        normalized["Kode_Desa"],
                    ) = find_location(
                        normalized["Kabupaten"],
                        normalized["Kecamatan"],
                        normalized["Desa_Kelurahan"],
                        normalized["Kode_Desa"],
                    )
                except ValueError:
                    continue
            records.append(normalized)
        return records


def append_record(
    path: Path,
    *,
    kabupaten: str,
    kecamatan: str,
    desa_kelurahan: str,
    komoditas: str,
    kualitas: str,
    harga_per_kg: int | str,
    catatan: str = "",
    tanggal: str | None = None,
    kode_desa: str | int | None = None,
) -> dict[str, str]:
    if komoditas not in KUALITAS:
        raise ValueError(f"Komoditas tidak dikenal: {komoditas}")
    if kualitas not in KUALITAS[komoditas]:
        raise ValueError(f"Kualitas tidak sesuai untuk {komoditas}: {kualitas}")
    (
        kabupaten,
        kecamatan,
        desa_kelurahan,
        kode_desa,
    ) = find_location(kabupaten, kecamatan, desa_kelurahan, kode_desa)
    observed_date = tanggal or today_jakarta()
    try:
        datetime.strptime(observed_date, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError("Tanggal harus berformat YYYY-MM-DD.") from error

    record = {
        "Tanggal": observed_date,
        "Kabupaten": kabupaten,
        "Kecamatan": kecamatan,
        "Desa_Kelurahan": desa_kelurahan,
        "Kode_Desa": str(kode_desa),
        "Lokasi": f"{kabupaten} - {kecamatan} - {desa_kelurahan}",
        "Komoditas": komoditas,
        "Kualitas": kualitas,
        "Harga_per_Kg": str(parse_price(str(harga_per_kg))),
        "Catatan": str(catatan).strip(),
    }
    init_file(path)
    with path.open("a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS).writerow(record)
    return record


def choose(
    title: str,
    options: list[str],
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> str:
    while True:
        output_fn(f"\n{title}")
        for index, option in enumerate(options, 1):
            output_fn(f"{index}. {option}")
        raw = input_fn(f"Pilih [1-{len(options)}]: ").strip()
        try:
            index = int(raw) - 1
            if 0 <= index < len(options):
                return options[index]
        except ValueError:
            pass
        output_fn("Pilihan tidak valid. Masukkan nomor yang tersedia.")


def choose_item(
    title: str,
    items: list[dict[str, object]],
    label: Callable[[dict[str, object]], str],
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> dict[str, object]:
    while True:
        output_fn(f"\n{title}")
        for index, item in enumerate(items, 1):
            output_fn(f"{index}. {label(item)}")
        raw = input_fn(f"Pilih [1-{len(items)}]: ").strip()
        try:
            index = int(raw) - 1
            if 0 <= index < len(items):
                return items[index]
        except ValueError:
            pass
        output_fn("Pilihan tidak valid. Masukkan nomor yang tersedia.")


def tambah_harga(
    path: Path,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> dict[str, str]:
    area = choose_item(
        "Kabupaten",
        ADMINISTRATIVE_AREAS,
        lambda item: str(item["nama"]),
        input_fn,
        output_fn,
    )
    district = choose_item(
        f"Kecamatan di {area['nama']}",
        kecamatan_records(area),
        lambda item: str(item["nama"]),
        input_fn,
        output_fn,
    )
    village = choose_item(
        f"Desa/Kelurahan di {district['nama']}",
        desa_records(district),
        lambda item: f"{item['nama']} [{item['jenis']}]",
        input_fn,
        output_fn,
    )
    komoditas = choose("Komoditas", list(KUALITAS), input_fn, output_fn)
    kualitas = choose(f"Kualitas {komoditas}", KUALITAS[komoditas], input_fn, output_fn)

    while True:
        try:
            harga = parse_price(input_fn(f"Harga {komoditas} {kualitas} per Kg: "))
            break
        except ValueError as error:
            output_fn(str(error))
    catatan = input_fn("Catatan (opsional): ").strip()
    record = append_record(
        path,
        kabupaten=kabupaten_label(area),
        kecamatan=str(district["nama"]),
        desa_kelurahan=str(village["nama"]),
        kode_desa=str(village["kode"]),
        komoditas=komoditas,
        kualitas=kualitas,
        harga_per_kg=harga,
        catatan=catatan,
    )
    output_fn(">> Berhasil disimpan!")
    return record


def rupiah(value: int) -> str:
    return f"Rp{value:,}".replace(",", ".")


def lihat_harga(path: Path, output_fn: Callable[[str], None] = print) -> None:
    records = read_records(path)
    if not records:
        output_fn("Belum ada data.")
        return
    output_fn("\n=== DATA HARGA GRESIK-LAMONGAN ===")
    output_fn(
        "Tanggal | Kabupaten | Kecamatan | Desa/Kelurahan | "
        "Komoditas | Kualitas | Harga/kg | Catatan"
    )
    for record in records:
        output_fn(
            " | ".join(
                [
                    record["Tanggal"],
                    record["Kabupaten"],
                    record["Kecamatan"],
                    record["Desa_Kelurahan"] or record["Lokasi"],
                    record["Komoditas"],
                    record["Kualitas"],
                    rupiah(int(record["Harga_per_Kg"])),
                    record["Catatan"],
                ]
            )
        )


def ringkasan(path: Path, output_fn: Callable[[str], None] = print) -> None:
    records = read_records(path)
    if not records:
        output_fn("Belum ada data.")
        return

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[(record["Komoditas"], record["Kualitas"])].append(record)

    output_fn("\n=== RINGKASAN HARGA TERBARU ===")
    for (komoditas, kualitas), group in grouped.items():
        latest_date = max(record["Tanggal"] for record in group)
        latest = next(
            record
            for record in reversed(group)
            if record["Tanggal"] == latest_date
        )
        prices = [int(record["Harga_per_Kg"]) for record in group]
        average = sum(prices) // len(prices)
        output_fn(
            f"{komoditas} - {kualitas}: "
            f"{rupiah(int(latest['Harga_per_Kg']))}/kg "
            f"(terakhir {latest['Tanggal']}, {latest['Lokasi']}; "
            f"rata-rata {rupiah(average)}/kg, {len(prices)} catatan)"
        )


def menu(
    path: Path,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    init_file(path)
    while True:
        output_fn("\n1. Tambah Harga  2. Lihat Semua  3. Ringkasan  4. Keluar")
        pilihan = input_fn("Pilih: ").strip()
        if pilihan == "1":
            tambah_harga(path, input_fn, output_fn)
        elif pilihan == "2":
            lihat_harga(path, output_fn)
        elif pilihan == "3":
            ringkasan(path, output_fn)
        elif pilihan == "4":
            output_fn("Selesai.")
            return
        else:
            output_fn("Pilihan tidak valid. Gunakan 1, 2, 3, atau 4.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pencatatan harga gabah, jagung, dan biji kangkung."
    )
    parser.add_argument(
        "--file",
        default=str(DEFAULT_FILE),
        help="Lokasi CSV penyimpanan data.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("menu", "tambah", "lihat", "ringkasan"),
        default="menu",
        help="Aksi yang dijalankan; default membuka menu interaktif.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    path = resolve_file(args.file)
    if args.command == "menu":
        menu(path)
    elif args.command == "tambah":
        tambah_harga(path)
    elif args.command == "lihat":
        lihat_harga(path)
    elif args.command == "ringkasan":
        ringkasan(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())