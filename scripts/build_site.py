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


def build_html(data: list, style: dict, styles_list: list) -> str:
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

            search_text = f"{name} {desc} {latest_text}".lower()

            feed_cards += f'''
            <div class="feed-card" data-recent="{"true" if has_news else "false"}" data-search="{escape_attr(search_text)}">
                <div class="feed-header">
                    <h3 class="feed-name">{escape_html(name)} {news_badge}</h3>
                    <span class="feed-date">{pub_date}</span>
                </div>
                <p class="feed-desc" title="{escape_html(desc)}">{escape_html(desc)}</p>
                <div class="feed-links">
                    <a href="{escape_attr(latest_url)}" target="_blank" rel="noopener" class="link-latest" title="{escape_html(latest_text) or "最新文章"}">
                        <i class="far fa-file-alt"></i> {escape_html(latest_text) or "最新文章"}
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
                <h2 class="category-title">
                    {escape_html(cat_name)}
                    <span class="category-badge">{count}</span>
                </h2>
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
    styles_json = json.dumps(styles_list)

    theme_options = ""
    for s in styles_list:
        selected = 'selected' if s["name"] == style["name"] else ''
        theme_options += f'<option value="{escape_attr(s["name"])}" {selected}>{escape_html(s["name"])}</option>'

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
        
        html {{
            scroll-behavior: smooth;
            scroll-padding-top: 170px;
        }}
        
        body, header, .nav, .feed-card, .nav-item, select, input, button, a {{
            transition: background 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
        }}
        
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
            box-shadow: 0 2px 10px var(--shadow);
        }}
        .header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            gap: 16px;
        }}
        .header-left {{
            display: flex;
            flex-direction: column;
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
        
        .header-right {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .stats {{
            display: flex;
            gap: 16px;
            font-size: 0.85rem;
            color: var(--muted);
        }}
        .stats span {{ display: flex; align-items: center; gap: 6px; }}

        .theme-selector-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--muted);
        }}
        .theme-selector-container select {{
            padding: 6px 24px 6px 10px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--card-bg);
            color: var(--text);
            font-family: var(--font-body);
            font-size: 0.85rem;
            cursor: pointer;
            outline: none;
            appearance: none;
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml;utf8,<svg fill='none' stroke='currentColor' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'><path d='m6 9 6 6 6-6'></path></svg>");
            background-repeat: no-repeat;
            background-position: right 8px center;
            background-size: 14px;
        }}
        .theme-selector-container select:hover {{
            border-color: var(--accent);
        }}

        .search-bar-container {{
            border-top: 1px solid var(--border);
            padding: 10px 0;
            background: var(--card-bg);
        }}
        .search-inner {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .search-box {{
            position: relative;
            flex: 1;
        }}
        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--muted);
        }}
        .search-input {{
            width: 100%;
            padding: 10px 14px 10px 40px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg);
            color: var(--text);
            font-family: var(--font-body);
            font-size: 0.95rem;
            outline: none;
        }}
        .search-input:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
        }}
        
        .filter-btn {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 10px 16px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg);
            color: var(--text);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            white-space: nowrap;
        }}
        .filter-btn:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        .filter-btn.active {{
            background: var(--accent);
            color: #ffffff;
            border-color: var(--accent);
        }}

        .nav {{
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
            overflow-x: auto;
            white-space: nowrap;
            -webkit-overflow-scrolling: touch;
            position: sticky;
            top: 121px;
            z-index: 95;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
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
            border: 1px solid transparent;
        }}
        .nav-item:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        .nav-item.active {{
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
        }}

        main {{ padding: 32px 0 48px; }}
        .category {{ margin-bottom: 40px; }}
        .category-header {{
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}
        .category-title {{
            font-family: var(--font-title);
            font-size: 1.4rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .category-badge {{
            display: inline-block;
            font-size: 0.8rem;
            background: var(--category-bg);
            color: var(--category-text);
            padding: 2px 10px;
            border-radius: 20px;
            font-weight: 600;
        }}

        .feeds-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        @media (min-width: 640px) {{ .feeds-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (min-width: 1024px) {{ .feeds-grid {{ grid-template-columns: repeat(3, 1fr); }} }}

        .feed-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 5px var(--shadow);
        }}
        .feed-card:hover {{
            box-shadow: 0 8px 24px var(--shadow);
            transform: translateY(-4px);
            border-color: var(--accent);
        }}
        .feed-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .feed-name {{
            font-family: var(--font-title);
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.4;
            flex: 1;
        }}
        .feed-date {{
            font-size: 0.75rem;
            color: var(--muted);
            white-space: nowrap;
            margin-top: 4px;
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
            box-shadow: 0 0 8px var(--accent);
            animation: pulse-accent 2s infinite;
        }}
        @keyframes pulse-accent {{
            0% {{ box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.4); }}
            70% {{ box-shadow: 0 0 0 6px rgba(13, 110, 253, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(13, 110, 253, 0); }}
        }}
        
        .feed-desc {{
            font-size: 0.9rem;
            color: var(--muted);
            margin-bottom: 16px;
            line-height: 1.6;
            flex: 1;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .feed-links {{
            display: flex;
            gap: 10px;
            margin-top: auto;
        }}
        .feed-links a {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            text-decoration: none;
            padding: 8px 12px;
            border-radius: var(--radius);
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .link-latest {{
            background: var(--accent);
            color: #ffffff !important;
            border: 1px solid var(--accent);
        }}
        .link-latest:hover {{
            background: var(--accent-hover);
            border-color: var(--accent-hover);
            box-shadow: 0 4px 10px var(--shadow);
        }}
        .link-home {{
            background: var(--bg);
            color: var(--text) !important;
            border: 1px solid var(--border);
        }}
        .link-home:hover {{
            background: var(--category-bg);
            border-color: var(--accent);
        }}
        .feed-links i {{ font-size: 0.8rem; }}

        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
        }}
        .no-results-icon {{
            font-size: 3rem;
            margin-bottom: 16px;
            color: var(--accent);
            opacity: 0.6;
        }}
        .no-results h3 {{
            font-size: 1.25rem;
            margin-bottom: 8px;
            color: var(--text);
        }}

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
            z-index: 200;
        }}
        .back-to-top:hover {{ background: var(--accent-hover); transform: scale(1.05); }}
        .back-to-top.visible {{ display: flex; }}

        .style-tag {{
            position: fixed;
            bottom: 24px;
            left: 24px;
            font-size: 0.7rem;
            color: var(--muted);
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 4px 10px;
            border-radius: var(--radius);
            z-index: 150;
            opacity: 0.7;
            box-shadow: 0 2px 5px var(--shadow);
        }}

        @media (max-width: 767px) {{
            .header-inner {{
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
                padding: 12px 0;
            }}
            .header-right {{
                width: 100%;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
            }}
            .search-inner {{
                flex-direction: column;
                align-items: stretch;
            }}
            .filter-btn {{
                justify-content: center;
            }}
            .nav {{
                top: 162px;
            }}
            html {{
                scroll-padding-top: 210px;
            }}
        }}
    </style>
</head>
<body>
    <div class="style-tag">{escape_html(style["name"])}</div>
    <header>
        <div class="container header-inner">
            <div class="header-left">
                <div class="site-title">中文技术周刊精选</div>
                <div class="site-subtitle">awesome-tech-weekly-zh</div>
            </div>
            <div class="header-right">
                <div class="stats">
                    <span><i class="fas fa-layer-group"></i> {total_cats} 分类</span>
                    <span><i class="fas fa-rss"></i> {total_feeds} 周刊</span>
                </div>
                <div class="theme-selector-container">
                    <i class="fas fa-palette"></i>
                    <select id="themeSelect" onchange="changeTheme(this.value)" aria-label="主题切换">
                        {theme_options}
                    </select>
                </div>
            </div>
        </div>
        <div class="search-bar-container">
            <div class="container search-inner">
                <div class="search-box">
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" id="searchInput" class="search-input" placeholder="搜索周刊名称、描述、最新文章标题..." oninput="handleSearch()">
                </div>
                <button id="btnRecent" class="filter-btn" onclick="toggleRecentFilter()">
                    <i class="far fa-clock"></i> 最近更新 (7天内)
                </button>
            </div>
        </div>
    </header>
    <nav class="nav">
        <div class="container nav-inner">
            {nav_items}
        </div>
    </nav>
    <main class="container">
        <div id="noResults" class="no-results" style="display: none;">
            <i class="fas fa-search-minus no-results-icon"></i>
            <h3>没有找到匹配的周刊</h3>
            <p>请尝试更换搜索关键词或关闭“最近更新”过滤器</p>
        </div>
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
        const STYLES = {styles_json};

        function changeTheme(themeName) {{
            const style = STYLES.find(s => s.name === themeName);
            if (!style) return;
            
            const root = document.documentElement;
            root.style.setProperty('--bg', style.bg);
            root.style.setProperty('--card-bg', style.card_bg);
            root.style.setProperty('--text', style.text);
            root.style.setProperty('--muted', style.muted);
            root.style.setProperty('--accent', style.accent);
            root.style.setProperty('--accent-hover', style.accent_hover);
            root.style.setProperty('--border', style.border);
            root.style.setProperty('--header-bg', style.header_bg);
            root.style.setProperty('--shadow', style.shadow);
            root.style.setProperty('--font-title', style.font_title);
            root.style.setProperty('--font-body', style.font_body);
            root.style.setProperty('--radius', style.radius);
            root.style.setProperty('--category-bg', style.category_bg);
            root.style.setProperty('--category-text', style.category_text);

            const tag = document.querySelector('.style-tag');
            if (tag) tag.textContent = style.name;

            localStorage.setItem('selected-theme', themeName);
            
            const select = document.getElementById('themeSelect');
            if (select) select.value = themeName;
            
            // Adjust keyframe pulse animation base color dynamically
            const styleSheet = document.createElement("style");
            styleSheet.innerText = `@keyframes pulse-accent {{
                0% {{ box-shadow: 0 0 0 0 ${{style.accent}}66; }}
                70% {{ box-shadow: 0 0 0 6px ${{style.accent}}00; }}
                100% {{ box-shadow: 0 0 0 0 ${{style.accent}}00; }}
            }}`;
            document.head.appendChild(styleSheet);
        }}

        function handleSearch() {{
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const showRecentOnly = document.getElementById('btnRecent').classList.contains('active');
            let totalVisible = 0;

            document.querySelectorAll('section.category').forEach(section => {{
                let visibleInCat = 0;
                section.querySelectorAll('.feed-card').forEach(card => {{
                    const searchText = card.getAttribute('data-search') || '';
                    const isRecent = card.getAttribute('data-recent') === 'true';
                    
                    const matchesSearch = searchText.includes(query);
                    const matchesRecent = !showRecentOnly || isRecent;
                    
                    if (matchesSearch && matchesRecent) {{
                        card.style.display = 'flex';
                        visibleInCat++;
                        totalVisible++;
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                
                const id = section.getAttribute('id');
                const navLink = document.querySelector('a[href="#' + id + '"]');
                if (visibleInCat > 0) {{
                    section.style.display = 'block';
                    if (navLink) navLink.style.display = 'inline-block';
                }} else {{
                    section.style.display = 'none';
                    if (navLink) navLink.style.display = 'none';
                }}
            }});

            const noResults = document.getElementById('noResults');
            if (totalVisible === 0) {{
                noResults.style.display = 'block';
            }} else {{
                noResults.style.display = 'none';
            }}
        }}

        function toggleRecentFilter() {{
            const btn = document.getElementById('btnRecent');
            btn.classList.toggle('active');
            handleSearch();
        }}

        // Back to top
        const btn = document.getElementById('backToTop');
        window.addEventListener('scroll', () => {{
            btn.classList.toggle('visible', window.scrollY > 300);
        }});
        btn.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});

        // ScrollSpy category navigation
        const observerOptions = {{
            root: null,
            rootMargin: '-180px 0px -55% 0px',
            threshold: 0
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const id = entry.target.getAttribute('id');
                    document.querySelectorAll('.nav-item').forEach(item => {{
                        const href = item.getAttribute('href');
                        if (href === '#' + id) {{
                            item.classList.add('active');
                            item.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                        }} else {{
                            item.classList.remove('active');
                        }}
                    }});
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('section.category').forEach(section => {{
            observer.observe(section);
        }});

        // On Load initialization
        window.addEventListener('DOMContentLoaded', () => {{
            const savedTheme = localStorage.getItem('selected-theme');
            if (savedTheme) {{
                changeTheme(savedTheme);
            }}
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
    print(f"Selected initial style: {style['name']}")

    html = build_html(data, style, STYLES)

    index_path = site_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated site at {index_path}")


if __name__ == "__main__":
    main()

