from apps.core.services.scraping.strategies.base import ScrapeResult, ScrapingStrategy
from apps.core.services.scraping.validators import validate_url


class SeleniumStrategy(ScrapingStrategy):
    name = "selenium"

    def fetch_html(self, url: str, timeout: int = 20) -> ScrapeResult:
        safe_url = validate_url(url)
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:
            raise RuntimeError("Selenium is not installed.") from exc

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(30)
            driver.get(safe_url)
            final_url = validate_url(driver.current_url)
            return ScrapeResult(
                url=final_url,
                html=driver.page_source,
                status_code=200,
                content_type="text/html",
                encoding="utf-8",
                strategy=self.name,
            )
        finally:
            driver.quit()
