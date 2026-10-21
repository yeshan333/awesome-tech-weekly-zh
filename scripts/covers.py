"""Fetch and cache public article cover images at build time (standard library only)."""

import hashlib
import gzip
import ipaddress
import json
import re
import shutil
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError, URLError
from cover_sources import CoverParser, image_identity, image_url, matches_issue, page_images, supplemental_images

MAX_BYTES = 4 * 1024 * 1024
SUCCESS_TTL = 7 * 86400
FAILURE_TTL = 30 * 60
EXTRACTOR_VERSION = 6
MAX_CANDIDATES = 8
USER_AGENT = 'Mozilla/5.0 (compatible; AwesomeWeeklyCover/1.0; +https://github.com/yeshan333/awesome-tech-weekly-zh)'


def validate_public_url(url: str):
    parsed = urlsplit(url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('not a public HTTP URL')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError('non-public destination')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_bytes(url: str, limit=MAX_BYTES, referer='') -> tuple[bytes, str, str]:
    """Retry one transient GET failure without disabling TLS verification."""
    for attempt in range(2):
        try:
            return _fetch_bytes(url, limit, referer)
        except HTTPError as error:
            retry_after = error.headers.get('Retry-After', '') if error.headers else ''
            if attempt or error.code not in (429, 500, 502, 503, 504, 520, 521, 522, 523, 524) or retry_after and (not retry_after.isdigit() or int(retry_after) > 2):
                raise
            error.close()
            time.sleep(int(retry_after) if retry_after else 0.2)
        except (URLError, TimeoutError):
            if attempt:
                raise
            time.sleep(0.2)


def _fetch_bytes(url: str, limit=MAX_BYTES, referer='') -> tuple[bytes, str, str]:
    # Validate every redirect rather than letting a public page redirect into a local service.
    opener = build_opener(NoRedirect())
    for _ in range(4):
        validate_public_url(url)
        parts = urlsplit(url)
        # README links may contain Chinese titles; urllib requires an ASCII request target.
        wire_url = urlunsplit((parts.scheme, parts.netloc.encode('idna').decode('ascii'),
                              quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
                              quote(parts.query, safe="/%?:@!$&'()*+,;=-._~"), ''))
        headers = {'User-Agent': USER_AGENT, 'Accept': 'text/html,image/avif,image/webp,image/*;q=0.9,*/*;q=0.5', 'Accept-Encoding': 'identity'}
        if referer:
            origin = urlsplit(referer)
            if origin.scheme in ('http', 'https') and origin.hostname and not origin.username and not origin.password:
                # Cross-origin image requests normally expose only the public page origin.
                headers['Referer'] = urlunsplit((origin.scheme, origin.netloc.encode('idna').decode(), '/', '', ''))
        request = Request(wire_url, headers=headers)
        try:
            response = opener.open(request, timeout=8)
        except HTTPError as error:
            if error.code in (301, 302, 303, 307, 308) and error.headers.get('Location'):
                url = urljoin(url, error.headers['Location'])
                error.close()
                continue
            raise
        with response:
            length = response.headers.get('Content-Length', '')
            if length.isdigit() and int(length) > limit:
                raise ValueError('response too large')
            chunks, size, deadline = [], 0, time.monotonic() + 12
            stream = gzip.GzipFile(fileobj=response) if response.headers.get('Content-Encoding', '').lower() == 'gzip' else response
            while True:
                chunk = stream.read(min(65536, limit + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                if size > limit or time.monotonic() > deadline:
                    raise ValueError('response exceeded size or time budget')
                chunks.append(chunk)
            return b''.join(chunks), response.headers.get_content_type(), response.geturl()
    raise ValueError('too many redirects')


def image_extension(body: bytes, content_type: str) -> str:
    if not (content_type.startswith('image/') or content_type in ('application/octet-stream', 'binary/octet-stream')) or len(body) < 24:
        return ''
    if body.startswith(b'\x89PNG\r\n\x1a\n'):
        width, height = int.from_bytes(body[16:20], 'big'), int.from_bytes(body[20:24], 'big')
        return '.png' if width >= 160 and height >= 90 else ''
    if body.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if body[:4] == b'RIFF' and body[8:12] == b'WEBP':
        return '.webp'
    if body[:6] in (b'GIF87a', b'GIF89a'):
        return '.gif' if int.from_bytes(body[6:8], 'little') >= 160 and int.from_bytes(body[8:10], 'little') >= 90 else ''
    if body[4:8] == b'ftyp' and body[8:12] in (b'avif', b'avis'):
        return '.avif'
    return ''


def cached_file(cache_dir: Path, entry: dict) -> Path | None:
    if entry.get('extractor_version') != EXTRACTOR_VERSION:
        return None
    if entry.get('source_url') and not image_url(entry['source_url'], ''):
        return None
    filename = entry.get('file', '')
    if not re.fullmatch(r'[a-f0-9]{24}\.(?:png|jpg|webp|gif|avif)', filename):
        return None
    path = cache_dir / filename
    return path if path.is_file() else None


def resolve_cover(article: str, rss_image: str, previous: dict, cache_dir: Path, fetch=fetch_bytes, now=None, home='', force=False, rss_images=None) -> dict:
    now = time.time() if now is None else now
    existing = cached_file(cache_dir, previous)
    ttl = SUCCESS_TTL if existing and not previous.get('refresh_failed') else FAILURE_TTL
    rss_images = list(dict.fromkeys([rss_image, *(rss_images or [])]))
    rss_images = [url for url in rss_images if url]
    if not force and previous.get('extractor_version') == EXTRACTOR_VERSION and previous.get('rss_image', '') == rss_image and previous.get('rss_images', [rss_image] if rss_image else []) == rss_images and now - previous.get('checked_at', 0) < ttl and (existing or not previous.get('file')):
        return previous

    attempts = []
    candidate_count = 0
    page_error = ''

    excluded = set()
    if home and home != article:
        root = urlunsplit((*urlsplit(home)[:2], '/', '', ''))
        for home_url in dict.fromkeys((home, root)):
            try:
                body, kind, final = fetch(home_url, limit=2 * 1024 * 1024)
                if kind in ('text/html', 'application/xhtml+xml'):
                    home_parser = CoverParser(final)
                    home_parser.feed(body.decode('utf-8', errors='replace'))
                    excluded = {image_identity(url) for _, url, source in home_parser.candidates if source != 'article-image'}
                    if excluded:
                        break
            except (OSError, ValueError, TimeoutError):
                pass

    def download(candidates):
        nonlocal candidate_count
        candidate_count += len(candidates)
        for candidate in candidates:
            url, source = candidate[:2]
            policy = candidate[2] if len(candidate) > 2 else None
            if len(attempts) >= MAX_CANDIDATES:
                break
            if not image_url(url, article) or not matches_issue(article, url) or image_identity(url) in excluded:
                continue
            attempt = {'url': url}
            attempts.append(attempt)
            try:
                referer = '' if policy == 'no-referrer' else article
                try:
                    body, kind, final_url = fetch(url, referer=referer)
                except HTTPError as error:
                    if error.code != 403 or not referer:
                        raise
                    # Some public image CDNs require a Referer, others reject it.
                    # Retry once without it; never add credentials or disable TLS.
                    error.close()
                    body, kind, final_url = fetch(url, referer='')
                if not image_url(final_url, article) or not matches_issue(article, final_url):
                    attempt['error'] = 'redirected image was excluded'
                    continue
                extension = image_extension(body, kind)
                if not extension:
                    attempt['error'] = 'unsupported image or invalid dimensions'
                    continue
                filename = hashlib.sha256((article + '\n' + url).encode()).hexdigest()[:24] + extension
                (cache_dir / filename).write_bytes(body)
                return {'file': filename, 'source_url': final_url, 'source': source,
                        'checked_at': now, 'rss_image': rss_image, 'rss_images': rss_images, 'extractor_version': EXTRACTOR_VERSION,
                        'status': 'downloaded', 'attempts': attempts, 'candidates_found': candidate_count}
            except (OSError, ValueError, TimeoutError, EOFError) as error:
                attempt['error'] = str(error)[:200]
                continue
        return None

    candidates = [(url, 'rss') for candidate in rss_images if (url := image_url(candidate, article))]
    result = download(candidates) if candidates else None
    if result:
        return result
    try:
        body, kind, final_url = fetch(article, limit=2 * 1024 * 1024)
        if kind in ('text/html', 'application/xhtml+xml'):
            markup = body.decode('utf-8', errors='replace')
            result = download(page_images(markup, final_url, excluded, with_policy=True))
            if result:
                return result
            result = download(supplemental_images(markup, final_url, fetch))
            if result:
                return result
        else:
            page_error = 'article did not return HTML'
    except (OSError, ValueError, TimeoutError, EOFError) as error:
        page_error = str(error)[:200]
    # A refresh failure can reuse this issue's last good image, never another issue's.
    if existing and image_identity(previous.get('source_url', '')) not in excluded:
        return {**previous, 'checked_at': now, 'rss_image': rss_image, 'rss_images': rss_images, 'refresh_failed': True,
                'status': 'cached-after-failure', 'attempts': attempts, 'error': page_error}
    status = 'image-fetch-failed' if attempts else 'page-fetch-failed' if page_error else 'no-usable-image'
    return {'checked_at': now, 'rss_image': rss_image, 'rss_images': rss_images, 'extractor_version': EXTRACTOR_VERSION,
            'status': status, 'error': page_error, 'attempts': attempts, 'candidates_found': candidate_count}


def prepare_covers(feeds: list[dict], output_dir: Path, cache_dir: Path, refresh=False, force=False) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = cache_dir / 'manifest.json'
    try:
        manifest = json.loads(manifest_file.read_text())
        if not isinstance(manifest, dict):
            manifest = {}
        manifest = {key: value for key, value in manifest.items() if isinstance(value, dict)}
    except (OSError, ValueError):
        manifest = {}
    articles = {feed['url']: feed.get('cover_url', '') for feed in feeds if feed['url']}
    homes = {feed['url']: feed.get('home', '') for feed in feeds if feed['url']}
    rss_images = {feed['url']: feed.get('cover_urls', []) for feed in feeds if feed['url']}
    if refresh:
        def resolve(pair):
            article, rss_image = pair
            previous = manifest.get(article, {})
            return article, resolve_cover(article, rss_image, previous, cache_dir, home=homes[article], force=force, rss_images=rss_images[article])
        with ThreadPoolExecutor(max_workers=5) as pool:
            for article, result in pool.map(resolve, articles.items()):
                manifest[article] = result
        # Retain only the current issues so the cache stays bounded as feeds advance.
        manifest = {url: manifest[url] for url in articles if url in manifest}
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        retained = {entry.get('file') for entry in manifest.values()}
        for path in cache_dir.iterdir():
            if re.fullmatch(r'[a-f0-9]{24}\.(?:png|jpg|webp|gif|avif)', path.name) and path.name not in retained:
                path.unlink()
    covers = {}
    destination = output_dir / 'covers'
    destination.mkdir(exist_ok=True)
    for article in articles:
        entry = manifest.get(article, {})
        source = cached_file(cache_dir, entry)
        if source:
            shutil.copy2(source, destination / source.name)
            covers[article] = {**entry, 'path': f'covers/{source.name}'}
    retained = {entry['file'] for entry in covers.values()}
    for path in destination.iterdir():
        if re.fullmatch(r'[a-f0-9]{24}\.(?:png|jpg|webp|gif|avif)', path.name) and path.name not in retained:
            path.unlink()
    (destination / 'sources.json').write_text(json.dumps(covers, ensure_ascii=False, indent=2), encoding='utf-8')
    status = {url: manifest.get(url, {'status': 'not-fetched'}) for url in articles}
    (destination / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Article covers: {len(covers)}/{len(articles)} cached; remaining articles use topic illustrations.')
    return covers
