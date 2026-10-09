from dataclasses import dataclass

import requests

from apps.core.services.scraping.exceptions import FetchError
from apps.core.services.scraping.validators import validate_url

USER_AGENT = "AtlasIntelligencePlatform/1.0 (+https://github.com/)"


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str
    text: str
    encoding: str | None
    headers: dict[str, str]


def fetch(url: str, timeout: int = 20, max_redirects: int = 5) -> FetchResult:
    current = validate_url(url)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})

    try:
        for _ in range(max_redirects + 1):
            current = validate_url(current)
            response = session.get(current, timeout=timeout, allow_redirects=False)

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                if not location:
                    raise FetchError("The website returned an invalid redirect.")
                from urllib.parse import urljoin

                current = urljoin(current, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise FetchError("The URL did not return an HTML page.")
            return FetchResult(
                url=response.url,
                status_code=response.status_code,
                content_type=content_type,
                text=response.text,
                encoding=response.encoding,
                headers=dict(response.headers),
            )
    except requests.Timeout as exc:
        raise FetchError("The website request timed out.") from exc
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else "unknown"
        raise FetchError(f"The website returned HTTP {code}.") from exc
    except requests.RequestException as exc:
        raise FetchError("The website could not be reached.") from exc

    raise FetchError("Too many redirects were encountered.")
