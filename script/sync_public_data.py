#!/usr/bin/env python3
"""Copy the canonical data snapshots into Vite's generated public directory."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public" / "data"
SNAPSHOTS = (
    "latest-price-report.json",
    "official-prices.json",
    "harga-panen-report.json",
    "price-history.csv",
)


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    missing = [name for name in SNAPSHOTS if not (SOURCE_DIR / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Snapshot data tidak ditemukan di data/: {joined}")
    for name in SNAPSHOTS:
        copyfile(SOURCE_DIR / name, PUBLIC_DIR / name)


if __name__ == "__main__":
    main()