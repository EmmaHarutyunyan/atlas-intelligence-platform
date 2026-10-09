from urllib.parse import urljoin, urlparse

from apps.core.services.scraping.validators import validate_url

NEXT_LABELS = {"next", "next page", "older", "older posts", "›", "→"}


def find_next_url(data: dict, current_url: str) -> str | None:
    for link in data.get("links", []):
        text = (link.get("text") or "").strip().lower()
        if text in NEXT_LABELS or "next" in text:
            target = link.get("url")
            if target and urlparse(target).netloc == urlparse(current_url).netloc:
                return validate_url(target)
    return None
