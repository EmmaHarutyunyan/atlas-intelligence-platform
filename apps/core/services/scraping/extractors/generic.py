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
    candidate = (
        soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body
    )
    if not candidate:
        return ""
    clone = BeautifulSoup(str(candidate), "html.parser")
    for tag in clone(["script", "style", "noscript", "template", "svg", "nav", "footer"]):
        tag.decompose()
    return clean_text(clone.get_text(" ", strip=True))[:100_000]


def extract_repeated_items(soup: BeautifulSoup, base_url: str) -> list[dict]:
    candidates = []
    for parent in soup.find_all(["ul", "ol", "div", "section"]):
        children = [
            child
            for child in parent.find_all(recursive=False)
            if child.name in {"li", "article", "div"}
        ]
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

        unique = {
            urlparse(absolute_url(base_url, links[0].get("href"))).path
            for _, _, links in signatures
            if links
        }
        if len(unique) < 3:
            continue

        for child, text, links in signatures:
            link = absolute_url(base_url, links[0].get("href")) if links else base_url
            image = child.find("img")
            heading = child.find(["h2", "h3", "h4"])
            title = (
                links[0].get_text(" ", strip=True)
                if links
                else heading.get_text(" ", strip=True) if heading else text
            )
            image_source = image.get("src") or image.get("data-src") if image else ""
            candidates.append(
                {
                    "title": clean_text(title[:500]),
                    "url": link,
                    "image_url": absolute_url(base_url, image_source) if image_source else "",
                    "description": text[:2000],
                    "record_type": "listing_item",
                }
            )
        break

    return candidates[:200]


def extract_product(soup: BeautifulSoup, structured: list, page_url: str) -> dict:
    items = find_schema(structured, {"Product"})
    product = items[0] if items else {}
    offers = product.get("offers", {})
    aggregate = product.get("aggregateRating", {})

    image = first_value(product.get("image"))
    title = first_value(product.get("name"))
    if not title:
        og_title = soup.find("meta", property="og:title")
        title = first_value(og_title.get("content") if og_title else "")

    price = first_value(offers.get("price")) if isinstance(offers, dict) else ""
    currency = first_value(offers.get("priceCurrency")) if isinstance(offers, dict) else ""
    availability = first_value(offers.get("availability")) if isinstance(offers, dict) else ""
    brand = first_value(product.get("brand"))

    return {
        "title": str(title)[:500],
        "url": page_url,
        "image_url": absolute_url(page_url, str(image)) if image else "",
        "record_type": "product",
        "description": str(first_value(product.get("description")))[:2000],
        "attributes": {
            "price": str(price),
            "currency": str(currency),
            "availability": str(availability),
            "rating": (
                str(first_value(aggregate.get("ratingValue")))
                if isinstance(aggregate, dict)
                else ""
            ),
            "review_count": (
                str(first_value(aggregate.get("reviewCount")))
                if isinstance(aggregate, dict)
                else ""
            ),
            "brand": str(brand),
            "category": str(first_value(product.get("category"))),
            "sku": str(first_value(product.get("sku"))),
        },
    }


def extract_article(soup: BeautifulSoup, structured: list, page_url: str) -> dict:
    items = find_schema(structured, {"Article", "NewsArticle", "BlogPosting"})
    article = items[0] if items else {}
    title = first_value(article.get("headline")) if article else ""

    if not title:
        heading = soup.find("h1") or soup.title
        title = clean_text(heading.get_text(" ", strip=True) if heading else "")

    author = first_value(article.get("author"))
    date = first_value(article.get("datePublished"))
    image = first_value(article.get("image"))

    return {
        "title": str(title)[:500],
        "url": page_url,
        "image_url": absolute_url(page_url, str(image)) if image else "",
        "record_type": "article",
        "description": str(first_value(article.get("description")))[:2000],
        "attributes": {
            "author": str(author),
            "publication_date": str(date),
            "category": str(first_value(article.get("articleSection"))),
        },
    }


def _extract_title(soup: BeautifulSoup) -> str:
    heading = soup.find("h1") or soup.find("title")
    return clean_text(heading.get_text(" ", strip=True) if heading else "")[:500]


def _extract_headings(soup: BeautifulSoup) -> list[dict]:
    result = []
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = clean_text(heading.get_text(" ", strip=True))
        if text:
            result.append({"level": heading.name, "text": text})
    return result


def _extract_links(soup: BeautifulSoup, page_url: str) -> list[dict]:
    links = []
    page_domain = urlparse(page_url).netloc

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href")
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        target = absolute_url(page_url, href)
        links.append(
            {
                "text": clean_text(anchor.get_text(" ", strip=True)),
                "url": target,
                "internal": urlparse(target).netloc == page_domain,
            }
        )

    return links


def _extract_images(soup: BeautifulSoup, page_url: str) -> list[dict]:
    images = []
    for img in soup.find_all("img"):
        source = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not source:
            continue

        images.append(
            {
                "url": absolute_url(page_url, source),
                "alt": clean_text(img.get("alt", "")),
                "title": clean_text(img.get("title", "")),
            }
        )
    return images


def _extract_tables(soup: BeautifulSoup) -> list[dict]:
    tables = []
    for table in soup.find_all("table"):
        rows = [
            [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            for row in table.find_all("tr")
        ]
        rows = [row for row in rows if row]
        if rows:
            tables.append(
                {
                    "rows": rows,
                    "row_count": len(rows),
                    "column_count": max(map(len, rows)),
                }
            )
    return tables


def _extract_lists(soup: BeautifulSoup) -> list[dict]:
    result = []
    for element in soup.find_all(["ul", "ol"]):
        items = [
            clean_text(item.get_text(" ", strip=True))
            for item in element.find_all("li", recursive=False)
        ]
        items = [item for item in items if item]
        if items:
            result.append(
                {
                    "type": element.name,
                    "items": items,
                    "count": len(items),
                }
            )
    return result


def _extract_custom_fields(soup: BeautifulSoup, custom_fields: dict | None) -> dict:
    custom = {}
    for field, selector in (custom_fields or {}).items():
        if not isinstance(selector, str):
            continue

        node = soup.select_one(selector)
        if not node:
            continue

        if node.name in {"img", "meta"}:
            custom[field] = node.get("src") or node.get("content", "")
        else:
            custom[field] = clean_text(node.get_text(" ", strip=True))
    return custom


def _detect_emails_and_prices(content: str) -> dict:
    emails = sorted(
        set(
            re.findall(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                content,
            )
        )
    )
    prices = sorted(
        set(
            re.findall(
                r"(?:[$€£¥₹]\s?\d+(?:[.,]\d{1,2})?"
                r"|\d+(?:[.,]\d{1,2})?\s?"
                r"(?:USD|EUR|GBP|AMD|RUB|JPY|INR))",
                content,
                re.I,
            )
        )
    )
    return {"emails": emails, "prices": prices}


def _detect_record_type(product, article, listing: list) -> str:
    if product:
        return "product"
    if article:
        return "article"
    if len(listing) >= 3:
        return "listing"
    return "page"


def _build_records(
    listing: list,
    product,
    article,
    title: str,
    page_url: str,
    detected_type: str,
    description: str,
    content: str,
    structured: list,
) -> list[dict]:
    if listing:
        return list(listing)

    base = (
        product
        or article
        or {
            "title": title,
            "url": page_url,
            "record_type": detected_type,
            "description": description,
            "attributes": {},
        }
    )
    base["content"] = content
    base["structured_data"] = structured
    return [base]


def _build_page_data(
    html: str,
    page_url: str,
    strategy: str,
    title: str,
    description: str,
    canonical: str,
    language: str,
    meta: dict,
    headings: list,
    links: list,
    images: list,
    structured: list,
    tables: list,
    lists: list,
    detected: dict,
    content: str,
    custom: dict,
) -> dict:
    return {
        "page": {
            "title": title,
            "description": description[:2000],
            "url": page_url,
            "canonical_url": canonical,
            "domain": urlparse(page_url).netloc,
            "language": language,
        },
        "headings": headings,
        "links": links[:1000],
        "images": images[:500],
        "metadata": meta,
        "open_graph": {key[3:]: value for key, value in meta.items() if key.startswith("og:")},
        "twitter_card": {
            key[8:]: value for key, value in meta.items() if key.startswith("twitter:")
        },
        "structured_data": structured,
        "tables": tables,
        "lists": lists[:200],
        "detected": detected,
        "statistics": {
            "characters": len(content),
            "words": len(content.split()),
            "sentences": len(re.findall(r"[.!?]+", content)),
            "headings": len(headings),
            "links": len(links),
            "images": len(images),
            "tables": len(tables),
            "lists": len(lists),
        },
        "technical": {"strategy": strategy, "html_size": len(html)},
        "custom_fields": custom,
    }


def extract_page(
    html: str, page_url: str, strategy: str, custom_fields: dict | None = None
) -> dict:
    soup = BeautifulSoup(html, "lxml")
    structured = json_ld(soup)
    meta = metadata(soup)

    title = _extract_title(soup)
    description = meta.get("description") or meta.get("og:description", "")
    canonical_tag = soup.find("link", rel="canonical")
    canonical = absolute_url(page_url, canonical_tag.get("href")) if canonical_tag else ""
    language = soup.html.get("lang", "") if soup.html else ""

    headings = _extract_headings(soup)
    links = _extract_links(soup, page_url)
    images = _extract_images(soup, page_url)
    tables = _extract_tables(soup)
    lists = _extract_lists(soup)
    content = extract_text(soup)
    detected = _detect_emails_and_prices(content)

    product = (
        extract_product(soup, structured, page_url)
        if find_schema(structured, {"Product"})
        else None
    )
    article = (
        extract_article(soup, structured, page_url)
        if find_schema(structured, {"Article", "NewsArticle", "BlogPosting"})
        else None
    )
    listing = extract_repeated_items(soup, page_url)
    custom = _extract_custom_fields(soup, custom_fields)

    signals = sum(bool(value) for value in [title, content, structured, headings, links])
    confidence = "High" if signals >= 5 else "Medium" if signals >= 3 else "Low"
    detected_type = _detect_record_type(product, article, listing)
    records = _build_records(
        listing,
        product,
        article,
        title,
        page_url,
        detected_type,
        description,
        content,
        structured,
    )
    data = _build_page_data(
        html,
        page_url,
        strategy,
        title,
        description,
        canonical,
        language,
        meta,
        headings,
        links,
        images,
        structured,
        tables,
        lists,
        detected,
        content,
        custom,
    )

    return {
        "title": title,
        "url": page_url,
        "content": content,
        "data": data,
        "records": records,
        "record_type": detected_type,
        "confidence": confidence,
        "structured_data": structured,
    }


def record_hash(record: dict) -> str:
    payload = json.dumps(
        {
            "url": record.get("url", ""),
            "title": record.get("title", ""),
            "content": record.get("content", ""),
            "attributes": record.get("attributes", {}),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
