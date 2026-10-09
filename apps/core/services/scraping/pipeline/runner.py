import logging
import time

from apps.core.services.scraping.exceptions import ScrapingError
from apps.core.services.scraping.extractors.generic import extract_page
from apps.core.services.scraping.deduplication import stable_record_hash
from apps.core.services.scraping.pagination import find_next_url
from apps.core.services.scraping.strategies import BeautifulSoupStrategy, PlaywrightStrategy, SeleniumStrategy
from apps.core.services.scraping.validators import validate_url

logger = logging.getLogger(__name__)
STRATEGIES = {"beautifulsoup": BeautifulSoupStrategy, "playwright": PlaywrightStrategy, "selenium": SeleniumStrategy}


def _useful(result: dict) -> bool:
    stats = result["data"]["statistics"]
    return bool(result["title"] or stats["words"] >= 30 or result["structured_data"] or result["data"]["images"] or result["data"]["tables"])


def _fetch_with_strategy(name, url, timeout):
    raw = STRATEGIES[name]().fetch_html(url, timeout=timeout)
    return raw, extract_page(raw["html"], raw["url"], name)


def scrape(url: str, strategy: str = "automatic", custom_fields: dict | None = None, max_pages: int = 1, max_records: int = 200, timeout: int = 20, delay: float = 0.0) -> dict:
    safe_url = validate_url(url)
    if strategy == "automatic":
        order = ["beautifulsoup", "playwright", "selenium"]
    elif strategy in STRATEGIES:
        order = [strategy]
    else:
        raise ScrapingError("Unsupported scraping strategy.")

    first_result = None
    last_error = None
    attempted = []
    for name in order:
        attempted.append(name)
        try:
            raw = STRATEGIES[name]().fetch_html(safe_url, timeout=timeout)
            result = extract_page(raw["html"], raw["url"], name, custom_fields)
            if strategy != "automatic" or _useful(result) or name == order[-1]:
                first_result = result
                first_result["strategy_used"] = name
                first_result["data"]["technical"].update({"status_code": raw["status_code"], "final_url": raw["url"], "attempted_strategies": attempted})
                break
        except Exception as exc:
            last_error = exc
            logger.warning("Scraper strategy %s failed for %s: %s", name, safe_url, exc)
            if strategy != "automatic":
                break
    if first_result is None:
        if isinstance(last_error, ScrapingError):
            raise last_error
        raise ScrapingError("Atlas could not extract useful content from this website.") from last_error

    all_records = list(first_result["records"])
    current_url = first_result["url"]
    strategy_used = first_result["strategy_used"]
    for _page in range(1, max(1, min(max_pages, 20))):
        if len(all_records) >= max_records:
            break
        next_url = find_next_url(first_result["data"], current_url)
        if not next_url or next_url == current_url:
            break
        if delay:
            time.sleep(min(delay, 10))
        try:
            raw = STRATEGIES[strategy_used]().fetch_html(next_url, timeout=timeout)
            first_result = extract_page(raw["html"], raw["url"], strategy_used, custom_fields)
            current_url = raw["url"]
            all_records.extend(first_result["records"])
        except Exception as exc:
            logger.warning("Pagination stopped at %s: %s", next_url, exc)
            break

    all_records = all_records[:max_records]
    for item in all_records:
        item.setdefault("content", first_result["content"])
        item["content_hash"] = stable_record_hash(item)
        item.setdefault("data", first_result["data"])
    first_result["records"] = all_records
    first_result["data"]["technical"]["pages_processed"] = min(max_pages, 20)
    first_result["data"]["technical"]["record_count"] = len(all_records)
    return first_result
