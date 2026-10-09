from abc import ABC, abstractmethod


class ScrapeResult(dict):
    """Normalized strategy output."""


class ScrapingStrategy(ABC):
    name = "base"

    @abstractmethod
    def fetch_html(self, url: str) -> ScrapeResult:
        raise NotImplementedError
