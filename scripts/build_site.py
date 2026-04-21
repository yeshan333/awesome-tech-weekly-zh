#!/usr/bin/env python3
"""Build static site for awesome-tech-weekly-zh from README.json."""

import json
import random
import re
import os
from datetime import datetime
from pathlib import Path

STYLES = [
    {
        "name": "Modern Clean",
        "bg": "#f8f9fa",
        "card_bg": "#ffffff",
        "text": "#212529",
        "muted": "#6c757d",
        "accent": "#0d6efd",
        "accent_hover": "#0b5ed7",
        "border": "#dee2e6",
        "header_bg": "#ffffff",
        "shadow": "rgba(0,0,0,0.08)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "12px",
        "category_bg": "#e9ecef",
        "category_text": "#495057",
    },
    {
        "name": "Classic Print",
        "bg": "#faf8f5",
        "card_bg": "#fffefc",
        "text": "#2c241b",
        "muted": "#8a7e72",
        "accent": "#8b4513",
        "accent_hover": "#6b3410",
        "border": "#d4c8b8",
        "header_bg": "#faf8f5",
        "shadow": "rgba(44,36,27,0.06)",
        "font_title": "'Noto Serif SC', serif",
        "font_body": "'Noto Serif SC', serif",
        "radius": "4px",
        "category_bg": "#efe8df",
        "category_text": "#5a4d3f",
    },
    {
        "name": "Japanese Minimalism",
        "bg": "#f5f5f0",
        "card_bg": "#ffffff",
        "text": "#333333",
        "muted": "#999999",
        "accent": "#c0392b",
        "accent_hover": "#a93226",
        "border": "#e0e0e0",
        "header_bg": "#ffffff",
        "shadow": "rgba(0,0,0,0.04)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "2px",
        "category_bg": "#eeeeee",
        "category_text": "#666666",
    },
    {
        "name": "Scandinavian",
        "bg": "#f0f4f3",
        "card_bg": "#ffffff",
        "text": "#2d3436",
        "muted": "#74b9ff",
        "accent": "#00b894",
        "accent_hover": "#00a383",
        "border": "#dfe6e9",
        "header_bg": "#ffffff",
        "shadow": "rgba(45,52,54,0.06)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "16px",
        "category_bg": "#e8f5e9",
        "category_text": "#2e7d32",
    },
    {
        "name": "Swiss International Style",
        "bg": "#ffffff",
        "card_bg": "#ffffff",
        "text": "#000000",
        "muted": "#666666",
        "accent": "#e74c3c",
        "accent_hover": "#c0392b",
        "border": "#000000",
        "header_bg": "#ffffff",
        "shadow": "rgba(0,0,0,0.1)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "0px",
        "category_bg": "#000000",
        "category_text": "#ffffff",
    },
    {
        "name": "Bauhaus",
        "bg": "#f4f1ea",
        "card_bg": "#ffffff",
        "text": "#1a1a1a",
        "muted": "#7a7a7a",
        "accent": "#d35400",
        "accent_hover": "#ba4a00",
        "border": "#333333",
        "header_bg": "#f4f1ea",
        "shadow": "rgba(0,0,0,0.12)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "0px",
        "category_bg": "#2c3e50",
        "category_text": "#f1c40f",
    },
    {
        "name": "Constructivism",
        "bg": "#e8e6e1",
        "card_bg": "#ffffff",
        "text": "#1a1a1a",
        "muted": "#555555",
        "accent": "#c0392b",
        "accent_hover": "#a93226",
        "border": "#1a1a1a",
        "header_bg": "#d4cfc7",
        "shadow": "rgba(0,0,0,0.15)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "0px",
        "category_bg": "#c0392b",
        "category_text": "#ffffff",
    },
    {
        "name": "Minimalist",
        "bg": "#ffffff",
        "card_bg": "#fafafa",
        "text": "#111111",
        "muted": "#888888",
        "accent": "#111111",
        "accent_hover": "#333333",
        "border": "#eeeeee",
        "header_bg": "#ffffff",
        "shadow": "rgba(0,0,0,0.03)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "8px",
        "category_bg": "#f0f0f0",
        "category_text": "#444444",
    },
    {
        "name": "Elegant Vintage",
        "bg": "#f7f3eb",
        "card_bg": "#fffcf7",
        "text": "#3d2b1f",
        "muted": "#9c8b7a",
        "accent": "#8e44ad",
        "accent_hover": "#7d3c98",
        "border": "#d5c9b8",
        "header_bg": "#f7f3eb",
        "shadow": "rgba(61,43,31,0.08)",
        "font_title": "'Noto Serif SC', serif",
        "font_body": "'Noto Serif SC', serif",
        "radius": "6px",
        "category_bg": "#e8e0d4",
        "category_text": "#5d4e3f",
    },
    {
        "name": "Bold Modern",
        "bg": "#0f0f0f",
        "card_bg": "#1a1a1a",
        "text": "#f0f0f0",
        "muted": "#999999",
        "accent": "#f39c12",
        "accent_hover": "#e67e22",
        "border": "#333333",
        "header_bg": "#0f0f0f",
        "shadow": "rgba(255,255,255,0.05)",
        "font_title": "'Noto Sans SC', sans-serif",
        "font_body": "'Noto Sans SC', sans-serif",
        "radius": "10px",
        "category_bg": "#2a2a2a",
        "category_text": "#cccccc",
    },
]


def parse_md_link(text: str) -> tuple[str, str] | None:
    """Parse markdown link [text](url) -> (text, url)."""
    if not text:
        return None
    m = re.match(r'\[(.*?)\]\((.*?)\)', text.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def strip_md_link(text: str) -> str:
    """Remove markdown link syntax, keep text only."""
    parsed = parse_md_link(text)
    if parsed:
        return parsed[0]
    return text or ""


def extract_url(text: str) -> str:
    """Extract URL from markdown link."""
    parsed = parse_md_link(text)
    if parsed:
        return parsed[1]
    return text or "#"


def format_date(iso_str: str) -> str:
    if not iso_str:
        return "未知"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


def build_html(data: list, style: dict) -> str:
    total_feeds = sum(len(cat["feeds"]) for cat in data)
    total_cats = len(data)

    categories_html = ""
    for cat in data:
        cat_name = cat["category"]
        feeds = cat["feeds"]
        count = len(feeds)
        feed_cards = ""
        for feed in feeds:
            name = feed.get("name", "")
            desc = feed.get("desc", "")
            latest = feed.get("latest_post", "")
            link = feed.get("link", "")
            pub_date = format_date(feed.get("published_date", ""))

            latest_text = strip_md_link(latest)
            latest_url = extract_url(latest)
            link_text = strip_md_link(link)
            link_url = extract_url(link)

            has_news = "![news]" in latest
            news_badge = '<span class="news-badge">NEW</span>' if has_news else ""
            # Remove the news image tag from display text
            latest_text = re.sub(r'!\[.*?\]\(.*?\)', '', latest_text).strip()

            feed_cards += f'''
            <div class="feed-card">
                <div class="feed-header">
                    <h3 class="feed-name">{escape_html(name)} {news_badge}</h3>
                    <span class="feed-date">{pub_date}</span>
                </div>
                <p class="feed-desc">{escape_html(desc)}</p>
                <div class="feed-links">
                    <a href="{escape_attr(latest_url)}" target="_blank" rel="noopener" class="link-latest">
                        <i class="fas fa-file-alt"></i> {escape_html(latest_text) or "最新文章"}
                    </a>
                    <a href="{escape_attr(link_url)}" target="_blank" rel="noopener" class="link-home">
                        <i class="fas fa-external-link-alt"></i> {escape_html(link_text) or "主页"}
                    </a>
                </div>
            </div>
            '''

        categories_html += f'''
        <section class="category" id="cat-{cat_name.lower().replace(" ", "-")}">
            <div class="category-header">
                <h2 class="category-title">{escape_html(cat_name)}</h2>
                <span class="category-count">{count} 个周刊</span>
            </div>
            <div class="feeds-grid">
                {feed_cards}
            </div>
        </section>
        '''

    nav_items = ""
    for cat in data:
        cat_name = cat["category"]
        nav_items += f'<a href="#cat-{cat_name.lower().replace(" ", "-")}" class="nav-item">{escape_html(cat_name)}</a>'

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中文技术周刊精选 - awesome-tech-weekly-zh</title>
    <link rel="stylesheet" href="https://lf6-cdn-tos.bytecdntp.com/cdn/expire-100-M/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: {style["bg"]};
            --card-bg: {style["card_bg"]};
            --text: {style["text"]};
            --muted: {style["muted"]};
            --accent: {style["accent"]};
            --accent-hover: {style["accent_hover"]};
            --border: {style["border"]};
            --header-bg: {style["header_bg"]};
            --shadow: {style["shadow"]};
            --font-title: {style["font_title"]};
            --font-body: {style["font_body"]};
            --radius: {style["radius"]};
            --category-bg: {style["category_bg"]};
            --category-text: {style["category_text"]};
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: var(--font-body);
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            font-size: 15px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 16px; }}
        @media (min-width: 768px) {{ .container {{ padding: 0 24px; }} }}
        @media (min-width: 1024px) {{ .container {{ padding: 0 32px; }} }}

        header {{
            background: var(--header-bg);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .site-title {{
            font-family: var(--font-title);
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
        }}
        .site-subtitle {{
            font-size: 0.85rem;
            color: var(--muted);
            margin-top: 2px;
        }}
        .stats {{
            display: flex;
            gap: 16px;
            font-size: 0.85rem;
            color: var(--muted);
        }}
        .stats span {{ display: flex; align-items: center; gap: 4px; }}

        .nav {{
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
            overflow-x: auto;
            white-space: nowrap;
            -webkit-overflow-scrolling: touch;
        }}
        .nav-inner {{ display: flex; gap: 8px; }}
        .nav-item {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: var(--radius);
            background: var(--category-bg);
            color: var(--category-text);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}
        .nav-item:hover {{
            background: var(--accent);
            color: #fff;
        }}

        main {{ padding: 32px 0 48px; }}
        .category {{ margin-bottom: 40px; }}
        .category-header {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}
        .category-title {{
            font-family: var(--font-title);
            font-size: 1.4rem;
            font-weight: 700;
        }}
        .category-count {{
            font-size: 0.85rem;
            color: var(--muted);
        }}

        .feeds-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
        }}
        @media (min-width: 640px) {{ .feeds-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (min-width: 1024px) {{ .feeds-grid {{ grid-template-columns: repeat(3, 1fr); }} }}

        .feed-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            transition: box-shadow 0.2s, transform 0.2s;
            display: flex;
            flex-direction: column;
        }}
        .feed-card:hover {{
            box-shadow: 0 4px 20px var(--shadow);
            transform: translateY(-2px);
        }}
        .feed-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 8px;
        }}
        .feed-name {{
            font-family: var(--font-title);
            font-size: 1.05rem;
            font-weight: 600;
            line-height: 1.4;
            flex: 1;
        }}
        .feed-date {{
            font-size: 0.75rem;
            color: var(--muted);
            white-space: nowrap;
        }}
        .news-badge {{
            display: inline-block;
            background: var(--accent);
            color: #fff;
            font-size: 0.65rem;
            padding: 1px 6px;
            border-radius: 10px;
            margin-left: 4px;
            vertical-align: middle;
            font-weight: 700;
        }}
        .feed-desc {{
            font-size: 0.9rem;
            color: var(--muted);
            margin-bottom: 12px;
            line-height: 1.6;
            flex: 1;
        }}
        .feed-links {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .feed-links a {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            text-decoration: none;
            padding: 4px 0;
            transition: color 0.2s;
        }}
        .link-latest {{ color: var(--accent); }}
        .link-latest:hover {{ color: var(--accent-hover); text-decoration: underline; }}
        .link-home {{ color: var(--muted); }}
        .link-home:hover {{ color: var(--text); text-decoration: underline; }}
        .feed-links i {{ font-size: 0.8rem; width: 14px; text-align: center; }}

        footer {{
            border-top: 1px solid var(--border);
            padding: 24px 0;
            text-align: center;
            font-size: 0.85rem;
            color: var(--muted);
        }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        footer a:hover {{ text-decoration: underline; }}

        .back-to-top {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--accent);
            color: #fff;
            border: none;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            box-shadow: 0 2px 12px var(--shadow);
            transition: background 0.2s, transform 0.2s;
            z-index: 200;
        }}
        .back-to-top:hover {{ background: var(--accent-hover); transform: scale(1.05); }}
        .back-to-top.visible {{ display: flex; }}

        .style-tag {{
            position: fixed;
            top: 12px;
            right: 12px;
            font-size: 0.7rem;
            color: var(--muted);
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 2px 8px;
            border-radius: var(--radius);
            z-index: 150;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="style-tag">{escape_html(style["name"])}</div>
    <header>
        <div class="container header-inner">
            <div>
                <div class="site-title">中文技术周刊精选</div>
                <div class="site-subtitle">awesome-tech-weekly-zh</div>
            </div>
            <div class="stats">
                <span><i class="fas fa-layer-group"></i> {total_cats} 分类</span>
                <span><i class="fas fa-rss"></i> {total_feeds} 周刊</span>
            </div>
        </div>
    </header>
    <nav class="nav">
        <div class="container nav-inner">
            {nav_items}
        </div>
    </nav>
    <main class="container">
        {categories_html}
    </main>
    <footer>
        <div class="container">
            <p>数据来源于 <a href="https://github.com/yeshan333/awesome-tech-weekly-zh" target="_blank" rel="noopener">awesome-tech-weekly-zh</a></p>
            <p style="margin-top:4px">生成于 {generated_at}</p>
        </div>
    </footer>
    <button class="back-to-top" id="backToTop" aria-label="回到顶部">
        <i class="fas fa-arrow-up"></i>
    </button>
    <script>
        const btn = document.getElementById('backToTop');
        window.addEventListener('scroll', () => {{
            btn.classList.toggle('visible', window.scrollY > 300);
        }});
        btn.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    </script>
</body>
</html>'''


def escape_html(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def escape_attr(text: str) -> str:
    return text.replace('"', "&quot;").replace("'", "&#39;")


def main():
    repo_root = Path(__file__).parent.parent
    readme_json = repo_root / "README.json"
    site_dir = repo_root / "site"
    site_dir.mkdir(exist_ok=True)

    with open(readme_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    style = random.choice(STYLES)
    print(f"Selected style: {style['name']}")

    html = build_html(data, style)

    index_path = site_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated site at {index_path}")


if __name__ == "__main__":
    main()
