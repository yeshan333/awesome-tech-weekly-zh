"""Newsletter metadata must remain correct when rendered as a website or RSS."""

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
spec = importlib.util.spec_from_file_location("build_site", Path(__file__).parents[1] / "scripts/build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)
NOW = datetime(2026, 10, 22, 0, 0, tzinfo=timezone.utc)


def dataset(**fields):
    return [{"category": "AI", "feeds": [{
        "name": "测试周刊", "desc": "真实的周刊描述", "link": "[主页](https://example.com)",
        "latest_post": "[一期文章](https://example.com/post)", "published_date": "2026-10-21T00:00:00Z",
        **fields,
    }]}]


class NewsletterPublishingTests(unittest.TestCase):
    def test_current_issue_uses_its_cached_cover_and_keeps_a_local_fallback(self):
        covers = {'https://example.com/post': {'path': 'covers/issue.jpg'}}
        rendered = site.build_html(dataset(), NOW, covers)
        self.assertIn('src="covers/issue.jpg" data-fallback="images/ai.webp"', rendered)
        newer = site.build_html(dataset(latest_post='[下一期](https://example.com/next)'), NOW, covers)
        self.assertNotIn('src="covers/issue.jpg"', newer)
        self.assertIn('src="images/ai.webp"', newer)

    def test_recent_filter_includes_seven_day_boundary_but_excludes_old_and_future_posts(self):
        for published, expected in [
            ("2026-10-15T00:00:00Z", True), ("2026-10-14T23:59:59Z", False),
            ("2026-10-22T00:00:01Z", False), ("bad-date", False),
        ]:
            with self.subTest(published=published):
                self.assertEqual(site.normalize(dataset(published_date=published), NOW)[0]["feeds"][0]["recent"], expected)

    def test_homepage_fallback_is_available_in_directory_but_is_not_published_as_an_article(self):
        data = dataset(latest_post="[主页](https://example.com)")
        rendered = site.build_html(data, NOW)
        self.assertIn("暂无最新文章", rendered)
        self.assertIn('href="https://example.com"', rendered)
        self.assertEqual(ET.fromstring(site.build_feed_xml(data, now=NOW)).findall("channel/item"), [])

    def test_rss_preserves_ampersands_and_parenthesized_urls_without_news_badge_markup(self):
        data = dataset(name="A & B", latest_post="[A & B](https://example.com/p_(1)?a=1&b=2)![news](https://example.com/new.png)")
        item = ET.fromstring(site.build_feed_xml(data, now=NOW)).find("channel/item")
        self.assertEqual(item.findtext("link"), "https://example.com/p_(1)?a=1&b=2")
        self.assertEqual(item.findtext("title"), "[AI] A & B - A & B")

    def test_untrusted_metadata_is_text_and_javascript_links_are_not_clickable(self):
        rendered = site.build_html(dataset(name='<script>alert("x")</script>', link="[主页](javascript:alert(1))", latest_post=""), NOW)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn('<script>alert("x")', rendered)
        self.assertNotIn('href="javascript:', rendered)

    def test_rss_sorts_timezone_aware_naive_and_missing_dates_without_failing(self):
        data = dataset(published_date="2026-10-21T09:00:00+08:00")
        data[0]["feeds"] += [dataset(published_date="2026-10-21T02:00:00")[0]["feeds"][0], dataset(published_date="")[0]["feeds"][0]]
        items = ET.fromstring(site.build_feed_xml(data, "https://example.org/directory", NOW)).findall("channel/item")
        self.assertEqual(len(items), 3)
        self.assertIn("02:00:00", items[0].findtext("pubDate"))
        self.assertIn("01:00:00", items[1].findtext("pubDate"))
        self.assertIsNone(items[2].find("pubDate"))


if __name__ == "__main__":
    unittest.main()
