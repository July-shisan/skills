#!/usr/bin/env python3
"""
GitHub 热门仓库日报 HTML 生成器
读取 template.html 模板并填充数据，保证每次生成格式一致
"""

import json
import sys
import os
from datetime import datetime


def format_stars(count):
    if count is None:
        return "0"
    count = int(count)
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)


# Compact inline rank number
BADGE_COLORS = {1: "#ff4757", 2: "#ff6348", 3: "#ffa502"}


def _badge(rank):
    """Generate compact inline rank number."""
    color = BADGE_COLORS.get(rank, "#ccc")
    return (
        f'<span style="color:{color};font-weight:700;font-size:12px;'
        f'margin-right:2px;">{rank}.</span>'
    )


def generate_trending_card(index, repo):
    """Generate one trending repo row (today/weekly, with period stars)."""
    desc = repo.get("description") or ""
    if len(desc) > 80:
        desc = desc[:77] + "..."

    lang = repo.get("language") or ""
    lang_color = repo.get("language_color") or "#959da5"
    stars = format_stars(repo.get("stargazers_count", 0))
    stars_period = repo.get("stars_period", 0)

    if stars_period > 0:
        period_html = (
            f' <span style="font-size:10px;color:#e36209;font-weight:700;">'
            f"+{format_stars(stars_period)}</span>"
        )
    else:
        period_html = ""

    desc_cn = repo.get("description_cn", "")
    if desc_cn:
        desc_cn_html = (
            '<p style="margin:1px 0 0;padding-left:12px;font-size:10px;'
            'color:#0366d6;line-height:1.4;">' + desc_cn + '</p>'
        )
    else:
        desc_cn_html = ""

    return (
        f'<section style="display:flex;align-items:flex-start;padding:7px 0;'
        f'border-bottom:1px solid #f2f2f2;">'
        f'<section style="flex:1;min-width:0;">'
        f'<p style="margin:0;font-weight:700;color:#0366d6;font-size:13px;'
        f'line-height:1.5;">{_badge(index)}{repo["full_name"]}'
        f'{period_html}</p>'
        f'{desc_cn_html}'
        f'<p style="margin:2px 0 0;padding-left:12px;font-size:11px;color:#6a737d;'
        f'line-height:1.5;">{desc}</p>'
        f'<section style="margin:2px 0 0;padding-left:12px;">'
        f'<span style="display:inline-block;width:5px;height:5px;'
        f'border-radius:50%;background:{lang_color};margin-right:2px;'
        f'vertical-align:middle;"></span>'
        f'<span style="font-size:10px;color:#586069;">{lang} ★{stars}</span>'
        f'</section></section></section>'
    )


def generate_active_card(index, repo):
    """Generate one active repo row (with forks)."""
    desc = repo.get("description") or ""
    if len(desc) > 80:
        desc = desc[:77] + "..."

    lang = repo.get("language") or ""
    lang_color = repo.get("language_color") or "#959da5"
    stars = format_stars(repo.get("stargazers_count", 0))
    forks = format_stars(repo.get("forks_count", 0))

    desc_cn = repo.get("description_cn", "")
    if desc_cn:
        desc_cn_html = (
            '<p style="margin:1px 0 0;padding-left:12px;font-size:10px;'
            'color:#0366d6;line-height:1.4;">' + desc_cn + '</p>'
        )
    else:
        desc_cn_html = ""

    return (
        f'<section style="display:flex;align-items:flex-start;padding:7px 0;'
        f'border-bottom:1px solid #f2f2f2;">'
        f'<section style="flex:1;min-width:0;">'
        f'<p style="margin:0;font-weight:700;color:#0366d6;font-size:13px;'
        f'line-height:1.5;">{_badge(index)}{repo["full_name"]}</p>'
        f'{desc_cn_html}'
        f'<p style="margin:2px 0 0;padding-left:12px;font-size:11px;color:#6a737d;'
        f'line-height:1.5;">{desc}</p>'
        f'<section style="margin:2px 0 0;padding-left:12px;">'
        f'<span style="display:inline-block;width:5px;height:5px;'
        f'border-radius:50%;background:{lang_color};margin-right:2px;'
        f'vertical-align:middle;"></span>'
        f'<span style="font-size:10px;color:#586069;">'
        f'{lang} ★{stars} ⑂{forks}</span>'
        f'</section></section></section>'
    )


def generate_recommendation_card(repo, reason):
    """Generate one recommendation card."""
    lang = repo.get("language") or ""
    lang_color = repo.get("language_color") or "#959da5"
    stars = format_stars(repo.get("stargazers_count", 0))
    desc = repo.get("description") or ""
    if len(desc) > 80:
        desc = desc[:77] + "..."

    desc_cn = repo.get("description_cn", "")
    if desc_cn:
        desc_cn_html = (
            '<section style="font-size:10px;color:#0366d6;'
            'line-height:1.3;margin:0 0 2px;">' + desc_cn + '</section>'
        )
    else:
        desc_cn_html = ""

    stars_period = repo.get("stars_period", 0)
    if stars_period > 0:
        period_html = (
            f' <span style="font-size:10px;color:#e36209;font-weight:700;">'
            f"+{format_stars(stars_period)}</span>"
        )
    else:
        period_html = ""

    return (
        f'<section style="background:#e8f4fd;border-radius:6px;'
        f'padding:8px 10px;margin:0 0 6px;border:1px solid #d0e4f7;">'
        f'<section style="margin:0 0 3px;">'
        f'<span style="color:#0366d6;font-weight:700;font-size:10px;'
        f'margin-right:2px;">▸</span>'
        f'<span style="font-size:13px;font-weight:700;color:#0366d6;">'
        f'{repo["full_name"]}</span></section>'
        f'<section style="margin:0 0 3px;">'
        f'<span style="display:inline-block;width:5px;height:5px;'
        f'border-radius:50%;background:{lang_color};margin-right:2px;'
        f'vertical-align:middle;"></span>'
        f'<span style="font-size:10px;color:#586069;">'
        f'{lang} ★{stars}{period_html}</span></section>'
        f'{desc_cn_html}'
        f'<p style="font-size:11px;color:#586069;margin:0 0 2px;'
        f'line-height:1.5;">{desc}</p>'
        f'<p style="font-size:10px;color:#6a737d;margin:0;'
        f'line-height:1.5;">{reason}</p></section>'
    )


def generate_language_bar(lang_stat):
    """Generate one language progress bar."""
    name = lang_stat["name"]
    count = lang_stat["count"]
    color = lang_stat["color"]
    percentage = lang_stat["percentage"]

    return (
        f'<section style="margin:0 0 8px;">'
        f'<section style="display:flex;align-items:center;'
        f'justify-content:space-between;margin:0 0 3px;">'
        f'<section style="display:flex;align-items:center;">'
        f'<span style="display:inline-block;width:8px;height:8px;'
        f'border-radius:50%;background:{color};margin-right:4px;"></span>'
        f'<span style="font-weight:700;color:#24292e;font-size:11px;">'
        f'{name}</span></section>'
        f'<span style="font-size:9px;color:#959da5;">'
        f'{count}个项目 · {percentage}%</span></section>'
        f'<section style="height:5px;background:#e1e4e8;'
        f'border-radius:3px;overflow:hidden;">'
        f'<section style="height:100%;background:{color};'
        f'width:{percentage}%;border-radius:3px;'
        f'min-width:3%;"></section></section></section>'
    )


def generate_html(data, recommendations=None, insights=None):
    """Generate full HTML report from template."""
    # Locate template file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    template_path = os.path.join(skill_dir, "template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    date_str = datetime.now().strftime("%Y年%m月%d日")
    today_repos = data.get("today", [])
    weekly_repos = data.get("weekly", [])
    active_repos = data.get("active", [])
    lang_stats = data.get("language_stats", [])

    # Build recommendation cards
    rec_cards = ""
    if recommendations:
        for rec in recommendations:
            repo = rec.get("repo", {})
            reason = rec.get("reason", "")
            rec_cards += generate_recommendation_card(repo, reason)

    # Build trending cards
    today_cards = "".join(
        generate_trending_card(i, repo) for i, repo in enumerate(today_repos, 1)
    )
    weekly_cards = "".join(
        generate_trending_card(i, repo) for i, repo in enumerate(weekly_repos, 1)
    )
    active_cards = "".join(
        generate_active_card(i, repo) for i, repo in enumerate(active_repos, 1)
    )

    # Build language bars
    lang_bars = "".join(generate_language_bar(stat) for stat in lang_stats)

    # Build insights
    insights_html = ""
    if insights:
        for ins in insights:
            title = ins.get("title", "")
            content = ins.get("content", "")
            if len(content) > 120:
                content = content[:117] + "..."
            insights_html += (
                f'<section style="margin:0 0 8px;">'
                f'<p style="font-size:11px;color:#24292e;margin:0 0 3px;'
                f'font-weight:700;">{title}</p>'
                f'<p style="font-size:10px;color:#586069;margin:0;'
                f'line-height:1.5;">{content}</p></section>'
            )

    # Empty state for failed sections
    empty_state = (
        '<section style="padding:14px 0;text-align:center;">'
        '<p style="font-size:11px;color:#ccc;margin:0;">数据获取失败</p></section>'
    )

    # Build recommendations section
    rec_section = ""
    if rec_cards:
        rec_section = (
            f'<h2 style="font-size:15px;font-weight:700;color:#24292e;'
            f'border-left:3px solid #0366d6;padding-left:8px;'
            f'margin:14px 0 5px;">编辑推荐</h2>'
            f'<p style="font-size:10px;color:#959da5;margin:0 0 8px;">'
            f"今日最值得关注的开源项目</p>"
            f"{rec_cards}"
            f'<section style="height:1px;background:#e1e4e8;'
            f'margin:12px 0;"></section>'
        )

    # Build insights section
    insights_section = ""
    if insights_html:
        insights_section = (
            f'<h2 style="font-size:15px;font-weight:700;color:#24292e;'
            f'border-left:3px solid #6f42c1;padding-left:8px;'
            f'margin:14px 0 5px;">趋势洞察</h2>'
            f'<p style="font-size:10px;color:#959da5;margin:0 0 8px;">'
            f"洞察开源世界最新风向</p>"
            f'<section style="background:#f0f7ff;border-radius:8px;'
            f'padding:10px 12px;margin:0 0 10px;">'
            f"{insights_html}</section>"
            f'<section style="height:1px;background:#e1e4e8;'
            f'margin:12px 0;"></section>'
        )

    # Build language section
    lang_section = ""
    if lang_bars:
        lang_section = (
            f'<h2 style="font-size:15px;font-weight:700;color:#24292e;'
            f'border-left:3px solid #6f42c1;padding-left:8px;'
            f'margin:14px 0 5px;">语言热度排行</h2>'
            f'<p style="font-size:10px;color:#959da5;margin:0 0 8px;">'
            f"本期热门项目使用的编程语言分布</p>"
            f'<section style="background:#f6f8fa;border-radius:8px;'
            f'padding:8px 12px;margin:0 0 10px;">'
            f"{lang_bars}</section>"
            f'<section style="height:1px;background:#e1e4e8;'
            f'margin:12px 0;"></section>'
        )

    # Fill template placeholders — order matches template: 推荐→语言→洞察→榜单
    html = template
    html = html.replace("{{DATE_STR}}", date_str)
    html = html.replace("{{TODAY_COUNT}}", str(len(today_repos)))
    html = html.replace("{{WEEKLY_COUNT}}", str(len(weekly_repos)))
    html = html.replace("{{ACTIVE_COUNT}}", str(len(active_repos)))
    html = html.replace("{{RECOMMENDATIONS_SECTION}}", rec_section)
    html = html.replace("{{LANGUAGE_SECTION}}", lang_section)
    html = html.replace("{{INSIGHTS_SECTION}}", insights_section)
    html = html.replace("{{TODAY_LIST}}", today_cards if today_cards else empty_state)
    html = html.replace("{{WEEKLY_LIST}}", weekly_cards if weekly_cards else empty_state)
    html = html.replace("{{ACTIVE_LIST}}", active_cards if active_cards else empty_state)

    return html


def main():
    """Main entry: generate HTML from JSON data file."""
    if len(sys.argv) < 2:
        print("用法: python3 generate_html.py <data.json> [output.html]", file=sys.stderr)
        print("  data.json  - fetch_github_trending.py 输出的 JSON 文件", file=sys.stderr)
        print("  output.html - 可选，默认输出到 stdout", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check for separate recommendations/insights files
    recommendations = None
    insights = None

    rec_path = json_path.replace(".json", "_rec.json")
    if os.path.exists(rec_path):
        with open(rec_path, "r", encoding="utf-8") as f:
            recommendations = json.load(f)

    ins_path = json_path.replace(".json", "_insights.json")
    if os.path.exists(ins_path):
        with open(ins_path, "r", encoding="utf-8") as f:
            insights = json.load(f)

    html = generate_html(data, recommendations, insights)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated: {output_path}")
    else:
        print(html)


if __name__ == "__main__":
    main()
