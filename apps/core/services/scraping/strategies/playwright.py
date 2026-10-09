from apps.core.services.scraping.strategies.base import ScrapeResult, ScrapingStrategy
from apps.core.services.scraping.validators import validate_url


class PlaywrightStrategy(ScrapingStrategy):
    name = "playwright"

    def fetch_html(self, url: str, timeout: int = 20) -> ScrapeResult:
        safe_url = validate_url(url)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed.") from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()

                def guard(route):
                    try:
                        validate_url(route.request.url)
                    except Exception:
                        route.abort()
                        return
                    route.continue_()

                page.route("**/*", guard)
                response = page.goto(safe_url, wait_until="domcontentloaded", timeout=timeout * 1000)
                page.wait_for_load_state("networkidle", timeout=10_000)
                final_url = validate_url(page.url)
                return ScrapeResult(
                    url=final_url,
                    html=page.content(),
                    status_code=response.status if response else 200,
                    content_type="text/html",
                    encoding="utf-8",
                    strategy=self.name,
                )
            finally:
                browser.close()
