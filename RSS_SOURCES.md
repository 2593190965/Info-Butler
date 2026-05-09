# 推荐的 RSS 订阅源

## 🇨🇳 中文 RSS 源

### 科技类

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| 阮一峰的网络日志 | https://www.ruanyifeng.com/blog/atom.xml | 科技、编程、思考 |
| 少数派 | https://sspai.com/feed | 数字生活、效率工具 |
| 利器 | https://liqi.io/feed/ | 工具、工作流 |
| 极客公园 | https://www.geekpark.net/rss | 科技资讯 |
| 36氪 | https://36kr.com/feed | 创投、商业 |
| 虎嗅 | https://www.huxiu.com/rss/0.xml | 商业、科技 |
| InfoQ 中文 | https://www.infoq.cn/feed | 技术文章 |

### 综合资讯

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| 知乎每日精选 | https://www.zhihu.com/rss | 高质量问答 |
| 豆瓣最受欢迎的影评 | https://www.douban.com/feed/review/movie | 电影评论 |
| 豆瓣最受欢迎的书评 | https://www.douban.com/feed/review/book | 书籍评论 |
| V2EX | https://www.v2ex.com/index.xml | 技术讨论 |
| 掘金前端 | https://juejin.cn/rss | 前端技术 |

### 博客类

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| 阮一峰 | https://www.ruanyifeng.com/blog/atom.xml | 知名博主 |
| 小茗同学 | https://blog.twofei.com/feed/ | 技术博客 |
| 王垠 | https://yinwang.org/ | 编程思想 |
| 木头有个小花园 | https://wood-garden.com/feed/ | 生活、技术 |

### 技术文档

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| Python Weekly | https://www.pythonweekly.com/feed | Python 资讯 |
| JavaScript Weekly | https://javascriptweekly.com/rss | JS 资讯 |
| Go Weekly | https://golangweekly.com/rss | Go 资讯 |
| DB Weekly | https://dbweekly.com/rss | 数据库资讯 |

---

## 🌍 英文 RSS 源

### 科技资讯

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| TechCrunch | https://techcrunch.com/feed/ | 科技资讯 |
| The Verge | https://www.theverge.com/rss/index.xml | 科技、产品 |
| Ars Technica | https://feeds.arstechnica.com/arstechnica/index | 深度科技报道 |
| Hacker News | https://hnrss.org/frontpage | 技术社区热门 |
| Reddit Programming | https://www.reddit.com/r/programming/.rss | 编程讨论 |

### 技术博客

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| Martin Fowler | https://martinfowler.com/feed.atom | 软件架构 |
| Joel on Software | https://www.joelonsoftware.com/feed/ | 软件开发 |
| CSS-Tricks | https://css-tricks.com/feed/ | 前端技术 |
| Smashing Magazine | https://www.smashingmagazine.com/feed/ | 设计、开发 |

---

## 🎮 娱乐类

| 名称 | RSS 地址 | 说明 |
|------|---------|------|
| Bilibili 热门 | https://rsshub.app/bilibili/ranking/0/3 | B站热门视频 |
| 抖音热门 | https://rsshub.app/douyin/trending | 抖音热门 |
| 微博热搜 | https://rsshub.app/weibo/search/hot | 微博热搜 |

---

## 🔧 自定义 RSS 源

### 使用 RSSHub 生成 RSS

如果网站没有 RSS，可以使用 [RSSHub](https://docs.rsshub.app/) 生成：

**今日头条 RSS 示例：**
```
# 今日头条 - 科技频道
https://rsshub.app/toutiao/category/tech

# 今日头条 - 热门
https://rsshub.app/toutiao/hot

# 今日头条 - 特定关键词
https://rsshub.app/toutiao/keyword/AI
```

**使用方法：**
1. 访问 https://docs.rsshub.app/
2. 搜索网站名称（如"今日头条"）
3. 复制生成的 RSS 地址
4. 粘贴到 Info-Butler 的 RSS 订阅中

---

## ⚠️ 注意事项

### 1. RSS 源识别

**✅ 正确的 RSS 源特征：**
- URL 包含 `/rss`, `/feed`, `/atom.xml`
- 返回 XML 格式（以 `<?xml version="1.0"?>` 开头）
- 包含 `<rss>` 或 `<feed>` 标签

**❌ 不是 RSS 源：**
- 普通网页 HTML
- 需要 JavaScript 的动态页面
- 文章详情页 URL

### 2. 测试 RSS 源

**方法 1：浏览器测试**
```
直接在浏览器中打开 RSS URL
应该看到 XML 格式的内容
```

**方法 2：命令行测试**
```bash
curl -s https://www.ruanyifeng.com/blog/atom.xml | head -5
# 应该看到 <?xml version="1.0" encoding="UTF-8"?>
```

**方法 3：在线工具**
- https://validator.w3.org/feed/
- 粘贴 RSS 地址，验证是否有效

---

## 📝 如何添加 RSS 订阅

### 在 Info-Butler 中添加：

1. 访问前端页面：http://localhost:5175
2. 点击左侧菜单"RSS 管理"
3. 点击"添加订阅"
4. 填写信息：
   - 名称：`阮一峰的网络日志`
   - URL：`https://www.ruanyifeng.com/blog/atom.xml`
   - 抓取间隔：`3600` 秒（1小时）
5. 点击"确定"
6. 点击"立即抓取"测试

---

## 🚀 批量导入 RSS 源

可以创建一个脚本批量导入优质 RSS 源：

```python
# scripts/import_rss.py
import asyncio
import httpx

RSS_SOURCES = [
    {"name": "阮一峰的网络日志", "url": "https://www.ruanyifeng.com/blog/atom.xml"},
    {"name": "少数派", "url": "https://sspai.com/feed"},
    {"name": "InfoQ 中文", "url": "https://www.infoq.cn/feed"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
]

async def import_rss():
    async with httpx.AsyncClient() as client:
        for rss in RSS_SOURCES:
            response = await client.post(
                "http://localhost:8001/api/v1/rss",
                headers={"X-API-Key": "dev-api-key-2026"},
                json=rss
            )
            print(f"✅ {rss['name']}: {response.status_code}")

asyncio.run(import_rss())
```

---

## 🔍 如果要爬取非 RSS 网站

如果确实需要爬取今日头条等非 RSS 网站，需要修改代码：

### 方案：添加网页抓取功能

```python
# backend/services/web_scraper.py

async def scrape_website(url: str) -> list[dict]:
    """抓取普通网站（非 RSS）"""
    from backend.clients.scraper_client import scraper_client

    # 抓取网页
    result = await scraper_client.fetch_url(url)

    # 提取文章列表（需要根据具体网站定制）
    articles = extract_articles(result["text"])

    return articles

def extract_articles(html: str) -> list[dict]:
    """从 HTML 中提取文章列表"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    # 根据网站结构提取
    for item in soup.select('.article-item'):
        articles.append({
            'title': item.select_one('.title').text,
            'url': item.select_one('a')['href'],
            'content': item.select_one('.summary').text,
        })

    return articles
```

---

## 📚 相关资源

- **RSSHub 官方文档**：https://docs.rsshub.app/
- **RSS 规范**：https://www.rssboard.org/rss-specification
- **Feed 验证工具**：https://validator.w3.org/feed/
- **优秀 RSS 源推荐**：https://github.com/ttglinkao/awesome-rss-feeds

---

需要我帮你添加一些优质的 RSS 源吗？
