from apps.core.services.scraping.fetchers.http import fetch
from apps.core.services.scraping.strategies.base import ScrapeResult, ScrapingStrategy


class BeautifulSoupStrategy(ScrapingStrategy):
    name = "beautifulsoup"

    def fetch_html(self, url: str, timeout: int = 20) -> ScrapeResult:
        result = fetch(url, timeout=timeout)
        return ScrapeResult(
            url=result.url,
            html=result.text,
            status_code=result.status_code,
            content_type=result.content_type,
            encoding=result.encoding,
            strategy=self.name,
        )
