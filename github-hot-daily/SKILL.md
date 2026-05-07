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

#### HTML 设计规范（手机端优化）

**紧凑 flex 布局**（替代表格+inline-block，最大化横向空间）：

| 元素 | 设计 | 样式 |
|------|------|------|
| 排名徽章 | 16×16px 圆形数字，内联在项目名行 | `width:16px;height:16px;font-size:9px`，红/橙/琥珀色前3，灰色4+ |
| 项目名 | 加粗蓝色，徽章后直接跟文字，允许换行 | `font-weight:700;color:#0366d6;font-size:13px` |
| 中文介绍 | 蓝色小字，缩进20px对齐徽章后文字 | `font-size:10px;color:#0366d6;padding-left:20px` |
| 描述 | 灰色文字，缩进20px，允许自然换行不截断 | `font-size:11px;color:#6a737d;padding-left:20px` |
| 语言+Star+期间 | 缩进20px行内排列，紧凑间距 | `font-size:10px;color:#586069;padding-left:20px` |
| 卡片行 | flex布局，padding 7px 0 | `display:flex;align-items:flex-start;padding:7px 0` |
| 卡片容器 | 白底、细边框、圆角 | `border:1px solid #e1e4e8;border-radius:6px` |
| 行分隔 | 细线 | `border-bottom:1px solid #f2f2f2` |

**推荐卡片**：

| 元素 | 设计 | 样式 |
|------|------|------|
| 容器 | 蓝白背景+蓝色边框+圆角 | `background:#e8f4fd;border:1px solid #d0e4f7;border-radius:8px` |
| 推荐标签 | 蓝色小徽章 | `background:#0366d6;color:#fff;font-size:9px;border-radius:8px` |
| 中文介绍 | 蓝色小字（与项目卡片同格式） | `font-size:10px;color:#0366d6` |

**数据概览**（标题下方三栏统计）：

| 元素 | 样式 |
|------|------|
| 数字 | 16px 加粗，对应分类色（橙/蓝/绿） |
| 标签 | 10px 灰色 |
| 布局 | display:table 三列等分 |

**语言热度进度条**：

| 元素 | 样式 |
|------|------|
| 容器 | 灰底圆角卡片 |
| 标签 | 8px 彩色圆点 + 11px 加粗语言名 + 9px 灰色"N 个项目 · X%" |
| 进度条 | 5px 高圆角，对应语言色 |

**趋势洞察**：

| 元素 | 样式 |
|------|------|
| 容器 | 浅蓝背景+圆角 | `background:#f0f7ff;border-radius:8px` |
| 标题 | 11px 加粗 |
| 内容 | 10px 灰色，1.5 行高 |

#### 语言颜色映射

| 语言 | 颜色 | 语言 | 颜色 |
|------|------|------|------|
| Python | `#3572A5` | TypeScript | `#2b7489` |
| JavaScript | `#f1e05a` | Go | `#00ADD8` |
| Rust | `#dea584` | Java | `#b07219` |
| C++ | `#f34b7d` | C | `#555555` |
| Swift | `#ffac45` | Kotlin | `#A97BFF` |
| Ruby | `#701516` | Shell | `#89e051` |
| Dart | `#00B4AB` | HTML | `#e34c26` |
| CSS | `#563d7c` | Jupyter | `#DA5B0B` |
| 其他/空 | `#959da5` | | |

#### Star 数格式化

- < 1000: 原始数字（如 856）
- >= 1000: 保留1位小写 + k（如 1.2k, 9.8k, 463.0k）

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
