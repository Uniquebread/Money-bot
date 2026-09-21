"""
Turns a list of scored/categorized items into:
  1. Telegram message text (HTML-lite formatting Telegram supports)
  2. A full HTML page for the website archive
"""
from datetime import datetime, timezone
from html import escape

import config


def _group_by_category(items):
    grouped = {}
    for item in items:
        grouped.setdefault(item["category"], []).append(item)
    return grouped


def build_telegram_message(items, run_time=None):
    run_time = run_time or datetime.now(timezone.utc)
    if not items:
        return (
            f"<b>Money Bot Digest</b>\n"
            f"{run_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"No new opportunities this run. Quiet couple of hours."
        )

    grouped = _group_by_category(items)
    lines = [
        f"<b>\U0001F4B0 Money Bot Digest</b>",
        f"{run_time.strftime('%Y-%m-%d %H:%M UTC')} \u2022 {len(items)} new item(s)",
        "",
    ]
    for category, cat_items in grouped.items():
        lines.append(f"<b>{escape(category)}</b>")
        for item in cat_items[: config.MAX_ITEMS_PER_CATEGORY]:
            title = escape(item["title"])
            link = escape(item["link"], quote=True)
            source = escape(item["source"])
            lines.append(f"\u2022 <a href=\"{link}\">{title}</a> \u2014 <i>{source}</i>")
        lines.append("")
    lines.append("Full archive: see your GitHub Pages site.")
    return "\n".join(lines)


def build_website_page(items, run_time=None, page_title="Latest Digest"):
    run_time = run_time or datetime.now(timezone.utc)
    grouped = _group_by_category(items)

    sections_html = ""
    if not items:
        sections_html = "<p class='empty'>No new opportunities in this run.</p>"
    else:
        for category, cat_items in grouped.items():
            rows = ""
            for item in cat_items:
                rows += f"""
                <li class="item">
                    <a href="{escape(item['link'], quote=True)}" target="_blank" rel="noopener">
                        {escape(item['title'])}
                    </a>
                    <div class="meta">{escape(item['source'])} &middot; score {item['score']}</div>
                    <div class="snippet">{escape(item.get('snippet', '')[:200])}</div>
                </li>"""
            sections_html += f"""
            <section>
                <h2>{escape(category)}</h2>
                <ul>{rows}</ul>
            </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{escape(page_title)} - Money Bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 780px;
         margin: 0 auto; padding: 24px 16px; background: #0b1210; color: #eee; }}
  h1 {{ color: #f0c419; }}
  h2 {{ color: #9fdcc4; border-bottom: 1px solid #234; padding-bottom: 6px; margin-top: 32px; }}
  .timestamp {{ color: #888; margin-bottom: 24px; }}
  ul {{ list-style: none; padding: 0; }}
  .item {{ background: #131c19; border: 1px solid #23342c; border-radius: 10px;
           padding: 12px 16px; margin-bottom: 10px; }}
  .item a {{ color: #f0c419; text-decoration: none; font-weight: 600; }}
  .item a:hover {{ text-decoration: underline; }}
  .meta {{ color: #7c9; font-size: 0.8em; margin-top: 4px; }}
  .snippet {{ color: #bbb; font-size: 0.9em; margin-top: 6px; }}
  .empty {{ color: #999; font-style: italic; }}
  nav a {{ color: #f0c419; margin-right: 16px; }}
</style>
</head>
<body>
  <nav><a href="index.html">Latest</a><a href="archive/">Archive</a></nav>
  <h1>Money Bot \u2014 {escape(page_title)}</h1>
  <div class="timestamp">Updated {run_time.strftime('%Y-%m-%d %H:%M UTC')} &middot; {len(items)} new item(s)</div>
  {sections_html}
</body>
</html>"""
