import copy
import json
import unittest

from scripts.render_report import ROOT, render


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/report.json").read_text())

    def test_external_content_is_escaped(self):
        self.data["title"] = '<script>alert("x")</script>'
        self.data["risks"][0]["text"] = '<img src=x onerror=alert(1)>'
        html = render(self.data)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)

    def test_active_source_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "data:text/html,test", "https://user:pass@example.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                render(dict(self.data, source_url=url))

    def test_invalid_scores_are_rejected(self):
        for score, maximum in ((-1, 20), (21, 20), (1, 0), (float('nan'), 20)):
            data = copy.deepcopy(self.data)
            data["scores"][0].update(value=score, max=maximum)
            with self.subTest(score=score), self.assertRaises(ValueError):
                render(data)


if __name__ == "__main__":
    unittest.main()
