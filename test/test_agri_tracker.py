import tempfile
import unittest
from pathlib import Path

import harga_gresik_lamongan as tracker


class AgricultureTrackerTests(unittest.TestCase):
    def test_append_record_creates_csv_and_keeps_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            record = tracker.append_record(
                path,
                kabupaten="Gresik",
                kecamatan="Menganti",
                desa_kelurahan="Bringkang",
                komoditas="GABAH",
                kualitas="GKP Panen (KA 25%)",
                harga_per_kg="Rp7.850",
                tanggal="2026-09-24",
            )
            self.assertEqual(record["Harga_per_Kg"], "7850")
            self.assertEqual(tracker.read_records(path), [record])

    def test_invalid_rows_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_text(
                ",".join(tracker.FIELDS)
                + "\n"
                + "2026-09-24,Gresik,Menganti,Bringkang,3525132004,Gresik - Menganti - Bringkang,GABAH,GKP Panen (KA 25%),7850,valid\n"
                + "2026-09-24,Gresik,Menganti,Bringkang,3525132004,Gresik - Menganti - Bringkang,GABAH,Bukan Kualitas,7850,bad\n"
                + "2026-09-24,Gresik,Menganti,Bringkang,3525132004,Gresik - Menganti - Bringkang,GABAH,GKP Panen (KA 25%),0,bad\n",
                encoding="utf-8",
            )
            records = tracker.read_records(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["Catatan"], "valid")

    def test_summary_uses_latest_date_not_last_csv_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_text(
                ",".join(tracker.FIELDS)
                + "\n"
                + "2026-09-24,Gresik,Menganti,Bringkang,3525132004,Gresik - Menganti - Bringkang,GABAH,GKP Panen (KA 25%),8000,baru\n"
                + "2026-09-20,Gresik,Menganti,Bringkang,3525132004,Gresik - Menganti - Bringkang,GABAH,GKP Panen (KA 25%),7000,lama\n",
                encoding="utf-8",
            )
            lines = []
            tracker.ringkasan(path, lines.append)
        self.assertIn("Rp8.000/kg", "\n".join(lines))
        self.assertIn("terakhir 2026-09-24", "\n".join(lines))

    def test_legacy_csv_is_read_and_migrated_without_losing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_text(
                ",".join(tracker.LEGACY_FIELDS)
                + "\n"
                + "2026-09-20,Gresik - Menganti,GABAH,GKP Panen (KA 25%),7000,legacy\n",
                encoding="utf-8",
            )
            tracker.init_file(path)
            records = tracker.read_records(path)
            header = path.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(records[0]["Harga_per_Kg"], "7000")
        self.assertEqual(records[0]["Desa_Kelurahan"], "")
        self.assertEqual(header, ",".join(tracker.FIELDS))

    def test_summary_reports_latest_and_average(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            tracker.append_record(
                path,
                kabupaten="Gresik",
                kecamatan="Menganti",
                desa_kelurahan="Bringkang",
                komoditas="JAGUNG",
                kualitas="Jagung Basah KA 30%",
                harga_per_kg=7000,
                tanggal="2026-09-23",
            )
            tracker.append_record(
                path,
                kabupaten="Lamongan",
                kecamatan="Babat",
                desa_kelurahan="Babat",
                komoditas="JAGUNG",
                kualitas="Jagung Basah KA 30%",
                harga_per_kg=8000,
                tanggal="2026-09-24",
            )
            lines = []
            tracker.ringkasan(path, lines.append)
        self.assertIn("Rp8.000/kg", "\n".join(lines))
        self.assertIn("rata-rata Rp7.500/kg", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()