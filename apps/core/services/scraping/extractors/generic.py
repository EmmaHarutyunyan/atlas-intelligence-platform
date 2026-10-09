import hashlib
import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def absolute_url(base_url: str, value: str | None) -> str:
    return urljoin(base_url, value) if value else base_url


def metadata(soup: BeautifulSoup) -> dict[str, str]:
    result = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property") or tag.get("http-equiv")
        content = tag.get("content")
        if name and content:
            result[name.lower()] = clean_text(content)
    return result


def json_ld(soup: BeautifulSoup) -> list:
    result = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.get_text(strip=True)
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, list):
            result.extend(value)
        else:
            result.append(value)
    return result


def _schema_type(value) -> str:
    if isinstance(value, dict):
        schema = value.get("@type", "")
        if isinstance(schema, list):
            return str(schema[0]) if schema else ""
        return str(schema)
    return ""


def find_schema(data: list, names: set[str]) -> list[dict]:
    matches = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if _schema_type(item) in names:
            matches.append(item)
        graph = item.get("@graph")
        if isinstance(graph, list):
            matches.extend(find_schema(graph, names))
    return matches


def first_value(value):
    if isinstance(value, list):
        return first_value(value[0]) if value else ""
    if isinstance(value, dict):
        return value.get("name") or value.get("url") or value.get("@id") or ""
    return value or ""


def extract_text(soup: BeautifulSoup) -> str:
    candidate = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body
    if not candidate:
        return ""
    clone = BeautifulSoup(str(candidate), "html.parser")
    for tag in clone(["script", "style", "noscript", "template", "svg", "nav", "footer"]):
        tag.decompose()
    return clean_text(clone.get_text(" ", strip=True))[:100_000]


def extract_repeated_items(soup: BeautifulSoup, base_url: str) -> list[dict]:
    candidates = []
    for parent in soup.find_all(["ul", "ol", "div", "section"]):
        children = [child for child in parent.find_all(recursive=False) if child.name in {"li", "article", "div"}]
        if len(children) < 3 or len(children) > 100:
            continue
        signatures = []
        for child in children:
            links = child.find_all("a", href=True)
            text = clean_text(child.get_text(" ", strip=True))
            if text and (links or child.find("img")):
                signatures.append((child, text, links))
        if len(signatures) < 3:
            continue
        unique = {urlparse(absolute_url(base_url, links[0].get("href"))).path for _, _, links in signatures if links}
        if len(unique) >= 3:
            for child, text, links in signatures:
                link = absolute_url(base_url, links[0].get("href")) if links else base_url
                image = child.find("img")
                candidates.append({
                    "title": clean_text((links[0].get_text(" ", strip=True) if links else child.find(["h2", "h3", "h4"]).get_text(" ", strip=True) if child.find(["h2", "h3", "h4"]) else text)[:500]),
                    "url": link,
                    "image_url": absolute_url(base_url, image.get("src") or image.get("data-src")) if image and (image.get("src") or image.get("data-src")) else "",
                    "description": text[:2000],
                    "record_type": "listing_item",
                })
            break
    return candidates[:200]


def extract_product(soup: BeautifulSoup, structured: list, page_url: str) -> dict:
    items = find_schema(structured, {"Product"})
    product = items[0] if items else {}
    offers = product.get("offers", {}) if isinstance(product, dict) else {}
    aggregate = product.get("aggregateRating", {}) if isinstance(product, dict) else {}
    image = first_value(product.get("image")) if isinstance(product, dict) else ""
    title = first_value(product.get("name")) if isinstance(product, dict) else ""
    if not title:
        title = first_value(soup.find("meta", property="og:title").get("content") if soup.find("meta", property="og:title") else "")
    price = first_value(offers.get("price")) if isinstance(offers, dict) else ""
    currency = first_value(offers.get("priceCurrency")) if isinstance(offers, dict) else ""
    availability = first_value(offers.get("availability")) if isinstance(offers, dict) else ""
    brand = first_value(product.get("brand")) if isinstance(product, dict) else ""
    return {
        "title": str(title)[:500],
        "url": page_url,
        "image_url": absolute_url(page_url, str(image)) if image else "",
        "record_type": "product",
        "description": str(first_value(product.get("description")))[:2000],
        "attributes": {
            "price": str(price), "currency": str(currency), "availability": str(availability),
            "rating": str(first_value(aggregate.get("ratingValue"))) if isinstance(aggregate, dict) else "",
            "review_count": str(first_value(aggregate.get("reviewCount"))) if isinstance(aggregate, dict) else "",
            "brand": str(brand), "category": str(first_value(product.get("category"))) if isinstance(product, dict) else "",
            "sku": str(first_value(product.get("sku"))) if isinstance(product, dict) else "",
        },
    }


def extract_article(soup: BeautifulSoup, structured: list, page_url: str) -> dict:
    items = find_schema(structured, {"Article", "NewsArticle", "BlogPosting"})
    article = items[0] if items else {}
    title = first_value(article.get("headline")) if article else ""
    title = title or clean_text((soup.find("h1") or soup.title).get_text(" ", strip=True) if (soup.find("h1") or soup.title) else "")
    author = first_value(article.get("author")) if article else ""
    date = first_value(article.get("datePublished")) if article else ""
    image = first_value(article.get("image")) if article else ""
    return {
        "title": str(title)[:500], "url": page_url, "image_url": absolute_url(page_url, str(image)) if image else "",
        "record_type": "article", "description": str(first_value(article.get("description")))[:2000],
        "attributes": {"author": str(author), "publication_date": str(date), "category": str(first_value(article.get("articleSection")))},
    }


def _remove_noise(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()


def extract_page(html: str, page_url: str, strategy: str, custom_fields: dict | None = None) -> dict:
    soup = BeautifulSoup(html, "lxml")
    structured = json_ld(soup)
    meta = metadata(soup)
    title_tag = soup.find("title")
    h1 = soup.find("h1")
    title = clean_text(h1.get_text(" ", strip=True) if h1 else title_tag.get_text(" ", strip=True) if title_tag else "")[:500]
    description = meta.get("description") or meta.get("og:description", "")
    canonical_tag = soup.find("link", rel="canonical")
    canonical = absolute_url(page_url, canonical_tag.get("href")) if canonical_tag else ""
    language = soup.html.get("lang", "") if soup.html else ""
    og = {k[3:]: v for k, v in meta.items() if k.startswith("og:")}
    twitter = {k[8:]: v for k, v in meta.items() if k.startswith("twitter:")}
    headings = [{"level": h.name, "text": clean_text(h.get_text(" ", strip=True))} for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]) if clean_text(h.get_text())]
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        target = absolute_url(page_url, href)
        links.append({"text": clean_text(a.get_text(" ", strip=True)), "url": target, "internal": urlparse(target).netloc == urlparse(page_url).netloc})
    images = []
    for img in soup.find_all("img"):
        source = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if source:
            images.append({"url": absolute_url(page_url, source), "alt": clean_text(img.get("alt", "")), "title": clean_text(img.get("title", ""))})
    tables = []
    for table in soup.find_all("table"):
        rows = [[clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])] for row in table.find_all("tr")]
        rows = [row for row in rows if row]
        if rows:
            tables.append({"rows": rows, "row_count": len(rows), "column_count": max(map(len, rows))})
    lists = []
    for element in soup.find_all(["ul", "ol"]):
        items = [clean_text(li.get_text(" ", strip=True)) for li in element.find_all("li", recursive=False)]
        items = [item for item in items if item]
        if items:
            lists.append({"type": element.name, "items": items, "count": len(items)})
    content = extract_text(soup)
    emails = sorted(set(re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", content)))
    prices = sorted(set(re.findall(r"(?:[$€£¥₹]\s?\d+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?\s?(?:USD|EUR|GBP|AMD|RUB|JPY|INR))", content, re.I)))
    product = extract_product(soup, structured, page_url) if find_schema(structured, {"Product"}) else None
    article = extract_article(soup, structured, page_url) if find_schema(structured, {"Article", "NewsArticle", "BlogPosting"}) else None
    listing = extract_repeated_items(soup, page_url)

    custom = {}
    for field, selector in (custom_fields or {}).items():
        if not isinstance(selector, str):
            continue
        node = soup.select_one(selector)
        if node:
            custom[field] = clean_text(node.get_text(" ", strip=True)) if node.name not in {"img", "meta"} else node.get("src") or node.get("content", "")

    signals = sum(bool(value) for value in [title, content, structured, headings, links])
    confidence = "High" if signals >= 5 else "Medium" if signals >= 3 else "Low"
    detected_type = "product" if product else "article" if article else "listing" if len(listing) >= 3 else "page"

    records = []
    if listing:
        records.extend(listing)
    else:
        base = product or article or {"title": title, "url": page_url, "record_type": detected_type, "description": description, "attributes": {}}
        base["content"] = content
        base["structured_data"] = structured
        records.append(base)

    data = {
        "page": {"title": title, "description": description[:2000], "url": page_url, "canonical_url": canonical, "domain": urlparse(page_url).netloc, "language": language},
        "headings": headings, "links": links[:1000], "images": images[:500], "metadata": meta, "open_graph": og, "twitter_card": twitter,
        "structured_data": structured, "tables": tables, "lists": lists[:200],
        "detected": {"emails": emails, "prices": prices},
        "statistics": {"characters": len(content), "words": len(content.split()), "sentences": len(re.findall(r"[.!?]+", content)), "headings": len(headings), "links": len(links), "images": len(images), "tables": len(tables), "lists": len(lists)},
        "technical": {"strategy": strategy, "html_size": len(html)}, "custom_fields": custom,
    }
    return {"title": title, "url": page_url, "content": content, "data": data, "records": records, "record_type": detected_type, "confidence": confidence, "structured_data": structured}


def record_hash(record: dict) -> str:
    payload = json.dumps({"url": record.get("url", ""), "title": record.get("title", ""), "content": record.get("content", ""), "attributes": record.get("attributes", {})}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()
