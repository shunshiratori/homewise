import unittest

from scripts.probe_homes import AcquisitionError, extract, validate_url


URL = "https://www.homes.co.jp/mansion/b-1259230001938/"


def overview(rows):
    return "<table>" + "".join(f"<tr><th>{key}</th><td>{value}</td></tr>" for key, value in rows) + "</table>"


class ExtractionTests(unittest.TestCase):
    def test_svg_titles_do_not_pollute_page_title(self):
        result = extract("<title>物件名</title><svg><title>評価</title></svg>" +
                         overview([("価格", "2,000万円"), ("専有面積", "30m²")]), URL)
        self.assertEqual(result["page_title"], "物件名")
        self.assertEqual(result["area_sqm"], 30)

    def test_extracts_overview_instead_of_recommendations_or_loan_estimate(self):
        html = "<p>おすすめ 1,000万円 支払い目安 12万円</p>" + overview([
            ("価格", "<span>3,400</span>万円"), ("専有面積", "40.85㎡"),
            ("管理費等", "14,314円"), ("修繕積立金", "9,234円"),
            ("現況", "賃貸中"), ("その他条件", "オーナーチェンジ"),
        ])
        result = extract(html, URL)
        self.assertEqual(result["price_yen"], 34000000)
        self.assertEqual(result["area_sqm"], 40.85)
        self.assertEqual(result["management_fee_yen"], 14314)
        self.assertEqual(result["repair_reserve_yen"], 9234)
        self.assertTrue(result["flags"])

    def test_unknown_fees_are_not_zero(self):
        result = extract(overview([("価格", "2,000万円"), ("専有面積", "30㎡"),
                                   ("管理費等", "確認中")]), URL)
        self.assertIsNone(result["management_fee_yen"])
        self.assertIsNone(result["repair_reserve_yen"])
        self.assertIn("管理費等", result["missing_fields"])

    def test_block_and_ended_pages_do_not_produce_property(self):
        for html in ("<h1>403 ERROR</h1>", "掲載終了", "<p>おすすめ 3,400万円 40.85㎡</p>"):
            with self.subTest(html=html), self.assertRaises(AcquisitionError):
                extract(html, URL)

    def test_only_homes_detail_urls_are_supported(self):
        for url in ("http://www.homes.co.jp/mansion/b-123/", "https://www.homes.co.jp.evil.test/mansion/b-123/",
                    "https://suumo.jp/", "https://www.homes.co.jp/", "https://user@www.homes.co.jp/mansion/b-123/"):
            with self.subTest(url=url), self.assertRaises(AcquisitionError):
                validate_url(url)


if __name__ == "__main__":
    unittest.main()
