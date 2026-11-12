# -*- coding: utf-8 -*-
"""crawler.py 的离线单元测试（不联网，用 mock 替身验证解析与异常处理）。"""

import csv
import io
import os
import unittest
from unittest import mock

import requests as real_requests

import crawler

SAMPLE = """<html><body>
<div class="quote">
  <span class="text">“To be or not to be.”</span>
  <span>by <small class="author">Author One</small>
        <a href="/author/Author-One">(about)</a></span>
  <div class="tags">Tags: <a class="tag" href="/tag/x">x</a>
        <a class="tag" href="/tag/y">y</a></div>
</div>
<div class="quote">
  <span class="text"></span>
  <span>by <small class="author">Nobody</small></span>
  <div class="tags"></div>
</div>
<ul class="pager"><li class="next"><a href="/page/2/">Next →</a></li></ul>
</body></html>"""


def fake_resp(status=200, text="<html></html>"):
    m = mock.Mock()
    m.status_code = status
    m.text = text
    m.raise_for_status = mock.Mock(return_value=None)
    return m


class TestParse(unittest.TestCase):
    def test_parse_fields_exact(self):
        rows = crawler.parse_page(SAMPLE, 3)
        self.assertEqual(len(rows), 1, "空 text 的行必须被丢弃")
        self.assertEqual(
            rows[0],
            {
                "text": "“To be or not to be.”",
                "author": "Author One",
                "author_url": "https://quotes.toscrape.com/author/Author-One",
                "tags": "x|y",
                "page": 3,
            },
        )
        self.assertEqual(list(rows[0].keys()), crawler.FIELDS)

    def test_next_page(self):
        self.assertEqual(crawler.next_page_url(SAMPLE),
                         "https://quotes.toscrape.com/page/2/")
        self.assertIsNone(crawler.next_page_url("<html><body>没有 pager</body></html>"))


class TestFetch(unittest.TestCase):
    def test_403_aborts(self):
        with mock.patch.object(crawler.requests, "get", return_value=fake_resp(403)), \
             mock.patch.object(crawler.time, "sleep"):
            with self.assertRaises(SystemExit) as ctx:
                crawler.fetch("https://x/page/1/", {"requests": 0})
            self.assertEqual(ctx.exception.code, 3)

    def test_retry_once_then_success(self):
        stats = {"requests": 0}
        seq = [real_requests.ConnectionError("boom"), fake_resp(200, SAMPLE)]
        with mock.patch.object(crawler.requests, "get", side_effect=seq), \
             mock.patch.object(crawler.time, "sleep"):
            html = crawler.fetch("https://x/page/1/", stats)
        self.assertEqual(html, SAMPLE)
        self.assertEqual(stats["requests"], 2, "重试 1 次 → 共 2 次请求")

    def test_both_attempts_fail(self):
        stats = {"requests": 0}
        with mock.patch.object(crawler.requests, "get",
                               side_effect=real_requests.ConnectionError("boom")), \
             mock.patch.object(crawler.time, "sleep"):
            html = crawler.fetch("https://x/page/1/", stats)
        self.assertIsNone(html)
        self.assertEqual(stats["requests"], 2)

    def test_sleep_called_after_every_request(self):
        with mock.patch.object(crawler.requests, "get", return_value=fake_resp(200, SAMPLE)) as g, \
             mock.patch.object(crawler.time, "sleep") as s:
            crawler.fetch("https://x/page/1/", {"requests": 0})
        g.assert_called_once()
        s.assert_called_once_with(crawler.SLEEP_SEC)


class TestSave(unittest.TestCase):
    def test_csv_utf8_sig(self):
        outdir = os.path.join(os.getcwd(), ".testout")
        os.makedirs(outdir, exist_ok=True)
        old = os.getcwd()
        os.chdir(outdir)
        try:
            rows = [{"text": "中文“引号”", "author": "张三",
                     "author_url": "https://q/a", "tags": "a|b", "page": 1}]
            fname = crawler.save_csv(rows)
            with open(fname, "rb") as f:
                raw = f.read()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), "必须带 UTF-8 BOM")
            parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            self.assertEqual(parsed[0]["text"], "中文“引号”")
            self.assertEqual(list(parsed[0].keys()), crawler.FIELDS)
        finally:
            os.chdir(old)


class TestSelfCheck(unittest.TestCase):
    def test_bad_data_detected(self):
        rows = [{"text": "", "author": "", "author_url": "", "tags": "", "page": 1}]
        out = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(out):
            crawler.self_check(rows)
        self.assertIn("未通过", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
