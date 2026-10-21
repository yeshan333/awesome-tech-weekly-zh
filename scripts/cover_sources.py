"""Extract article image candidates without executing publisher scripts."""

import json
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urljoin, urlsplit


def image_url(value: str, base: str) -> str:
    try:
        url = urljoin(base, value.strip()) if value else ''
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            return ''
        if re.search(r'(?:avatar|favicon|tracking|pixel|badge|logo|qr[-_]|qrcode|/profile\.)', parsed.hostname + parsed.path, re.I):
            return ''
        return url
    except (ValueError, AttributeError):
        return ''


def image_identity(url: str) -> str:
    """Ignore CDN resizing, but preserve query parameters that identify different images."""
    parsed = urlsplit(url)
    decoded_path = unquote(parsed.path)
    for marker in ('/https://', '/http://'):
        if marker in decoded_path:
            return image_identity(marker[1:] + decoded_path.rsplit(marker, 1)[1])
    params = parse_qsl(parsed.query, keep_blank_values=True)
    if parsed.path == '/_next/image' and dict(params).get('url'):
        return image_identity(urljoin(url, dict(params)['url']))
    resize = {'w', 'width', 'h', 'height', 'q', 'quality', 'fit', 'crop', 'format', 'fm', 'dpr'}
    query = urlencode(sorted((key, value) for key, value in params if key.lower() not in resize))
    return parsed.netloc.lower() + re.sub(r'/size/w\d+/', '/', decoded_path) + ('?' + query if query else '')


def matches_issue(article: str, image: str) -> bool:
    issue = re.search(r'/releases/tag/#?(\d+)$', unquote(urlsplit(article).path))
    banner = re.search(r'/weekly-header/(\d+)\.', unquote(urlsplit(image).path))
    return not (issue and banner and issue[1] != banner[1])


def srcset_urls(value: str) -> list[str]:
    """Handle commas inside CDN URLs; prefer a useful size, with smaller backups."""
    candidates = []
    remaining = value.strip()
    while remaining:
        remaining = remaining.lstrip(' ,\t\r\n')
        match = re.match(r'\S+', remaining)
        if not match:
            break
        url = match[0]
        remaining = remaining[len(url):]
        descriptor = ''
        if url.endswith(','):
            url = url.rstrip(',')
        else:
            descriptor, separator, remaining = remaining.partition(',')
        dimension = re.fullmatch(r'\s*(\d+(?:\.\d+)?)([wx])\s*', descriptor)
        size = float(dimension[1]) * (800 if dimension[2] == 'x' else 1) if dimension else 800
        if not descriptor.strip() or dimension:
            candidates.append((size, url))
    candidates.sort(key=lambda candidate: (candidate[0] > 1600, -candidate[0] if candidate[0] <= 1600 else candidate[0]))
    return [url for _, url in candidates]


def element_images(attrs: dict, base: str) -> list[str]:
    values = [attrs.get(key) for key in ('data-original', 'data-lazy-src', 'data-src')]
    for key in ('data-srcset', 'srcset'):
        values.extend(srcset_urls(attrs.get(key) or ''))
    values.append(attrs.get('src'))
    return list(dict.fromkeys(url for value in values if (url := image_url(value, base))))


def page_key(url: str) -> tuple:
    parsed = urlsplit(url)
    return parsed.netloc.lower(), unquote(parsed.path).rstrip('/'), tuple(sorted(parse_qsl(parsed.query)))


class CoverParser(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.page_url = base
        self.base = base
        self.has_base = False
        self.candidates = []
        self.stack = []
        self.excluded_images = set()
        self.og_url = ''
        self.canonical = ''
        self.scripts = []
        self.json_ld = []
        self.capture_json = False
        self.json_text = []
        self.no_referrer = False
        self.image_policies = {}

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        hint = ' '.join(attrs.get(key) or '' for key in ('class', 'id', 'alt', 'role', 'aria-label'))
        blocked = bool(re.search(r'(?:^|[\s_-])(?:avatar|logo|profile|author|similar|related|recommend|comment|comments|reply|replies|advertisement|ads|sponsor)(?:$|[\s_-])|(?:^|\s)(?:sidebar|sidebar-wrapper|sidebar-container|rightbar|leftbar)(?:\s|$)|qrcode|二维码', hint, re.I))
        blocked = blocked or tag in ('nav', 'aside', 'footer') or any(entry[1] for entry in self.stack)
        scope = max((entry[2] for entry in self.stack), default=0)
        own_scope = 2 if tag == 'article' or re.search(r'(?:^|\s)(?:topic[_-]content|markdown[_-]body|post-content|entry-content|article-body|article-content)(?:\s|$)', hint) or attrs.get('itemprop') == 'articleBody' else 1 if tag == 'main' or attrs.get('role') == 'main' else 0
        post = attrs.get('data-post') or next((entry[3] for entry in reversed(self.stack) if entry[3]), '')
        if tag not in ('img', 'meta', 'link', 'br', 'hr', 'input', 'source', 'area', 'base', 'embed', 'param', 'track', 'wbr'):
            self.stack.append((tag, blocked, own_scope, post))
        if tag == 'base' and not self.has_base:
            base = urljoin(self.base, attrs.get('href') or '')
            if urlsplit(base).scheme in ('http', 'https'):
                self.base, self.has_base = base, True
        if tag == 'script':
            if attrs.get('src'):
                self.scripts.append(urljoin(self.base, attrs['src']))
            self.capture_json = attrs.get('type', '').lower() == 'application/ld+json'
            self.json_text = []
        value, priority, source = '', 99, ''
        if tag == 'meta':
            prop = (attrs.get('property') or attrs.get('name') or attrs.get('itemprop') or '').lower()
            if prop == 'referrer' and attrs.get('content', '').lower() == 'no-referrer':
                self.no_referrer = True
            if prop == 'og:url':
                self.og_url = urljoin(self.base, attrs.get('content') or '')
            if prop in ('og:image:secure_url', 'og:image', 'og:image:url'):
                value, priority, source = attrs.get('content', ''), 0, 'og:image'
            elif prop in ('twitter:image', 'twitter:image:src'):
                value, priority, source = attrs.get('content', ''), 1, 'twitter:image'
            elif prop == 'image' and not blocked:
                value, priority, source = attrs.get('content', ''), 2, 'article-metadata'
        elif tag == 'link':
            rel = (attrs.get('rel') or '').lower().split()
            if 'canonical' in rel:
                self.canonical = urljoin(self.base, attrs.get('href') or '')
            if 'image_src' in rel:
                value, priority, source = attrs.get('href', ''), 2, 'image_src'
        elif tag in ('img', 'source'):
            if tag == 'source' and not any(entry[0] == 'picture' for entry in self.stack):
                return
            urls = element_images(attrs, self.base)
            if attrs.get('referrerpolicy', '').lower() == 'no-referrer':
                self.image_policies.update({url: 'no-referrer' for url in urls})
            if blocked:
                self.excluded_images.update(image_identity(url) for url in urls)
                return
            if not scope:
                return
            for dimension, minimum in [('width', 160), ('height', 90)]:
                raw = attrs.get(dimension) or ''
                # Lazy-load placeholders often declare 1x1 while the real source is large.
                lazy = any(attrs.get(key) for key in ('data-original', 'data-lazy-src', 'data-src', 'data-srcset', 'srcset'))
                if raw.isdigit() and int(raw) < minimum and not lazy:
                    return
            self.candidates.extend((3 if scope == 2 else 4, url, 'article-image') for url in urls)
        elif 'tgme_widget_message_photo_wrap' in hint and post == urlsplit(self.page_url).path.strip('/') and not blocked:
            match = re.search(r'background-image\s*:\s*url\([\s\'"]*(.*?)[\s\'"]*\)', attrs.get('style') or '', re.I)
            if match:
                value, priority, source = match[1], 2, 'telegram-photo'
        if url := image_url(value, self.base):
            self.candidates.append((priority, url, source))

    def handle_data(self, data):
        if self.capture_json:
            self.json_text.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture_json:
            try:
                self.json_ld.append(json.loads(''.join(self.json_text)))
            except (ValueError, RecursionError):
                pass
            self.capture_json = False
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def structured_images(self):
        def nodes(value, depth=0):
            if depth > 12:
                return
            if isinstance(value, list):
                for item in value:
                    yield from nodes(item, depth + 1)
            elif isinstance(value, dict):
                yield value
                yield from nodes(value.get('@graph', []), depth + 1)
        for document in self.json_ld:
            graph = list(nodes(document))
            refs = {node['@id']: node for node in graph if isinstance(node.get('@id'), str)}
            for node in graph:
                kinds = node.get('@type', [])
                kinds = [kinds] if isinstance(kinds, str) else kinds
                if not isinstance(kinds, list):
                    continue
                if not any(kind in ('Article', 'NewsArticle', 'BlogPosting', 'TechArticle', 'Report') for kind in kinds):
                    continue
                identity = node.get('mainEntityOfPage') or node.get('url') or node.get('@id')
                if isinstance(identity, dict):
                    identity = identity.get('@id') or identity.get('url')
                if isinstance(identity, str) and page_key(urljoin(self.base, identity)) not in {page_key(self.page_url), page_key(self.canonical or self.page_url)}:
                    continue
                pictures = node.get('image', [])
                for item in pictures if isinstance(pictures, list) else [pictures]:
                    if isinstance(item, str) and item in refs:
                        item = refs[item]
                    if isinstance(item, dict):
                        ref = item.get('@id')
                        item = refs.get(ref, item) if isinstance(ref, str) else item
                        item = item.get('contentUrl') or item.get('url')
                    if url := image_url(item, self.base):
                        yield 2, url, 'article-jsonld'


def page_images(markup: str, base: str, excluded=frozenset(), with_policy=False) -> list[tuple]:
    parser = CoverParser(base)
    parser.feed(markup)
    seen, result = set(), []
    generic = bool(parser.og_url and urlsplit(parser.og_url).path in ('', '/') and urlsplit(base).path not in ('', '/'))
    generic = generic or urlsplit(base).hostname in ('t.me', 'telegram.me')
    for _, url, source in sorted([*parser.candidates, *parser.structured_images()], key=lambda candidate: candidate[0]):
        if image_identity(url) in excluded | parser.excluded_images or not matches_issue(base, url):
            continue
        if generic and source not in ('article-image', 'article-jsonld', 'telegram-photo'):
            continue
        if url not in seen:
            policy = 'no-referrer' if parser.no_referrer else parser.image_policies.get(url)
            result.append((url, source, policy) if with_policy else (url, source))
            seen.add(url)
    return result


def supplemental_images(markup: str, article: str, fetch) -> list[tuple[str, str]]:
    """Small, explicit adapters for publishers whose initial HTML contains no article."""
    parts = urlsplit(article)
    if parts.hostname == 'sanhao-design-weekly.pages.dev':
        issue = parse_qs(parts.query).get('issue', [''])[0]
        if not issue.isdigit():
            return []
        parser = CoverParser(article)
        parser.feed(markup)
        scripts = [url for url in parser.scripts if urlsplit(url).netloc == parts.netloc and urlsplit(url).path == '/script.js']
        if not scripts:
            return []
        body, _, final = fetch(scripts[0], limit=1024 * 1024)
        if urlsplit(final).netloc != parts.netloc:
            return []
        script = body.decode('utf-8', errors='replace')
        # Parse only the literal issue block and lead image; never evaluate remote JavaScript.
        block = re.search(r'^  [\'"]?' + re.escape(issue) + r'[\'"]?:\s*\{(.*?)(?=^  [\'"]?\d+[\'"]?:\s*\{|^};)', script, re.M | re.S)
        if not block or not re.search(r'issue:\s*"ISSUE\s+0*' + re.escape(issue) + r'"', block[1]):
            return []
        lead = re.search(r'\blead:\s*\{(.*?)^    \}', block[1], re.M | re.S)
        match = re.search(r'\bimage:\s*("(?:[^"\\]|\\.)*")', lead[1]) if lead else None
        if match:
            image = image_url(json.loads(match[1]), article)
            if image and re.search(r'/vol0*' + re.escape(issue) + r'[-_.]', urlsplit(image).path):
                return [(image, 'issue-script')]
    if parts.hostname in ('t.me', 'telegram.me') and re.fullmatch(r'/[A-Za-z0-9_]+/\d+/?', parts.path):
        embed = parts._replace(query='embed=1&mode=tme', fragment='').geturl()
        body, kind, final = fetch(embed, limit=2 * 1024 * 1024)
        if kind == 'text/html' and page_key(final)[:2] == page_key(article)[:2]:
            return [(url, source) for url, source in page_images(body.decode('utf-8', errors='replace'), final) if source == 'telegram-photo']
    return []
