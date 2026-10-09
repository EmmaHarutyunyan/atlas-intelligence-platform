from apps.core.services.scraping.strategies.beautifulsoup import BeautifulSoupStrategy
from apps.core.services.scraping.strategies.playwright import PlaywrightStrategy
from apps.core.services.scraping.strategies.selenium import SeleniumStrategy

__all__ = ["BeautifulSoupStrategy", "PlaywrightStrategy", "SeleniumStrategy"]
