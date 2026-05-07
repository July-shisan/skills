#!/usr/bin/env python3
"""
Generate daily skills report HTML from template and data.

Usage:
    python3 generate_html.py <data.json> <output.html>

Data JSON format:
{
  "overview": { "trending_new": N, "hot_new": N, "recommendations": N, "insights": N },
  "recommendations": [
    {
      "type": "trending|quality|new",
      "name": "skill-name",
      "source": "owner/repo",
      "installs_str": "28.1K 安装",
      "tags": "标签：AI绘图 / 工具类",
      "detail": "4-6 句详细介绍..."
    }
  ],
  "trending": [
    { "name": "...", "source": "owner/repo", "installs": 28100, "desc": "一句话简介", "cross_list": true }
  ],
  "hot": [
    { "name": "...", "source": "owner/repo", "installs": 325, "change": 325, "desc": "一句话简介", "is_new": true }
  ],
  "historical": [
    { "name": "...", "source": "owner/repo", "installs": 28100, "desc": "一句话简介" }
  ],
  "insights": {
    "summary": "2-3 句总结",
    "item_1": "洞察1", "item_2": "洞察2", "item_3": "洞察3", "item_4": "洞察4"
  }
}
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

# Recommendation card styles
CARD_STYLES = {
    "trending": ("#ff6b35", "#fffbf5"),
    "quality": ("#3498db", "#f0f7ff"),
    "new": ("#27ae60", "#f0fff4"),
}


def format_installs(n):
    """Format install count: >=1000 use K suffix, else raw number."""
    if n >= 1000:
        k = n / 1000
        # Remove trailing .0 for clean display
        return f"{k:.1f}K" if k != int(k) else f"{int(k)}K"
    return str(n)


def badge_html(rank):
    """Generate inline rank badge HTML (16x16, no separate column)."""
    if rank in BADGE_STYLES:
        extra = BADGE_STYLES[rank]
        return (
            f'<span style="display:inline-block;width:16px;height:16px;'
            f"border-radius:50%;{extra}text-align:center;line-height:16px;"
            f'font-size:9px;font-weight:800;vertical-align:middle;'
            f'margin-right:4px;">{rank}</span>'
        )
    return (
        f'<span style="display:inline-block;width:16px;height:16px;'
        f"text-align:center;line-height:16px;font-size:9px;"
        f'color:#ccc;font-weight:800;vertical-align:middle;'
        f'margin-right:4px;">{rank}</span>'
    )


def _name_style(rank):
    """Return inline style for skill name based on rank."""
    if rank <= 3:
        return "font-weight:800;color:#1a1a1a"
    return "font-weight:500;color:#444"


def trending_item_html(rank, skill):
    """Generate one trending list item."""
    badge = badge_html(rank)
    style = _name_style(rank)
    fire = " 🔥" if skill.get("cross_list") else ""
    installs = format_installs(skill["installs"])
    desc = skill.get("desc", "")
    return (
        f'<section style="display:flex;align-items:flex-start;padding:7px 0;'
        f'border-bottom:1px solid #f2f2f2;">'
        f'<section style="flex:1;min-width:0;">'
        f'<p style="margin:0;{style};font-size:14px;line-height:1.6;">'
        f"{badge}{skill['name']}"
        f"</p>"
        f'<p style="margin:2px 0 0;font-size:11px;color:#bbb;'
        f'padding-left:20px;">{skill["source"]} · {desc}</p>'
        f"</section>"
        f'<section style="flex-shrink:0;padding-left:6px;text-align:right;">'
        f'<p style="margin:0;font-size:13px;font-weight:800;color:#1a1a1a;'
        f'white-space:nowrap;">{installs}{fire}</p>'
        f"</section></section>"
    )


def hot_item_html(rank, skill):
    """Generate one hot list item."""
    badge = badge_html(rank)
    style = _name_style(rank)
    daily = skill.get("change", 0)
    total = format_installs(skill["installs"])
    is_new = skill.get("is_new", False)
    daily_str = f"+{daily}"
    if is_new:
        daily_str += " 🆕"
    desc = skill.get("desc", "")
    return (
        f'<section style="display:flex;align-items:flex-start;padding:7px 0;'
        f'border-bottom:1px solid #f2f2f2;">'
        f'<section style="flex:1;min-width:0;">'
        f'<p style="margin:0;{style};font-size:14px;line-height:1.6;">'
        f"{badge}{skill['name']}"
        f"</p>"
        f'<p style="margin:2px 0 0;font-size:11px;color:#bbb;'
        f'padding-left:20px;">{skill["source"]} · {desc}</p>'
        f"</section>"
        f'<section style="flex-shrink:0;padding-left:6px;text-align:right;">'
        f'<p style="margin:0;font-size:13px;font-weight:800;color:#e74c3c;'
        f'white-space:nowrap;">{daily_str}</p>'
        f'<p style="margin:2px 0 0;font-size:9px;color:#ccc;">'
        f"{total} 总安装</p>"
        f"</section></section>"
    )


def historical_item_html(rank, skill):
    """Generate one historical list item."""
    badge = badge_html(rank)
    style = _name_style(rank)
    installs = format_installs(skill["installs"])
    desc = skill.get("desc", "")
    return (
        f'<section style="display:flex;align-items:flex-start;padding:7px 0;'
        f'border-bottom:1px solid #f2f2f2;">'
        f'<section style="flex:1;min-width:0;">'
        f'<p style="margin:0;{style};font-size:14px;line-height:1.6;">'
        f"{badge}{skill['name']}"
        f"</p>"
        f'<p style="margin:2px 0 0;font-size:11px;color:#bbb;'
        f'padding-left:20px;">{skill["source"]} · {desc}</p>'
        f"</section>"
        f'<section style="flex-shrink:0;padding-left:6px;text-align:right;">'
        f'<p style="margin:0;font-size:13px;font-weight:800;color:#1a1a1a;'
        f'white-space:nowrap;">{installs}</p>'
        f"</section></section>"
    )


def recommendation_card_html(card):
    """Generate one recommendation card HTML."""
    card_type = card.get("type", "trending")
    border_color, bg_color = CARD_STYLES.get(card_type, CARD_STYLES["trending"])
    badge = badge_html(card.get("rank", 1))
    return (
        f'<section style="border-left:4px solid {border_color};'
        f"background:{bg_color};border-radius:0 10px 10px 0;"
        f'padding:14px 14px 12px 12px;margin:0 0 10px;">'
        f'<h3 style="font-size:15px;font-weight:800;color:#1a1a1a;'
        f'margin:0 0 6px;">{badge}{card["name"]}</h3>'
        f'<p style="font-size:11px;color:{border_color};'
        f'margin:0 0 8px;font-weight:700;letter-spacing:0.3px;">'
        f'{card["source"]} · {card["installs_str"]} · {card.get("tags","")}</p>'
        f'<p style="font-size:14px;color:#555;margin:0 0 10px;'
        f'line-height:1.75;">{card["detail"]}</p>'
        f'<p style="font-size:13px;color:#999;margin:0;">安装：'
        f'<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;'
        f"font-family:'SF Mono',Menlo,Consolas,monospace;font-size:12px;\">"
        f"npx skills add {card['source']}@{card['name']} -g -y</code></p>"
        f"</section>"
    )


def generate_report(data, output_path):
    """Generate the HTML report from template and data."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    date_str = f"{now.year}年{now.month:02d}月{now.day:02d}日"

    # Simple placeholders
    html = template.replace("{{YYYY年MM月DD日}}", date_str)

    # Overview stats - replace {{N}} one at a time
    overview = data.get("overview", {})
    overview_keys = ["trending_new", "hot_new", "recommendations", "insights"]
    for key in overview_keys:
        html = html.replace("{{N}}", str(overview.get(key, 0)), 1)

    # Recommendations
    recs = data.get("recommendations", [])
    rec_html = "\n".join(recommendation_card_html(c) for c in recs)
    html = html.replace("{{RECOMMENDATIONS}}", rec_html)

    # Trending list
    trending = data.get("trending", [])
    trending_html = "\n".join(trending_item_html(i + 1, s) for i, s in enumerate(trending))
    html = html.replace("{{TRENDING_LIST}}", trending_html)

    # Hot list
    hot = data.get("hot", [])
    hot_html = "\n".join(hot_item_html(i + 1, s) for i, s in enumerate(hot))
    html = html.replace("{{HOT_LIST}}", hot_html)

    # Historical list
    historical = data.get("historical", [])
    historical_html = "\n".join(historical_item_html(i + 1, s) for i, s in enumerate(historical))
    html = html.replace("{{HISTORICAL_LIST}}", historical_html)

    # Insights
    insights = data.get("insights", {})
    html = html.replace("{{INSIGHTS_SUMMARY}}", insights.get("summary", ""))
    for i in range(1, 5):
        html = html.replace(f"{{{{INSIGHT_{i}}}}}", insights.get(f"item_{i}", ""))

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
