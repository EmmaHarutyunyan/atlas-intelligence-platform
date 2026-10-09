from .scraping import scrape


class ScraperError(Exception):
    pass


def scrape_website(url, strategy="beautifulsoup", custom_fields=None):
    try:
        result = scrape(url, strategy, custom_fields)
    except Exception as exc:
        raise ScraperError(str(exc)) from exc
    return {
        "title": result["title"], "url": result["url"], "content": result["content"],
        "data": result["data"], "content_hash": result["records"][0]["content_hash"] if result["records"] else "",
    }
