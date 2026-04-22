import asyncio
import concurrent.futures
import logging
import re

import httpx
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

TAG_PATTERN = re.compile(r"<[^>]+>")
MULTI_SPACE = re.compile(r"\s+")

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")

_SKIP_TAGS = {
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    "noscript",
    "iframe",
    "svg",
}

_SKIP_ROLES = {"navigation", "banner", "contentinfo", "complementary"}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

_CHALLENGE_KEYWORDS = {"欢迎来到", "验证", "安全检查", "请登录", "访问被限制", "人机验证", "点击继续"}

_MIN_CONTENT_LENGTH = 200


def _is_challenge_page(text: str) -> bool:
    if len(text) < _MIN_CONTENT_LENGTH:
        return True
    clean = MULTI_SPACE.sub(" ", text).strip()
    for kw in _CHALLENGE_KEYWORDS:
        if kw in clean:
            return True
    return False


def _extract_text(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(_SKIP_TAGS):
        tag.decompose()

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    for el in soup.find_all(attrs={"role": True}):
        if el.get("role", "").lower() in _SKIP_ROLES:
            el.decompose()

    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    text = main.get_text(separator="\n") if main else soup.get_text(separator="\n")

    lines = [MULTI_SPACE.sub(" ", line).strip() for line in text.split("\n")]
    lines = [l for l in lines if l and len(l) > 1]
    clean_text = "\n".join(lines)

    return {"title": title, "text": clean_text}


class ScraperClient:
    def _fetch_httpx(self, url: str) -> dict[str, str]:
        resp = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=30)
        html = resp.text

        if resp.status_code >= 400 and len(html) < 100:
            raise ValueError(f"HTTP {resp.status_code}: {url}")

        result = _extract_text(html)

        if _is_challenge_page(result["text"]):
            raise ValueError(f"anti_scraping:{resp.status_code}")

        return result

    def _fetch_jina(self, url: str) -> dict[str, str]:
        r = httpx.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain"},
            timeout=30,
        )
        if r.status_code >= 400:
            raise ValueError(f"jina_error:{r.status_code}: {r.text[:200]}")

        text = r.text.strip()
        title = ""
        for line in text.split("\n"):
            if line.startswith("Title: "):
                title = line[7:].strip()
                break

        body_lines = []
        in_body = False
        for line in text.split("\n"):
            if line.startswith("---"):
                in_body = not in_body
                continue
            if in_body:
                body_lines.append(line)

        if not body_lines:
            body_lines = [l for l in text.split("\n") if l.strip() and not l.startswith(("Title:", "URL:", "Source:"))]

        clean = "\n".join(l.strip() for l in body_lines if len(l.strip()) > 1)
        return {"title": title, "text": clean}

    def _sync_fetch(self, url: str) -> dict[str, str]:
        last_err = None

        try:
            result = self._fetch_httpx(url)
            logger.info(f"httpx OK: {url[:50]}... len={len(result['text'])}")
            return result
        except ValueError as e:
            last_err = e
            err_str = str(e)
            if not err_str.startswith("anti_scraping"):
                raise

        logger.warning(f"httpx blocked ({last_err}), trying jina reader: {url[:50]}")
        try:
            result = self._fetch_jina(url)
            logger.info(f"jina OK: {url[:50]}... len={len(result['text'])}")
            return result
        except Exception as e:
            last_err = e
            logger.warning(f"jina failed: {e}")

        domain = re.sub(r"https?://([^/]+).*", r"\1", url)
        raise ValueError(
            f"无法抓取该页面（{domain} 可能有反爬机制）。"
            f"建议：1) 手动复制页面正文粘贴到「文本」模式提交；"
            f"2) 如需支持更多站点，可在设置中配置 Jina Reader API Key。"
        )

    async def fetch_url(self, url: str) -> dict[str, str]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, self._sync_fetch, url)
        logger.info(f"URL fetched: {url[:60]}... title={result['title'][:40]} len={len(result['text'])}")
        return result

    async def close(self):
        pass


scraper_client = ScraperClient()
