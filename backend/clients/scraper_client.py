import logging

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)


class ScraperClient:
    def __init__(self):
        self.client = AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

    async def fetch_url(self, url: str) -> dict[str, str]:
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            html = resp.text

            try:
                from readability import Document
                doc = Document(html)
                title = doc.title()
                text = doc.summary()
            except Exception as e:
                logger.warning(f"readability extraction failed for {url}: {e}, using raw HTML")
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self._text = []
                        self._in_script = False
                        self._in_style = False

                    def handle_starttag(self, tag, attrs):
                        if tag in ("script", "style"):
                            if tag == "script":
                                self._in_script = True
                            elif tag == "style":
                                self._in_style = True

                    def handle_endtag(self, tag):
                        if tag == "script":
                            self._in_script = False
                        elif tag == "style":
                            self._in_style = False

                    def handle_data(self, data):
                        if not (self._in_script or self._in_style):
                            stripped = data.strip()
                            if stripped:
                                self._text.append(stripped)

                    def get_text(self):
                        return "\n".join(self._text)

                extractor = TextExtractor()
                extractor.feed(html)
                title = ""
                text = extractor.get_text()

            return {"title": title or "", "text": text.strip()}

        except HTTPError as e:
            raise ValueError(f"Failed to fetch URL: {url}, error: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching URL: {url}, error: {e}")

    async def close(self):
        await self.client.aclose()


scraper_client = ScraperClient()
