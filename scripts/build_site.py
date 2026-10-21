#!/usr/bin/env python3
"""Build the newsletter directory and RSS feed using only the Python standard library."""

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from covers import prepare_covers

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://yeshan333.github.io/awesome-tech-weekly-zh"


def parse_md_link(text: str) -> tuple[str, str] | None:
    # README metadata can append a news badge after the link.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text or "").strip()
    match = re.match(r"\[(.*?)\]\((.*)\)$", text)
    return (match[1], match[2]) if match else None


def safe_url(value: str) -> str:
    """Only emit web links; configuration data must never become executable markup."""
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ("https", "http") and parsed.netloc else ""
    except ValueError:
        return ""


def parse_date(value: str) -> datetime | None:
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date.replace(tzinfo=date.tzinfo or timezone.utc).astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        return None


def normalize(data: list, now: datetime) -> list:
    categories = []
    for index, category in enumerate(data):
        feeds = []
        for feed in category["feeds"]:
            home = parse_md_link(feed.get("link", ""))
            home_url = safe_url(home[1] if home else feed.get("link", ""))
            latest = parse_md_link(feed.get("latest_post", ""))
            latest_url = safe_url(latest[1]) if latest else ""
            has_article = bool(latest and latest_url and latest_url != home_url)
            date = parse_date(feed.get("published_date", "")) if has_article else None
            feeds.append({
                "name": feed.get("name", ""), "desc": feed.get("desc", ""),
                "home": home_url, "url": latest_url if has_article else "",
                "title": latest[0] if has_article else "", "date": date,
                "cover_url": safe_url(feed.get("cover_url", "")),
                "cover_urls": [safe_url(url) for url in feed.get("cover_urls", []) if isinstance(url, str)] if isinstance(feed.get("cover_urls"), list) else [],
                "recent": bool(date and now - timedelta(days=7) <= date <= now),
                "category": category["category"], "category_id": f"category-{index}",
            })
        categories.append({"name": category["category"], "id": f"category-{index}", "feeds": feeds})
    return categories


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def link(url: str, label: str, css: str = "", extra: str = "") -> str:
    if not url:
        return f'<span class="{css}">{label}</span>'
    return f'<a class="{css}" href="{esc(url)}" target="_blank" rel="noopener noreferrer" {extra}>{label}</a>'


def editorial_image(feed: dict) -> str:
    """Select a locally hosted topic illustration, independent of article scraping."""
    if feed["category"] == "AI":
        return "ai"
    if feed["category"] == "产品-体验-设计":
        return "discovery"
    if feed["category"] == "其他":
        return "community" if any(word in feed["name"].lower() for word in ("news", "新闻", "摘要")) else "discovery"
    return "systems"


def build_html(data: list, now: datetime | None = None, covers: dict | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    categories = normalize(data, now)
    feeds = [feed for cat in categories for feed in cat["feeds"]]
    articles = sorted((f for f in feeds if f["url"] and f["date"]), key=lambda f: f["date"], reverse=True)[:10]
    recent_count = sum(f["recent"] for f in feeds)
    nav = ['<a class="nav-item" href="#directory" data-test="nav-item" data-category="all" aria-current="true">全部周刊</a>']
    sections = []
    for cat in categories:
        nav.append(f'<a class="nav-item" href="#{cat["id"]}" data-test="nav-item" data-category="{cat["id"]}">{esc(cat["name"])}</a>')
        rows = []
        for feed in cat["feeds"]:
            search = esc(f'{feed["name"]} {feed["desc"]} {feed["title"]} {feed["category"]}'.lower())
            published = feed["date"].isoformat() if feed["date"] else ""
            date_label = feed["date"].strftime("%Y-%m-%d") if feed["date"] else "暂无发布日期"
            status = '<span class="recent-mark">7 天内更新</span>' if feed["recent"] else ""
            latest = link(feed["url"], esc(feed["title"]), "article-link") if feed["url"] else '<p class="missing">暂无最新文章，可前往周刊主页阅读。</p>'
            rows.append(f'''<article class="feed-row" data-test="feed-card" data-category="{cat['id']}" data-search="{search}" data-published="{published}" data-recent="{str(feed['recent']).lower()}">
                <div class="feed-identity"><h3>{link(feed['home'], esc(feed['name']), 'feed-name', 'data-test="feed-card-link"')}</h3><p class="feed-description">{esc(feed['desc'])}</p></div>
                <div class="feed-article"><div class="feed-meta"><time datetime="{published}">{date_label}</time>{status}</div>{latest}</div>
                {link(feed['home'], '主页 <span aria-hidden="true">↗</span>', 'home-link', f'aria-label="{esc(feed["name"])}主页"')}
            </article>''')
        sections.append(f'''<section class="category" id="{cat['id']}"><div class="category-heading"><h2>{esc(cat['name'])}</h2><span class="category-count">{len(cat['feeds'])} 份周刊</span></div>{''.join(rows)}</section>''')

    featured = []
    for index, feed in enumerate(articles):
        fallback = f'images/{editorial_image(feed)}.webp'
        cover = (covers or {}).get(feed['url'], {}).get('path') or fallback
        loading = 'loading="eager" fetchpriority="high"' if index == 0 else ('loading="eager"' if index < 3 else 'loading="lazy"')
        featured.append(f'''<article class="featured-card" data-test="featured-card" data-active="{str(index == 0).lower()}">
            <img class="featured-image" src="{esc(cover)}" data-fallback="{fallback}" width="960" height="640" alt="" {loading} decoding="async">
            <div class="featured-body">
            <div class="featured-meta"><span>{esc(feed['category'])}</span><time datetime="{feed['date'].isoformat()}">{feed['date'].strftime('%Y-%m-%d')}</time></div>
            <p class="featured-name">{esc(feed['name'])}</p>
            {link(feed['url'], esc(feed['title']), 'featured-title', f'title="{esc(feed["title"])}"')}
            <span class="read-cue" aria-hidden="true">阅读这一期 ↗</span>
            </div>
        </article>''')
    featured_html = f'''<section class="latest-section" aria-labelledby="latestTitle">
        <div class="section-heading"><div><h2 id="latestTitle">最新一期</h2><p>来自各个技术领域，按发布时间排列。</p></div>
        <div class="carousel-controls js-only"><button type="button" class="icon-button" id="previousArticle" data-test="carousel-prev" aria-label="上一篇">←</button><button type="button" class="icon-button" id="nextArticle" data-test="carousel-next" aria-label="下一篇">→</button></div></div>
        <div class="featured-track" data-test="featured" id="featuredTrack" tabindex="0" aria-label="最新文章，可左右滚动">{''.join(featured)}</div>
        <div class="carousel-pagination js-only"><span id="articlePosition" aria-live="polite">1 / {len(featured)}</span><div id="articleDots" class="carousel-dots"></div></div>
        </section>''' if articles else ""
    newest = max((f["date"] for f in feeds if f["date"]), default=None)
    replacements = {
        "total": str(len(feeds)), "category_total": str(len(categories)), "recent_total": str(recent_count),
        "newest": newest.strftime("%Y-%m-%d") if newest else "暂无发布日期",
        "generated": now.strftime("%Y-%m-%d %H:%M UTC"), "generated_iso": now.isoformat(),
        "navigation": "".join(nav), "categories": "".join(sections), "featured": featured_html,
    }
    return Template((ROOT / "template/site/index.html").read_text()).substitute(replacements)


def build_feed_xml(data: list, site_url: str = SITE_URL, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for key, value in {"title": "中文技术周刊精选 - awesome-tech-weekly-zh", "link": site_url,
                       "description": "汇聚各技术领域优质中文周刊的最新一期", "language": "zh-CN",
                       "lastBuildDate": format_datetime(now)}.items():
        ET.SubElement(channel, key).text = value
    feeds = [f for cat in normalize(data, now) for f in cat["feeds"] if f["url"]]
    feeds.sort(key=lambda f: f["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    for feed in feeds:
        item = ET.SubElement(channel, "item")
        for key, value in {"title": f'[{feed["category"]}] {feed["name"]} - {feed["title"]}',
                           "link": feed["url"], "description": feed["desc"]}.items():
            ET.SubElement(item, key).text = value
        ET.SubElement(item, "guid", isPermaLink="true").text = feed["url"]
        if feed["date"]:
            ET.SubElement(item, "pubDate").text = format_datetime(feed["date"])
    ET.indent(rss)
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-only", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "site")
    parser.add_argument("--site-url", default=SITE_URL)
    parser.add_argument("--fetch-covers", action="store_true", help="Fetch current issue images; otherwise reuse local cache")
    parser.add_argument("--force-cover-refresh", action="store_true", help="Recheck all current images without waiting for cache expiry")
    parser.add_argument("--cover-cache-dir", type=Path, default=ROOT / ".cover-cache")
    args = parser.parse_args()
    data = json.loads((ROOT / "README.json").read_text())
    now = datetime.now(timezone.utc)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "feed.xml").write_text(build_feed_xml(data, args.site_url, now), encoding="utf-8")
    if not args.feed_only:
        feeds = [feed for category in normalize(data, now) for feed in category['feeds']]
        covers = prepare_covers(feeds, args.output_dir, args.cover_cache_dir, refresh=args.fetch_covers or args.force_cover_refresh, force=args.force_cover_refresh)
        (args.output_dir / "index.html").write_text(build_html(data, now, covers), encoding="utf-8")
        for name in ("site.css", "site.js", "theme.js", "mark.svg"):
            shutil.copy2(ROOT / "template/site" / name, args.output_dir / name)
        shutil.copytree(ROOT / "template/site/fonts", args.output_dir / "fonts", dirs_exist_ok=True)
        (args.output_dir / "images").mkdir(exist_ok=True)
        for image in (ROOT / "template/site/images").glob("*.webp"):
            shutil.copy2(image, args.output_dir / "images" / image.name)
        (args.output_dir / ".nojekyll").touch()
    print(f"Generated {'RSS' if args.feed_only else 'site and RSS'} at {args.output_dir}")


if __name__ == "__main__":
    main()
