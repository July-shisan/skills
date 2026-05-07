---
name: daily-hot-report
description: 自动生成每日全网热榜日报并发布到微信公众号。抓取中文平台（微博/抖音/知乎/贴吧/36氪/V2EX/雪球/东方财富/同花顺/B站/豆瓣/虎扑）的热榜数据，AI 智能生成跨平台热点摘要，生成 HTML 日报保存到本地，然后自动发布到公众号草稿箱。当用户提到"生成热榜日报"、"发布热榜报告"、"每日热点总结"、"全网热榜"、"今日热点"、"热榜日报"、"hot daily"、"trending report"时触发此技能。
---

# 全网热榜日报生成与发布

自动完成：抓取数据 → AI 跨平台分析 → 生成 HTML 日报 → 保存本地 → 发布微信公众号

## 前置条件

- opencli 已安装（`npm install -g @jackwener/opencli`）
- jq 已安装（`brew install jq`）
- WECHAT_API_KEY 环境变量已设置（在 `/Users/guohua/.env` 中）

## 完整工作流

### Phase 1: 预检

```bash
# 检查 opencli 和 jq
command -v opencli &>/dev/null || { echo "错误: opencli 未安装"; exit 1; }
command -v jq &>/dev/null || { echo "错误: jq 未安装"; exit 1; }

# 列出可用适配器，确认目标站点存在
opencli list -f yaml 2>/dev/null | head -500

# 检查 WeChat API Key（不阻塞流程）
cat /Users/guohua/.env | grep WECHAT_API_KEY
```

### Phase 2: 并行抓取数据

创建临时目录，将 12 个中文平台命令**全部并行**执行，每个命令添加 `--limit 15 -f json` 参数。

```bash
TMPDIR=$(mktemp -d /tmp/hot-report.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT
```

#### 中文社交媒体 (cn-social) — 4 个平台

| 平台 | 命令 | 输出文件 | 关键字段 |
|------|------|----------|----------|
| 微博热搜 | `opencli weibo hot --limit 15 -f json` | weibo.json | rank, word, hot_value, category |
| 抖音热点榜 | `opencli douyin hot --limit 15 -f json` | douyin.json | rank, title, hotValue, label |
| 知乎热榜 | `opencli zhihu hot --limit 15 -f json` | zhihu.json | rank, title, heat, answers |
| 百度贴吧 | `opencli tieba hot --limit 15 -f json` | tieba.json | rank, title, discussions |

#### 中文科技社区 (cn-tech) — 2 个平台

| 平台 | 命令 | 输出文件 | 关键字段 |
|------|------|----------|----------|
| 36氪热榜 | `opencli 36kr hot --limit 15 -f json` | 36kr.json | rank, title |
| V2EX 热门 | `opencli v2ex hot --limit 15 -f json` | v2ex.json | rank, title, node, replies |

#### 中文财经 (cn-finance) — 3 个平台

| 平台 | 命令 | 输出文件 | 关键字段 |
|------|------|----------|----------|
| 雪球热股 | `opencli xueqiu hot-stock --limit 15 -f json` | xueqiu.json | rank, name, code, change |
| 东方财富热股 | `opencli eastmoney hot-rank --limit 15 -f json` | eastmoney.json | rank, name, code, heat |
| 同花顺热股 | `opencli ths hot-rank --limit 15 -f json` | ths.json | rank, name, code, heat |

#### 中文娱乐 (cn-ent) — 3 个平台

| 平台 | 命令 | 输出文件 | 关键字段 |
|------|------|----------|----------|
| B站热门 | `opencli bilibili hot --limit 15 -f json` | bilibili.json | rank, title, author, play, danmaku |
| 豆瓣电影 | `opencli douban movie-hot --limit 15 -f json` | douban.json | rank, title, rating, director, year |
| 虎扑热门 | `opencli hupu hot --limit 15 -f json` | hupu.json | rank, title |

**执行方式**：所有 12 条命令用 `&` 后台并行执行，然后 `wait` 等待全部完成。

**验证**：对每个输出文件执行 `jq empty`，标记格式错误或为空的文件为"获取失败"。

### Phase 3: AI 跨平台分析

读取所有有效的 JSON 输出，执行以下分析：

#### 3a. 跨平台热点识别

比较所有平台的标题/关键词，识别出现在 **2 个及以上平台** 的相同话题：
- 标准化标题（去除平台特定后缀词，如"事件始末"、"最新进展"）
- 提取核心实体词（人名、事件名、产品名、赛事名）
- 同一话题出现在 3+ 平台标记为**重大跨平台热点**

#### 3b. 生成 5-8 条今日焦点

每条焦点包含：
- **标题**：话题的标准名称
- **出现平台**：列出具体平台及排名（如"微博#2 / 抖音#1 / 知乎#3"）
- **综合热度**：根据跨平台数量和各平台排名综合判定（极高/高/中）
- **简要分析**：1-2 句话解释该话题为何今天在多平台同时爆发

#### 3c. 趋势洞察

生成 3-4 条趋势洞察，覆盖：
- 今日主导话题类型（娱乐/科技/财经/社会事件）
- 值得关注的异常热点或意外上榜话题
- 跨平台共振模式（如"娱乐事件主导社交平台，科技领域独立热点"）
- 各平台间差异（某些话题仅在某类平台突出）

### Phase 4: 生成 HTML 日报

文件保存路径：`/Users/guohua/guohua/wechat_hot/`
文件命名：`hot-daily-{YYYYMMDD-HHmmss}.html`

**关键约束：微信公众号不支持 `<style>` 标签和 class 属性，所有样式必须内联。使用 `<section>` 代替 `<div>`。最大宽度 677px。**

#### HTML 模板与生成脚本

完整模板文件位于：`/Users/guohua/.claude/skills/daily-hot-report/template.html`
Python 生成脚本：`/Users/guohua/.claude/skills/daily-hot-report/generate_html.py`

**生成流程：**

1. 将 Phase 2-3 抓取和分析后的数据组装为 JSON 文件（见下方格式）
2. 调用 Python 脚本读取模板并填充数据：

```bash
python3 ~/.claude/skills/daily-hot-report/generate_html.py data.json output.html
```

3. 脚本会自动替换模板中的 `{{占位符}}` 和 `{{BLOCK_*}}` 块级占位符，生成最终 HTML

**数据 JSON 格式：**

```json
{
  "overview": {
    "platforms": 12,
    "focus_topics": 6,
    "insights": 4,
    "finance_stocks": 3
  },
  "focus": [
    {
      "rank": 1,
      "title": "话题名称",
      "platforms": "微博#2 / 抖音#1 / 知乎#3",
      "heat_level": "极高|高|中",
      "analysis": "1-2 句 AI 分析"
    }
  ],
  "weibo": [
    { "rank": 1, "word": "热搜词", "hot_value": "523万" }
  ],
  "douyin": [
    { "rank": 1, "title": "热点标题", "hotValue": "1188万" }
  ],
  "zhihu": [
    { "rank": 1, "title": "问题标题", "heat": "1234万热度", "answers": "456" }
  ],
  "tieba": [
    { "rank": 1, "title": "帖子标题", "discussions": "152万讨论" }
  ],
  "36kr": [
    { "rank": 1, "title": "文章标题" }
  ],
  "v2ex": [
    { "rank": 1, "title": "帖子标题", "node": "programmers", "replies": "42" }
  ],
  "xueqiu": [
    { "rank": 1, "name": "股票名", "code": "SH600519", "change": "+3.52%", "heat": "12345" }
  ],
  "eastmoney": [
    { "rank": 1, "name": "股票名", "code": "SH600519", "change": "+3.52%" }
  ],
  "ths": [
    { "rank": 1, "name": "股票名", "code": "SH600519", "change": "-1.23%" }
  ],
  "bilibili": [
    { "rank": 1, "title": "视频标题", "author": "UP主名", "play": "123万" }
  ],
  "douban": [
    { "rank": 1, "title": "电影名", "rating": "8.5", "director": "导演名", "year": "2024" }
  ],
  "hupu": [
    { "rank": 1, "title": "帖子标题" }
  ],
  "insights": {
    "summary": "2-3 句总结今日全网趋势",
    "item_1": "洞察 1",
    "item_2": "洞察 2",
    "item_3": "洞察 3",
    "item_4": "洞察 4（可选，可留空字符串）"
  }
}
```

> 获取失败的平台设为 `null`（如 `"weibo": null`），脚本会自动生成"数据获取失败"占位行。

**模板设计要点（已针对手机端优化）：**
- 排名徽章 16×16px，font-size:9px，徽章列宽 20px，行内 padding 7px
- 焦点卡片按热度分级着色（极高红、高蓝、中灰），padding 14px 紧凑布局
- 分类标题左边框颜色：社交媒体橙 / 科技社区蓝 / 财经热股红 / 娱乐影视紫
- 平台标题品牌色：微博红 / 抖音黑 / 知乎蓝 / 贴吧蓝 / 36氪黑 / V2EX灰 / 财经红 / B站粉 / 豆瓣绿 / 虎扑红
- 财经涨跌幅：涨红 `#e74c3c` / 跌绿 `#27ae60`，15px 加粗
- 豆瓣评分：>=8.0 红色加粗带星 / <8.0 灰色普通
- 所有样式内联，兼容微信渲染

#### 热度值格式化

- 微博 hot_value: 格式化为可读形式（如 523万、391万）
- 抖音 hotValue: 格式化为可读形式（如 1188万、1151万）
- 知乎 heat: 格式化为"1234万热度"
- 贴吧 discussions: 格式化为可读形式（如 152.1W → 152万）
- 财经 heat: 原始数值

> 注意：具体格式以实际 JSON 输出为准，灵活处理数值和已有格式。

### Phase 5: 保存文档

```bash
mkdir -p /Users/guohua/guohua/wechat_hot

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILEPATH="/Users/guohua/guohua/wechat_hot/hot-daily-${TIMESTAMP}.html"

# 将数据写入临时 JSON 文件，然后调用 Python 脚本生成 HTML
# 1. 先将组装好的数据 JSON 写入 /tmp/hot-data-${TIMESTAMP}.json（使用 Write 工具）
# 2. 执行生成脚本：
python3 ~/.claude/skills/daily-hot-report/generate_html.py /tmp/hot-data-${TIMESTAMP}.json "${FILEPATH}"
```

### Phase 6: 发布到微信公众号

```bash
# Step 1: 确认 API Key
cat /Users/guohua/.env | grep WECHAT_API_KEY

# Step 2: 获取公众号列表
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py list-accounts

# Step 3: 发布 HTML 文件
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py publish \
  --appid <wechatAppid> \
  --html /Users/guohua/guohua/wechat_hot/hot-daily-{TIMESTAMP}.html
```

发布成功后告知用户：
- 本地文件已保存至 `/Users/guohua/guohua/wechat_hot/hot-daily-{TIMESTAMP}.html`
- 文章已发布到公众号草稿箱
- 提醒用户登录微信公众平台预览并手动发布

### Phase 7: 错误处理

| 场景 | 处理方式 |
|------|----------|
| opencli 未安装 | 中止 Phase 1，显示安装命令 |
| 单个平台命令失败 | 在对应表格中标注"获取失败"，继续其他平台 |
| 平台返回无效 JSON | 同上 — `jq empty` 验证捕获 |
| 所有 12 个平台失败 | 仍生成包含标题和说明的 HTML，在焦点区标注"数据获取异常" |
| WECHAT_API_KEY 未配置 | 完成 Phase 4-5 保存 HTML，跳过 Phase 6，告知配置方法 |
| WeChat API 返回 ACCOUNT_TOKEN_EXPIRED | 告知用户到 wx.limyai.com 重新授权，提供本地文件路径 |
| WeChat API 返回其他错误 | 重试 1 次，仍失败则告知用户并提供本地文件路径 |
| 最多重试 1 次 | 不无限重试 |

**核心原则：不让单个平台的失败阻塞整个流水线。**

## 使用示例

| 用户输入 | 执行范围 |
|----------|----------|
| "生成今天的热榜日报" | Phase 1-6 全流程 |
| "写一篇全网热点文章并发布" | Phase 1-6 全流程 |
| "只抓取热榜数据" | Phase 1-2，展示 Markdown 摘要 |
| "发布今天的热榜日报" | 跳到 Phase 6，查找当天最新文件 |
| "分析一下今天的热点趋势" | Phase 1-3，重点输出跨平台分析 |

## 查找当天最新文件

如用户说"发布今天的热榜日报"但未指定文件，自动查找：

```bash
ls -t /Users/guohua/guohua/wechat_hot/hot-daily-*.html | head -1
```

## 重要约束

1. **只使用 `opencli` 命令**获取数据，不直接 curl/fetch API
2. **所有命令添加 `--limit 15 -f json`** 参数
3. **并行执行**所有平台命令提升速度
4. **先运行 `opencli list`** 确认适配器存在
5. **不要假设输出格式**：以实际 JSON 输出为准，SKILL.md 中的字段仅供参考
6. **不要无限重试**：失败平台跳过并标注原因
7. **HTML 全部内联样式**：微信公众号不支持 `<style>` 标签
8. **使用 `<section>` 而非 `<div>`**：微信渲染兼容
9. **最大宽度 677px**：微信文章标准宽度
10. **只保存到草稿箱**：不自动正式发布，用户手动操作
11. **使用 generate_html.py 生成 HTML**：将数据组装为 JSON，调用脚本生成，不再手动拼接
12. **获取失败的平台在 JSON 中设为 null**：脚本会自动生成"数据获取失败"占位行
13. **排名 1-3 必须使用彩色圆形徽章**，4+ 使用灰色数字
14. **焦点卡片按热度分级着色**：极高红、高蓝、中灰
