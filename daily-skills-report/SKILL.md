---
name: daily-skills-report
description: 自动生成每日热门 Skills 日报并发布到微信公众号。抓取 skills.sh 上的 Trending、Hot 和历史热门 Skills，生成 HTML 文档保存到本地，然后自动发布到公众号草稿箱。当用户提到"生成skills日报"、"发布skill报告"、"每日skill总结"、"skill日更"、"写一篇skill推荐文章并发布"时触发此技能。
---

# 每日热门 Skills 日报生成与发布

自动完成：抓取数据 → 生成 HTML 日报 → 保存本地 → 发布微信公众号

## 完整工作流

### Phase 1: 数据抓取

并行抓取 skills.sh 的三个数据源：

#### 1.1 Trending Skills（本周趋势）

```bash
curl -s "https://skills.sh/trending" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" | python3 -c "
import sys, re, json
html = sys.stdin.read()
chunks = re.findall(r'self\.__next_f\.push\(\[1,\"(.*?)\"\]\)', html, re.DOTALL)
all_text = ''
for c in chunks:
    try: all_text += c.encode().decode('unicode_escape')
    except: pass
match = re.search(r'\"initialSkills\":\[(.*?)\]', all_text)
if match:
    skills = json.loads('[' + match.group(1) + ']')
    print(json.dumps(skills))
else:
    print('[]')
"
```

字段：`source`, `skillId`, `name`, `installs`

#### 1.2 Hot Skills（新晋热门）

```bash
curl -s "https://skills.sh/hot" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" | python3 -c "
import sys, re, json
html = sys.stdin.read()
chunks = re.findall(r'self\.__next_f\.push\(\[1,\"(.*?)\"\]\)', html, re.DOTALL)
all_text = ''
for c in chunks:
    try: all_text += c.encode().decode('unicode_escape')
    except: pass
match = re.search(r'\"initialSkills\":\[(.*?)\]', all_text)
if match:
    skills = json.loads('[' + match.group(1) + ']')
    print(json.dumps(skills))
else:
    print('[]')
"
```

字段：`source`, `skillId`, `name`, `installs`, `installsYesterday`, `change`

#### 1.3 分类搜索（可选补充）

当需要丰富内容时，使用 `npx skills find` 按类别搜索：

```bash
npx skills find "AI agent"
npx skills find "web development"
npx skills find "devops"
```

### Phase 2: 数据处理

将原始数据整理为三个 Top 20 榜单：

| 榜单 | 数据来源 | 排序依据 | 说明 |
|------|----------|----------|------|
| **本周趋势 Top 20** | trending 数据 | 页面原始顺序 | 本周安装增速最快 |
| **新晋热门 Top 20** | hot 数据 | `change` 降序 | 日增量最大，标注 NEW |
| **历史热门 Top 20** | trending 数据 | `installs` 降序 | 历史累计安装量最高 |

日报中三个榜单的展示顺序为：本周趋势 → 新晋热门 → 历史热门（把最新动态放前面，历史数据放后面）。

处理规则：
- 安装量格式化：≥1000 用 "K" 后缀（如 28.1K），<1000 用原数字
- Hot 榜中 `installsYesterday == 0 && change == installs` 的标记为 **NEW**（全新上线）
- 跨榜出现的 skill 在趋势榜中标注 🔥
- 去重：三个榜单独立展示，不做跨榜去重

### Phase 3: 生成 HTML 日报

文件保存路径：`/Users/guohua/guohua/wechat_docs/`
文件命名：`skills-daily-{YYYYMMDD-HHmmss}.html`

**重要：微信公众号不支持 `<style>` 标签和 class 属性，所有样式必须内联。使用 `<section>` 标签代替 `<div>`。最大宽度 677px。**

HTML 生成脚本：`/Users/guohua/.claude/skills/daily-skills-report/generate_html.py`
HTML 模板文件：`/Users/guohua/.claude/skills/daily-skills-report/template.html`

**生成流程：**

1. 将 Phase 1-2 抓取和处理后的数据组装为 JSON 文件（见下方格式）
2. 调用 Python 脚本读取模板并填充数据：

```bash
python3 ~/.claude/skills/daily-skills-report/generate_html.py data.json output.html
```

3. 脚本会自动替换模板中的 `{{占位符}}` 并生成最终 HTML

**数据 JSON 格式：**

```json
{
  "overview": {
    "trending_new": 5,
    "hot_new": 3,
    "recommendations": 3,
    "insights": 4
  },
  "recommendations": [
    {
      "type": "trending|quality|new",
      "rank": 1,
      "name": "skill-name",
      "source": "owner/repo",
      "installs_str": "28.1K 安装",
      "tags": "标签：AI绘图 / 工具类",
      "detail": "4-6 句详细介绍..."
    }
  ],
  "trending": [
    {
      "name": "skill-name",
      "source": "owner/repo",
      "installs": 28100,
      "desc": "一句话简介（15-30字）",
      "cross_list": true
    }
  ],
  "hot": [
    {
      "name": "skill-name",
      "source": "owner/repo",
      "installs": 325,
      "change": 325,
      "desc": "一句话简介（15-30字）",
      "is_new": true
    }
  ],
  "historical": [
    {
      "name": "skill-name",
      "source": "owner/repo",
      "installs": 28100,
      "desc": "一句话简介（15-30字）"
    }
  ],
  "insights": {
    "summary": "2-3 句总结今日趋势",
    "item_1": "洞察 1：哪些来源/组织占据主导",
    "item_2": "洞察 2：值得关注的新晋 skill 及其亮点",
    "item_3": "洞察 3：推荐安装的 skill 及理由",
    "item_4": "洞察 4（可选，可留空字符串）"
  }
}
```

**模板设计要点（已针对手机端优化）：**
- 排名徽章内联在名称行内，不占独立 flex 列（节省 ~22px 宽度）
- 徽章 16×16px，font-size:9px，vertical-align:middle
- Skill 名称允许自然换行，不做 white-space:nowrap 截断
- 来源和简介缩进对齐（padding-left:20px）
- 右侧数据列紧凑排列，padding-left:6px
- 概览统计条用 display:table 四列布局
- 所有样式内联，兼容微信渲染

### 榜单格式说明

所有三个榜单统一使用 **flex 列表布局**（而非 table，手机端更友好）：
- 每行包含：排名徽章（内联在名称行）+ 名称+来源+简介（左）+ 安装量/日增（右）
- 排名 1-3 使用彩色圆形徽章（红/橙/琥珀），4+ 使用灰色数字
- Skill 名称加粗，来源和简介用小字灰色附在下方
- 安装量/日增数据右对齐，日增数字用红色 `color:#e74c3c`
- 本周趋势中跨榜出现的 Skill 在安装量后标注 🔥
- 新晋热门中全新上线的标注 🆕（在日增列）
- 新晋热门右列显示两行：日增量（大红字）+ 总安装量（小灰字）
- 历史热门只显示总安装量，不显示日增量
- 榜单下方用浅灰背景圆角框标注安装命令格式

### 简要介绍要求

每个榜单中的 Skill 都必须附带一句话简要介绍（区别于"今日推荐"的 4-6 句详细介绍）：
- **字数**：15-30 字，一句话说清楚这个 Skill 做什么
- **风格**：客观描述核心功能，不带主观评价
- **示例**：
  - ai-image-generation → "调用多种 AI 模型实现文本生成图像"
  - grill-me → "以烤问风格深度审查代码质量和架构设计"
  - entra-agent-id → "为 AI Agent 提供企业级 Entra 身份认证与审计"

### Phase 4: 使用 find-skills 补充详细说明

从 Top 20 中挑选 3-5 个最具代表性的 skill，用 `npx skills find` 获取更多信息。挑选原则：
- 历史热门中安装量最高或最具代表性的 1-2 个
- 本周趋势中增速最猛的 1-2 个
- 新晋热门中标记为 NEW 或日增最高的 1 个

每个推荐 skill 需要包含：
- **标签**：用 2-3 个关键词分类（如"AI绘图 / 工具类"、"代码审查 / 质量类"、"新晋 / 创新类"）
- **详细介绍**：4-6 句话，必须包含以下要素：
  1. 这个 Skill 做什么（核心功能）
  2. 解决了什么问题（痛点场景）
  3. 核心功能亮点（差异化特性）
  4. 适用人群和使用场景
  5. 如果是 NEW，强调新上线背景和爆发原因
  6. 与同类 Skill 的差异优势（如有）

### Phase 5: 保存文档

```bash
# 确保目录存在
mkdir -p /Users/guohua/guohua/wechat_docs

# 生成时间戳文件名
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILEPATH="/Users/guohua/guohua/wechat_docs/skills-daily-${TIMESTAMP}.html"

# 将数据写入临时 JSON 文件，然后调用 Python 脚本生成 HTML
# 1. 先将组装好的数据 JSON 写入 /tmp/skills-data-${TIMESTAMP}.json（使用 Write 工具）
# 2. 执行生成脚本：
python3 ~/.claude/skills/daily-skills-report/generate_html.py /tmp/skills-data-${TIMESTAMP}.json "${FILEPATH}"
```

### Phase 6: 发布到微信公众号

使用 wechat-article-publisher skill 发布刚刚保存的文件：

```bash
# Step 1: 检查 API Key
cat .env | grep WECHAT_API_KEY

# Step 2: 获取公众号列表
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py list-accounts

# Step 3: 发布（使用 Phase 5 中生成的 HTML 文件路径，注意使用 --html 参数）
python3 ~/.claude/skills/wechat-article-publisher/scripts/wechat_api.py publish \
  --appid <wechatAppid> \
  --html /Users/guohua/guohua/wechat_docs/skills-daily-{TIMESTAMP}.html
```

发布成功后告知用户：
- 文章已保存到本地路径
- 文章已发布到公众号草稿箱
- 提醒用户登录微信公众平台预览并正式发布

### Phase 7: 错误处理

- 如果 skills.sh 抓取失败：仍然生成日报，标注"数据获取失败"，跳过对应榜单
- 如果微信公众号发布失败：告知用户文件已保存到本地，手动发布方法
- 如果 API Key 未配置：提醒用户配置 `.env` 文件，不阻塞日报生成

## 使用示例

用户说：
- "生成今天的 skills 日报" — 完整执行 Phase 1-6
- "写一篇 skill 推荐文章并发布" — 完整执行 Phase 1-6
- "抓取热门 skills 数据" — 只执行 Phase 1-3，保存文件
- "发布今天的 skills 日报" — 跳到 Phase 6，查找当天最新文件并发布

## 查找当天最新文件

如果用户说"发布今天的 skills 日报"但未指定文件，自动查找：

```bash
ls -t /Users/guohua/guohua/wechat_docs/skills-daily-*.html | head -1
```
