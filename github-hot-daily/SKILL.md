---
name: github-hot-daily
description: 自动生成每日 GitHub 热门仓库日报并发布到微信公众号。抓取 GitHub Trending 页面获取今日/本周新增 Star 最多的仓库 Top20，通过 GitHub Search API 获取近期活跃高星项目 Top20，AI 智能分析生成趋势洞察与编辑推荐，生成适配微信公众号格式的 HTML 日报保存到本地，然后自动发布到公众号草稿箱。当用户提到"生成GitHub热榜日报"、"GitHub热门仓库报告"、"GitHub trending日报"、"GitHub热榜"、"GitHub热门项目"、"github hot daily"、"github trending report"时触发此技能。
---

# GitHub 热门仓库日报生成与发布

自动完成：GitHub Trending 抓取 → Search API → AI 分析 → 生成 HTML 日报 → 保存本地 → 发布微信公众号

## 前置条件

- curl 已安装
- jq 已安装（`brew install jq`）
- WECHAT_API_KEY 环境变量已设置（在 `/Users/guohua/.env` 中）
- 可选：GITHUB_TOKEN 环境变量（提高 API 速率限制，无 token 时限制 10 次/分钟）

## 完整工作流

### Phase 1: 预检

```bash
command -v curl &>/dev/null || { echo "错误: curl 未安装"; exit 1; }
command -v jq &>/dev/null || { echo "错误: jq 未安装"; exit 1; }
cat /Users/guohua/.env | grep WECHAT_API_KEY
```

### Phase 2: 获取三类 GitHub 数据

**并行**执行三类数据获取：trending 页面抓取（2类）+ Search API（1类）。

#### 数据类别

| 类别 | 数据源 | 说明 | 关键字段 |
|------|--------|------|----------|
| 今日热门 Top20 | 抓取 `github.com/trending`（daily） | 今日新增 Star 最多的项目 | full_name, description, language, stargazers_count, **stars_period** |
| 本周热门 Top20 | 抓取 `github.com/trending?since=weekly` | 本周新增 Star 最多的项目 | full_name, description, language, stargazers_count, **stars_period** |
| 近期活跃高星 Top20 | GitHub Search API `pushed:>3天前 stars:>=10000` | 近3天有推送且 1万+ 星的成熟项目 | full_name, stargazers_count, forks_count, language |

**执行方式**：使用脚本并行获取三类数据

```bash
python3 ~/.claude/skills/github-hot-daily/scripts/fetch_github_trending.py 2>/tmp/gh_fetch.log > /tmp/github_trending_data.json
```

**验证**：检查 JSON 输出中三个数组的长度，0 表示该类别获取失败（不阻塞其他类别）。

**关键字段说明**：
- `stars_period`：今日/本周热门中，该项目在该时间段内新增的 Star 数（如 "今日+1,234" 或 "本周+5,678"）
- `stargazers_count`：项目总 Star 数
- `forks_count`：项目总 Fork 数（仅活跃高星类别显示）

### Phase 3: AI 智能分析

读取 JSON 数据，执行以下分析：

#### 3a. 中文介绍生成

为三类榜单中的**每个项目**生成中文介绍（`description_cn` 字段）：
- 基于英文 description 翻译/意译，补充项目定位和核心功能说明
- 每条中文介绍 15-30 字，简洁精准，突出项目价值
- 示例：英文 "An adaptive Web Scraping framework" → 中文 "自适应网页爬虫框架，智能应对反爬策略"
- description 为 "No description" 时，根据项目名和上下文推断项目定位

#### 3b. 语言热度分布

统计所有项目中编程语言出现频次，生成 Top 5 语言排行（含项目数和占比）。

#### 3c. 趋势洞察

生成 3-5 条趋势洞察，覆盖：
- 当前最受关注的技术领域（AI/LLM、Web开发、DevOps、安全等）
- 新兴语言/框架的崛起趋势
- 值得关注的项目类型模式
- 今日与本周热门的对比分析

#### 3d. 精选推荐

从三类榜单中选出 3-5 个最值得关注的"编辑推荐"项目：
- 优先选择创新性强、实用价值高、Star 增速快的项目
- 每个项目给出 1-2 句推荐理由

### Phase 4: 生成 HTML 日报

文件保存路径：`/Users/guohua/guohua/wechat_hot_github/`
文件命名：`github-hot-{YYYYMMDD-HHmmss}.html`

**关键约束：微信公众号不支持 `<style>` 标签和 class 属性，所有样式必须内联。使用 `<section>` 代替 `<div>`。最大宽度 677px。**

#### 标题格式

- H1 标题：`GitHub 热门仓库日报 | {YYYY年MM月DD日}`（日期直接显示在标题中）
- 日期不再单独用 `<p>` 标签显示

#### HTML 模板文件

**模板路径**：`/Users/guohua/.claude/skills/github-hot-daily/template.html`
**生成脚本**：`/Users/guohua/.claude/skills/github-hot-daily/scripts/generate_html.py`

**生成流程**：

1. 将 Phase 2-3 处理和 AI 分析后的数据组装为 JSON 文件
2. 调用 Python 脚本读取模板并填充数据：

```bash
python3 ~/.claude/skills/github-hot-daily/scripts/generate_html.py data.json output.html
```

3. 脚本自动定位同目录的 `template.html`，替换 `{{占位符}}` 后生成最终 HTML

**模板占位符说明**：

| 占位符 | 说明 | 数据来源 |
|--------|------|----------|
| `{{DATE_STR}}` | 中文日期（如"2026年05月08日"） | 当前日期 |
| `{{TODAY_COUNT}}` | 今日热门项目数 | `len(today)` |
| `{{WEEKLY_COUNT}}` | 本周热门项目数 | `len(weekly)` |
| `{{ACTIVE_COUNT}}` | 活跃高星项目数 | `len(active)` |
| `{{RECOMMENDATIONS_SECTION}}` | 编辑推荐区域（含标题+卡片列表） | AI 分析生成 |
| `{{TODAY_LIST}}` | 今日热门项目卡片列表 | trending 数据渲染 |
| `{{WEEKLY_LIST}}` | 本周热门项目卡片列表 | trending 数据渲染 |
| `{{ACTIVE_LIST}}` | 活跃高星项目卡片列表 | Search API 数据渲染 |
| `{{LANGUAGE_SECTION}}` | 语言热度排行区域（含标题+进度条） | language_stats 数据渲染 |
| `{{INSIGHTS_SECTION}}` | 趋势洞察区域（含标题+洞察条目） | AI 分析生成 |

**模板设计要点（已针对手机端优化）**：
- 排名序号内联在项目名行内，不占独立 flex 列（节省横向空间）
- 项目名允许自然换行，不做 white-space:nowrap 截断
- 中文介绍蓝色小字缩进对齐（padding-left:12px）
- 英文描述灰色文字缩进对齐
- 语言圆点+Star+期间增量紧凑行内排列
- 数据概览用 display:flex 三等分（flex:1），确保占比均匀
- 所有样式内联，兼容微信渲染

**内容模块顺序**（模板中从上到下）：
1. 标题 + 渐变分割线
2. 数据概览（今日/本周/活跃 三等分 flex）
3. 编辑推荐
4. 语言热度排行
5. 趋势洞察
6. 今日热门 Top 20
7. 本周热门 Top 20
8. 近期活跃高星 Top 20
9. 页脚

### Phase 5: 保存文档

```bash
mkdir -p /Users/guohua/guohua/wechat_hot_github

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILEPATH="/Users/guohua/guohua/wechat_hot_github/github-hot-${TIMESTAMP}.html"
```

使用 Write 工具将 HTML 内容写入 FILEPATH。

### Phase 6: 发布到微信公众号

使用 wechat-article-publisher 技能发布：

```bash
# Step 1: 确认 API Key
cat /Users/guohua/.env | grep WECHAT_API_KEY

# Step 2: 获取公众号列表
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py list-accounts

# Step 3: 发布 HTML 文件
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py publish \
  --appid <wechatAppid> \
  --html /Users/guohua/guohua/wechat_hot_github/github-hot-{TIMESTAMP}.html
```

发布成功后告知用户：
- 本地文件已保存至 `/Users/guohua/guohua/wechat_hot_github/github-hot-{TIMESTAMP}.html`
- 文章已发布到公众号草稿箱
- 提醒用户登录微信公众平台预览并手动发布

### Phase 7: 错误处理

| 场景 | 处理方式 |
|------|----------|
| curl/jq 未安装 | 中止 Phase 1，显示安装命令 |
| Trending 页面抓取失败 | 对应榜单区标注"数据获取失败"，继续其他榜单 |
| Search API 返回 rate limit | 如有 GITHUB_TOKEN 重试一次，否则告知用户设置 token |
| 三类数据全部失败 | 仍生成包含标题和说明的 HTML，在榜单区标注"数据获取异常" |
| WECHAT_API_KEY 未配置 | 完成 Phase 4-5 保存 HTML，跳过 Phase 6，告知配置方法 |
| WeChat API 返回 ACCOUNT_TOKEN_EXPIRED | 告知用户到 wx.limyai.com 重新授权，提供本地文件路径 |
| WeChat API 返回其他错误 | 重试 1 次，仍失败则告知用户并提供本地文件路径 |
| 最多重试 1 次 | 不无限重试 |

**核心原则：不让单个数据源的失败阻塞整个流水线。**

## 使用示例

| 用户输入 | 执行范围 |
|----------|----------|
| "生成GitHub热榜日报" | Phase 1-6 全流程 |
| "GitHub热门仓库报告并发布" | Phase 1-6 全流程 |
| "只获取GitHub trending数据" | Phase 1-2，展示 Markdown 摘要 |
| "发布今天的GitHub热榜日报" | 跳到 Phase 6，查找当天最新文件 |
| "分析GitHub开源趋势" | Phase 1-3，重点输出趋势分析 |

## 查找当天最新文件

如用户说"发布今天的GitHub热榜日报"但未指定文件，自动查找：

```bash
ls -t /Users/guohua/guohua/wechat_hot_github/github-hot-*.html | head -1
```

## 黑名单项目配置

可以在 `blacklist.json` 中配置不需要出现在日报中的项目。文件路径：`~/.claude/skills/github-hot-daily/blacklist.json`

```json
{
  "projects": [
    "owner/repo",
    "another-owner/another-repo"
  ]
}
```

- 将项目的 `full_name`（如 `facebook/react`）添加到 `projects` 数组中即可过滤
- 过滤在数据获取阶段执行，被过滤的项目不会出现在任何榜单中
- AI 分析阶段（中文介绍、趋势洞察、编辑推荐）也不会涉及黑名单项目

## 重要约束

1. **今日/本周热门：抓取 GitHub Trending 页面**，获取真正的新增 Star 排名
2. **活跃高星：使用 GitHub Search API**，获取近期推送的万星项目
3. **数据获取并行执行**提升速度
4. **今日/本周热门必须展示 `stars_period`**（期间新增 Star 数），这是核心差异化数据
5. **不无限重试**：失败数据源跳过并标注原因
6. **HTML 全部内联样式**：微信公众号不支持 `<style>` 标签
7. **使用 `<section>` 而非 `<div>`**：微信渲染兼容
8. **最大宽度 677px**：微信文章标准宽度
9. **卡片式布局替代表格**：优化手机端阅读体验
10. **只保存到草稿箱**：不自动正式发布，用户手动操作
11. **description 为 null 时显示 "No description"**
12. **HTML 模板独立维护**：模板存放在 `template.html`，`generate_html.py` 读取模板并填充占位符，保证每次生成格式一致
