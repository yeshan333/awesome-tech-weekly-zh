"""Article images survive publisher markup variations without leaking sidebar images."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from cover_sources import image_identity, page_images, supplemental_images

ARTICLE = 'https://example.com/issues/42'


class PublisherImageMarkupTests(unittest.TestCase):
    def test_forum_body_without_article_tag_is_read_but_sidebar_ad_and_comments_are_excluded(self):
        # Reduced from V2EX's Rightbar + topic_content / markdown_body structure.
        markup = '<div id="Rightbar"><div class="markdown_body"><img src="/ad.jpg"></div></div><div id="Main"><div class="topic_content"><div class="markdown_body"><img src="/issue.jpg"></div></div><div class="comment-list"><div class="markdown_body"><img src="/reply.jpg"></div></div></div>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/issue.jpg', 'article-image')])

    def test_lazy_image_with_one_pixel_placeholder_uses_actual_source_and_keeps_backup(self):
        markup = '<article><img width="1" height="1" data-original="/real.jpg" data-lazy-src="/backup.jpg" src="data:image/gif;base64,AA"></article>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/real.jpg', 'article-image'), ('https://example.com/backup.jpg', 'article-image')])

    def test_picture_srcset_preserves_commas_in_cdn_urls_and_keeps_img_fallback(self):
        markup = '<article><picture><source srcset="https://cdn.example.com/w_400,q_80/a.webp 400w, https://cdn.example.com/w_1200,q_80/a.webp 1200w"><img src="/fallback.jpg"></picture></article>'
        self.assertEqual([url for url, _ in page_images(markup, ARTICLE)], ['https://cdn.example.com/w_1200,q_80/a.webp', 'https://cdn.example.com/w_400,q_80/a.webp', 'https://example.com/fallback.jpg'])

    def test_base_href_and_noscript_images_resolve_to_the_publishers_actual_image_directory(self):
        markup = '<base href="https://cdn.example.com/assets/"><article><noscript><img src="issue.jpg"></noscript></article>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://cdn.example.com/assets/issue.jpg', 'article-image')])

    def test_image_referrer_policy_is_preserved_for_hotlink_sensitive_cdn(self):
        markup = '<div class="topic_content"><img referrerpolicy="no-referrer" src="https://cdn.example.com/issue.jpg"></div>'
        self.assertEqual(page_images(markup, ARTICLE, with_policy=True), [('https://cdn.example.com/issue.jpg', 'article-image', 'no-referrer')])

    def test_jsonld_selects_current_article_image_object_and_ignores_publisher_and_other_articles(self):
        graph = {'@graph': [
            {'@type': 'Organization', 'image': '/brand.jpg'},
            {'@type': 'BlogPosting', 'url': '/issues/41', 'image': '/old.jpg'},
            {'@type': 'Article', 'mainEntityOfPage': {'@id': ARTICLE}, 'image': {'@id': '#cover'}},
            {'@type': 'ImageObject', '@id': '#cover', 'contentUrl': '/issue.jpg'},
        ]}
        markup = '<script type="application/ld+json">' + json.dumps(graph) + '</script>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/issue.jpg', 'article-jsonld')])

    def test_broken_structured_metadata_does_not_hide_valid_body_image(self):
        markup = '<script type="application/ld+json">{bad json}</script><script type="application/ld+json">{"@type":null}</script><article><img src="/issue.jpg"></article>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/issue.jpg', 'article-image')])

    def test_image_endpoint_query_id_is_preserved_so_homepage_image_does_not_hide_article_image(self):
        excluded = {image_identity('https://cdn.example.com/image?id=home&w=300')}
        markup = '<meta property="og:image" content="https://cdn.example.com/image?id=issue42&w=1200">'
        self.assertEqual(page_images(markup, ARTICLE, excluded), [('https://cdn.example.com/image?id=issue42&w=1200', 'og:image')])

    def test_next_image_wrapper_and_resized_original_have_same_asset_identity(self):
        self.assertEqual(image_identity('https://example.com/_next/image?url=%2Fphoto.jpg&w=1200&q=80'), image_identity('https://example.com/photo.jpg'))

    def test_script_loaded_newsletter_selects_requested_issue_even_when_a_newer_issue_is_first(self):
        script = '''const issues = {
  42: { issue: "ISSUE 042", lead: { image: "./assets/vol42-new.png" } },
  41: {
    issue: "ISSUE 041",
    lead: {
      image: "./assets/vol41-cover.png",
    },
  },
};
throw new Error("must never execute publisher code");'''
        fetch = Mock(return_value=(script.encode(), 'application/javascript', 'https://sanhao-design-weekly.pages.dev/script.js?v=2'))
        result = supplemental_images('<script src="./script.js?v=2"></script>', 'https://sanhao-design-weekly.pages.dev/?issue=41', fetch)
        self.assertEqual(result, [('https://sanhao-design-weekly.pages.dev/assets/vol41-cover.png', 'issue-script')])

    def test_unknown_script_issue_does_not_fall_back_to_another_issue(self):
        fetch = Mock(return_value=(b'const issues = {41: {image:"/assets/vol41.png"}};', 'application/javascript', 'https://sanhao-design-weekly.pages.dev/script.js'))
        self.assertEqual(supplemental_images('<script src="/script.js"></script>', 'https://sanhao-design-weekly.pages.dev/?issue=99', fetch), [])

    def test_telegram_embed_uses_only_photo_attached_to_requested_message(self):
        markup = '<div data-post="news/123"><a class="tgme_widget_message_photo_wrap" style="background-image:url(\'https://cdn.example.com/issue.jpg\')"></a></div><div data-post="news/124"><a class="tgme_widget_message_photo_wrap" style="background-image:url(\'https://cdn.example.com/other.jpg\')"></a></div>'
        self.assertEqual(page_images(markup, 'https://t.me/news/123?embed=1'), [('https://cdn.example.com/issue.jpg', 'telegram-photo')])


if __name__ == '__main__':
    unittest.main()
