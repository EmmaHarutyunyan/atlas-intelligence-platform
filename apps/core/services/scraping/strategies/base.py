from abc import ABC, abstractmethod
from typing import Any


class ScrapeResult(dict[str, Any]):
    """Normalized strategy output."""


class ScrapingStrategy(ABC):
    name = "base"

    @abstractmethod
    def fetch_html(self, url: str, timeout: int = 20) -> ScrapeResult:
        raise NotImplementedError
