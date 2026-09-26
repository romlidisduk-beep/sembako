import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "script" / "pull_prices.py"
SPEC = importlib.util.spec_from_file_location("pull_prices", MODULE_PATH)
assert SPEC and SPEC.loader
pull_prices = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pull_prices)


class KementanCollectorTests(unittest.TestCase):
    def test_reads_province_average_from_simharga_table(self):
        html = """
        <table>
          <tr><th>Provinsi</th><th>Januari</th><th>Rata-rata</th></tr>
          <tr><td>Jawa Timur</td><td>7.000</td><td>7.250</td></tr>
        </table>
        """

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return html.encode("utf-8")

        with patch.object(pull_prices.urllib.request, "urlopen", return_value=Response()):
            records = pull_prices.fetch_kementan_gabah("2026-09-26T00:00:00+00:00")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sumber"], "SIMHARGA Kementerian Pertanian")
        self.assertEqual(records[0]["wilayah"], "Jawa Timur")
        self.assertEqual(records[0]["harga"], 7250)
        self.assertEqual(records[0]["level"], "petani")
