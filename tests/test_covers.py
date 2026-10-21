"""Issue covers remain associated with their article, including cache and network failures."""

import json
import gzip
import io
import socket
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from covers import EXTRACTOR_VERSION, FAILURE_TTL, SUCCESS_TTL, fetch_bytes, image_extension, page_images, prepare_covers, resolve_cover, validate_public_url

ARTICLE = 'https://example.com/issues/42'
PNG = b'\x89PNG\r\n\x1a\n' + bytes(8) + (640).to_bytes(4, 'big') + (360).to_bytes(4, 'big') + bytes(600)


class IssueCoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name)

    def test_webpage_prefers_share_image_and_resolves_relative_urls_after_redirect(self):
        markup = '<main><img src="/avatar.jpg"><img src="/body.jpg"></main><meta content="../cover.jpg?a=1&amp;b=2" property="og:image"><meta name="twitter:image" content="/share.jpg">'
        images = page_images(markup, ARTICLE)
        self.assertEqual(images, [('https://example.com/cover.jpg?a=1&b=2', 'og:image'), ('https://example.com/share.jpg', 'twitter:image'), ('https://example.com/body.jpg', 'article-image')])

    def test_rss_image_is_saved_locally_without_fetching_article_page(self):
        fetch = Mock(return_value=(PNG, 'image/png', 'https://cdn.example.com/image.png'))
        result = resolve_cover(ARTICLE, '/cover.png', {}, self.cache, fetch, now=100000)
        self.assertEqual(result['source'], 'rss')
        self.assertEqual((self.cache / result['file']).read_bytes(), PNG)
        fetch.assert_called_once_with('https://example.com/cover.png', referer=ARTICLE)

    def test_failed_rss_image_falls_back_to_article_share_image(self):
        fetch = Mock(side_effect=[OSError('unavailable'), (b'<meta property="og:image" content="/share.png">', 'text/html', ARTICLE), (PNG, 'image/png', 'https://example.com/share.png')])
        result = resolve_cover(ARTICLE, '/missing.png', {}, self.cache, fetch, now=100000)
        self.assertEqual(result['source'], 'og:image')
        self.assertEqual(result['source_url'], 'https://example.com/share.png')

    def test_fresh_cached_cover_avoids_network_and_failed_refresh_preserves_same_issue_image(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        previous = {'file': filename, 'checked_at': 100000, 'rss_image': '', 'extractor_version': EXTRACTOR_VERSION}
        fetch = Mock(side_effect=OSError('offline'))
        self.assertEqual(resolve_cover(ARTICLE, '', previous, self.cache, fetch, now=100001), previous)
        fetch.assert_not_called()
        refreshed = resolve_cover(ARTICLE, '', previous, self.cache, fetch, now=100001 + SUCCESS_TTL)
        self.assertEqual(refreshed['file'], filename)
        fetch.assert_called_once()

    def test_changed_rss_image_for_same_issue_refreshes_before_cache_expiry(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        previous = {'file': filename, 'checked_at': 100000, 'rss_image': '/old.png', 'extractor_version': EXTRACTOR_VERSION}
        fetch = Mock(return_value=(PNG, 'image/png', 'https://example.com/new.png'))
        result = resolve_cover(ARTICLE, '/new.png', previous, self.cache, fetch, now=100001)
        self.assertNotEqual(result['file'], filename)
        fetch.assert_called_once()

    def test_unavailable_article_records_failure_and_retries_only_after_failure_cache_expires(self):
        fetch = Mock(side_effect=OSError('offline'))
        result = resolve_cover(ARTICLE, '', {}, self.cache, fetch, now=100000)
        self.assertNotIn('file', result)
        resolve_cover(ARTICLE, '', result, self.cache, fetch, now=100001)
        self.assertEqual(fetch.call_count, 1)
        resolve_cover(ARTICLE, '', result, self.cache, fetch, now=100001 + FAILURE_TTL)
        self.assertEqual(fetch.call_count, 2)

    def test_new_issue_does_not_reuse_previous_issue_cover_when_building_offline(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        (self.cache / 'manifest.json').write_text(json.dumps({ARTICLE: {'file': filename, 'extractor_version': EXTRACTOR_VERSION}}))
        output = self.cache / 'output'
        output.mkdir()
        self.assertEqual(prepare_covers([{'url': 'https://example.com/issues/43'}], output, self.cache), {})
        self.assertFalse((output / 'covers' / filename).exists())

    def test_html_disguised_as_image_and_tiny_tracking_images_are_rejected(self):
        self.assertEqual(image_extension(b'<html>' + bytes(600), 'image/jpeg'), '')
        self.assertEqual(image_extension(PNG, 'text/html'), '')
        tiny = PNG[:16] + (1).to_bytes(4, 'big') + (1).to_bytes(4, 'big') + PNG[24:]
        self.assertEqual(image_extension(tiny, 'image/png'), '')

    def test_local_or_private_image_destinations_are_rejected_before_request(self):
        for address in ('127.0.0.1', '10.0.0.1', '169.254.169.254', '::1'):
            with self.subTest(address=address), patch('covers.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', (address, 443))]):
                with self.assertRaises(ValueError):
                    validate_public_url('https://example.com/cover.png')

    def test_chinese_article_urls_are_percent_encoded_before_http_request(self):
        headers = Message()
        headers['Content-Type'] = 'text/html'
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = headers
        response.read.side_effect = [b'<html></html>', b'']
        response.geturl.return_value = 'https://example.com/%E5%91%A8%E5%88%8A'
        opener = Mock()
        opener.open.return_value = response
        with patch('covers.validate_public_url'), patch('covers.build_opener', return_value=opener):
            body, kind, url = fetch_bytes('https://example.com/周刊')
        self.assertEqual(opener.open.call_args.args[0].full_url, 'https://example.com/%E5%91%A8%E5%88%8A')
        self.assertEqual(body, b'<html></html>')
        self.assertEqual(kind, 'text/html')

    def test_navigation_and_author_images_are_skipped_in_favor_of_article_content(self):
        markup = '<div class="theme-container sidebar-open"><main><nav><img src="/person.jpg"></nav><img alt="logo" src="/mark.jpg"><article><div class="author"><img src="/face.jpg"></div><img src="/issue.jpg"></article></main></div>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/issue.jpg', 'article-image')])

    def test_metadata_pointing_to_homepage_does_not_override_issue_banner(self):
        markup = '<meta property="og:url" content="https://example.com/"><meta property="og:image" content="/generic.jpg"><article><img src="/issue.jpg"></article>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/issue.jpg', 'article-image')])

    def test_image_reused_in_related_articles_is_not_treated_as_unique_issue_cover(self):
        markup = '<meta property="og:image" content="https://cdn.example.com/a/plain/https://assets.example.com/shared.jpg"><article><img src="/body.jpg"></article><div class="similar-item"><img src="https://cdn.example.com/b/plain/https://assets.example.com/shared.jpg"></div>'
        self.assertEqual(page_images(markup, ARTICLE), [('https://example.com/body.jpg', 'article-image')])

    def test_homepage_share_image_is_rejected_even_when_rss_and_article_both_reuse_it(self):
        home = b'<meta property="og:url" content="https://example.com/"><meta property="og:image" content="/shared.jpg">'
        article = home + b'<article><img src="/issue.png"></article>'
        fetch = Mock(side_effect=[(home, 'text/html', 'https://example.com/issues'), (article, 'text/html', ARTICLE), (PNG, 'image/png', 'https://example.com/issue.png')])
        result = resolve_cover(ARTICLE, '/shared.jpg', {}, self.cache, fetch, home='https://example.com/issues')
        self.assertEqual(result['source_url'], 'https://example.com/issue.png')
        self.assertEqual(fetch.call_count, 3)

    def test_previous_issue_number_in_release_banner_is_rejected(self):
        markup = '<article><img src="https://raw.example.com/weekly-header/380.png"></article>'
        self.assertEqual(page_images(markup, 'https://github.com/team/weekly/releases/tag/%23381'), [])

    def test_telegram_channel_avatar_is_not_treated_as_message_cover(self):
        markup = '<meta property="og:image" content="https://cdn.example.com/cat.jpg">'
        self.assertEqual(page_images(markup, 'https://t.me/news/123'), [])

    def test_old_extraction_rules_do_not_keep_wrong_cached_image_after_failed_recheck(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        previous = {'file': filename, 'checked_at': 100000, 'rss_image': '', 'extractor_version': EXTRACTOR_VERSION - 1}
        result = resolve_cover(ARTICLE, '', previous, self.cache, Mock(side_effect=OSError('offline')), now=100001)
        self.assertNotIn('file', result)

    def test_image_redirecting_to_avatar_is_rejected(self):
        fetch = Mock(side_effect=[(PNG, 'image/png', 'https://avatars.example.com/u/1'), OSError('no article')])
        result = resolve_cover(ARTICLE, '/image', {}, self.cache, fetch)
        self.assertNotIn('file', result)

    def test_archive_without_metadata_uses_site_root_to_identify_generic_share_image(self):
        share = b'<meta property="og:image" content="/shared.png">'
        fetch = Mock(side_effect=[(b'<html></html>', 'text/html', 'https://example.com/issues/'), (share, 'text/html', 'https://example.com/'), (share, 'text/html', ARTICLE)])
        result = resolve_cover(ARTICLE, '', {}, self.cache, fetch, home='https://example.com/issues')
        self.assertNotIn('file', result)
        self.assertEqual(fetch.call_count, 3)

    def test_image_hotlink_request_sends_public_article_origin_without_query_or_fragment(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = Message()
        response.headers['Content-Type'] = 'image/png'
        response.read.side_effect = [PNG, b'']
        response.geturl.return_value = 'https://cdn.example.com/image.png'
        opener = Mock()
        opener.open.return_value = response
        with patch('covers.validate_public_url'), patch('covers.build_opener', return_value=opener):
            fetch_bytes('https://cdn.example.com/image.png', referer=ARTICLE + '?token=private#section')
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header('Referer'), 'https://example.com/')

    def test_temporary_service_failure_is_retried_once_but_forbidden_response_is_not_retried(self):
        for status, expected_calls in [(503, 2), (521, 2), (403, 1)]:
            with self.subTest(status=status):
                error = HTTPError(ARTICLE, status, 'unavailable', Message(), io.BytesIO())
                with patch('covers._fetch_bytes', side_effect=[error, (PNG, 'image/png', ARTICLE)]) as fetch, patch('covers.time.sleep'):
                    if expected_calls == 2:
                        self.assertEqual(fetch_bytes(ARTICLE)[0], PNG)
                    else:
                        with self.assertRaises(HTTPError):
                            fetch_bytes(ARTICLE)
                    self.assertEqual(fetch.call_count, expected_calls)

    def test_rate_limit_with_long_retry_after_does_not_trigger_immediate_retry(self):
        headers = Message()
        headers['Retry-After'] = '120'
        error = HTTPError(ARTICLE, 429, 'rate limited', headers, io.BytesIO())
        with patch('covers._fetch_bytes', side_effect=error) as fetch:
            with self.assertRaises(HTTPError):
                fetch_bytes(ARTICLE)
            fetch.assert_called_once()

    def test_gzipped_article_is_decoded_and_uncompressed_size_limit_is_enforced(self):
        for limit in (1024, 10):
            response = MagicMock()
            response.__enter__.return_value = response
            response.headers = Message()
            response.headers['Content-Type'] = 'text/html'
            response.headers['Content-Encoding'] = 'gzip'
            body = b'<article>content</article>'
            response.read.side_effect = io.BytesIO(gzip.compress(body)).read
            response.geturl.return_value = ARTICLE
            with patch('covers.validate_public_url'), patch('covers.build_opener') as opener:
                opener.return_value.open.return_value = response
                if limit > len(body):
                    self.assertEqual(fetch_bytes(ARTICLE, limit=limit)[0], body)
                else:
                    with self.assertRaises(ValueError):
                        fetch_bytes(ARTICLE, limit=limit)

    def test_valid_image_with_generic_binary_mime_type_is_accepted_but_html_is_rejected(self):
        self.assertEqual(image_extension(PNG, 'application/octet-stream'), '.png')
        self.assertEqual(image_extension(b'<html>' + bytes(600), 'application/octet-stream'), '')

    def test_fifth_candidate_is_tried_after_four_broken_images(self):
        markup = '<article>' + ''.join(f'<img src="/{i}.png">' for i in range(5)) + '</article>'
        fetch = Mock(side_effect=[(markup.encode(), 'text/html', ARTICLE), *[OSError('broken')] * 4, (PNG, 'image/png', 'https://example.com/4.png')])
        result = resolve_cover(ARTICLE, '', {}, self.cache, fetch)
        self.assertEqual(result['source_url'], 'https://example.com/4.png')
        self.assertEqual(len(result['attempts']), 5)

    def test_second_rss_candidate_can_succeed_without_fetching_unavailable_article_page(self):
        fetch = Mock(side_effect=[OSError('broken first image'), (PNG, 'image/png', 'https://example.com/second.png')])
        result = resolve_cover(ARTICLE, '/first.png', {}, self.cache, fetch, rss_images=['/first.png', '/second.png'])
        self.assertEqual(result['source_url'], 'https://example.com/second.png')
        self.assertEqual(fetch.call_count, 2)

    def test_failed_refresh_keeps_same_issue_image_but_retries_after_short_failure_ttl(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        previous = {'file': filename, 'checked_at': 1, 'rss_image': '', 'extractor_version': EXTRACTOR_VERSION}
        fetch = Mock(side_effect=OSError('temporary outage'))
        first = resolve_cover(ARTICLE, '', previous, self.cache, fetch, now=SUCCESS_TTL + 2)
        self.assertTrue(first['refresh_failed'])
        second = resolve_cover(ARTICLE, '', first, self.cache, fetch, now=SUCCESS_TTL + FAILURE_TTL + 3)
        self.assertEqual(second['file'], filename)
        self.assertEqual(fetch.call_count, 2)

    def test_force_refresh_rechecks_image_even_when_success_cache_is_fresh(self):
        filename = 'a' * 24 + '.png'
        (self.cache / filename).write_bytes(PNG)
        previous = {'file': filename, 'checked_at': 100000, 'rss_image': '/cover.png', 'extractor_version': EXTRACTOR_VERSION}
        fetch = Mock(return_value=(PNG, 'image/png', 'https://example.com/cover.png'))
        resolve_cover(ARTICLE, '/cover.png', previous, self.cache, fetch, now=100001, force=True)
        fetch.assert_called_once()

    def test_article_image_request_honors_no_referrer_policy(self):
        markup = b'<article><img referrerpolicy="no-referrer" src="/image.png"></article>'
        fetch = Mock(side_effect=[(markup, 'text/html', ARTICLE), (PNG, 'image/png', 'https://example.com/image.png')])
        result = resolve_cover(ARTICLE, '', {}, self.cache, fetch)
        self.assertEqual(result['status'], 'downloaded')
        fetch.assert_called_with('https://example.com/image.png', referer='')

    def test_cdn_rejecting_referer_gets_one_anonymous_retry(self):
        denied = HTTPError('https://cdn.example.com/cover.png', 403, 'forbidden referrer', Message(), io.BytesIO())
        fetch = Mock(side_effect=[denied, (PNG, 'image/png', 'https://cdn.example.com/cover.png')])
        result = resolve_cover(ARTICLE, 'https://cdn.example.com/cover.png', {}, self.cache, fetch)
        self.assertEqual(result['status'], 'downloaded')
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(fetch.call_args_list[1].kwargs['referer'], '')


if __name__ == '__main__':
    unittest.main()
