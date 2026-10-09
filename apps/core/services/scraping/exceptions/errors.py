class ScrapingError(Exception):
    """Base exception for user-facing scraping failures."""


class UnsafeURLError(ScrapingError):
    pass


class InvalidURLError(ScrapingError):
    pass


class FetchError(ScrapingError):
    pass


class JavaScriptRequiredError(ScrapingError):
    pass


class ExtractionError(ScrapingError):
    pass
