#!/usr/bin/env python3
"""
Generate daily hot report HTML from template and data.

Usage:
    python3 generate_html.py <data.json> <output.html>

Data JSON format:
{
  "overview": { "platforms": 12, "focus_topics": 6, "insights": 4, "finance_stocks": 3 },
  "focus": [
    {
      "rank": 1,
      "title": "...",
      "platforms": "微博#2 / 抖音#1 / 知乎#3",
      "heat_level": "极高|高|中",
      "analysis": "1-2 句 AI 分析"
    }
  ],
  "weibo": [
    { "rank": 1, "word": "...", "hot_value": "523万" }
  ],
  "douyin": [
    { "rank": 1, "title": "...", "hotValue": "1188万" }
  ],
  "zhihu": [
    { "rank": 1, "title": "...", "heat": "1234万热度", "answers": "456" }
  ],
  "tieba": [
    { "rank": 1, "title": "...", "discussions": "152万讨论" }
  ],
  "36kr": [
    { "rank": 1, "title": "..." }
  ],
  "v2ex": [
    { "rank": 1, "title": "...", "node": "programmers", "replies": "42" }
  ],
  "xueqiu": [
    { "rank": 1, "name": "...", "code": "SH600519", "change": "+3.52%", "heat": "12345" }
  ],
  "eastmoney": [
    { "rank": 1, "name": "...", "code": "SH600519", "change": "+3.52%" }
  ],
  "ths": [
    { "rank": 1, "name": "...", "code": "SH600519", "change": "-1.23%" }
  ],
  "bilibili": [
    { "rank": 1, "title": "...", "author": "UP主名", "play": "123万" }
  ],
  "douban": [
    { "rank": 1, "title": "...", "rating": "8.5", "director": "导演名", "year": "2024" }
  ],
  "hupu": [
    { "rank": 1, "title": "..." }
  ],
  "insights": {
    "summary": "...",
    "item_1": "...",
    "item_2": "...",
    "item_3": "...",
    "item_4": ""
  }
}

Failed platforms can be represented as:
  "weibo": null   — will show "数据获取失败"
"""

import json
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template.html")

# Badge colors for top 3
BADGE_STYLES = {
    1: "background:#ff4757;color:#fff;",
    2: "background:#ff6348;color:#fff;",
    3: "background:#ffa502;color:#fff;",
}

# Focus card heat level styles
HEAT_STYLES = {
    "极高": ("#e74c3c", "#fef5f5", "#e74c3c"),
    "高": ("#3498db", "#f0f7ff", "#3498db"),
    "中": ("#95a5a6", "#f8f9fa", "#95a5a6"),
}

# Platform sub-heading brand colors
PLATFORM_COLORS = {
    "weibo": "#e74c3c",
    "douyin": "#1a1a1a",
    "zhihu": "#0066ff",
    "tieba": "#4876ff",
    "36kr": "#1a1a1a",
    "v2ex": "#333333",
    "xueqiu": "#e74c3c",
    "eastmoney": "#e74c3c",
    "ths": "#e74c3c",
    "bilibili": "#fb7299",
    "douban": "#00b51d",
    "hupu": "#d4341e",
}

# Section title border colors
SECTION_COLORS = {
    "social": "#ff6b35",
    "tech": "#3498db",
    "finance": "#e74c3c",
    "entertainment": "#9b59b6",
}


def _badge(rank):
    """Generate 16x16 inline rank badge."""
    if rank in BADGE_STYLES:
        extra = BADGE_STYLES[rank]
        return (
            f'<section style="width:16px;height:16px;border-radius:50%;'
            f"{extra}text-align:center;line-height:16px;"
            f'font-size:9px;font-weight:800;">{rank}</section>'
        )
    return (
        f'<section style="width:16px;height:16px;text-align:center;'
        f'line-height:16px;font-size:9px;color:#ccc;'
        f'font-weight:800;">{rank}</section>'
    )


def _badge_td(rank):
    """Generate the table cell containing a rank badge."""
    return (
        f'<td style="padding:7px 4px 7px 0;width:20px;vertical-align:top;">'
        f"{_badge(rank)}</td>"
    )


def _change_style(change_str):
    """Return (color, font-weight, font-size) for a change string like '+3.52%' or '-1.23%'."""
    s = str(change_str).strip()
    if s.startswith("-") or s.startswith("跌"):
        return "#27ae60", "800", "15px"
    if s.startswith("+") or s.startswith("涨"):
        return "#e74c3c", "800", "15px"
    # Try parsing as float
    try:
        val = float(s.replace("%", ""))
        if val < 0:
            return "#27ae60", "800", "15px"
        return "#e74c3c", "800", "15px"
    except ValueError:
        return "#999", "normal", "13px"


def _douban_rating_html(rating):
    """Generate the rating td content for douban movies."""
    try:
        r = float(rating)
    except (ValueError, TypeError):
        return f'<span style="font-size:13px;color:#999;">{rating}</span>'

    if r >= 8.0:
        return (
            f'<span style="font-weight:800;font-size:15px;color:#e74c3c;">'
            f"{rating} ★</span>"
        )
    return f'<span style="font-size:13px;color:#999;">{rating}</span>'


# ---- Focus Cards ----

def focus_card_html(item):
    """Generate one focus card."""
    level = item.get("heat_level", "中")
    border_color, bg_color, tag_color = HEAT_STYLES.get(level, HEAT_STYLES["中"])
    rank = item.get("rank", 1)
    return (
        f'<section style="border-left:4px solid {border_color};'
        f"background:{bg_color};border-radius:0 10px 10px 0;"
        f'padding:14px 14px 12px 12px;margin:0 0 10px;">'
        f'<section style="display:flex;justify-content:space-between;align-items:baseline;margin:0 0 6px;">'
        f'<h3 style="font-size:15px;font-weight:800;color:#1a1a1a;margin:0;flex:1;">'
        f"{rank}. {item['title']}</h3></section>"
        f'<p style="font-size:11px;color:{tag_color};margin:0 0 6px;font-weight:700;letter-spacing:0.3px;">'
        f"{item.get('platforms', '')} · {level}</p>"
        f'<p style="font-size:14px;color:#555;margin:0;line-height:1.75;">'
        f"{item.get('analysis', '')}</p></section>"
    )


# ---- Social Media Table Rows ----

def weibo_row_html(item):
    """Generate one weibo table row."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;font-weight:800;color:#1a1a1a;line-height:1.5;">'
        f"{item['word']}</td>"
        f'<td style="padding:7px 0 7px 4px;text-align:right;color:#bbb;font-size:10px;'
        f'white-space:nowrap;vertical-align:top;line-height:16px;">'
        f"{item.get('hot_value', '')}</td></tr>"
    )


def douyin_row_html(item):
    """Generate one douyin table row."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;font-weight:800;color:#1a1a1a;line-height:1.5;">'
        f"{item['title']}</td>"
        f'<td style="padding:7px 0 7px 4px;text-align:right;color:#bbb;font-size:10px;'
        f'white-space:nowrap;vertical-align:top;line-height:16px;">'
        f"{item.get('hotValue', '')}</td></tr>"
    )


def zhihu_row_html(item):
    """Generate one zhihu table row (two-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['title']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"{item.get('heat', '')} · {item.get('answers', '')}回答</p></td></tr>"
    )


def tieba_row_html(item):
    """Generate one tieba table row (two-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['title']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"{item.get('discussions', '')}讨论</p></td></tr>"
    )


# ---- Tech Table Rows ----

def kr36_row_html(item):
    """Generate one 36kr table row (single-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;font-weight:800;color:#1a1a1a;line-height:1.5;">'
        f"{item['title']}</td></tr>"
    )


def v2ex_row_html(item):
    """Generate one v2ex table row (two-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['title']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"{item.get('node', '')} · {item.get('replies', '')}回复</p></td></tr>"
    )


# ---- Finance Table Rows ----

def xueqiu_row_html(item):
    """Generate one xueqiu table row (three-column, two-line)."""
    change = item.get("change", "")
    color, weight, size = _change_style(change)
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['name']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f'{item.get("code", "")} · 热度{item.get("heat", "")}</p></td>'
        f'<td style="padding:7px 0 7px 4px;text-align:right;font-weight:{weight};font-size:{size};color:{color};white-space:nowrap;vertical-align:top;line-height:16px;">{change}</td></tr>'
    )


def eastmoney_row_html(item):
    """Generate one eastmoney table row (three-column, two-line)."""
    change = item.get("change", "")
    color, weight, size = _change_style(change)
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['name']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"{item.get('code', '')}</p></td>"
        f'<td style="padding:7px 0 7px 4px;text-align:right;font-weight:{weight};font-size:{size};color:{color};white-space:nowrap;vertical-align:top;line-height:16px;">{change}</td></tr>'
    )


# ths rows look the same as eastmoney
def ths_row_html(item):
    return eastmoney_row_html(item)


# ---- Entertainment Table Rows ----

def bilibili_row_html(item):
    """Generate one bilibili table row (two-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['title']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"UP: {item.get('author', '')} · {item.get('play', '')}播放</p></td></tr>"
    )


def douban_row_html(item):
    """Generate one douban table row (three-column, two-line + rating)."""
    rating_html = _douban_rating_html(item.get("rating", ""))
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;">'
        f'<p style="margin:0;font-weight:800;color:#1a1a1a;font-size:14px;line-height:1.5;">'
        f"{item['title']}</p>"
        f'<p style="margin:2px 0 0;font-size:10px;color:#bbb;">'
        f"{item.get('director', '')} · {item.get('year', '')}年</p></td>"
        f'<td style="padding:7px 0 7px 4px;text-align:right;white-space:nowrap;'
        f'vertical-align:top;line-height:16px;">'
        f"{rating_html}</td></tr>"
    )


def hupu_row_html(item):
    """Generate one hupu table row (single-line)."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f"{_badge_td(item['rank'])}"
        f'<td style="padding:7px 2px;font-weight:800;color:#1a1a1a;line-height:1.5;">'
        f"{item['title']}</td></tr>"
    )


# ---- Failed platform placeholder ----

def failed_rows_html(count=15):
    """Generate a single row showing '数据获取失败' for a failed platform."""
    return (
        f'<tr style="border-bottom:1px solid #f2f2f2;">'
        f'<td style="padding:7px 4px 7px 0;width:20px;vertical-align:top;">'
        f'<section style="width:16px;height:16px;text-align:center;line-height:16px;'
        f'font-size:9px;color:#ddd;font-weight:800;">-</section></td>'
        f'<td style="padding:7px 2px;color:#ccc;line-height:1.5;" colspan="2">'
        f"数据获取失败</td></tr>"
    )


# ---- Row generators per platform ----

ROW_GENERATORS = {
    "weibo": weibo_row_html,
    "douyin": douyin_row_html,
    "zhihu": zhihu_row_html,
    "tieba": tieba_row_html,
    "36kr": kr36_row_html,
    "v2ex": v2ex_row_html,
    "xueqiu": xueqiu_row_html,
    "eastmoney": eastmoney_row_html,
    "ths": ths_row_html,
    "bilibili": bilibili_row_html,
    "douban": douban_row_html,
    "hupu": hupu_row_html,
}

# ---- Block placeholders to generator mapping ----

BLOCK_MAP = {
    "FOCUS_CARDS": "focus",
    "WEIBO_ROWS": "weibo",
    "DOUYIN_ROWS": "douyin",
    "ZHIHU_ROWS": "zhihu",
    "TIEBA_ROWS": "tieba",
    "KR36_ROWS": "36kr",
    "V2EX_ROWS": "v2ex",
    "XUEQIU_ROWS": "xueqiu",
    "EASTMONEY_ROWS": "eastmoney",
    "THS_ROWS": "ths",
    "BILIBILI_ROWS": "bilibili",
    "DOUBAN_ROWS": "douban",
    "HUPU_ROWS": "hupu",
}


def generate_rows(data, platform_key):
    """Generate HTML rows for a given platform. Returns failed placeholder if null/empty."""
    items = data.get(platform_key)
    if items is None:
        return failed_rows_html()

    gen = ROW_GENERATORS.get(platform_key)
    if gen is None:
        return failed_rows_html()

    return "\n".join(gen(item) for item in items)


def generate_report(data, output_path):
    """Generate the HTML report from template and data."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    date_str = f"{now.year}年{now.month:02d}月{now.day:02d}日"

    html = template.replace("{{YYYY年MM月DD日}}", date_str)

    # Overview stats
    overview = data.get("overview", {})
    html = html.replace("{{PLATFORM_COUNT}}", str(overview.get("platforms", 0)))
    html = html.replace("{{FOCUS_COUNT}}", str(overview.get("focus_topics", 0)))
    html = html.replace("{{INSIGHT_COUNT}}", str(overview.get("insights", 0)))
    html = html.replace("{{FINANCE_COUNT}}", str(overview.get("finance_stocks", 0)))

    # Focus cards
    focus_items = data.get("focus", [])
    if focus_items is None:
        focus_html = (
            '<section style="border-left:4px solid #ccc;background:#f8f9fa;'
            'border-radius:0 10px 10px 0;padding:14px 14px 12px 12px;margin:0 0 10px;">'
            '<p style="font-size:14px;color:#999;margin:0;">数据获取异常</p></section>'
        )
    else:
        focus_html = "\n".join(focus_card_html(item) for item in focus_items)
    html = html.replace("{{FOCUS_CARDS}}", focus_html)

    # Platform table rows
    for placeholder, platform_key in BLOCK_MAP.items():
        if placeholder == "FOCUS_CARDS":
            continue  # handled above
        html = html.replace("{{" + placeholder + "}}", generate_rows(data, platform_key))

    # Insights
    insights = data.get("insights", {})
    html = html.replace("{{INSIGHTS_SUMMARY}}", insights.get("summary", ""))
    for i in range(1, 5):
        html = html.replace("{{INSIGHT_" + str(i) + "}}", insights.get(f"item_{i}", ""))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <data.json> <output.html>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    generate_report(data, sys.argv[2])
