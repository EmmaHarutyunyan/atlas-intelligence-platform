import logging
import time
from typing import Any

from apps.core.services.scraping.deduplication import stable_record_hash
from apps.core.services.scraping.exceptions import ScrapingError
from apps.core.services.scraping.extractors.generic import extract_page
from apps.core.services.scraping.pagination import find_next_url
from apps.core.services.scraping.strategies import (
    BeautifulSoupStrategy,
    PlaywrightStrategy,
    SeleniumStrategy,
)
from apps.core.services.scraping.validators import validate_url

logger = logging.getLogger(__name__)

ScrapingData = dict[str, Any]

STRATEGIES = {
    "beautifulsoup": BeautifulSoupStrategy,
    "playwright": PlaywrightStrategy,
    "selenium": SeleniumStrategy,
}


def _useful(result: ScrapingData) -> bool:
    stats = result["data"]["statistics"]
    return bool(
        result["title"]
        or stats["words"] >= 30
        or result["structured_data"]
        or result["data"]["images"]
        or result["data"]["tables"]
    )


def _fetch_page(
    name: str,
    url: str,
    timeout: int,
    custom_fields: dict[str, Any] | None,
) -> tuple[ScrapingData, ScrapingData]:
    raw = STRATEGIES[name]().fetch_html(url, timeout=timeout)
    result = extract_page(raw["html"], raw["url"], name, custom_fields)
    return raw, result


def _select_strategy(
    url: str,
    strategy: str,
    timeout: int,
    custom_fields: dict[str, Any] | None,
) -> ScrapingData:
    if strategy == "automatic":
        order = ["beautifulsoup", "playwright", "selenium"]
    elif strategy in STRATEGIES:
        order = [strategy]
    else:
        raise ScrapingError("Unsupported scraping strategy.")

    attempted: list[str] = []
    last_error: Exception | None = None

    for name in order:
        attempted.append(name)

        try:
            raw, result = _fetch_page(name, url, timeout, custom_fields)

            if strategy != "automatic" or _useful(result):
                result["strategy_used"] = name
                result["data"]["technical"].update(
                    {
                        "status_code": raw["status_code"],
                        "final_url": raw["url"],
                        "attempted_strategies": attempted.copy(),
                    }
                )
                return result

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Scraper strategy %s failed for %s: %s",
                name,
                url,
                exc,
            )

            if strategy != "automatic":
                break

    if isinstance(last_error, ScrapingError):
        raise last_error

    raise ScrapingError("Atlas could not extract useful content from this website.") from last_error


def _paginate(
    result: ScrapingData,
    strategy: str,
    custom_fields: dict[str, Any] | None,
    max_pages: int,
    max_records: int,
    timeout: int,
    delay: float,
) -> ScrapingData:
    first_result = result
    records: list[ScrapingData] = []
    current_url: str = result["url"]
    seen_urls: set[str] = {current_url}
    pages_processed = 1

    def add_records(page: ScrapingData) -> None:
        for item in page["records"]:
            item.setdefault("content", page["content"])
            item.setdefault("data", page["data"])
            item["content_hash"] = stable_record_hash(item)
            records.append(item)

    add_records(result)

    page_limit = max(1, min(max_pages, 20))
    record_limit = max(1, max_records)

    while pages_processed < page_limit and len(records) < record_limit:
        next_url = find_next_url(result["data"], current_url)

        if not next_url:
            break

        try:
            safe_url = validate_url(next_url)

            if safe_url in seen_urls:
                break

            if delay:
                time.sleep(min(max(delay, 0), 10))

            raw, page_result = _fetch_page(
                strategy,
                safe_url,
                timeout,
                custom_fields,
            )

            current_url = raw["url"]

            if current_url in seen_urls:
                break

            seen_urls.add(current_url)
            pages_processed += 1
            add_records(page_result)
            result = page_result

        except Exception as exc:
            logger.warning("Pagination stopped at %s: %s", next_url, exc)
            break

    first_result["records"] = records[:record_limit]
    first_result["data"]["technical"]["pages_processed"] = pages_processed
    first_result["data"]["technical"]["record_count"] = len(first_result["records"])

    return first_result


def scrape(
    url: str,
    strategy: str = "automatic",
    custom_fields: dict[str, Any] | None = None,
    max_pages: int = 1,
    max_records: int = 200,
    timeout: int = 20,
    delay: float = 0.0,
) -> ScrapingData:
    safe_url = validate_url(url)

    result = _select_strategy(safe_url, strategy, timeout, custom_fields)

    return _paginate(
        result,
        result["strategy_used"],
        custom_fields,
        max_pages,
        max_records,
        timeout,
        delay,
    )
