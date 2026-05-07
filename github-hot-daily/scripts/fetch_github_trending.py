#!/usr/bin/env python3
"""
GitHub Trending 数据获取脚本
通过抓取 github.com/trending 获取今日/本周热门仓库，通过 GitHub Search API 获取活跃高星项目：
1. 今日热门 Top20 - 今日增加星数最多的项目（抓取 github.com/trending）
2. 本周热门 Top20 - 本周增加星数最多的项目（抓取 github.com/trending?since=weekly）
3. 近期活跃高星 Top20 - 近3天有推送且 1万+ 星的成熟项目（GitHub Search API）
"""

import json
import sys
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta


# 语言颜色映射
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#2b7489",
    "JavaScript": "#f1e05a",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Swift": "#ffac45",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "Shell": "#89e051",
    "Dart": "#00B4AB",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "PHP": "#4F5D95",
    "Scala": "#c22d40",
    "Lua": "#000080",
    "R": "#198CE7",
    "Elixir": "#6e4a7e",
    "Haskell": "#5e5086",
    "Zig": "#ec915c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
}


def get_language_color(lang):
    if not lang:
        return "#959da5"
    return LANGUAGE_COLORS.get(lang, "#959da5")


def format_stars(count):
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)


def parse_number(text):
    """将文本数字转为整数，支持逗号和 k 后缀"""
    clean = text.strip().replace(",", "")
    if not clean:
        return 0
    if clean.endswith("k") or clean.endswith("K"):
        return int(float(clean[:-1]) * 1000)
    try:
        return int(clean)
    except ValueError:
        return 0


def make_request(url, is_api=False):
    """发送 HTTP 请求"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if is_api:
        headers["Accept"] = "application/vnd.github.v3+json"
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"⚠️  请求被限制: {e.read().decode()}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"⚠️  请求失败: {e}", file=sys.stderr)
        raise


def scrape_trending(since="daily"):
    """抓取 GitHub Trending 页面，解析仓库列表"""
    url = "https://github.com/trending"
    if since == "weekly":
        url += "?since=weekly"
    elif since == "monthly":
        url += "?since=monthly"

    html = make_request(url)
    repos = []

    # 匹配每个仓库的 article 块
    # GitHub trending 页面使用 article.Box-row 包含每个仓库
    article_pattern = re.compile(
        r'<article\s+class="Box-row.*?">(.*?)</article>',
        re.DOTALL,
    )

    for match in article_pattern.finditer(html):
        block = match.group(1)

        # 提取仓库链接 /owner/repo
        repo_match = re.search(r'<h2[^>]*>.*?<a\s+href="(/[^"]+)"[^>]*>', block, re.DOTALL)
        if not repo_match:
            continue
        repo_path = repo_match.group(1).strip()
        parts = repo_path.strip("/").split("/")
        if len(parts) < 2:
            continue
        owner = parts[0]
        name = parts[1]
        full_name = f"{owner}/{name}"

        # 提取描述
        desc_match = re.search(r'<p\s+class="col-9[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        description = ""
        if desc_match:
            description = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()
        if not description:
            description = "No description"

        # 提取语言
        lang_match = re.search(
            r'<span\s+itemprop="programmingLanguage">(.*?)</span>', block
        )
        language = ""
        if lang_match:
            language = lang_match.group(1).strip()

        # 提取语言颜色
        lang_color_match = re.search(
            r'<span\s+class="repo-language-color"[^>]*style="background-color:\s*([^;"]+)"', block
        )
        language_color = ""
        if lang_color_match:
            language_color = lang_color_match.group(1).strip()

        # 提取总 Star 数
        stars_match = re.search(
            r'<a\s+href="[^"]*/stargazers"[^>]*>\s*(.*?)\s*</a>', block, re.DOTALL
        )
        total_stars = 0
        if stars_match:
            total_stars = parse_number(re.sub(r"<[^>]+>", "", stars_match.group(1)))

        # 提取 Fork 数
        forks_match = re.search(
            r'<a\s+href="[^"]*/forks"[^>]*>\s*(.*?)\s*</a>', block, re.DOTALL
        )
        total_forks = 0
        if forks_match:
            total_forks = parse_number(re.sub(r"<[^>]+>", "", forks_match.group(1)))

        # 提取本期新增 Star 数（如 "1,234 stars today" 或 "5,678 stars this week"）
        stars_today_match = re.search(
            r'([\d,]+)\s+stars?\s+(today|this week|this month)', block
        )
        stars_period = 0
        if stars_today_match:
            stars_period = parse_number(stars_today_match.group(1))

        # 提取今日 Star（兼容另一种格式）
        if stars_period == 0:
            float_match = re.search(r'([\d.]+k)\s+stars?\s+(today|this week|this month)', block)
            if float_match:
                stars_period = parse_number(float_match.group(1))

        repos.append({
            "full_name": full_name,
            "html_url": f"https://github.com{repo_path}",
            "description": description[:100],
            "language": language or "N/A",
            "language_color": language_color or get_language_color(language),
            "stargazers_count": total_stars,
            "forks_count": total_forks,
            "stars_period": stars_period,
            "period_label": "today" if since == "daily" else "this week",
        })

    return repos[:20]


def fetch_active_repos():
    """通过 GitHub Search API 获取近期活跃高星项目"""
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    url = (
        f"https://api.github.com/search/repositories?"
        f"q=pushed:>{three_days_ago}+stars:>=10000"
        f"&sort=stars&order=desc&per_page=20"
    )
    try:
        data = json.loads(make_request(url, is_api=True))
        items = data.get("items", [])
        processed = []
        for item in items:
            lang = item.get("language")
            processed.append({
                "full_name": item.get("full_name", ""),
                "html_url": item.get("html_url", ""),
                "description": (item.get("description") or "No description")[:100],
                "language": lang or "N/A",
                "language_color": get_language_color(lang),
                "stargazers_count": item.get("stargazers_count", 0),
                "forks_count": item.get("forks_count", 0),
                "stars_period": 0,
                "period_label": "",
            })
        return processed
    except Exception as e:
        print(f"❌ 活跃高星获取失败: {e}", file=sys.stderr)
        return []


def compute_language_stats(results):
    """统计所有榜单中编程语言出现频次"""
    lang_count = {}
    for category in ["today", "weekly", "active"]:
        for repo in results.get(category, []):
            lang = repo["language"]
            if lang and lang != "N/A":
                lang_count[lang] = lang_count.get(lang, 0) + 1

    sorted_langs = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:5]
    total = sum(lang_count.values()) or 1

    return [
        {
            "name": name,
            "count": count,
            "percentage": round(count / total * 100),
            "color": get_language_color(name),
        }
        for name, count in sorted_langs
    ]


def main():
    """主函数：获取数据并输出 JSON"""
    print("🚀 开始获取 GitHub 热门仓库数据...", file=sys.stderr)

    results = {}

    # 1. 今日热门：抓取 github.com/trending (daily)
    try:
        results["today"] = scrape_trending("daily")
        print(f"✅ 今日热门: 获取到 {len(results['today'])} 个项目", file=sys.stderr)
    except Exception as e:
        print(f"❌ 今日热门获取失败: {e}", file=sys.stderr)
        results["today"] = []

    # 2. 本周热门：抓取 github.com/trending (weekly)
    try:
        results["weekly"] = scrape_trending("weekly")
        print(f"✅ 本周热门: 获取到 {len(results['weekly'])} 个项目", file=sys.stderr)
    except Exception as e:
        print(f"❌ 本周热门获取失败: {e}", file=sys.stderr)
        results["weekly"] = []

    # 3. 近期活跃高星 Top20
    results["active"] = fetch_active_repos()
    if results["active"]:
        print(f"✅ 近期活跃高星: 获取到 {len(results['active'])} 个项目", file=sys.stderr)

    lang_stats = compute_language_stats(results)

    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "today": results["today"],
        "weekly": results["weekly"],
        "active": results["active"],
        "language_stats": lang_stats,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
