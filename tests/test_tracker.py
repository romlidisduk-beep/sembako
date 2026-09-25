import csv
import io
import os
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import track_prices


class TrackerTests(unittest.TestCase):
    def test_extract_price_from_html(self):
        html = "<div>Beras Medium / kg</div><strong>Rp12.500</strong>"
        self.assertEqual(track_prices.extract_price(track_prices.clean_html(html), "Beras Medium / kg"), 12500)

    def test_extract_price_accepts_rupiah_abbreviation_with_period(self):
        html = "<div>Beras Medium / kg</div><strong>Rp. 12.500</strong>"
        self.assertEqual(track_prices.extract_price(track_prices.clean_html(html), "Beras Medium / kg"), 12500)

    def test_extract_missing_price(self):
        self.assertIsNone(track_prices.extract_price("Beras Medium / kg belum tersedia", "Beras Medium / kg"))

    def test_extract_price_does_not_steal_next_product_price(self):
        page = track_prices.clean_html(
            "<div>Beras Medium / kg</div><div>Belum tersedia</div>"
            "<div>Gula Kristal Putih / kg</div><div>Rp17.500</div>"
        )
        self.assertIsNone(track_prices.extract_price(page, "Beras Medium / kg"))

    def test_merge_history_replaces_same_market_day(self):
        old = [
            {
                "date": "2026-09-21",
                "area": "gresik",
                "marketId": "45",
                "location": "Pasar Baru",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "commodity": "Gula",
                "unit": "kg",
                "price": 17000,
                "address": "",
                "sourceUrl": "",
            }
        ]
        new = [dict(old[0], price=17500)]
        result = track_prices.merge_history(old, new)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["price"], 17500)

    def test_trend_warning_after_rising_days(self):
        history = []
        for date, price in [
            ("2026-09-18", 60000),
            ("2026-09-19", 61000),
            ("2026-09-20", 62000),
        ]:
            history.append(
                {
                    "date": date,
                    "area": "gresik",
                    "marketId": "45",
                    "location": "Pasar Baru",
                    "sourceType": "pasar rakyat",
                    "commodityKey": "cabai-rawit",
                    "commodity": "Cabai rawit merah",
                    "unit": "kg",
                    "price": price,
                    "address": "",
                    "sourceUrl": "",
                }
            )
        current = [dict(history[-1], date="2026-09-21", price=63000)]
        signal = track_prices.trend_signal(
            history,
            "2026-09-21",
            "gresik",
            track_prices.COMMODITY_BY_KEY["cabai-rawit"],
            current,
        )
        self.assertEqual(signal["signal"], "WASPADA NAIK")

    def test_csv_round_trip(self):
        record = {
            "date": "2026-09-21",
            "area": "lamongan",
            "marketId": "retail:1",
            "location": "Koperasi",
            "sourceType": "koperasi",
            "commodityKey": "gula",
            "commodity": "Gula kristal putih",
            "brand": "Gulaku",
            "productName": "Gula Premium",
            "size": "1 kg",
            "unit": "kg",
            "price": 17000,
            "priceType": "promo",
            "stockStatus": "tersedia",
            "confidence": "input-manual",
            "observedAt": "2026-09-21 08:00",
            "address": "Jalan A, Lamongan",
            "sourceUrl": "https://example.com",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            track_prices.write_csv_records(path, [record])
            self.assertEqual(track_prices.read_csv_records(path)[0], record)

    def test_telegram_messages_are_sorted_and_include_brand_location(self):
        records = [
            {
                "area": "gresik",
                "commodity": "Gula",
                "productName": "Gula Premium",
                "brand": "Gulaku",
                "price": 17000,
                "unit": "kg",
                "location": "Koperasi Contoh",
                "sourceType": "koperasi",
                "address": "Jalan A, Gresik",
            },
            {
                "area": "lamongan",
                "commodity": "Beras",
                "productName": "Beras Medium",
                "brand": "Merk Hemat",
                "price": 12500,
                "unit": "kg",
                "location": "Toko Contoh",
                "sourceType": "toko",
                "address": "Jalan B, Lamongan",
            },
        ]

        message = track_prices.build_telegram_messages(records, "2026-09-21")[0]

        self.assertLess(message.index("Beras Medium"), message.index("Gula Premium"))
        self.assertIn("Merk Hemat", message)
        self.assertIn("Toko Contoh (toko)", message)

    def test_daily_notifications_are_separated_by_type(self):
        records = [
            {
                "area": "gresik",
                "marketId": "45",
                "location": "Pasar Baru",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "commodity": "Gula kristal putih",
                "productName": "Gula kristal putih",
                "brand": "Komoditas pasar",
                "size": "1 kg",
                "unit": "kg",
                "price": 17000,
            }
        ]
        trends = [
            {
                "area": "gresik",
                "commodity": "Gula kristal putih",
                "unit": "kg",
                "latestPrice": 17500,
                "changePercent": 3.2,
                "signal": "WASPADA NAIK",
                "reason": "Harga naik.",
            }
        ]
        national = {
            "panelBapanas": "6500",
            "pihps": "7000",
            "bpsGresik": "rilis",
            "bpsLamongan": "rilis",
            "hppKdmp": 6500,
            "pengepulManual": "",
        }
        messages = track_prices.build_notification_messages(
            records,
            "2026-09-25",
            trends=trends,
            national=national,
            limit=1,
        )
        self.assertGreaterEqual(len(messages), 4)
        self.assertTrue(messages[0].startswith("🌾 UPDATE HARGA SEMBAKO"))
        self.assertTrue(any("🛒 HARGA SEMBAKO TERMURAH" in message for message in messages))
        self.assertTrue(any("⚠️ WASPADA KENAIKAN HARGA" in message for message in messages))
        self.assertTrue(any("🌾 REFERENSI NASIONAL & PRODUSEN" in message for message in messages))

    def test_package_price_is_normalized_for_comparison(self):
        record = {
            "price": 62500,
            "size": "5 kg",
            "unit": "kg",
        }
        self.assertEqual(track_prices.comparison_price(record), 12500)
        self.assertIn("Rp62.500/5 kg", track_prices.price_description(record))
        self.assertIn("Rp12.500/kg", track_prices.price_description(record))

    def test_missing_current_data_does_not_become_fake_cheap_signal(self):
        history = [
            {
                "date": "2026-09-18",
                "area": "gresik",
                "marketId": "45",
                "location": "Pasar Baru",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "price": 17000,
            },
            {
                "date": "2026-09-19",
                "area": "gresik",
                "marketId": "45",
                "location": "Pasar Baru",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "price": 17100,
            },
        ]
        signal = track_prices.trend_signal(
            history,
            "2026-09-20",
            "gresik",
            track_prices.COMMODITY_BY_KEY["gula"],
            [],
        )
        self.assertEqual(signal["signal"], "TIDAK ADA DATA")
        self.assertIsNone(signal["latestPrice"])

    def test_trend_does_not_call_non_consecutive_dates_consecutive(self):
        history = [
            {
                "date": date,
                "area": "gresik",
                "marketId": "45",
                "location": "Pasar Baru",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "price": price,
            }
            for date, price in [
                ("2026-09-18", 17000),
                ("2026-09-20", 17100),
                ("2026-09-21", 17200),
            ]
        ]
        signal = track_prices.trend_signal(
            history,
            "2026-09-22",
            "gresik",
            track_prices.COMMODITY_BY_KEY["gula"],
            [dict(history[-1], date="2026-09-22", price=17300)],
        )
        self.assertEqual(signal["signal"], "NORMAL")

    def test_invalid_retail_rows_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_text(
                "date,area,marketId,location,sourceType,commodityKey,price\n"
                "2026-09-21,gresik,retail:valid,Toko Valid,toko,gula,17000\n"
                "21-09-2026,gresik,retail:bad,Toko Bad,toko,gula,17000\n"
                "2026-09-21,gresik,retail:bad,Toko Bad,toko,not-a-commodity,17000\n"
                "2026-09-21,gresik,retail:bad,Toko Bad,toko,gula,-1\n",
                encoding="utf-8",
            )
            records = track_prices.read_csv_records(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["location"], "Toko Valid")

    def test_extract_rupiah_figures(self):
        text = "Harga GKP Rp 6.500 per kg, harga GKG Rp7.200/kg"
        self.assertEqual(track_prices.extract_rupiah_figures(text), ["6.500", "7.200"])

    def test_extract_rupiah_figures_empty_when_none_found(self):
        self.assertEqual(track_prices.extract_rupiah_figures("Data belum tersedia"), [])

    def test_extract_bps_press_release_title_indonesian(self):
        html = (
            "<h1>Nilai Tukar Petani (NTP) Provinsi Jawa Timur bulan April 2024 "
            "sebesar 107,58 atau turun 5,81 persen</h1>"
        )
        title = track_prices.extract_bps_press_release_title(html)
        self.assertIsNotNone(title)
        self.assertTrue(title.startswith("Nilai Tukar Petani"))

    def test_extract_bps_press_release_title_english(self):
        html = "<h1>Farmer Exchange Rate for Jawa Timur Province in April 2024</h1>"
        title = track_prices.extract_bps_press_release_title(html)
        self.assertIsNotNone(title)
        self.assertTrue(title.startswith("Farmer Exchange Rate"))

    def test_extract_bps_press_release_title_missing(self):
        self.assertIsNone(track_prices.extract_bps_press_release_title("<h1>Halaman tidak ditemukan</h1>"))

    def test_whatsapp_messages_are_shorter_than_telegram(self):
        records = [
            {
                "date": "2026-09-25",
                "area": "gresik",
                "marketId": "1",
                "location": f"Pasar {i}",
                "sourceType": "pasar rakyat",
                "commodityKey": "gula",
                "commodity": "Gula",
                "brand": "Komoditas pasar",
                "productName": "Gula",
                "unit": "kg",
                "price": 17000 + i,
                "address": "",
            }
            for i in range(30)
        ]
        wa_messages = track_prices.build_whatsapp_messages(records, "2026-09-25", limit=30)
        for message in wa_messages:
            self.assertLessEqual(len(message), track_prices.WHATSAPP_MAX_MESSAGE_LENGTH + 200)
        # Pesan WhatsApp harus lebih banyak/pendek daripada kalau dipaksa satu
        # pesan panjang seperti Telegram, karena batas panjangnya jauh lebih kecil.
        telegram_messages = track_prices.build_telegram_messages(records, "2026-09-25", limit=30)
        self.assertGreaterEqual(len(wa_messages), len(telegram_messages))

    def test_message_builder_splits_an_unusually_long_line(self):
        records = [
            {
                "area": "gresik",
                "commodity": "Gula",
                "productName": "Gula",
                "brand": "Komoditas pasar",
                "price": 17000,
                "unit": "kg",
                "location": "Pasar " + ("X" * 500),
                "sourceType": "pasar rakyat",
                "address": "",
            }
        ]
        messages = track_prices.build_telegram_messages(
            records, "2026-09-25", limit=1, max_length=120
        )
        self.assertGreater(len(messages), 1)
        self.assertTrue(all(len(message) <= 120 for message in messages))

    def test_message_builder_respects_small_limit_for_header(self):
        messages = track_prices.build_telegram_messages(
            [], "2026-09-25", max_length=20
        )
        self.assertTrue(messages)
        self.assertTrue(all(len(message) <= 20 for message in messages))

    def test_parse_whatsapp_recipients_supports_multiple_formats(self):
        recipients = track_prices.parse_whatsapp_recipients(
            " +6281234567890 = key-one\n6289876543210:key-two"
        )
        self.assertEqual(
            recipients,
            [("6281234567890", "key-one"), ("6289876543210", "key-two")],
        )

        with patch.dict(
            os.environ,
            {"WHATSAPP_PHONE": "+6281234567890,6289876543210", "WHATSAPP_APIKEY": "same-key"},
            clear=False,
        ):
            self.assertEqual(
                track_prices.parse_whatsapp_recipients(),
                [("6281234567890", "same-key"), ("6289876543210", "same-key")],
            )

    def test_whatsapp_sends_to_all_recipients(self):
        calls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"Message queued"

        def fake_urlopen(request, timeout=30):
            del timeout
            query = parse_qs(urlparse(request.full_url).query)
            calls.append(query["phone"][0])
            return FakeResponse()

        with patch.dict(
            os.environ,
            {
                "WHATSAPP_RECIPIENTS": (
                    "6281234567890=key-one\n6289876543210=key-two"
                )
            },
            clear=False,
        ), patch.object(track_prices, "urlopen", side_effect=fake_urlopen), patch.object(
            track_prices.time, "sleep"
        ):
            sent = track_prices.send_whatsapp_messages(["pesan 1", "pesan 2"])

        self.assertEqual(sent, 4)
        self.assertEqual(
            calls,
            [
                "6281234567890",
                "6281234567890",
                "6289876543210",
                "6289876543210",
            ],
        )

    def test_whatsapp_continues_when_one_recipient_fails(self):
        calls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"Message queued"

        def fake_urlopen(request, timeout=30):
            del timeout
            phone = parse_qs(urlparse(request.full_url).query)["phone"][0]
            calls.append(phone)
            if phone == "6281234567890":
                raise HTTPError(
                    request.full_url,
                    400,
                    "bad request",
                    hdrs=None,
                    fp=io.BytesIO(b"invalid api key"),
                )
            return FakeResponse()

        with patch.dict(
            os.environ,
            {
                "WHATSAPP_RECIPIENTS": (
                    "6281234567890=bad-key\n6289876543210=good-key"
                )
            },
            clear=False,
        ), patch.object(track_prices, "urlopen", side_effect=fake_urlopen), patch.object(
            track_prices.time, "sleep"
        ):
            with self.assertRaisesRegex(RuntimeError, "1 dari 2"):
                track_prices.send_whatsapp_messages(["pesan"])

        self.assertEqual(calls, ["6281234567890", "6289876543210"])

    def test_national_reference_history_appends_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "national-reference-history.csv"
            entry1 = {
                "date": "2026-09-25",
                "panelBapanas": "6500,7200",
                "pihps": "12000",
                "bpsGresik": "(belum waktunya cek - rilis BPS bulanan)",
                "bpsLamongan": "(belum waktunya cek - rilis BPS bulanan)",
                "hppKdmp": 6500,
                "pengepulManual": "",
            }
            track_prices.append_national_reference_history(path, entry1)
            entry2 = dict(entry1, date="2026-09-26", pengepulManual="7100")
            track_prices.append_national_reference_history(path, entry2)
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["date"], "2026-09-26")
        self.assertEqual(rows[1]["pengepulManual"], "7100")


if __name__ == "__main__":
    unittest.main()